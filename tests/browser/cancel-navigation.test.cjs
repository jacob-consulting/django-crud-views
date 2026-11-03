const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const vm = require('node:vm');
const {EventEmitter} = require('node:events');
const harness = require('./cancel-navigation.cjs');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
function fixture(t) {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cancel-assets-test-'));
    t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
    const url = 'https://fixture.invalid/app.js', body = '/* fixture bytes */';
    fs.writeFileSync(path.join(dir, 'app.js'), body);
    const manifest = {version: 1, assets: {[url]: {file: 'app.js', sha256: sha(body)}}};
    const write = () => fs.writeFileSync(path.join(dir, 'assets.json'), JSON.stringify(manifest));
    write();
    return {dir, url, body, manifest, write, declarations: [{url, integrity: null}]};
}
test('missing asset manifest fails closed', t => {
    const f = fixture(t);
    fs.unlinkSync(path.join(f.dir, 'assets.json'));
    assert.throws(() => harness.loadAssets(f.dir, f.declarations), /assets.json/);
});
test('exact local bytes are accepted and undeclared URLs rejected', t => {
    const f = fixture(t), assets = harness.loadAssets(f.dir, f.declarations);
    assert.equal(harness.assetFor(assets, f.url).body.toString(), f.body);
    assert.throws(() => harness.assetFor(assets, 'https://other.invalid/a.js'), /Undeclared external/);
});
test('missing file and incorrect hash fail closed', t => {
    const f = fixture(t);
    f.manifest.assets[f.url].sha256 = '0'.repeat(64); f.write();
    assert.throws(() => harness.loadAssets(f.dir, f.declarations), /SHA-256/);
    fs.unlinkSync(path.join(f.dir, 'app.js'));
    assert.throws(() => harness.loadAssets(f.dir, f.declarations), /app.js/);
});
test('SRI is checked against fixture declaration, not a substituted manifest', t => {
    const f = fixture(t);
    assert.throws(() => harness.loadAssets(f.dir, [{url: f.url, integrity: 'sha384-incorrect'}]), /SRI/);
});
test('manifest paths cannot escape through traversal or symlink', t => {
    const f = fixture(t);
    f.manifest.assets[f.url].file = '../outside.js'; f.write();
    assert.throws(() => harness.loadAssets(f.dir, f.declarations), /containment/);
    fs.symlinkSync(__filename, path.join(f.dir, 'escape.js'));
    f.manifest.assets[f.url].file = 'escape.js'; f.write();
    assert.throws(() => harness.loadAssets(f.dir, f.declarations), /containment/);
});
test('CSS dependencies must be declared and unexpected manifest entries are rejected', t => {
    const f = fixture(t);
    f.manifest.assets['https://other.invalid/tracker.js'] = f.manifest.assets[f.url]; f.write();
    assert.throws(() => harness.loadAssets(f.dir, f.declarations), /Undeclared/);
    delete f.manifest.assets['https://other.invalid/tracker.js'];
    const css = 'url(../font.woff2)';
    fs.writeFileSync(path.join(f.dir, 'app.js'), css);
    f.manifest.assets[f.url].sha256 = sha(css); f.write();
    assert.throws(() => harness.loadAssets(f.dir, [{url: f.url, integrity: null, css: true}]), /Missing declared asset/);
});
test('options reject unknown cases, flags and missing values', () => {
    assert.deepEqual(harness.options(['--case', 'smoke', '--output', '/tmp/result.json']), {case: 'smoke', output: '/tmp/result.json'});
    for (const argv of [['--case', 'fake'], ['--case'], ['--download'], ['--output', '--case']]) {
        assert.throws(() => harness.options(argv));
    }
});
test('default reports live in distinct private directories', t => {
    const first = harness.options([]), second = harness.options([]);
    for (const opts of [first, second]) {
        const directory = path.dirname(opts.output);
        assert.notEqual(directory, os.tmpdir());
        assert.equal(fs.statSync(directory).mode & 0o777, 0o700);
        t.after(() => fs.rmSync(directory, {recursive: true, force: true}));
    }
    assert.notEqual(first.output, second.output);
});
test('sequential operations settle before the next starts and stop after rejection', async () => {
    const events = [];
    await harness.sequence([1, 2], async value => {
        events.push(`start-${value}`);
        await new Promise(resolve => setTimeout(resolve, 5));
        events.push(`end-${value}`);
    });
    assert.deepEqual(events, ['start-1', 'end-1', 'start-2', 'end-2']);
    const failure = new Error('primary scenario');
    await assert.rejects(harness.sequence([3, 4], async value => {
        events.push(`start-${value}`);
        throw failure;
    }), error => error === failure);
    assert.equal(events.at(-1), 'start-3');
});
test('git executable must be an explicit immutable executable file', t => {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'cancel-git-test-'));
    t.after(() => fs.rmSync(directory, {recursive: true, force: true}));
    const file = path.join(directory, 'git');
    fs.writeFileSync(file, 'not executable', {mode: 0o666});
    assert.throws(() => harness.validateExecutable('git'), /absolute/);
    assert.throws(() => harness.validateExecutable(file));
    fs.chmodSync(file, 0o777);
    assert.throws(() => harness.validateExecutable(file), /writable/);
    assert.equal(harness.validateExecutable('/usr/bin/git'), fs.realpathSync('/usr/bin/git'));
});
test('startup readiness handles split output and removes listeners', async () => {
    const child = Object.assign(new EventEmitter(), {stdout: new EventEmitter(), exitCode: null, signalCode: null});
    let stdout = '{"ready":';
    const waiting = harness.waitForReady(child, () => ({stdout, stderr: ''}), 100);
    child.stdout.emit('data');
    stdout += '1234}\n';
    child.stdout.emit('data');
    assert.deepEqual(await waiting, {ready: 1234});
    assert.equal(child.stdout.listenerCount('data'), 0);
    assert.equal(child.listenerCount('exit'), 0);
    assert.equal(child.listenerCount('error'), 0);
});
test('startup timeout and early process exit reject without retaining listeners', async () => {
    const child = Object.assign(new EventEmitter(), {stdout: new EventEmitter(), exitCode: null, signalCode: null});
    const logs = () => ({stdout: '', stderr: 'diagnostic'});
    await assert.rejects(harness.waitForReady(child, logs, 5), /timed out: diagnostic/);
    const waiting = harness.waitForReady(child, logs, 100);
    child.exitCode = 1;
    child.emit('exit');
    await assert.rejects(waiting, /startup failed: diagnostic/);
    assert.equal(child.stdout.listenerCount('data'), 0);
    assert.equal(child.listenerCount('exit'), 0);
});
test('explicit unavailable runtime exits nonzero without browser launch', () => {
    const result = cp.spawnSync(process.execPath, [path.join(__dirname, 'cancel-navigation.cjs')], {
        encoding: 'utf8', env: {...process.env, CV_CANCEL_PYTHON: '/missing/cancel/python'}, timeout: 5000,
    });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /CV_CANCEL_PYTHON/);
});
test('owned process cleanup terminates only the supplied child', async () => {
    const child = cp.spawn(process.execPath, ['-e', 'setInterval(()=>{}, 1000)']);
    const other = cp.spawn(process.execPath, ['-e', 'setInterval(()=>{}, 1000)']);
    try {
        await harness.stopOwned(child);
        assert(child.exitCode !== null || child.signalCode !== null);
        assert.equal(other.exitCode, null);
        assert.equal(other.signalCode, null);
    } finally {child.kill(); other.kill();}
});

async function failedOrchestration({stopFails = false, writeFails = false} = {}) {
    const events = [], output = [], reports = [];
    const primary = Error('injected context failure');
    const child = new EventEmitter();
    Object.assign(child, {pid: 12345, exitCode: null, signalCode: null});
    let databaseExists = true;
    child.kill = signal => {
        events.push('server.kill');
        if (stopFails) throw Error('injected server cleanup failure');
        child.signalCode = signal;
        databaseExists = false;
        child.emit('exit');
    };
    const browser = {
        version: () => 'test-browser',
        newContext: async () => {throw primary;},
        close: async () => {events.push('browser.close'); throw Error('injected browser close failure');},
    };
    const fakeProcess = {argv: ['node', __filename, '--output', '/fixture-report.json'], env: {HOME: '/cached', CV_CANCEL_ASSETS_DIR: '/assets'},
        execPath: process.execPath, version: process.version};
    const sandbox = {
        __dirname, __filename: path.join(__dirname, 'cancel-navigation.cjs'), module: {exports: {}},
        process: fakeProcess, console: {log: text => output.push(JSON.parse(text))}, URL, setTimeout,
        server: {child, ready: {ready: 12345, database: '/fixture.sqlite3', runtime: {
            packagePath: path.resolve(__dirname, '../../src/crud_views'), django: '5.2.0',
        }}, logs: () => ({stdout: '', stderr: ''})},
        require: name => {
            if (name === 'node:fs') return {...fs,
                existsSync: name => name === '/fixture.sqlite3' ? databaseExists : false,
                readFileSync: () => Buffer.from('{}'),
                writeFileSync: (name, text) => {
                    events.push('report.write');
                    if (writeFails) throw Error('injected report write failure');
                    reports.push(JSON.parse(text));
                },
            };
            if (name === 'node:child_process') return {execFileSync: () => 'test-revision'};
            if (name === '/playwright/package.json') return {version: 'test-playwright'};
            if (name === '/playwright') return {chromium: {launch: async () => browser}};
            return require(name);
        },
    };
    // Run the actual main/finally and stopOwned code. Replace only external prerequisites
    // and startup; this test must detect orchestration failures, not just test a helper.
    const source = fs.readFileSync(path.join(__dirname, 'cancel-navigation.cjs'), 'utf8');
    let rejected;
    try {
        await vm.runInNewContext(source + `
            runtime = variable => variable === 'CV_CANCEL_GIT' ? '/usr/bin/git' : '/playwright';
            loadAssets = () => new Map();
            sourceHashes = () => ({});
            startServer = async () => server;
            main();
        `, sandbox);
    } catch (error) {rejected = error;}
    return {events, output, reports, primary, child, fakeProcess, rejected, databaseExists};
}

test('browser close rejection still tears down owned server and finalizes the primary failure report', async () => {
    const result = await failedOrchestration();
    assert.deepEqual(result.events, ['browser.close', 'server.kill', 'report.write']);
    assert.equal(result.rejected, undefined);
    assert.equal(result.fakeProcess.exitCode, 1);
    assert.equal(result.databaseExists, false);
    assert.equal(result.child.signalCode, 'SIGTERM');
    const [report] = result.reports;
    assert.equal(report.status, 'failed');
    assert.equal(report.error, result.primary.stack);
    assert.equal(report.cleanup.stopped, true);
    assert.equal(report.cleanup.databaseRemoved, true);
    assert.deepEqual(report.cleanupErrors.map(error => error.stage), ['browser.close']);
    assert.match(report.cleanupErrors[0].error, /injected browser close failure/);
});

test('secondary teardown and report errors cannot mask the primary orchestration failure', async () => {
    const result = await failedOrchestration({stopFails: true, writeFails: true});
    assert.deepEqual(result.events, ['browser.close', 'server.kill', 'report.write']);
    assert.equal(result.rejected, undefined);
    assert.equal(result.fakeProcess.exitCode, 1);
    const [summary] = result.output;
    assert.equal(summary.status, 'failed');
    assert.equal(summary.error, result.primary.stack);
    assert.deepEqual(summary.cleanupErrors.map(error => error.stage), ['browser.close', 'server.stop', 'report.write']);
});
