const {test} = require('node:test');
const assert = require('node:assert/strict');
const harness = require('./action-tooltips.cjs');
const cp = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

function runStartupFailure(dir, python, output) {
    // Isolate only prerequisites unrelated to starting the owned fixture. Keep
    // the real Python validation, OS spawn, main catch/finally and JSON writer.
    // The subprocess module cache prevents these doubles leaking to other tests.
    fs.writeFileSync(path.join(dir, 'assets.json'), '{}');
    const bootstrap = `
        const shared = require(process.argv[1]), realRuntime = shared.runtime;
        shared.runtime = (variable, ...args) => variable === 'CV_CANCEL_PYTHON'
            ? realRuntime(variable, ...args) : '/unused/browser-runtime';
        shared.loadAssets = () => new Map();
        require(process.argv[2]).main(['--case', 'smoke', '--output', process.argv[3]])
            .catch(error => {console.error(error.stack); process.exitCode = 1;});
    `;
    return cp.spawnSync(process.execPath, ['-e', bootstrap, path.join(__dirname, 'cancel-navigation.cjs'),
        path.join(__dirname, 'action-tooltips.cjs'), output],
        {encoding: 'utf8', timeout: 5000, env: {...process.env,
            CV_CANCEL_PYTHON: python, CV_CANCEL_ASSETS_DIR: dir}});
}

test('smoke evidence rejects missing required cases', () => {
    assert.throws(() => harness.validateEvidence({cases: []}, 'smoke'), /Missing case/);
});
test('full evidence rejects smoke-only results', () => {
    const report = {cases: ['stock-smoke', 'custom-smoke', 'stock-repeat'].map(id => ({id, controls: 1, passed: true})),
        failures: [], cleanup: {stopped: true, databaseRemoved: true}};
    assert.throws(() => harness.validateEvidence(report, 'all'), /Missing case/);
});

test('options reject unknown cases and flags', () => {
    for (const args of [['--case', 'fake'], ['--case'], ['--download'], ['--output', '--case']]) {
        assert.throws(() => harness.options(args));
    }
});
test('stock delegation cannot satisfy migrated root identity', () => {
    assert.throws(() => harness.identity(null, 'custom'), /identity/);
    assert.throws(() => harness.identity('action-leaf', 'stock'), /identity/);
    harness.identity('action-leaf', 'custom');
});
test('missing runtime writes failed evidence', t => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tooltip-runtime-'));
    t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
    const output = path.join(dir, 'failed.json');
    const result = cp.spawnSync(process.execPath, [path.join(__dirname, 'action-tooltips.cjs'), '--case', 'smoke', '--output', output],
        {encoding: 'utf8', env: {...process.env, CV_CANCEL_PYTHON: '/missing/tooltip/python'}});
    assert.equal(result.status, 1);
    const report = JSON.parse(fs.readFileSync(output));
    assert.equal(report.status, 'failed'); assert.match(report.error, /CV_CANCEL_PYTHON/);
});
test('OS spawn failure replaces stale success with failed evidence', t => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tooltip-spawn-'));
    t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
    const python = path.join(dir, 'python'), output = path.join(dir, 'failed.json');
    // This is an executable regular file; the OS rejects its missing interpreter.
    fs.writeFileSync(python, '#!/missing/tooltip/interpreter\n', {mode: 0o755});
    fs.writeFileSync(output, JSON.stringify({status: 'passed', stale: true}));
    const result = runStartupFailure(dir, python, output);
    assert.equal(result.status, 1); assert.equal(result.error, undefined);
    const report = JSON.parse(fs.readFileSync(output));
    assert.equal(report.status, 'failed'); assert.equal(report.stale, undefined);
    assert.match(report.error, /ENOENT/); assert.doesNotMatch(result.stderr, /Unhandled 'error'/);
    assert.equal(report.cleanup.spawned, false); assert.equal(report.cleanup.stopped, true);
});
test('directory runtime override replaces stale success with failed evidence', t => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tooltip-directory-'));
    t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
    const output = path.join(dir, 'failed.json'); fs.writeFileSync(output, JSON.stringify({status: 'passed'}));
    const result = cp.spawnSync(process.execPath, [path.join(__dirname, 'action-tooltips.cjs'), '--case', 'smoke', '--output', output],
        {encoding: 'utf8', timeout: 5000, env: {...process.env, CV_CANCEL_PYTHON: dir}});
    assert.equal(result.status, 1);
    const report = JSON.parse(fs.readFileSync(output)); assert.equal(report.status, 'failed');
    assert.match(report.error, /regular file/); assert.doesNotMatch(result.stderr, /Unhandled 'error'/);
});
test('fixture exiting before readiness records owned process cleanup', t => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tooltip-early-exit-'));
    t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
    const python = path.join(dir, 'python'), output = path.join(dir, 'failed.json');
    fs.writeFileSync(python, '#!/bin/sh\nexit 9\n', {mode: 0o755});
    const result = runStartupFailure(dir, python, output);
    assert.equal(result.status, 1); assert.equal(result.error, undefined);
    const report = JSON.parse(fs.readFileSync(output)); assert.equal(report.status, 'failed');
    assert.match(report.error, /Fixture startup failed/);
    assert.equal(report.cleanup.spawned, true); assert.equal(report.cleanup.stopped, true);
    assert(report.cleanup.pid > 0); assert.throws(() => process.kill(report.cleanup.pid, 0), {code: 'ESRCH'});
});
test('browser close failure still stops only the owned child', async () => {
    const child = cp.spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)']);
    const other = cp.spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)']);
    const report = {status: 'failed', error: 'primary failure'};
    try {
        await harness.cleanup({close: async () => {throw Error('close failed');}},
            {child, ready: {database: '/missing/fixture/database'}, logs: () => ({})}, report);
        assert.equal(report.error, 'primary failure');
        assert.equal(report.cleanup.stopped, true);
        assert.equal(report.cleanup.databaseRemoved, true);
        assert.equal(report.cleanupErrors[0].stage, 'browser.close');
        assert.equal(other.exitCode, null); assert.equal(other.signalCode, null);
    } finally {child.kill(); other.kill();}
});

function fullEvidence(t) {
    const crypto = require('node:crypto'), dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tooltip-evidence-'));
    t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
    fs.mkdirSync(path.join(dir, 'screenshots'));
    const report = {cases: ['stock-smoke', 'custom-smoke', 'stock-repeat'].map(id => ({id, controls: 1, passed: true})),
        failures: [], cleanup: {stopped: true, databaseRemoved: true}, screenshots: []};
    for (const mode of ['stock', 'custom']) {
        for (const name of harness.matrix) report.cases.push({id: `${mode}-${name}`,
            controls: name.startsWith('mixed-') || name === 'modal' || name.startsWith('menu-') ? 3 : 1, passed: true,
            strict: name === 'missing-icon' ? 'False' : 'True', initial: 1, replacement: 1, reopened: 1, disposed: 1, hide: 1});
        for (const kind of ['tooltip', 'menu', 'modal']) {
            const file = `screenshots/${mode}-${kind}.png`, body = Buffer.from('fixture image bytes');
            fs.writeFileSync(path.join(dir, file), body);
            report.screenshots.push({path: file, sha256: crypto.createHash('sha256').update(body).digest('hex')});
        }
    }
    return {report, output: path.join(dir, 'evidence.json'), dir};
}
test('full validation rejects missing, corrupt or non-durable screenshots', t => {
    const f = fullEvidence(t); harness.validateEvidence(f.report, 'all', f.output);
    f.report.screenshots[0].sha256 = 'invalid';
    assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /Screenshot hash/);
    fs.unlinkSync(path.join(f.dir, f.report.screenshots[0].path));
    assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /ENOENT/);
    f.report.screenshots.shift();
    assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /Missing screenshot/);
});
test('full validation rejects zero modal observations and strict leakage', t => {
    const f = fullEvidence(t), modal = f.report.cases.find(item => item.id === 'custom-modal');
    for (const key of ['controls', 'initial', 'replacement', 'reopened', 'disposed', 'hide']) {
        const before = modal[key]; modal[key] = 0;
        assert.throws(() => harness.validateEvidence(f.report, 'all', f.output)); modal[key] = before;
    }
    modal.strict = 'False'; assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /Strict scope/);
});
test('full validation rejects incorrect nonzero specimen counts', t => {
    const f = fullEvidence(t);
    f.report.cases.find(item => item.id === 'stock-mixed-list').controls = 1;
    assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /Incorrect control count/);
});
