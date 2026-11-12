const {test} = require('node:test');
const assert = require('node:assert/strict');
const {validateEvidence} = require('./choice-example-browser.cjs');

test('rejects success without actual widget coverage and cleanup', () => {
    assert.throws(() => validateEvidence({passed:true}), /./);
});
