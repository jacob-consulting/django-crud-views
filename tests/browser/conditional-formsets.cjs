// Real Chromium + authenticated CSRF HTTP acceptance; no installs or mocked application responses.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const net = require('node:net');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
process.chdir(root);
const runtimeManifest = '.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json';
const runtime = JSON.parse(fs.readFileSync(runtimeManifest));
const node = process.env.CV_FOCUS_NODE || runtime.node.path;
assert(fs.existsSync(node), `Missing CV_FOCUS_NODE/runtime: ${node}`);
if (fs.realpathSync(process.execPath) !== fs.realpathSync(node)) {
    const result = cp.spawnSync(node, [__filename, ...process.argv.slice(2)], {stdio: 'inherit'});
    if (result.error) console.error(result.error);
    process.exit(result.status ?? 1);
}
const argv = process.argv.slice(2);
function option(name, fallback) {
    const i = argv.indexOf(name);
    if (i < 0) return fallback;
    assert(argv[i + 1] && !argv[i + 1].startsWith('--'), `Missing ${name} value`);
    return argv[i + 1];
}
const output = option('--output', '.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/08-browser-results.json');
const requested = option('--case', 'all');
assert(['tracer', 'all'].includes(requested), 'Use --case tracer|all');
const portText = process.env.CV_CONDITIONAL_PORT || '8144';
assert(/^\d+$/.test(portText), 'Invalid CV_CONDITIONAL_PORT');
const port = Number(portText);
assert(port >= 1024 && port <= 65535 && port !== 8143, 'CV_CONDITIONAL_PORT must be 1024..65535, excluding reserved 8143');
const base = `http://127.0.0.1:${port}`;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
function filesIn(dir) {
    return fs.readdirSync(dir, {withFileTypes: true}).flatMap(e => e.isDirectory() ? filesIn(`${dir}/${e.name}`) : [`${dir}/${e.name}`]);
}
function hashes() {
    const files = [runtimeManifest, 'package-lock.json', 'tests/browser/conditional-formsets.cjs',
        'tests/browser/conditional_formsets_server.py', 'tests/test1/app/models.py', 'tests/test1/conftest.py',
        ...filesIn('tests/browser/templates/conditional_formsets'), ...filesIn('src/crud_views/lib/conditional'),
        ...filesIn('src/crud_views/lib/formsets'), ...filesIn('src/crud_views/templates/crud_views/formsets'),
        ...filesIn('src/crud_views/templates/crud_views/conditional'),
        ...['toggle', 'formset', 'modal', 'adapters'].map(n => `src/crud_views/static/crud_views/js/${n}.js`),
        'src/crud_views/lib/views/mixins.py', 'src/crud_views/lib/views/update.py', 'src/crud_views/lib/view/base.py'];
    return Object.fromEntries(files.filter(f => !f.includes('__pycache__')).sort().map(f => [f, digest(f)]));
}
const REQUIRED = {
    'tracer': ['real-page', 'prefixed-group', 'actual-fragment', 'post-management', 'persisted-added-row'],
    'fragment-raw-balance': ['raw-wrapper-stack-balanced', 'rows-only-outer-wrapper-absent', 'parsed-nesting-correct', 'second-sibling-post-persisted'],
    'inline-file-clear-unchanged': ['file-has-changed-false', 'image-has-changed-false', 'actual-inline-save', 'file-reference-cleared', 'image-reference-cleared', 'stored-content-retained', 'disabled-reference-retained', 'explicit-none-retained', 'untouched-extra-not-created', 'file-upload-received', 'off-file-upload-discarded', 'uploaded-file-not-stored'],
    'native-reset-user-default': ['click-default-reset', 'keyboard-default-reset', 'post-task-default-state', 'other-form-unchanged', 'dynamic-rows-retained'],
    'native-reset-user-cancelled': ['later-listener-cancels-click', 'later-listener-cancels-keyboard', 'values-and-state-unchanged'],
    'disabled-same-value-ownership': ['external-true-while-already-disabled', 'independent-true-survives-off-on', 'external-false-still-conditionally-disabled', 'external-false-released-on-active', 'reinit-preserves-owners'],
    'conditional-focus': ['keyboard-checkbox-tab', 'retained-off-on-text', 'focus-toggle-fallback', 'focus-ancestor-fallback', 'focus-owning-form-fallback', 'outside-focus-unchanged', 'two-form-isolation'],
    'lifecycle': ['no-early-focus', 'real-422', '422-focus-usable', 'unload-before-replacement', 'reinitialized-once', 'completed-close-restores-opener', 'cancel-restores-opener', 'delete-reorder-management', 'widgets-once'],
    'tampered-post': ['edit-only-extra', 'missing-id', 'foreign-id', 'filtered-id', 'invalid-zero-saves', 'generic-policy-errors', 'js-disabled-direct-post'],
    'late-init': ['fragment-element-roots', 'late-checkbox-retry', 'late-script-ready', 'reinit-single-action'],
};
function checkEvidence(file) {
    const r = JSON.parse(fs.readFileSync(file));
    assert(r.completed && r.passed && !r.error && r.pageErrors.length === 0, 'Incomplete/failed browser record');
    assert.deepEqual(r.sourceHashes, hashes(), 'Stale source hashes or wrong input set');
    const expected = r.scope === 'tracer' ? ['stock:tracer'] : ['stock', 'native'].flatMap(t => Object.keys(REQUIRED).map(id => `${t}:${id}`));
    assert.deepEqual(r.cases.map(c => `${c.theme}:${c.id}`).sort(), expected.sort(), 'Missing/duplicate/extra case');
    if (requested === 'all') assert.equal(r.scope, 'all', 'Tracer cannot satisfy all-case acceptance');
    for (const c of r.cases) {
        assert(c.passed && !c.skipped, `Case failed/skipped: ${c.id}`);
        assert.deepEqual(c.assertions.map(a => a.id).sort(), REQUIRED[c.id].slice().sort(), `Missing/duplicate assertion ${c.id}`);
        assert(c.assertions.every(a => a.passed === true), `False assertion ${c.id}`);
    }
    for (const key of ['nodePath', 'pythonPath', 'playwrightPath', 'chromiumPath', 'node', 'python', 'django', 'playwright', 'chromium']) assert(r.runtime[key], `Missing runtime ${key}`);
    assert(r.command.length && r.revision && r.captured && r.cleanup.reaped, 'Missing provenance/cleanup');
    console.log(`CONDITIONAL_EVIDENCE_OK ${r.cases.length} cases`);
}
// Strict original wrapper stack, before Chromium can repair malformed div/fieldset nesting.
function rawBalance(html) {
    const stack = [];
    const tokens = html.replace(/<!--[\s\S]*?-->/g, '').matchAll(/<\/?(div|fieldset)\b[^>]*>/gi);
    for (const [token, tag] of tokens) {
        if (token.startsWith('</')) assert.equal(stack.pop(), tag.toLowerCase(), `Unbalanced raw wrapper ${token}`);
        else stack.push(tag.toLowerCase());
    }
    assert.equal(stack.length, 0, 'Unclosed raw wrapper');
    return true;
}
async function main() {
    const record = {captured: new Date().toISOString(), revision: cp.execFileSync('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}).trim(),
        sourceHashes: hashes(), command: [process.execPath, __filename, ...argv], scope: requested,
        runtime: {node: process.version, nodePath: fs.realpathSync(process.execPath)}, cases: [], pageErrors: [], cleanup: {}, completed: false, passed: false};
    let child, browser;
    let childExit;
    try {
        await new Promise((resolve, reject) => { const probe = net.createServer(); probe.once('error', reject); probe.listen(port, '127.0.0.1', () => probe.close(resolve)); });
        const python = process.env.CV_FOCUS_PYTHON || `${root}/.nox/crispy_floor-3-12-django-6-0/bin/python`;
        const playwright = process.env.CV_FOCUS_PLAYWRIGHT || '/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
        const chromium = process.env.CV_FOCUS_CHROMIUM || '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
        for (const p of [python, playwright, chromium]) assert(fs.existsSync(p), `Missing explicit/runtime path: ${p}`);
        Object.assign(record.runtime, {pythonPath: fs.realpathSync(python), playwrightPath: fs.realpathSync(playwright), chromiumPath: fs.realpathSync(chromium)});
        const versions = JSON.parse(cp.execFileSync(python, ['-c', 'import json,sys,django; print(json.dumps({"python":sys.version,"django":django.get_version()}))'], {encoding:'utf8'}));
        Object.assign(record.runtime, versions, {playwright: require(`${playwright}/package.json`).version});
        child = cp.spawn(python, ['tests/browser/conditional_formsets_server.py'], {cwd:root, env:{...process.env, CV_CONDITIONAL_PORT:String(port), PYTHONPATH:`${root}/src:${root}`, PYTHONUNBUFFERED:'1'}, stdio:['ignore','pipe','pipe']});
        let serverLog = '';
        child.stdout.on('data', data => { serverLog += data; }); child.stderr.on('data', data => { serverLog += data; });
        let spawnError; child.on('error', e => { spawnError = e; });
        childExit = new Promise(resolve => child.once('exit', (code, signal) => resolve({code, signal})));
        let ready = false;
        for (let i = 0; i < 150; i++) {
            if (spawnError) throw spawnError;
            assert(child.exitCode === null && child.signalCode === null, `Fixture exited ${child.exitCode}: ${serverLog}`);
            try { ready = (await fetch(`${base}/cases/`, {signal:AbortSignal.timeout(500)})).ok; } catch (_) {}
            if (ready) break;
            await delay(100);
        }
        assert(ready, `Fixture readiness timeout: ${serverLog}`);
        browser = await require(playwright).chromium.launch({headless:true, executablePath:chromium, args:['--no-sandbox']});
        record.runtime.chromium = browser.version();
        const context = await browser.newContext({ignoreHTTPSErrors:true});
        await context.request.get(`${base}/signin/`);
        const fixtures = await (await context.request.get(`${base}/cases/`)).json();
        const selected = requested === 'tracer' ? fixtures.filter(c => c.theme === 'stock' && c.id === 'tracer') : fixtures;
        for (const c of selected) {
            const result = {theme:c.theme, id:c.id, assertions:[], requests:[], passed:false}; record.cases.push(result);
            const check = (id, value, detail) => { result.assertions.push({id, passed:Boolean(value), ...(detail === undefined ? {} : {detail})}); assert(value, `${c.theme}:${c.id}: ${id} ${JSON.stringify(detail)}`); };
            const page = await context.newPage(); page.setDefaultTimeout(12000);
            page.on('pageerror', e => record.pageErrors.push(e.message));
            const before = await (await context.request.get(`${base}/state/`)).json();
            async function state() { return (await context.request.get(`${base}/state/`)).json(); }
            async function load(url = c.url) {
                const response = await page.goto(base + url);
                assert.equal(response.status(), 200, (await response.text()).match(/<pre class="exception_value">([\s\S]*?)<\/pre>/)?.[1] || response.statusText());
                await page.waitForFunction(() => typeof cv?.initFormsets === 'function' && typeof cv?.initConditional === 'function');
                await delay(80); return response;
            }
            async function post(form = '#editor', url = c.url, mutate = {}) {
                const data = await page.evaluate(async ({form, url, mutate}) => {
                    const el = document.querySelector(form);
                    if (!el.dispatchEvent(new Event('submit', {bubbles:true,cancelable:true}))) throw Error('Submit prevented');
                    const payload = new FormData(el);
                    for (const [key,value] of Object.entries(mutate)) value === null ? payload.delete(key) : payload.set(key,value);
                    const sent = [...payload.entries()].map(([k,v])=>[k,typeof v === 'string' ? v : {name:v.name,size:v.size}]);
                    const response = await fetch(url, {method:'POST',body:payload});
                    return {status:response.status, sent, body:await response.text()};
                }, {form,url,mutate}); result.requests.push(data); return data;
            }
            async function add(button) {
                const response = page.waitForResponse(r => r.url().includes('template=') && r.request().method() === 'GET');
                await button.click(); const r = await response; assert.equal(r.status(),200);
                const body = await r.json(); rawBalance(body.html); result.requests.push({status:r.status(),url:r.url(), ...body});
                await page.waitForFunction(prefix => [...document.querySelectorAll('#editor [cv-data-formset-form-prefix]')].some(el=>el.getAttribute('cv-data-formset-form-prefix')===prefix), body.rows[0]);
                await delay(50); return body;
            }
            await load();
            if (c.id === 'tracer') {
                check('real-page', await page.locator('#editor').count() === 1);
                check('prefixed-group', await page.locator('#editor [cv-data-toggle-field="outer"]').count() === 1);
                const body = await add(page.locator('#editor .cv-form-ctrl-add').first());
                check('actual-fragment', body.rows.length > 0 && body.html.includes(body.rows[0]));
                await page.locator(`#editor input[name="${body.rows[0]}-title"]`).fill('Browser added book');
                const response = await post(); check('post-management', response.status === 200 && response.sent.some(([k,v])=>k.endsWith('-TOTAL_FORMS') && v === '3'), response);
                const final = await state(); result.state = final;
                check('persisted-added-row', final.books.some(b=>b.publisher_id===c.pk && b.title==='Browser added book'));
            } else {
                await runCase({c, page, context, base, before, result, check, load, state, post, add, delay, rawBalance});
            }
            assert.equal(record.pageErrors.length, 0, record.pageErrors.join('\n'));
            result.passed = true; await page.close();
            console.log(`PASS ${c.theme}:${c.id} (${result.assertions.length} assertions)`);
        }
        record.completed = true; record.passed = true;
    } finally {
        if (browser) await browser.close();
        if (child && child.exitCode === null && child.signalCode === null) {
            child.kill('SIGTERM');
            if (!await Promise.race([childExit, delay(3000).then(()=>false)])) { child.kill('SIGKILL'); await childExit; }
        }
        record.cleanup.reaped = !child || child.exitCode !== null || child.signalCode !== null;
        if (record.passed) {
            fs.mkdirSync(path.dirname(output), {recursive:true});
            fs.writeFileSync(output, JSON.stringify(record,null,2)+'\n');
        }
    }
    checkEvidence(output);
}
async function runCase() { throw Error('Full case expansion belongs to task 08-02'); }
(argv.includes('--check-evidence') ? Promise.resolve().then(()=>checkEvidence(option('--check-evidence'))) : main()).catch(error => { console.error(error); process.exitCode = 1; });
