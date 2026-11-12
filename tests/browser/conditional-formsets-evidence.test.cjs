// Checker-only mutations of a captured fixture; no browser or evidence file writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const source = fs.readFileSync(path.join(__dirname, 'conditional-formsets.cjs'), 'utf8');
const checker = source.split('// Strict original wrapper stack')[0];
const fixture = '.planning/phases/06.27-choice-driven-conditional-groups-354/evidence/choice-widgets.json';

function sample() {
    return vm.runInNewContext(checker + `
        const record = JSON.parse(fs.readFileSync(${JSON.stringify(fixture)}));
        // Unit-test setup only: isolate outcome validation from source freshness.
        // Actual evidence commands independently require freshly captured hashes.
        record.sourceHashes = hashes();
        ({record, validateEvidence});
    `, {require, __dirname, console, structuredClone,
        process: {argv: [process.execPath, 'conditional-formsets.cjs', '--case', 'choice-widgets'],
            env: {...process.env, CV_FOCUS_NODE: process.execPath}, execPath: process.execPath, chdir() {}}});
}

test('accepts the captured choice outcomes', () => {
    const {record, validateEvidence} = sample();
    validateEvidence(record);
});

const corruptions = {
    'initial-create-edit': o => o.created.value = 'wrong',
    'keyboard-change': o => o.value = 'wrong',
    'shared-active-kept': o => o.groups[0].fields[0].value = 'lost',
    'unsaved-away-back': o => o.groups[1].fields[0].value = 'lost',
    'final-inactive-cleared': o => o.persisted.nullable_text = 'forged',
    'invalid-controller-zero-save': o => o.eventsAfter = o.eventsBefore + 1,
    'active-required-redisplay': o => o.errors = false,
    'exact-prefix-two-forms': o => o.peerDisabled = false,
    'disabled-trusted': o => o.after.number = 999,
    'independent-disabled': o => o.independent = false,
    'native-reset': o => o.value = 'wrong',
    'canceled-reset': o => o.value = 'wrong',
    'modal-422-rebind': o => o.focus.usable = false,
    'unload-listener-cleanup': o => {o.detached = false; o.released = false; o.unchanged = false;},
    'usable-radio-focus': o => o.usable = false,
    'adversarial-token-inert': o => o.executed = true,
};
for (const [id, corrupt] of Object.entries(corruptions)) {
    test(`rejects contradictory ${id} observation even with passed=true`, () => {
        const {record, validateEvidence} = sample();
        validateEvidence(record);
        const assertion = record.cases[0].assertions.find(a => a.id === id);
        corrupt(assertion.detail.observed);
        assert.equal(assertion.passed, true);
        assert.throws(() => validateEvidence(record), /./);
    });
}

for (const [id, outcome, corrupt] of [
    ['initial-create-edit', 'native control count', o => o.initial.controls = 0],
    ['final-inactive-cleared', 'reopened clearing', o => o.reopened.groups[0].fields[0].value = 'forged'],
    ['invalid-controller-zero-save', 'native error', o => o.invalidChoice = false],
    ['invalid-controller-zero-save', 'database preservation', o => o.recordsAfter[0].nullable_text = 'changed'],
    ['disabled-trusted', 'disabled controller', o => o.controllerDisabled = false],
    ['independent-disabled', 'release on active', o => o.snapshot.groups[0].fields[0].disabled = true],
    ['modal-422-rebind', 'unload timing', o => o.unloadedAttached = false],
    ['modal-422-rebind', 'rebound field', o => o.snapshot.groups[0].fields[0].disabled = true],
    ['usable-radio-focus', 'checked radio', o => o.checked = false],
    ['adversarial-token-inert', 'native control count', o => o.controls = 0],
]) {
    test(`rejects contradictory ${id}: ${outcome}`, () => {
        const {record, validateEvidence} = sample();
        validateEvidence(record);
        const cell = record.cases.find(c => c.widget === 'radio');
        corrupt(cell.assertions.find(a => a.id === id).detail.observed);
        assert.throws(() => validateEvidence(record), /./);
    });
}
