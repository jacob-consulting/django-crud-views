const {test} = require('node:test');
const assert = require('node:assert/strict');
const harness = require('./protected-delete.cjs');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');

test('evidence rejects missing required cases', () => {
    assert.throws(() => harness.validateEvidence({cases: []}, 'smoke'), /case/i);
});

function evidence(t, selection = 'all') {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'protected-evidence-'));
    t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
    const report = {status: 'passed', sourceHashes: harness.sourceHashes(), recipeHashes: harness.recipes().hashes,
        failures: [], cleanupErrors: [], cleanup: {stopped: true, databaseRemoved: true}, screenshots: [], cases: []};
    for (const id of harness.requiredCases(selection)) {
        const nav = id.endsWith('-click') || id.endsWith('-enter') || id === 'stock-repeat', href = 'http://127.0.0.1:123/book/1/detail/';
        const hidden = id.endsWith('hidden-only') || id.endsWith('preview-off');
        report.cases.push({id, passed: true, mode: id.startsWith('custom-') ? 'custom' : 'stock', sourceKind: id.includes('-modal-') ? 'modal' : 'page',
            activation: nav ? (id.endsWith('-enter') ? 'Enter' : 'click') : 'none', href: nav ? href : null,
            beforeUrl: 'http://127.0.0.1:123/delete/', afterUrl: nav ? href : 'http://127.0.0.1:123/delete/',
            detailStatus: nav ? 200 : null, detailModalHeader: null, requestResourceType: nav ? 'document' : null,
            focusedAnchorBeforeEnter: true, activeElementTag: 'A', activeElementHref: href,
            dom: {...Object.fromEntries(['noHiddenLabel', 'noHiddenHref', 'wholeFormAbsent', 'sharedAlert', 'recipeIdentity', 'escapedLabel',
                'fullDocument', 'sameRow', 'ordinaryAnchor', 'modalCapable', 'linkDisabledText', 'previewDisabledHidden', 'plainProtected'].map(key => [key, true])),
                displayedCount: hidden ? 0 : id.endsWith('blockers-exhaust') ? 2 : id.endsWith('finite-over') ? 3 : 4,
                shortenedNoticeCount: /(?:blockers-exhaust|finite-over)$/.test(id) ? 1 : 0,
                summaryBookCount: id.endsWith('preview-off') ? null : 2,
                detailsAbsent: hidden || id.endsWith('blockers-exhaust')}});
    }
    fs.mkdirSync(path.join(dir, 'screenshots'));
    for (const mode of ['stock', 'custom']) {
        const relative = `screenshots/protected-${mode}-modal.png`, bytes = Buffer.from('test-only image bytes');
        fs.writeFileSync(path.join(dir, relative), bytes);
        report.screenshots.push({path: relative, sha256: crypto.createHash('sha256').update(bytes).digest('hex')});
    }
    return {report, dir, output: path.join(dir, 'report.json')};
}

test('valid complete schema passes, while missing and duplicate IDs reject', t => {
    const f = evidence(t); harness.validateEvidence(f.report, 'all', f.output);
    f.report.cases.pop(); assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /case IDs/);
    f.report.cases.push(f.report.cases[0]); assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /case IDs/);
});
test('navigation evidence rejects false success, modal requests and wrong rows', t => {
    const f = evidence(t), item = f.report.cases[0];
    for (const [key, value] of Object.entries({passed: false, afterUrl: item.beforeUrl, detailStatus: 403, detailModalHeader: 'true', requestResourceType: 'fetch'})) {
        const original = item[key]; item[key] = value; assert.throws(() => harness.validateEvidence(f.report, 'all', f.output)); item[key] = original;
    }
    for (const key of Object.keys(item.dom)) {
        if (['linkDisabledText', 'previewDisabledHidden', 'displayedCount', 'shortenedNoticeCount', 'summaryBookCount', 'detailsAbsent'].includes(key)) continue;
        item.dom[key] = false; assert.throws(() => harness.validateEvidence(f.report, 'all', f.output)); item.dom[key] = true;
    }
});
test('Enter requires exact anchor focus and document resource type', t => {
    const f = evidence(t), item = f.report.cases.find(item => item.id === 'custom-modal-enter');
    for (const [key, value] of Object.entries({focusedAnchorBeforeEnter: false, activeElementTag: 'BODY', activeElementHref: '/wrong/', requestResourceType: 'xhr'})) {
        const original = item[key]; item[key] = value; assert.throws(() => harness.validateEvidence(f.report, 'all', f.output)); item[key] = original;
    }
    delete item.focusedAnchorBeforeEnter; assert.throws(() => harness.validateEvidence(f.report, 'all', f.output));
});
test('matrix covers capped plain previews on every stock/custom page/modal surface', () => {
    const ids = harness.requiredCases('all');
    for (const mode of ['stock', 'custom']) for (const kind of ['page', 'modal']) {
        for (const scenario of ['finite-exact', 'finite-over', 'blockers-exhaust', 'hidden-tail', 'unlimited', 'hidden-only', 'preview-off', 'escaping']) {
            assert(ids.includes(`${mode}-${kind}-${scenario}`), `Missing ${mode}-${kind}-${scenario}`);
        }
    }
});
test('evidence rejects protected anchors and false preview counts', t => {
    const f = evidence(t), item = f.report.cases[0];
    for (const [key, value] of Object.entries({plainProtected: false, displayedCount: 99, shortenedNoticeCount: 1, summaryBookCount: 0, detailsAbsent: true})) {
        const original = item.dom[key]; item.dom[key] = value;
        assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), undefined, key);
        item.dom[key] = original;
        delete item.dom[key]; assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), undefined, `Missing ${key}`);
        item.dom[key] = original;
    }
});
test('evidence rejects missing shortening and an empty detail frame when blockers exhaust the budget', t => {
    const f = evidence(t), item = f.report.cases.find(item => item.id === 'custom-modal-blockers-exhaust');
    assert(item, 'Missing blocker-exhaustion case');
    for (const [key, value] of Object.entries({shortenedNoticeCount: 0, detailsAbsent: false, summaryBookCount: 0, displayedCount: 3})) {
        const original = item.dom[key]; item.dom[key] = value;
        assert.throws(() => harness.validateEvidence(f.report, 'all', f.output)); item.dom[key] = original;
    }
});
test('evidence rejects stale source, recipe, screenshot and failed cleanup', t => {
    const f = evidence(t);
    for (const key of ['sourceHashes', 'recipeHashes']) {
        const original = f.report[key]; f.report[key] = {}; assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /Stale/); f.report[key] = original;
    }
    f.report.cleanup.stopped = false; assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /cleanup/); f.report.cleanup.stopped = true;
    f.report.cleanupErrors.push({stage: 'browser.close'}); assert.throws(() => harness.validateEvidence(f.report, 'all', f.output)); f.report.cleanupErrors = [];
    fs.writeFileSync(path.join(f.dir, f.report.screenshots[0].path), 'corrupt');
    assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /Screenshot hash/);
    fs.unlinkSync(path.join(f.dir, f.report.screenshots[0].path)); assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /ENOENT/);
    f.report.screenshots.shift(); assert.throws(() => harness.validateEvidence(f.report, 'all', f.output), /Missing screenshot/);
});
test('recipe extraction rejects separated, duplicate, wrong-language markers and final-LF differences', () => {
    const source = fs.readFileSync(path.join(__dirname, '../../docs/migrating-1.0.md'), 'utf8'), good = harness.recipes(source);
    for (const name of ['content', 'related', 'body']) {
        const marker = `<!-- protected-delete-recipe: ${name} -->`;
        for (const replacement of ['', marker + '\n', marker + '\n' + marker, marker + '\nprose']) assert.throws(() => harness.recipes(source.replace(marker, replacement)));
        assert.throws(() => harness.recipes(source.replace(marker + '\n```django', marker + '\n```html')));
        assert(good.bodies[name].endsWith('\n'));
        assert.throws(() => harness.recipes(source.replace(good.bodies[name], good.bodies[name] + '\n'), good.hashes), /bytes changed/);
    }
});
test('options reject unsupported modes and flags', () => {
    for (const args of [['--case', 'fake'], ['--case'], ['--install'], ['--output', '--case']]) assert.throws(() => harness.options(args));
});
test('browser-close failure still stops owned child and preserves unrelated child', async () => {
    const child = cp.spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)']), other = cp.spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)']);
    const report = {status: 'passed', cleanupErrors: []};
    try {
        await harness.cleanup({close: async () => {throw Error('close failed');}}, {child, ready: {database: '/missing/cv-fixture'}, logs: () => ({})}, report);
        assert.equal(report.status, 'failed'); assert.equal(report.cleanup.stopped, true); assert.equal(report.cleanup.databaseRemoved, true);
        assert.equal(report.cleanupErrors[0].stage, 'browser.close'); assert.equal(other.exitCode, null); assert.equal(other.signalCode, null);
    } finally {child.kill(); other.kill();}
});

function startupFailure(t, body) {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'protected-startup-'));
    t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
    const python = path.join(dir, 'python'), output = path.join(dir, 'failed.json');
    fs.writeFileSync(python, body, {mode: 0o755}); fs.writeFileSync(path.join(dir, 'assets.json'), '{}');
    fs.writeFileSync(output, JSON.stringify({status: 'passed', stale: true}));
    const bootstrap = `const shared=require(process.argv[1]),real=shared.runtime;
        shared.runtime=(v,...a)=>v==='CV_CANCEL_PYTHON'?real(v,...a):'/unused';shared.loadAssets=()=>new Map();
        require(process.argv[2]).main(['--case','smoke','--output',process.argv[3]]).catch(e=>{console.error(e.stack);process.exitCode=1;});`;
    const result = cp.spawnSync(process.execPath, ['-e', bootstrap, path.join(__dirname, 'cancel-navigation.cjs'),
        path.join(__dirname, 'protected-delete.cjs'), output], {encoding: 'utf8', timeout: 5000,
        env: {...process.env, CV_CANCEL_PYTHON: python, CV_CANCEL_ASSETS_DIR: dir}});
    assert.equal(result.status, 1); assert.equal(result.error, undefined); assert.doesNotMatch(result.stderr, /Unhandled 'error'/);
    const report = JSON.parse(fs.readFileSync(output)); assert.equal(report.status, 'failed'); assert.equal(report.stale, undefined);
    return report;
}
test('asynchronous OS spawn errors replace stale success with failure', t => {
    const report = startupFailure(t, '#!/missing/protected/interpreter\n');
    assert.match(report.error, /ENOENT/); assert.equal(report.cleanup.spawned, false); assert.equal(report.cleanup.stopped, true);
});
test('early fixture exit records owned cleanup', t => {
    const report = startupFailure(t, '#!/bin/sh\nexit 9\n');
    assert.match(report.error, /Fixture startup failed/); assert.equal(report.cleanup.spawned, true); assert.equal(report.cleanup.stopped, true);
    assert.throws(() => process.kill(report.cleanup.pid, 0), {code: 'ESRCH'});
});
