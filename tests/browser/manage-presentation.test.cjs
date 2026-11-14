'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {CSP, preflight, declarations, assetFor, validateEvidence, validateAssets, requiredCases, uiMappings, startOwned} = require('./manage-presentation.cjs');
const digest = 'a'.repeat(64);
function valid() {
    return {cases: requiredCases('all').map(id => ({id, passed: true, facts: {verified: true}})), preflight: {status: 'passed'}, csp: CSP,
        ui: uiMappings(), screenshots: requiredCases('all').map(id => ({case: id, sha256: digest})),
        failures: [], requiredAssets: ['manage.js', 'bootstrap.css'], assets: ['manage.js', 'bootstrap.css'].map(url => ({url, status: 200, sha256: digest})),
        cleanup: [{stopped: true, databaseRemoved: true}], sources: {files: Object.fromEntries(Array.from({length: 11}, (_, i) => [i, digest]))}};
}
test('empty or incomplete evidence never passes', () => {
    assert.throws(() => validateEvidence({cases: []}, 'all'), /Missing case/);
    validateEvidence(valid(), 'all');
    for (const id of requiredCases('all')) {
        const report = valid(); report.cases = report.cases.filter(item => item.id !== id);
        assert.throws(() => validateEvidence(report, 'all'), /Missing case/);
    }
});
test('all 52 exact UI source IDs require passed cases and actual captures/DOM facts', () => {
    const coverage = fs.readFileSync(path.resolve(__dirname, '../../.planning/phases/06.33-structured-manage-page-366/COVERAGE.md'), 'utf8');
    const ids = [...coverage.matchAll(/^\| ((?:permissions|views|presentation|facts|checks|defaults|help)\.[a-z-]+) \|/gm)].map(match => match[1]);
    assert.deepEqual(Object.keys(uiMappings()).sort(), ids.sort());
    for (const mutate of [r => delete r.ui['help.loading'], r => r.ui['help.error'] = ['absent'], r => r.screenshots.pop(), r => r.cases[0].facts = {}]) {
        const report = valid(); mutate(report); assert.throws(() => validateEvidence(report, 'all'));
    }
});
test('assets, CSP, errors, sources and owned cleanup are mandatory', () => {
    for (const mutate of [r => r.assets.pop(), r => r.assets[0].status = 404, r => r.cleanup[0].stopped = false,
        r => r.cleanup[0].databaseRemoved = false, r => r.failures.push('CSP error'), r => r.csp += " 'unsafe-inline'",
        r => r.preflight.status = 'environment-blocked', r => r.sources.files = {}]) {
        const report = valid(); mutate(report); assert.throws(() => validateEvidence(report, 'all'));
    }
    assert.throws(() => validateAssets([], []));
});
test('startup timeout cleans only owned process/data and retains diagnostics', async () => {
    const script = "const fs=require('node:fs');fs.writeFileSync(process.argv.at(-1)+'/owned.sqlite3','test');console.error('fixture-start');setInterval(()=>{},1000)";
    await assert.rejects(startOwned(process.execPath, ['-e', script, '--'], 250), error => {
        assert.match(error.message, /startup timed out/); assert.match(error.logs.stderr, /fixture-start/);
        assert(error.cleanup.stopped && error.cleanup.databaseRemoved); assert(!fs.existsSync(error.cleanup.directory));
        assert.throws(() => process.kill(error.cleanup.pid, 0), /ESRCH/); return true;
    });
});
test('missing executable and early startup failure are cleaned', async () => {
    for (const [executable, args] of [['/nonexistent/cv-manage-python', []], [process.execPath, ['-e', "console.error('early failure');process.exit(2)", '--']]]) {
        await assert.rejects(startOwned(executable, args), error => {
            assert(error.cleanup.stopped && error.cleanup.databaseRemoved); return true;
        });
    }
});
test('missing/mismatched cached bytes and undeclared remote URLs fail closed', () => {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-manage-cache-test-'));
    try {
        assert.throws(() => preflight(directory));
        fs.writeFileSync(path.join(directory, 'asset'), 'wrong');
        fs.writeFileSync(path.join(directory, 'assets.json'), JSON.stringify({assets: {[declarations()[0].url]: {file: 'asset', sha256: digest}}}));
        assert.throws(() => preflight(directory), /digest mismatch/);
        assert.throws(() => assetFor(new Map(), 'https://unexpected.invalid/font.woff2'), /Undeclared/);
    } finally {fs.rmSync(directory, {recursive: true, force: true});}
});
