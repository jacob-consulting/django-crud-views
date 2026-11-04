const {test} = require('node:test');
const assert = require('node:assert/strict');
const harness = require('./protected-delete.cjs');

test('evidence rejects missing required cases', () => {
    assert.throws(() => harness.validateEvidence({cases: []}, 'smoke'), /case/i);
});
