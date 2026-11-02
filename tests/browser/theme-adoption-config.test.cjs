const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const entry = path.join(__dirname, 'theme-adoption.cjs');

test('shared recorded interpreter resolver exists without starting the CLI', () => {
    const harness = fs.existsSync(entry) ? require(entry) : {};
    assert.equal(typeof harness.resolveCompanionPython, 'function');
});
