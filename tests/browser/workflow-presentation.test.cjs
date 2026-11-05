'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {validateEvidence, validateAssets, requiredCases, startOwned} = require('./workflow-presentation.cjs');

test('empty execution cannot pass workflow acceptance', () => {
    assert.throws(() => validateEvidence({cases: [], failures: [], cleanup: []}, 'smoke'), /Missing case/);
});

test('each required case and both owned cleanups are mandatory', () => {
    const report = {cases: requiredCases('all').map(id => ({id, passed: true})), failures: [],
        cleanup: [{stopped: true, databaseRemoved: true}, {stopped: true, databaseRemoved: true}]};
    validateEvidence(report, 'all');
    report.cases.pop();
    assert.throws(() => validateEvidence(report, 'all'), /Missing case/);
});

test('startup timeout stops only the owned process and removes its temporary database', async () => {
    const script = `const fs=require('node:fs');const dir=process.argv.at(-1);
        fs.writeFileSync(dir+'/owned.sqlite3','fixture'); console.error('startup fixture'); setInterval(()=>{},1000);`;
    await assert.rejects(startOwned(process.execPath, ['-e', script, '--'], 150), error => {
        assert.match(error.message, /startup timed out/);
        assert(error.cleanup.stopped && error.cleanup.databaseRemoved);
        assert(!fs.existsSync(error.cleanup.directory));
        assert.throws(() => process.kill(error.cleanup.pid, 0), /ESRCH/);
        assert.match(error.logs.stderr, /startup fixture/);
        return true;
    });
});

test('asynchronous executable failure retains diagnostics and cleans temporary data', async () => {
    await assert.rejects(startOwned('/nonexistent/cv-workflow-python', []), error => {
        assert.equal(error.code, 'ENOENT');
        assert(error.cleanup.stopped && error.cleanup.databaseRemoved);
        return true;
    });
});

test('missing or failed required stylesheet cannot pass', () => {
    assert.throws(() => validateAssets(['https://example.invalid/theme.css'], []), /Missing required asset/);
    assert.throws(() => validateAssets(['https://example.invalid/theme.css'], [
        {url: 'https://example.invalid/theme.css', status: 404},
    ]), /Failed required asset/);
});
