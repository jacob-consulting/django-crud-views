// Bounded real-page acceptance runner. Self-tests never start Django or Chromium.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const REQUIRED = {upstream: ['standalone', 'ordinary', 'compact', 'lifecycle', 'mutation', 'navigation']};
function parseArgs(args) { return {target: args[args.indexOf('--target') + 1]}; }
async function selfTest(target) {
    const started = Date.now();
    let count = 0;
    const test = (name, callback) => { callback(); count++; console.log(`ok ${name}`); };
    test('parse target', () => assert.equal(parseArgs(['--self-test', '--target', target]).target, target));
    for (const args of [['--target', 'other'], ['--unknown'], ['--self-test', '--output', 'x'], ['--target']]) {
        test(`reject ${args.join(' ')}`, () => assert.throws(() => parseArgs(args)));
    }
    const sources = {upstream: '/expected/upstream', downstream: target === 'downstream' ? '/expected/downstream' : null};
    const valid = {target, sources, sourceHashes: {'upstream/src/example.py': 'abc'},
        scenarios: REQUIRED[target].map(id => ({id, assertions: [{id: 'observed', passed: true}], dbConfirmed: true})),
        cleanup: {reaped: true, temporaryRemoved: true}};
    test('accept complete target', () => validateEvidence(valid, target, sources, valid.sourceHashes));
    for (const [name, corrupt] of [
        ['zero scenarios', r => r.scenarios = []],
        ['missing scenario', r => r.scenarios.pop()],
        ['false assertion', r => r.scenarios[0].assertions[0].passed = false],
        ['false database proof', r => r.scenarios[0].dbConfirmed = false],
        ['wrong source', r => r.sources.upstream = '/wrong'],
        ['stale fingerprint', r => r.sourceHashes = {}],
        ['failed cleanup', r => r.cleanup.reaped = false],
    ]) test(name, () => { const r = structuredClone(valid); corrupt(r); assert.throws(() => validateEvidence(r, target, sources, valid.sourceHashes)); });
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-queryset-self-'));
    const child = cp.spawn(process.execPath, ['-e', 'setInterval(() => {}, 1000)']);
    const resources = {dir, child};
    await assert.rejects(async () => {
        try { throw new Error('injected scenario failure'); }
        finally { await cleanup(resources); }
    }, /injected scenario failure/);
    test('exception cleanup reaps child and removes directory', () => {
        assert(child.exitCode !== null || child.signalCode !== null);
        assert(!fs.existsSync(dir));
    });
    assert(count > 0);
    console.log(`SELF_TEST_OK ${target}: ${count} named assertions in ${Date.now() - started}ms`);
}
if (require.main === module) selfTest(process.argv.includes('downstream') ? 'downstream' : 'upstream').catch(error => {console.error(error); process.exitCode = 1;});
