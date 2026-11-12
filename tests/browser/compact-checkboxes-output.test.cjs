// Exercise the actual runner's capture/output functions without a browser or disk writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const root = path.resolve(__dirname, '../..');
const canonical = '.planning/phases/06.26-issue-351';

function runner(output) {
    const writes = [], files = new Map();
    const fakeFs = {
        ...fs,
        mkdirSync: file => writes.push(['mkdir', file]),
        mkdtempSync: prefix => `${prefix}test-stage`,
        writeFileSync: (file, data) => {writes.push(['write', file]);files.set(file, Buffer.from(data));},
        readFileSync: file => files.has(file) ? files.get(file) : fs.readFileSync(file),
        existsSync: file => files.has(file) || fs.existsSync(file),
        copyFileSync: (from, to) => {writes.push(['copy', to]);files.set(to, files.get(from));},
        rmSync: file => {writes.push(['remove', file]);},
    };
    const sandbox = {
        __dirname, console: {log() {}, error() {}}, Buffer, URL, setTimeout,
        process: {argv: ['node', 'compact-checkboxes.cjs', '--variant', 'current', '--output', output],
            env: process.env, execPath: process.execPath, version: process.version, chdir() {}},
        require: name => name === 'node:fs' ? fakeFs : name === 'node:test' ? () => {} :
            name === 'node:child_process' ? {execFileSync: () => 'test-head\n', spawnSync: () => ({status: 1})} : require(name),
    };
    const source = fs.readFileSync(path.join(__dirname, 'compact-checkboxes.cjs'), 'utf8');
    const api = vm.runInNewContext(source + '\n;({capture, record, finishOutput: typeof finishOutput === "function" ? finishOutput : null});', sandbox);
    return {api, writes, page: {screenshot: async ({path: file}) => fakeFs.writeFileSync(file, 'new screenshot')}};
}

test('temporary report and failed ordinary run never write canonical evidence', async () => {
    const {api, writes, page} = runner('/tmp/checkbox-probe.json');
    await api.capture(page, '390-initial');
    assert(writes.every(([, file]) => !path.resolve(root, file).startsWith(path.resolve(root, canonical) + path.sep)),
        'ordinary capture wrote inside the canonical evidence directory');
    assert.equal(api.record.captures[0].path, '/tmp/checkbox-probe.json.captures/current-390-initial.png');
    assert.equal(api.record.captures[0].trackable, null, 'ordinary captures do not require Git trackability');
    api.record.error = 'injected failure after first screenshot';
    api.finishOutput();
    assert(writes.every(([, file]) => !path.resolve(root, file).startsWith(path.resolve(root, canonical) + path.sep)),
        'failed ordinary run wrote inside the canonical evidence directory');
    assert(writes.some(([operation, file]) => operation === 'write' && file === '/tmp/checkbox-probe.json'));
});

test('a variant mismatch cannot overwrite another canonical report', () => {
    assert.throws(() => runner(`${canonical}/06.26-browser-floor.json`), /variant must match/);
});

test('failed explicit canonical refresh preserves the canonical report and captures', async () => {
    const output = `${canonical}/06.26-browser-current.json`;
    const {api, writes, page} = runner(output);
    await api.capture(page, '390-initial');
    api.record.error = 'injected failure after first screenshot';
    api.finishOutput();
    assert(writes.every(([, file]) => !path.resolve(root, file).startsWith(path.resolve(root, canonical) + path.sep)));
    assert(writes.some(([operation]) => operation === 'remove'), 'staged captures must be cleaned up');
});

test('successful explicit canonical refresh publishes all captures before its report', async () => {
    const output = `${canonical}/06.26-browser-current.json`;
    const {api, writes, page} = runner(path.resolve(root, output));
    for(const name of ['390-initial', '390-invalid', '390-added', '1280-initial', '1280-invalid', '1280-added', '767-nested', '768-nested']) {
        await api.capture(page, name);
    }
    assert(writes.every(([, file]) => !path.resolve(root, file).startsWith(path.resolve(root, canonical) + path.sep)),
        'captures must remain staged until the run passes');
    api.record.completed = true;api.record.passed = true;
    api.finishOutput();
    const copies = writes.filter(([operation]) => operation === 'copy');
    assert.equal(copies.length, 8);
    assert(copies.every(([, file]) => file.startsWith(`${canonical}/browser-captures/current-`)));
    const reportIndex = writes.findIndex(([operation, file]) => operation === 'write' && file === path.resolve(root, output));
    assert(reportIndex > writes.findLastIndex(([operation]) => operation === 'copy'));
    assert.equal(writes.at(-1)[0], 'remove');
});
