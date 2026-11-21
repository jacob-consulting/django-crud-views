// Checker/writer regressions use isolated fixtures; never write historical evidence.
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

// Compact capture bytes and Git state are isolated in memory: never write historical PNGs.
const compactDefault = '.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m/browser-captures';
const compactLocal = '.planning/phases/06.44-css-tokens-for-manage-pages-and-formsets-with-bootstrap-fall/evidence/compact-captures';
const compactWriter = source.slice(source.indexOf('async function compactCapture('), source.indexOf("(argv.includes('--check-evidence')"));
function compactSample({flag, destination = compactDefault, ignored = true, tracked = false, realFiles = false} = {}) {
    const bytes = new Map(), calls = [], writes = [];
    const mockFs = {...fs,
        readFileSync(file, ...args) {
            if (!realFiles && String(file).endsWith('.png')) {
                assert(bytes.has(file), `Missing fixture PNG: ${file}`);
                return bytes.get(file);
            }
            return fs.readFileSync(file, ...args);
        },
        lstatSync(file, options) {
            if (!realFiles && String(file).endsWith('.png')) {
                return bytes.has(file) ? {isFile: () => true} : undefined;
            }
            return fs.lstatSync(file, options);
        },
        mkdirSync(...args) {if (realFiles) fs.mkdirSync(...args);},
    };
    const mockCp = {...require('node:child_process'), spawnSync(command, args) {
        assert.equal(command, 'git'); calls.push(args);
        if (args[0] === 'check-ignore') return {status: ignored ? 0 : 1};
        if (args[0] === 'ls-files') return {status: 0, stdout: tracked ? args.at(-1) + '\n' : ''};
        throw Error(`Unexpected Git command: ${args}`);
    }};
    const api = vm.runInNewContext(checker + compactWriter + `
        const record = JSON.parse(fs.readFileSync(${JSON.stringify(compactDefault + '/../browser-lifecycle.json')}));
        record.sourceHashes = hashes();
        ({record, validateEvidence, compactCapture});
    `, {require: name => name === 'node:fs' ? mockFs : name === 'node:child_process' ? mockCp : require(name),
        __dirname, console, structuredClone,
        process: {argv: [process.execPath, 'conditional-formsets.cjs', '--case', 'compact-lifecycle',
            ...(flag === undefined ? [] : ['--compact-capture-root', flag])],
        env: {...process.env, CV_FOCUS_NODE: process.execPath}, execPath: process.execPath, chdir() {}}});
    for (const capture of api.record.cases[0].captures) {
        capture.path = `${destination}/compact-lifecycle/${path.basename(capture.path)}`;
        const body = Buffer.from(`unit fixture ${capture.path}`);
        bytes.set(capture.path, body);
        if (realFiles) {
            fs.mkdirSync(path.dirname(capture.path), {recursive: true});
            fs.writeFileSync(capture.path, body);
        }
        capture.sha256 = require('node:crypto').createHash('sha256').update(body).digest('hex');
    }
    const page = {async screenshot({path: file}) {
        writes.push(file);
        bytes.set(file, Buffer.from('new screenshot'));
        if (realFiles) fs.writeFileSync(file, 'new screenshot');
    }};
    return {...api, bytes, calls, writes, page};
}

test('compact default accepts historical paths without override', () => {
    const {record, validateEvidence} = compactSample(); validateEvidence(record);
});
test('compact override accepts local receipt paths', () => {
    const {record, validateEvidence} = compactSample({flag: compactLocal, destination: compactLocal});
    validateEvidence(record);
});
for (const options of [{destination: compactLocal}, {flag: compactLocal}]) {
    test(`compact rejects mismatched root ${JSON.stringify(options)}`, () => {
        const {record, validateEvidence} = compactSample(options);
        assert.throws(() => validateEvidence(record));
    });
}
for (const badPath of ['../outside', '/tmp/cv-outside-captures']) {
    test(`compact rejects outside override ${badPath}`, () => {
        assert.throws(() => compactSample({flag: badPath}));
    });
}
for (const [name, corrupt] of [
    ['traversal', s => {s.record.cases[0].captures[0].path = `${compactDefault}/compact-lifecycle/../compact-lifecycle/invalid-390.png`;}],
    ['nested directory', s => {s.record.cases[0].captures[0].path = `${compactDefault}/compact-lifecycle/extra/invalid-390.png`;}],
    ['missing PNG', s => s.bytes.delete(s.record.cases[0].captures[0].path)],
    ['stale PNG', s => s.bytes.set(s.record.cases[0].captures[0].path, Buffer.from('changed'))],
    ['stale source', s => {s.record.sourceHashes[Object.keys(s.record.sourceHashes)[0]] = 'stale';}],
]) {
    test(`compact rejects ${name}`, () => {
        const sample = compactSample(); sample.validateEvidence(sample.record);
        const originalPath = sample.record.cases[0].captures[0].path;
        corrupt(sample);
        if (name === 'traversal' || name === 'nested directory') {
            sample.bytes.set(sample.record.cases[0].captures[0].path, sample.bytes.get(originalPath));
        }
        assert.throws(() => sample.validateEvidence(sample.record));
    });
}
for (const options of [{ignored: false}, {flag: compactLocal, destination: compactLocal, tracked: true}]) {
    test(`compact rejects unsafe Git destination ${JSON.stringify(options)}`, () => {
        const {record, validateEvidence} = compactSample(options);
        assert.throws(() => validateEvidence(record));
    });
}
for (const flag of [undefined, compactLocal]) {
    test(`compact writer and checker agree for ${flag ?? 'default'}`, async () => {
        const sample = compactSample({flag, destination: flag ?? compactDefault});
        const result = sample.record.cases[0]; result.captures.length = 0;
        for (const name of ['invalid-390', 'invalid-1280', 'saved-390', 'saved-1280']) {
            await sample.compactCapture(sample.page, result, name, Number(name.split('-')[1]), {unit: true});
        }
        assert.equal(sample.writes[0], `${flag ?? compactDefault}/compact-lifecycle/invalid-390.png`);
        sample.validateEvidence(sample.record);
        if (flag) {
            const firstChecks = sample.calls.slice(0, 8);
            assert.equal(firstChecks.filter(args => args[0] === 'check-ignore').length, 4);
            assert.equal(firstChecks.filter(args => args[0] === 'ls-files').length, 4);
        }
    });
}
for (const unsafe of [{ignored: false}, {tracked: true}]) {
    test(`compact writer rejects unsafe override before screenshot ${JSON.stringify(unsafe)}`, async () => {
        const sample = compactSample({flag: compactLocal, destination: compactLocal, ...unsafe});
        const result = sample.record.cases[0]; result.captures.length = 0;
        await assert.rejects(sample.compactCapture(sample.page, result, 'invalid-390', 390, {unit: true}));
        assert.deepEqual(sample.writes, []);
    });
}
test('compact default writer preserves tracked historical destination behavior', async () => {
    const sample = compactSample({tracked: true});
    const result = sample.record.cases[0]; result.captures.length = 0;
    await sample.compactCapture(sample.page, result, 'invalid-390', 390, {unit: true});
    assert.equal(sample.writes.length, 1);
});

for (const kind of ['symlink', 'dangling symlink', 'directory']) {
    for (const mode of ['writer', 'checker']) {
        test(`compact override ${mode} rejects later ${kind} leaf before writing`, async t => {
            const root = path.resolve(__dirname, '../..');
            const temporary = fs.mkdtempSync(path.join(root, '.compact-capture-test-'));
            t.after(() => fs.rmSync(temporary, {recursive: true, force: true}));
            const destination = path.relative(root, temporary);
            // Git results are isolated; leaf inspection and screenshot file writes use the real filesystem.
            const sample = compactSample({flag: destination, destination, realFiles: true});
            sample.validateEvidence(sample.record);
            const result = sample.record.cases[0];
            const later = result.captures.at(-1).path;
            const protectedFile = path.join(temporary, 'protected.txt');
            fs.writeFileSync(protectedFile, 'protected target');
            const missingFile = path.join(temporary, 'missing.txt');
            fs.unlinkSync(later);
            if (kind === 'directory') fs.mkdirSync(later);
            else fs.symlinkSync(kind === 'symlink' ? protectedFile : missingFile, later);
            if (kind === 'symlink') {
                // A matching digest must not allow the checker to accept a symlink.
                result.captures.at(-1).sha256 = require('node:crypto').createHash('sha256')
                    .update('protected target').digest('hex');
            }
            if (mode === 'writer') {
                result.captures.length = 0;
                await assert.rejects(sample.compactCapture(sample.page, result, 'invalid-390', 390, {unit: true}),
                    /regular file/);
            } else {
                assert.throws(() => sample.validateEvidence(sample.record), /regular file/);
            }
            assert.deepEqual(sample.writes, []);
            assert.equal(fs.readFileSync(protectedFile, 'utf8'), 'protected target');
            assert.equal(fs.existsSync(missingFile), false);
        });
    }
}
