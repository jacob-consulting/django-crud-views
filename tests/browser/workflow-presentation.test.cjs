'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {validateEvidence, validateAssets} = require('./workflow-presentation.cjs');

test('empty execution cannot pass workflow acceptance', () => {
    assert.throws(() => validateEvidence({cases: [], failures: [], cleanup: []}, 'smoke'), /Missing case/);
});

test('missing or failed required stylesheet cannot pass', () => {
    assert.throws(() => validateAssets(['https://example.invalid/theme.css'], []), /Missing required asset/);
    assert.throws(() => validateAssets(['https://example.invalid/theme.css'], [
        {url: 'https://example.invalid/theme.css', status: 404},
    ]), /Failed required asset/);
});
