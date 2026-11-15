'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
const harness = fs.existsSync(path.join(__dirname, 'access-trace.cjs')) ? require('./access-trace.cjs') : {};

test('fingerprints include untracked source and required harness bytes', () => {
    assert.equal(typeof harness.sources, 'function', 'Current-byte source fingerprint function is required');
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'access-sources-'));
    try {
        cp.execFileSync('git', ['init', '-q', root]);
        for (const file of [...harness.requiredInputs, 'src/crud_views/untracked.html', 'src/crud_views_guardian/untracked.py']) {
            fs.mkdirSync(path.dirname(path.join(root, file)), {recursive: true});
            fs.writeFileSync(path.join(root, file), file);
        }
        const initial = harness.sources(root);
        assert(Object.hasOwn(initial.files, 'src/crud_views/untracked.html'));
        assert(Object.hasOwn(initial.files, 'tests/browser/access-trace.cjs'));
        cp.execFileSync('git', ['add', 'tests', 'src'], {cwd: root});
        assert.deepEqual(harness.sources(root), initial, 'Staging unchanged bytes does not invalidate evidence');
        fs.writeFileSync(path.join(root, 'src/crud_views/untracked.html'), 'modified');
        assert.notDeepEqual(harness.sources(root), initial);
        fs.writeFileSync(path.join(root, 'src/crud_views/new.py'), 'added');
        assert(Object.hasOwn(harness.sources(root).files, 'src/crud_views/new.py'));
        fs.unlinkSync(path.join(root, harness.requiredInputs[0]));
        assert.throws(() => harness.sources(root), /required|ENOENT/);
    } finally {fs.rmSync(root, {recursive: true, force: true});}
});

test('receipt validation rejects missing cases, false measurements, failed assets and leaks', () => {
    assert.equal(typeof harness.validateEvidence, 'function');
    const digest = 'a'.repeat(64);
    const valid = () => ({selection: 'all', status: 'passed', preflight: {status: 'passed'}, csp: harness.CSP,
        cases: harness.requiredCases('all').map(id => ({id, passed: true, assertions: [{name: 'measured', actual: 1, expected: 1}],
            facts: {width: 390, documentWidth: 390, inline: 0, csp: [], labels: true}})),
        failures: [], cleanup: [{stopped: true, databaseRemoved: true}],
        sources: {files: Object.fromEntries(harness.requiredInputs.map(file => [file, digest]))},
        requiredAssets: ['manage.css'], assets: [{url: 'manage.css', status: 200, sha256: digest}],
        screenshots: harness.requiredCases('all').map(id => ({case: id, path: `${id}.png`, sha256: digest}))});
    harness.validateEvidence(valid());
    for (const mutate of [r => r.cases.pop(), r => r.cases[0].assertions[0].actual = 0,
        r => r.cases[0].facts.documentWidth = 600, r => r.cases[0].facts.inline = 1,
        r => r.cases[0].facts.labels = false, r => r.cases[0].facts.csp.push('blocked'),
        r => r.assets[0].status = 404, r => r.cleanup[0].stopped = false,
        r => r.cleanup[0].databaseRemoved = false, r => r.screenshots.pop(),
        r => r.sources.files = {}, r => r.failures.push('unexpected fetch'), r => r.csp += " 'unsafe-inline'"]) {
        const receipt = valid(); mutate(receipt);
        assert.throws(() => harness.validateEvidence(receipt));
    }
});

test('read-only receipt verification rejects stale bytes and changed captures', () => {
    assert.equal(typeof harness.verifyReceipt, 'function');
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'access-receipt-'));
    try {
        cp.execFileSync('git', ['init', '-q', root]);
        for (const file of harness.requiredInputs) {
            fs.mkdirSync(path.dirname(path.join(root, file)), {recursive: true}); fs.writeFileSync(path.join(root, file), file);
        }
        const receipt = {sources: harness.sources(root), screenshots: [{path: 'capture.png', sha256: harness.sha('capture')}]};
        fs.writeFileSync(path.join(root, 'capture.png'), 'capture');
        harness.verifyReceipt(receipt, root, root, false);
        fs.writeFileSync(path.join(root, harness.requiredInputs[0]), 'changed');
        assert.throws(() => harness.verifyReceipt(receipt, root, root, false), /source/i);
        receipt.sources = harness.sources(root); fs.writeFileSync(path.join(root, 'capture.png'), 'changed');
        assert.throws(() => harness.verifyReceipt(receipt, root, root, false), /capture/i);
    } finally {fs.rmSync(root, {recursive: true, force: true});}
});
