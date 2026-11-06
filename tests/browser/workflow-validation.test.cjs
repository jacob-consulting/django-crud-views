'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const {requiredCases, validateEvidence, loadAssets, assetFor} = require('./workflow-validation.cjs');

test('all requires actual label-safety and native Enter cases', () => {
    for (const id of ['label-safety-page', 'label-safety-modal', 'implicit-submit-custom-input-page', 'textarea-enter-page']) {
        assert(requiredCases('all').includes(id), `Missing mandatory browser case: ${id}`);
    }
});

function receipt(selection) {
    return {kind: 'synthetic-validator-control', cases: requiredCases(selection).map(id => ({id, passed: true})),
        failures: [], cleanup: {stopped: true, databaseRemoved: true}, sources: {'fixture.py': 'a'.repeat(64)},
        command: ['/usr/bin/node', '/fixture/harness.cjs', '--case', selection],
        environment: {CV_WORKFLOW_ASSETS_DIR: '/assets'},
        assetManifest: {suppliedDirectory: '/assets', directory: '/assets', path: '/assets/assets.json', sha256: 'a'.repeat(64)}};
}
for (const selection of ['smoke', 'all']) {
    test(`${selection}: complete control accepted`, () => validateEvidence(receipt(selection), selection));
    test(`${selection}: empty receipt rejected`, () => assert.throws(() => validateEvidence({}, selection)));
    for (const id of requiredCases(selection)) test(`${selection}: missing ${id} rejected`, () => {
        const report = receipt(selection); report.cases = report.cases.filter(item => item.id !== id);
        assert.throws(() => validateEvidence(report, selection));
    });
    test(`${selection}: failed case rejected`, () => {
        const report = receipt(selection); report.cases[0].passed = false;
        assert.throws(() => validateEvidence(report, selection));
    });
    test(`${selection}: cleanup required`, () => {
        const report = receipt(selection); report.cleanup.stopped = false;
        assert.throws(() => validateEvidence(report, selection));
    });
    for (const field of ['directory', 'path', 'suppliedDirectory', 'sha256']) test(`${selection}: missing manifest ${field} rejected`, () => {
        const report = receipt(selection); delete report.assetManifest[field];
        assert.throws(() => validateEvidence(report, selection));
    });
    for (const field of ['command', 'environment', 'sources']) test(`${selection}: missing ${field} rejected`, () => {
        const report = receipt(selection); delete report[field];
        assert.throws(() => validateEvidence(report, selection));
    });
    test(`${selection}: asset environment setting required`, () => {
        const report = receipt(selection); report.environment = {};
        assert.throws(() => validateEvidence(report, selection));
    });
}
test('local assets enforce declarations, hashes, SRI, transitive fonts and containment', () => {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-workflow-asset-test-'));
    try {
        const css = Buffer.from('body {background:url(font.woff2)}'), font = Buffer.from('font bytes');
        const sha = body => crypto.createHash('sha256').update(body).digest('hex');
        fs.writeFileSync(path.join(directory, 'style.css'), css); fs.writeFileSync(path.join(directory, 'font.woff2'), font);
        const declarations = [{url: 'https://assets.test/style.css', css: true,
            integrity: 'sha256-' + crypto.createHash('sha256').update(css).digest('base64')}];
        const manifest = {version: 1, assets: {
            'https://assets.test/style.css': {file: 'style.css', sha256: sha(css)},
            'https://assets.test/font.woff2': {file: 'font.woff2', sha256: sha(font)},
        }};
        const write = value => fs.writeFileSync(path.join(directory, 'assets.json'), JSON.stringify(value));
        write(manifest); const assets = loadAssets(directory, declarations); assert.equal(assets.size, 2);
        assert.throws(() => assetFor(assets, 'https://undeclared.test/x.js'));
        assert.throws(() => loadAssets(directory, [{...declarations[0], integrity: 'sha256-invalid'}]));
        for (const mode of ['missing', 'hash', 'undeclared', 'escape']) {
            const changed = structuredClone(manifest);
            if (mode === 'missing') delete changed.assets['https://assets.test/font.woff2'];
            if (mode === 'hash') changed.assets['https://assets.test/style.css'].sha256 = 'bad';
            if (mode === 'undeclared') changed.assets['https://assets.test/extra.js'] = {file: 'style.css', sha256: sha(css)};
            if (mode === 'escape') changed.assets['https://assets.test/style.css'].file = '../outside';
            write(changed); assert.throws(() => loadAssets(directory, declarations), mode);
        }
    } finally {fs.rmSync(directory, {recursive: true, force: true});}
});
