const {test} = require('node:test');
const assert = require('node:assert/strict');
const cp = require('node:child_process');
const fs = require('node:fs');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const {once} = require('node:events');

// Execute the runner's actual finally/report-writing path, without requiring a
// browser/CDN. The fixture is a real listening child; only browser.close is faulty.
const source = fs.readFileSync(path.join(__dirname, 'presentation.cjs'), 'utf8');
const boundedSource = source.slice(source.indexOf('async function bounded('), source.indexOf('async function preflight('));
const cleanupSource = source.slice(source.lastIndexOf('    } finally {') + '    } finally {'.length,
    source.lastIndexOf('\n    }\n}\nmain().catch'));

async function exercise(t, {close = async () => {}, stubborn = false, startup = false} = {}) {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-presentation-cleanup-'));
    const output = path.join(directory, 'report.json');
    let child, childExit, port;
    t.after(async () => {
        if (child && child.exitCode === null && child.signalCode === null) child.kill('SIGKILL');
        if (childExit) await childExit;
        fs.rmSync(directory, {recursive: true, force: true});
    });
    if (!startup) {
        child = cp.spawn(process.execPath, ['-e', `
            const server = require('node:net').createServer();
            process.on('SIGTERM', () => { ${stubborn ? '' : "server.close(() => process.exit(0));"} });
            server.listen(0, '127.0.0.1', () => process.send(server.address().port));
        `], {stdio: ['ignore', 'pipe', 'pipe', 'ipc']});
        childExit = new Promise((resolve, reject) => {
            child.once('exit', (code, signal) => resolve({code, signal}));
            child.once('error', reject);
        });
        [port] = await once(child, 'message', {signal: AbortSignal.timeout(3000)});
    }
    const report = {status: startup ? 'failed' : 'passed', passed: !startup, cleanup: {}, cases: [],
        ...(startup ? {error: 'original startup failure'} : {})};
    const fakeProcess = {exitCode: startup ? 1 : 0};
    await vm.runInNewContext(`(async () => { ${boundedSource}\n${cleanupSource}\n})()`, {
        browser: startup ? undefined : {close}, child, childExit, report, process: fakeProcess,
        // Exercise the real timeout branch with a shorter clock, keeping tests bounded.
        setTimeout: (fn, ms) => setTimeout(fn, Math.min(ms, 60)), clearTimeout,
        fs, path, output, serverLog: '', console: {log() {}, error() {}},
    }, {timeout: 1000});
    const saved = JSON.parse(fs.readFileSync(output, 'utf8'));
    if (child) {
        assert(child.exitCode !== null || child.signalCode !== null, 'fixture must exit before report is saved');
        assert.throws(() => process.kill(child.pid, 0), {code: 'ESRCH'}, 'fixture must be reaped');
        const socket = net.connect({host: '127.0.0.1', port});
        t.after(() => socket.destroy());
        const [error] = await once(socket, 'error', {signal: AbortSignal.timeout(1000)});
        assert.equal(error.code, 'ECONNREFUSED', 'fixture must release its listening port');
    }
    return {saved, exitCode: fakeProcess.exitCode};
}

for (const [name, close, message] of [
    ['rejection', async () => {throw Error('browser close rejected');}, 'browser close rejected'],
    ['timeout', () => new Promise(() => {}), 'Browser cleanup timed out'],
]) {
    test(`browser close ${name} still terminates and reaps fixture`, {timeout: 5000}, async t => {
        const {saved, exitCode} = await exercise(t, {close});
        assert.equal(saved.status, 'failed');
        assert.equal(saved.passed, false);
        assert.equal(saved.completed, false);
        assert.equal(exitCode, 1);
        assert.equal(saved.cleanup.error, message);
        assert.notEqual(saved.cleanup.browserClosed, true);
        assert.equal(saved.cleanup.reaped, true);
        assert.deepEqual(saved.cleanup.serverExit, {code: 0, signal: null});
    });
}

test('successful cleanup retains a passing report', {timeout: 5000}, async t => {
    const {saved, exitCode} = await exercise(t);
    assert.equal(saved.status, 'passed');
    assert.equal(saved.completed, true);
    assert.equal(exitCode, 0);
    assert.deepEqual(saved.cleanup, {browserClosed: true, serverExit: {code: 0, signal: null}, reaped: true});
});

test('early startup failure retains original failure without resources', {timeout: 5000}, async t => {
    const {saved, exitCode} = await exercise(t, {startup: true});
    assert.equal(saved.status, 'failed');
    assert.equal(saved.error, 'original startup failure');
    assert.equal(saved.completed, false);
    assert.equal(saved.cleanup.reaped, true);
    assert.equal(exitCode, 1);
});

test('browser failure and server timeout retain both errors and reap after SIGKILL', {timeout: 5000}, async t => {
    const {saved, exitCode} = await exercise(t, {
        close: async () => {throw Error('browser close rejected');}, stubborn: true,
    });
    assert.equal(saved.status, 'failed');
    assert.equal(saved.completed, false);
    assert.equal(exitCode, 1);
    assert.match(saved.cleanup.error, /browser close rejected/);
    assert.match(saved.cleanup.error, /Fixture cleanup timed out/);
    assert.equal(saved.cleanup.reaped, true);
    assert.deepEqual(saved.cleanup.serverExit, {code: null, signal: 'SIGKILL'});
});
