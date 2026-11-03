const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');
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
