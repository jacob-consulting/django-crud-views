const assert = require('node:assert/strict');

function validateEvidence(record) {
    assert.equal(record.passed, true);
}

module.exports = {validateEvidence};
