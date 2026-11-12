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
const runtime = process.env.CV_FOCUS_NODE ? {} : JSON.parse(fs.readFileSync(runtimeManifest));
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
const compactPhase = '.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m';
const compositions = ['compact-compact', 'compact-classic', 'classic-compact'];
const widths = [390, 767, 768, 1280];
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
    const files = [...(process.env.CV_FOCUS_NODE ? [] : [runtimeManifest]), 'package-lock.json', 'tests/browser/conditional-formsets.cjs',
        'tests/js-integration/formset.test.js', 'tests/js/formset.test.js', 'src/crud_views/static/crud_views/css/formset.css',
        `${compactPhase}/browser-captures/.gitignore`,
        'tests/browser/conditional_formsets_server.py', 'tests/test1/app/models.py', 'tests/test1/conftest.py',
        'tests/test1/test_fragment_authorization.py', 'tests/test1/app/templates/app/base.html',
        ...filesIn('tests/browser/templates/conditional_formsets'), ...filesIn('src/crud_views/lib/conditional'),
        ...filesIn('src/crud_views/lib/formsets'), ...filesIn('src/crud_views/templates/crud_views/formsets'),
        ...filesIn('src/crud_views/templates/crud_views/conditional'),
        ...['toggle', 'formset', 'modal', 'adapters'].map(n => `src/crud_views/static/crud_views/js/${n}.js`),
        'src/crud_views/lib/views/mixins.py', 'src/crud_views/lib/views/update.py', 'src/crud_views/lib/view/base.py'];
    return Object.fromEntries(files.filter(f => !f.includes('__pycache__')).sort().map(f => [f, digest(f)])); // NOSONAR S2871: test harness
}
const REQUIRED = {
    'choice-widgets': ['initial-create-edit', 'keyboard-change', 'shared-active-kept', 'unsaved-away-back',
        'final-inactive-cleared', 'invalid-controller-zero-save', 'active-required-redisplay', 'exact-prefix-two-forms',
        'disabled-trusted', 'independent-disabled', 'native-reset', 'canceled-reset', 'modal-422-rebind',
        'unload-listener-cleanup', 'usable-radio-focus', 'adversarial-token-inert'],
    'value-tracer': ['rendered-shared-metadata', 'initial-selection-equals-saved', 'reopened-selection-equals-saved',
        'prefixed-select', 'active-required', 'retain-before-submit', 'forged-inactive-cleared', 'persisted-reopen', 'invalid-controller-blocked'],
    'compact-lifecycle': ['assets', 'pending-preserves-data', 'authorized-parent-fragment', 'nonfirst-child-fragment',
        'heading-ownership', 'delete-unmark-order', 'labels-and-events', 'formdata-once', 'persisted-relationships',
        'unauthorized-no-insertion', 'invalid-390', 'invalid-1280', 'management-error',
        'edge-blank', 'edge-zero', 'edge-extra-zero', 'edge-no-controls', 'edge-delete-absent', 'captures'],
    'compact-presentation': compositions.flatMap(composition => widths.flatMap(width =>
        ['assets', 'geometry', 'labels', 'nesting', 'classic-isolation', 'keyboard', 'resize-identity', 'capture'].map(id => `${composition}:${width}:${id}`))),
    'tracer': ['real-page', 'prefixed-group', 'actual-fragment', 'post-management', 'persisted-added-row'],
    'fragment-raw-balance': ['raw-wrapper-stack-balanced', 'rows-only-outer-wrapper-absent', 'parsed-nesting-correct', 'second-sibling-post-persisted'],
    'inline-file-clear-unchanged': ['file-has-changed-false', 'image-has-changed-false', 'actual-inline-save', 'file-reference-cleared', 'image-reference-cleared', 'stored-content-retained', 'disabled-reference-retained', 'explicit-none-retained', 'untouched-extra-not-created', 'file-upload-received', 'off-file-upload-discarded', 'uploaded-file-not-stored'],
    'native-reset-user-default': ['click-default-reset', 'keyboard-default-reset', 'post-task-default-state', 'other-form-unchanged', 'dynamic-rows-retained'],
    'native-reset-user-cancelled': ['later-listener-cancels-click', 'later-listener-cancels-keyboard', 'values-and-state-unchanged'],
    'disabled-same-value-ownership': ['external-true-while-already-disabled', 'independent-true-survives-off-on', 'external-false-still-conditionally-disabled', 'external-false-released-on-active', 'reinit-preserves-owners', 'inactive-row-action-rejected'],
    'conditional-focus': ['keyboard-checkbox-tab', 'retained-off-on-text', 'focus-toggle-fallback', 'focus-ancestor-fallback', 'focus-owning-form-fallback', 'outside-focus-unchanged', 'two-form-isolation'],
    'lifecycle': ['no-early-focus', 'real-422', '422-focus-usable', 'unload-before-replacement', 'reinitialized-once', 'completed-close-restores-opener', 'cancel-restores-opener', 'delete-reorder-management', 'widgets-once', 'authorized-modal-persistence'],
    'tampered-post': ['edit-only-extra', 'missing-id', 'foreign-id', 'filtered-id', 'invalid-zero-saves', 'generic-policy-errors', 'js-disabled-direct-post'],
    'late-init': ['fragment-element-roots', 'late-checkbox-retry', 'late-script-ready', 'reinit-single-action'],
    'gap-capability': ['native-delete-presence', 'add-once', 'extra-before-initial', 'stable-initial-delete', 'ordered-post-persisted', 'all-extra-add-order-post', 'reclean-policy-zero-saves', 'host-assets'],
    'gap-ambiguity': ['bound-off-native-valid', 'ambiguous-retains-state', 'no-arbitrary-checkbox-follow', 'obsolete-listener-detached', 'unique-recovery', 'independent-owner-retained', 'ancestor-owner-retained', 'other-form-unaffected', 'native-reset-focus', 'modal-422-ambiguity-focus', 'modal-reset-focus', 'responsive-containment', 'loaded-rendered-glyphs', 'screenshot-provenance', 'human-review-pending'],
};
assert(requested === 'all' || Object.hasOwn(REQUIRED, requested), 'Unknown --case');
function checkEvidence(file) {
    const r = JSON.parse(fs.readFileSync(file));
    validateEvidence(r);
    // The checker itself must fail closed on the review's adversarial evidence shapes.
    const corruptions = [
        copy=>copy.cases.pop(),
        copy=>copy.cases.push(structuredClone(copy.cases[0])),
        copy=>copy.cases[0].skipped=true,
        copy=>copy.cases[0].assertions.pop(),
        copy=>copy.cases[0].assertions.push(structuredClone(copy.cases[0].assertions[0])),
        copy=>copy.cases[0].assertions[0].passed=false,
        copy=>copy.sourceHashes[Object.keys(copy.sourceHashes)[0]]='stale',
        copy=>copy.cleanup.reaped=false,
        copy=>copy.command=[],
        copy=>copy.pageErrors.push('uncaught error'),
        copy=>copy.cleanup.temporaryRemoved=false,
    ];
    if (r.scope === 'choice-widgets') corruptions.push(
        copy=>copy.cases[0].widget='unsupported',
        copy=>delete copy.cases[0].numeric,
        copy=>delete copy.cases[0].assertions[0].detail,
        copy=>copy.cases[0].assertions[0].widget='unsupported',
    );
    if (r.scope.startsWith('compact-')) corruptions.push(
        copy=>copy.cases[0].captures.pop(),
        copy=>copy.cases[0].captures[0].sha256='stale',
        copy=>copy.cleanup.temporaryRemoved=false,
    );
    for (const corrupt of corruptions) {const copy=structuredClone(r);corrupt(copy);assert.throws(()=>validateEvidence(copy));}
    console.log(`CONDITIONAL_EVIDENCE_OK ${r.cases.length} cases`);
}
function validateEvidence(r) {
    assert(r.completed && r.passed && !r.error && r.pageErrors.length === 0, 'Incomplete/failed browser record');
    assert.deepEqual(r.sourceHashes, hashes(), 'Stale source hashes or wrong input set');
    assert(r.scope === 'all' || Object.hasOwn(REQUIRED, r.scope), 'Unknown evidence scope');
    const ids = r.scope === 'all' ? Object.keys(REQUIRED) : [r.scope];
    const caseKey = c => `${c.theme}:${c.id}${c.id === 'choice-widgets' ? `:${c.widget}:${c.numeric}` : ''}`;
    const expected = ids.flatMap(id => id === 'choice-widgets'
        ? ['stock', 'native'].flatMap(theme => ['select', 'radio'].flatMap(widget => [false, true].map(numeric => caseKey({theme,id,widget,numeric}))))
        : (r.scope === 'tracer' || id === 'value-tracer' || id.startsWith('compact-') ? ['stock'] : ['stock', 'native']).map(t => `${t}:${id}`));
    assert.deepEqual(r.cases.map(caseKey).sort(), expected.sort(), 'Missing/duplicate/extra case'); // NOSONAR S2871: test harness
    assert.equal(r.scope, requested, 'Evidence must match exact requested scope');
    for (const c of r.cases) {
        assert(c.passed && !c.skipped, `Case failed/skipped: ${c.id}`);
        assert.deepEqual(c.assertions.map(a => a.id).sort(), REQUIRED[c.id].slice().sort(), `Missing/duplicate assertion ${c.id}`);
        assert(c.assertions.every(a => a.passed === true), `False assertion ${c.id}`);
        if (c.id === 'choice-widgets') {
            assert(c.assertions.every(a => a.theme === c.theme && a.widget === c.widget && a.numeric === c.numeric &&
                a.detail && Object.hasOwn(a.detail, 'observed') && Object.hasOwn(a.detail, 'expected')), 'Missing choice dimensions/observations');
            assert(c.requests.some(r => r.status === 422) && c.requests.some(r => r.status === 200), 'Missing choice HTTP evidence');
            assert(c.state?.choice_records?.some(row => row.id === c.pk), 'Missing choice database evidence');
        }
        if (c.id.startsWith('compact-')) {
            assert(r.cleanup.temporaryRemoved, 'Disposable database/media were not removed');
            assert.equal(c.humanReview, 'pending');
            assert.equal(c.captures.length, c.id === 'compact-presentation' ? 12 : 4);
            assert.equal(new Set(c.captures.map(s => s.path)).size, c.captures.length);
            const expectedCaptures=c.id==='compact-presentation'
                ? compositions.flatMap(composition=>widths.map(width=>`${composition}-${width}.png`))
                : ['invalid-390.png','invalid-1280.png','saved-390.png','saved-1280.png'];
            assert.deepEqual(c.captures.map(s=>path.basename(s.path)).sort(),expectedCaptures.sort());
            for (const capture of c.captures) {
                assert(capture.path.startsWith(`${compactPhase}/browser-captures/${c.id}/`));
                assert.equal(cp.spawnSync('git', ['check-ignore', '--no-index', capture.path]).status, 0);
                assert.equal(capture.sha256, digest(capture.path), 'Missing/stale compact screenshot');
                assert(capture.measurements && capture.width, 'Missing browser measurements');
            }
        }
        if(c.id==='gap-ambiguity') {
            assert(c.humanReview.H1==='pending'&&c.humanReview.H2==='pending');
            assert.equal(c.captures.length,c.theme==='stock'?3:0);
            for(const capture of c.captures) {
                assert.equal(capture.sha256,digest(capture.path),'Missing/stale screenshot');
                assert.equal(capture.document.scrollWidth,capture.document.clientWidth,'Document overflow');
                assert(capture.icons.loaded&&capture.icons.glyphs.length>0);
            }
        }
    }
    for (const key of ['nodePath', 'pythonPath', 'playwrightPath', 'chromiumPath', 'node', 'python', 'django', 'playwright', 'chromium']) assert(r.runtime[key], `Missing runtime ${key}`);
    assert(r.command.length && r.revision && r.captured && r.cleanup.reaped && r.cleanup.temporaryRemoved, 'Missing provenance/cleanup');
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
    const record = {captured: new Date().toISOString(), revision: cp.execFileSync('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}).trim(), // NOSONAR S4036: test harness
        sourceHashes: hashes(), command: [process.execPath, __filename, ...argv], scope: requested,
        runtime: {node: process.version, nodePath: fs.realpathSync(process.execPath)}, cases: [], pageErrors: [], cleanup: {}, completed: false, passed: false};
    let child, browser;
    let childExit, temporaryPath;
    try {
        await new Promise((resolve, reject) => { const probe = net.createServer(); probe.once('error', reject); probe.listen(port, '127.0.0.1', () => probe.close(resolve)); });
        const python = process.env.CV_FOCUS_PYTHON || `${root}/.nox/crispy_floor-3-12-django-6-0/bin/python`;
        const playwright = process.env.CV_FOCUS_PLAYWRIGHT || '/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
        const chromium = process.env.CV_FOCUS_CHROMIUM || '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
        for (const p of [python, playwright, chromium]) assert(fs.existsSync(p), `Missing explicit/runtime path: ${p}`);
        Object.assign(record.runtime, {pythonPath: path.resolve(python), pythonRealPath: fs.realpathSync(python), playwrightPath: fs.realpathSync(playwright), chromiumPath: fs.realpathSync(chromium)});
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
        const startup=serverLog.split('\n').map(line=>{try{return JSON.parse(line);}catch{return null;}}).find(item=>item?.temporary);
        temporaryPath=startup?.temporary;
        assert(temporaryPath && fs.existsSync(temporaryPath), 'Missing disposable fixture directory');
        browser = await require(playwright).chromium.launch({headless:true, executablePath:chromium, args:['--no-sandbox']});
        record.runtime.chromium = browser.version();
        const context = await browser.newContext({ignoreHTTPSErrors:true});
        await context.request.get(`${base}/signin/`);
        const fixtures = await (await context.request.get(`${base}/cases/`)).json();
        const selected = requested === 'tracer' ? fixtures.filter(c => c.theme === 'stock' && c.id === 'tracer') : requested === 'all' ? fixtures : fixtures.filter(c=>c.id===requested);
        assert(selected.length > 0, 'No selected browser cases');
        for (const c of selected) {
            const dimensions = c.id === 'choice-widgets' ? {widget:c.widget, numeric:c.numeric, pk:c.pk} : {};
            const result = {theme:c.theme, id:c.id, ...dimensions, assertions:[], requests:[], passed:false}; record.cases.push(result);
            const check = (id, value, detail) => { result.assertions.push({id, passed:Boolean(value), ...(c.id === 'choice-widgets' ? {theme:c.theme,widget:c.widget,numeric:c.numeric} : {}), ...(detail === undefined ? {} : {detail})}); assert(value, `${c.theme}:${c.id}: ${id} ${JSON.stringify(detail)}`); };
            const page = await context.newPage(); page.setDefaultTimeout(12000);
            result.diagnostics=[];page.on('console',message=>{if(message.type()==='warning')result.diagnostics.push(message.text());});
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
                    for (const [key,value] of Object.entries(mutate)) {
                        if (key === '__upload') payload.set(value, new File(['received off-group bytes'], 'off-upload.txt', {type:'text/plain'}));
                        else value === null ? payload.delete(key) : payload.set(key,value);
                    }
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
                const filePage = await context.newPage(); await filePage.goto(base+c.filesUrl);
                const bound = await filePage.locator('#editor [cv-data-toggle-field]').evaluateAll(groups=>groups.some(g=>/^records-\d+-0-0-active$/.test(g.getAttribute('cv-data-toggle-field'))));
                check('prefixed-group', bound); await filePage.close();
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
        try { if (browser) await browser.close(); }
        finally {
            if (child && child.exitCode === null && child.signalCode === null) {
                child.kill('SIGTERM');
                if (!await Promise.race([childExit, delay(3000).then(()=>false)])) { child.kill('SIGKILL'); await childExit; }
            }
            record.cleanup.reaped = !child || child.exitCode !== null || child.signalCode !== null;
            record.cleanup.temporaryPath=temporaryPath;
            record.cleanup.temporaryRemoved=!!temporaryPath&&!fs.existsSync(temporaryPath);
        }
        if (record.passed) {
            validateEvidence(record);
            fs.mkdirSync(path.dirname(output), {recursive:true});
            fs.writeFileSync(output, JSON.stringify(record,null,2)+'\n');
        }
    }
    checkEvidence(output);
}
async function runCase({c, page, context, base, before, result, check, load, state, post, add, delay, rawBalance}) {
    if (c.id === 'choice-widgets') {
        const tokens = c.numeric ? ['0', '1', '2'] : ['consumer', 'wholesale', 'distributor'];
        const name = 'choice[<]-0-blank_text';
        const field = key => page.locator(`#editor [name="choice[<]-0-${key}"]`);
        const controls = () => page.locator(`#editor ${c.widget === 'radio' ? 'input[type=radio]' : 'select'}[name="${name}"]`);
        async function choose(index) {
            if (c.widget === 'radio') await controls().nth(index).check();
            else await controls().selectOption(tokens[index]);
        }
        async function snapshot(selector = '#editor') {
            return page.locator(selector).evaluate((form, {name, widget}) => {
                const owned = [...form.elements].filter(el => el.name === name && el.form === form);
                const chosen = widget === 'radio' ? owned.find(el => el.checked) : owned[0];
                return {value:chosen?.value, controls:owned.length, groups:[...form.querySelectorAll('[cv-data-toggle-group]')].map(group => ({
                    visible:getComputedStyle(group).display !== 'none', values:JSON.parse(group.getAttribute('cv-data-toggle-values')),
                    fields:[...group.querySelectorAll('input,select,textarea')].map(el => ({name:el.name,value:el.value,disabled:el.disabled}))})),
                    data:[...new FormData(form)].filter(([key])=>key !== 'csrfmiddlewaretoken')};
            }, {name,widget:c.widget});
        }
        const evidence = (id, value, observed, expected) => check(id, value, {observed,expected});
        const savedInitial = before.choice_records.find(row => row.id === c.pk);
        const initial = await snapshot();
        // This is the RED boundary: it asserts the real rendered widget and exact prefix, before using it.
        assert.equal(initial.controls, c.widget === 'radio' ? 3 : 1, 'choice widget must render its exact owning-form controls');
        assert.equal(initial.value, tokens[1]);
        await load(c.url + '&create=1');
        const created = await snapshot();
        await load();
        evidence('initial-create-edit', created.value === tokens[0] && initial.value === savedInitial.blank_text &&
            initial.groups.length === 3 && initial.groups[0].visible && initial.groups[1].visible && !initial.groups[2].visible,
            {created,initial,savedInitial}, {create:tokens[0],edit:tokens[1],groups:[true,true,false]});
        // Real keyboard change on both native widgets, not a synthetic change event.
        await (c.widget === 'radio' ? controls().nth(1) : controls()).focus();
        await page.keyboard.press('ArrowDown');
        if (c.widget === 'select') await page.keyboard.press('Enter');
        const keyboard = await snapshot();
        evidence('keyboard-change', keyboard.value === tokens[2] && keyboard.groups[0].visible && !keyboard.groups[1].visible,
            keyboard, {value:tokens[2],groups:[true,false,false]});
        await field('nullable_text').fill('unsaved shared');
        await choose(1); await field('number').fill('71');
        await choose(2);
        evidence('shared-active-kept', await field('nullable_text').inputValue() === 'unsaved shared' && !await field('nullable_text').isDisabled(),
            await snapshot(), {shared:'unsaved shared',disabled:false});
        await choose(0);
        assert(await field('nullable_text').isDisabled());
        await choose(1);
        evidence('unsaved-away-back', await field('nullable_text').inputValue() === 'unsaved shared' && await field('number').inputValue() === '71',
            await snapshot(), {shared:'unsaved shared',number:'71'});
        const isolation = await page.evaluate(({name,tokens,widget}) => {
            const original = document.getElementById('editor'), peer = original.cloneNode(true); peer.id = 'choice-peer';
            peer.querySelectorAll('[id]').forEach(el => el.id = `peer-${el.id}`); original.after(peer); cv.initConditional(peer);
            const originalField = original.elements['choice[<]-0-nullable_text'];
            const own = [...peer.elements].filter(el => el.name === name);
            const control = widget === 'radio' ? own[0] : own[0];
            if (widget === 'radio') control.checked = true; else control.value = tokens[0];
            control.dispatchEvent(new Event('change',{bubbles:true}));
            const observed = {originalDisabled:originalField.disabled,peerDisabled:peer.elements['choice[<]-0-nullable_text'].disabled,
                exactName:peer.querySelector('[cv-data-toggle-group]').getAttribute('cv-data-toggle-field')};
            peer.dispatchEvent(new CustomEvent('cv:modal:unload',{bubbles:true})); peer.remove(); return observed;
        }, {name,tokens,widget:c.widget});
        evidence('exact-prefix-two-forms', !isolation.originalDisabled && isolation.peerDisabled && isolation.exactName === name,
            isolation,{originalDisabled:false,peerDisabled:true,exactName:name});
        await choose(0);
        await field('nullable_text').evaluate(el => { el.disabled = true; });
        await choose(1); const independent = await field('nullable_text').isDisabled();
        await choose(0); await field('nullable_text').evaluate(el => { el.disabled = false; });
        assert(await field('nullable_text').isDisabled());
        await choose(1);
        evidence('independent-disabled', independent && !await field('nullable_text').isDisabled(),
            {independent,snapshot:await snapshot()},{independent:true,releasedOnActive:true});
        await choose(0);
        await page.locator('#editor .native-reset').click(); await delay(40);
        evidence('native-reset', (await snapshot()).value === tokens[1] && await field('nullable_text').inputValue() === savedInitial.nullable_text,
            await snapshot(), {value:tokens[1],shared:savedInitial.nullable_text});
        await choose(2); await field('nullable_text').fill('canceled retained');
        await page.evaluate(()=>document.addEventListener('reset',e=>e.preventDefault(),{once:true}));
        await page.locator('#editor .native-reset').focus(); await page.keyboard.press('Enter'); await delay(40);
        evidence('canceled-reset', (await snapshot()).value === tokens[2] && await field('nullable_text').inputValue() === 'canceled retained',
            await snapshot(),{value:tokens[2],shared:'canceled retained'});
        // Programmatic condition updates can strand focused content; recovery must prefer checked usable radio.
        const focusResult = await page.evaluate(({name,widget,tokens}) => {
            const form=document.getElementById('editor'), group=form.querySelector('[cv-data-toggle-group]');
            form.elements['choice[<]-0-nullable_text'].focus();
            group.setAttribute('cv-data-toggle-values',JSON.stringify([tokens[0]])); cv.initConditional(form);
            const active=document.activeElement;
            const observed={name:active.name,value:active.value,checked:active.checked,usable:!active.disabled&&!!active.getClientRects().length};
            group.setAttribute('cv-data-toggle-values',JSON.stringify(tokens.slice(1))); cv.initConditional(form); return observed;
        },{name,widget:c.widget,tokens});
        evidence('usable-radio-focus', focusResult.name === name && focusResult.value === tokens[2] && focusResult.usable &&
            (c.widget !== 'radio' || focusResult.checked),focusResult,{name,value:tokens[2],usable:true});
        const beforeInvalid = await state();
        const invalid = await post('#editor',c.url,{[name]:'not-a-choice'});
        const afterInvalid = await state();
        evidence('invalid-controller-zero-save',invalid.status===422 && invalid.body.includes('Select a valid choice.') &&
            JSON.stringify(beforeInvalid.choice_records)===JSON.stringify(afterInvalid.choice_records) && beforeInvalid.events.length===afterInvalid.events.length,
            {status:invalid.status,eventsBefore:beforeInvalid.events.length,eventsAfter:afterInvalid.events.length}, {status:422,saves:0});
        await field('nullable_text').fill('');
        const required = await post();
        const requiredBody = await page.evaluate(html => {
            const doc=new DOMParser().parseFromString(html,'text/html');
            return {errors:doc.body.textContent.includes('This field is required.'),groups:doc.querySelectorAll('[cv-data-toggle-group]').length};
        },required.body);
        evidence('active-required-redisplay',required.status===422&&requiredBody.errors&&requiredBody.groups===3,
            {status:required.status,...requiredBody},{status:422,errors:true,groups:3});
        await load(c.url+'&disabled=1');
        const trustedBefore=(await state()).choice_records.find(row=>row.id===c.pk);
        const trusted=await post('#editor',c.url+'&disabled=1',{[name]:tokens[0],'choice[<]-0-number':'999','choice[<]-0-nullable_text':'trusted submission'});
        const trustedAfter=(await state()).choice_records.find(row=>row.id===c.pk);
        evidence('disabled-trusted',await controls().first().isDisabled()&&trusted.status===200&&trustedAfter.blank_text===trustedBefore.blank_text&&trustedAfter.number===trustedBefore.number,
            {status:trusted.status,before:trustedBefore,after:trustedAfter},{controller:trustedBefore.blank_text,number:trustedBefore.number});
        await load(); await choose(0);
        await field('flag').uncheck(); await field('active').check();
        const finalPost=await post('#editor',c.url,{'choice[<]-0-nullable_text':'forged','choice[<]-0-number':'999'});
        const persisted=(await state()).choice_records.find(row=>row.id===c.pk);
        await load(); const reopened=await snapshot();
        evidence('final-inactive-cleared',finalPost.status===200&&persisted.blank_text===tokens[0]&&persisted.nullable_text===null&&persisted.number===null&&
            persisted.flag===false&&persisted.active===true&&await field('nullable_text').inputValue()===''&&await field('number').inputValue()==='',
            {status:finalPost.status,persisted,reopened},{value:tokens[0],shared:null,number:null,flag:false,outside:true});
        // A server-rendered hostile option is inert in both metadata and native controls.
        await load(c.url+'&adversarial=1');
        const hostile = await page.evaluate(() => ({executed:!!window.choiceInjected,metadata:JSON.parse(document.querySelector('[cv-data-toggle-values]').getAttribute('cv-data-toggle-values'))}));
        evidence('adversarial-token-inert',!hostile.executed&&hostile.metadata[0].includes('<img')&&await controls().count()===(c.widget==='radio'?3:1),
            hostile,{executed:false,escapedMetadata:true});
        // Exercise the shipped modal transport: real HTTP partial, 422 replacement, unload and rebind.
        await load(c.url+'&harness=1'); await page.locator('#launch').click();
        await page.locator('#cv-modal #editor').waitFor(); await delay(c.theme==='stock'?400:60);
        await choose(2); await field('nullable_text').fill('');
        await page.evaluate(() => {
            window.oldChoiceForm=document.getElementById('editor');
            window.oldChoiceControls=[...oldChoiceForm.elements].filter(el=>el.name==='choice[<]-0-blank_text');
            document.addEventListener('cv:modal:unload',()=>{window.choiceUnloadedAttached=oldChoiceForm.isConnected;},{once:true});
        });
        const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/choice/'));
        await page.locator('#editor [type=submit]').first().focus(); await page.keyboard.press('Enter');
        const actual=await response; await actual.finished(); await page.waitForFunction(()=>loadedCount===2);
        result.requests.push({status:actual.status(),url:actual.url(),body:await actual.text()});
        const modalFocus=await page.evaluate(()=>({name:document.activeElement.name,usable:!!document.activeElement.getClientRects().length&&!document.activeElement.disabled}));
        await choose(0); assert(await field('nullable_text').isDisabled()); await choose(2);
        evidence('modal-422-rebind',actual.status()===422&&modalFocus.usable&&await field('nullable_text').isEnabled()&&await page.evaluate(()=>choiceUnloadedAttached),
            {status:actual.status(),focus:modalFocus,snapshot:await snapshot()},{status:422,usableFocus:true,rebound:true});
        const cleanup=await page.evaluate(tokens=>{
            const groups=[...oldChoiceForm.querySelectorAll('[cv-data-toggle-group]')], displays=groups.map(g=>g.style.display);
            const field=oldChoiceForm.elements['choice[<]-0-nullable_text'];
            oldChoiceControls.forEach(el=>{if(el.type==='radio')el.checked=el.value===tokens[0];else el.value=tokens[0];el.dispatchEvent(new Event('change',{bubbles:true}));});
            return {detached:!oldChoiceForm.isConnected,released:!field.disabled,unchanged:JSON.stringify(displays)===JSON.stringify(groups.map(g=>g.style.display))};
        },tokens);
        evidence('unload-listener-cleanup',cleanup.detached&&cleanup.released&&cleanup.unchanged,cleanup,{detached:true,released:true,unchanged:true});
        result.state=await state();
        return;
    }
    if (c.id === 'value-tracer') {
        const controller = page.locator('#editor select[name="choice-0-blank_text"]');
        const detail = page.locator('#editor [name="choice-0-nullable_text"]');
        const group = page.locator('#editor [cv-data-toggle-group]');
        check('rendered-shared-metadata', await group.getAttribute('cv-data-toggle-values') === '["wholesale"]');
        const initial = before.choice_records.find(row=>row.id===c.pk);
        check('initial-selection-equals-saved', await controller.inputValue() === initial.blank_text && initial.blank_text === 'wholesale' && await group.isVisible(), {selected:await controller.inputValue(), saved:initial});
        check('prefixed-select', await group.getAttribute('cv-data-toggle-field') === 'choice-0-blank_text');
        await detail.fill('');
        const required = await post();
        check('active-required', required.status === 422 && required.body.includes('This field is required.') && (await state()).choice_records[0].nullable_text === initial.nullable_text, {status:required.status, exception:required.body.match(/<pre class="exception_value">([\s\S]*?)<\/pre>/)?.[1]});
        await detail.fill('Unsaved wholesale detail');
        await controller.selectOption('consumer');
        assert(!await group.isVisible() && await detail.isDisabled());
        await controller.selectOption('wholesale');
        check('retain-before-submit', await group.isVisible() && await detail.inputValue() === 'Unsaved wholesale detail');
        const invalid = await post('#editor', c.url, {'choice-0-blank_text':'invalid'});
        check('invalid-controller-blocked', invalid.status === 422 && invalid.body.includes('Select a valid choice.') && (await state()).choice_records[0].blank_text === 'wholesale', {status:invalid.status, posted:'invalid'});
        await controller.selectOption('consumer');
        const saved = await post('#editor', c.url, {'choice-0-nullable_text':'Forged inactive detail'});
        const final = (await state()).choice_records.find(row=>row.id===c.pk);
        check('forged-inactive-cleared', saved.status === 200 && final.nullable_text === null && final.blank_text === 'consumer', {status:saved.status, sent:saved.sent, saved:final});
        await load();
        check('reopened-selection-equals-saved', await controller.inputValue() === final.blank_text && final.blank_text === 'consumer', {selected:await controller.inputValue(), saved:final.blank_text});
        check('persisted-reopen', !await group.isVisible() && await detail.isDisabled() && await detail.inputValue() === '');
        return;
    }
    if (c.id === 'compact-lifecycle') {
        result.captures=[]; result.humanReview='pending'; result.edges=[];
        await page.setViewportSize({width:1280,height:900});
        let measured=await compactMeasurements(page);
        check('assets',measured.assets.bootstrap&&measured.assets.compact&&measured.assets.grid&&measured.geometry);
        const rootPrefix=`books-${c.pk}-0`;
        const content=prefix=>page.locator(`#editor .cv-formset-content[cv-data-formset-prefix="${prefix}"]`);
        const ownButton=(node,kind)=>node.locator(`:scope > .cv-formset-row > .cv-formset-form .cv-form-ctrl-${kind}`);
        await page.evaluate(()=>{window.originalHeadings=[...document.querySelectorAll('#editor .cv-formset-compact-headings')];});
        const originalRows=await page.locator('#editor .cv-formset-row').count();
        const firstTitle=page.locator(`#editor [name="${rootPrefix}-0-title"]`);
        await firstTitle.fill('Retained while loading');
        let release, routed;
        const pending=new Promise(resolve=>{routed=resolve;});
        await page.route('**/*template=*',async route=>{routed();await new Promise(resolve=>{release=resolve;});await route.continue();});
        const parentPromise=add(ownButton(content(rootPrefix),'add').last());
        await pending;
        check('pending-preserves-data',await page.locator('#editor .cv-formset-row').count()===originalRows && await firstTitle.inputValue()==='Retained while loading' && await firstTitle.isVisible());
        release();const parent=await parentPromise;await page.unroute('**/*template=*');
        const newParent=parent.rows[0];
        await page.locator(`#editor [name="${newParent}-title"]`).fill('Browser compact added parent');
        const parentRow=page.locator(`#editor .cv-formset-row[cv-data-formset-form-prefix="${newParent}"]`);
        check('authorized-parent-fragment',parent.html.includes('cv-formset-row-compact') && await parentRow.locator('.cv-formset-compact-headings').count()>=3 && !parent.html.trim().startsWith('<div class="row cv-formset-compact-headings'));
        const childContent=parentRow.locator('.cv-formset-content[cv-data-formset-prefix^="books-notes-"]').first();
        const child=await add(ownButton(childContent,'add').last());
        await page.locator(`#editor [name="${child.rows[0]}-note"]`).fill('Added parent child');
        const secondBook=before.books.filter(b=>b.publisher_id===c.pk)[1];
        const siblingPrefix=`books-memos-${c.pk}-0-1-${secondBook.id}-1`;
        const sibling=await add(ownButton(content(siblingPrefix),'add').last());
        const siblingRow=page.locator(`#editor .cv-formset-row[cv-data-formset-form-prefix="${sibling.rows[0]}"]`);
        await page.locator(`#editor [name="${sibling.rows[0]}-text"]`).fill('Nonfirst parent new memo');
        check('nonfirst-child-fragment',await siblingRow.evaluate((el,id)=>el.closest('.cv-formset-fieldset').closest('.cv-formset-row').querySelector(':scope > .cv-formset-form input[name$="-id"]').value===String(id),secondBook.id));
        const firstDelete=ownButton(content(rootPrefix),'delete').first();
        await firstDelete.click();
        const marked=await page.locator(`#editor [name="${rootPrefix}-0-DELETE"]`).inputValue();
        await firstDelete.click();
        const unmarked=await page.locator(`#editor [name="${rootPrefix}-0-DELETE"]`).inputValue();
        await siblingRow.locator(':scope > .cv-formset-form .cv-form-ctrl-up').click();
        await siblingRow.locator(':scope > .cv-formset-form .cv-form-ctrl-up').click();
        const firstMemo=before.memos.find(m=>m.book_id===before.books.find(b=>b.publisher_id===c.pk).id);
        const firstMemoPrefix=`books-memos-${c.pk}-0-0-${firstMemo.book_id}-1`;
        await ownButton(content(firstMemoPrefix),'delete').first().click();
        check('delete-unmark-order',marked==='1'&&unmarked!=='1' && await content(siblingPrefix).locator(':scope > .cv-formset-row').first().getAttribute('cv-data-formset-form-prefix')===sibling.rows[0]);
        check('heading-ownership',await page.evaluate(()=>originalHeadings.every(h=>h.isConnected&&!h.closest('.cv-formset-row')?.matches(`[cv-data-formset-prefix="${h.parentElement.getAttribute('cv-data-formset-prefix')}"]`))));
        const labels=await compactMeasurements(page);
        check('labels-and-events',labels.labels && await page.evaluate(()=>widgetEvents.length===3&&widgetEvents.every(e=>!e.duplicate)));
        const saved=await post();
        const names=saved.sent.map(([name])=>name);
        check('formdata-once',new Set(names).size===names.length && saved.sent.some(([name,value])=>name.endsWith('-DELETE')&&value==='1')&&saved.sent.some(([name])=>name.endsWith('-ORDER')),
            {duplicates:names.filter((name,index)=>names.indexOf(name)!==index),policy:saved.sent.filter(([name])=>/-DELETE$|-ORDER$/.test(name)),status:saved.status});
        assert.equal(saved.status,200,saved.body.slice(0,1000));
        const final=await state();result.persisted=final;
        const added=final.books.find(b=>b.publisher_id===c.pk&&b.title==='Browser compact added parent');
        const addedMemo=final.memos.find(m=>m.book_id===secondBook.id&&m.text==='Nonfirst parent new memo');
        check('persisted-relationships',!!added&&final.notes.some(n=>n.book_id===added.id&&n.note==='Added parent child') && !!addedMemo && addedMemo.order===1 && !final.memos.some(m=>m.id===firstMemo.id) && final.books.some(b=>b.id===firstMemo.book_id&&b.title==='Retained while loading'), {added,addedMemo,books:final.books.filter(b=>b.publisher_id===c.pk)});
        await load();
        const count=await page.locator('#editor .cv-formset-row').count();
        const stable=await state();
        await context.request.get(`${base}/signin/?denied=1`);
        const failed=page.waitForResponse(r=>r.url().includes('template=')&&r.request().method()==='GET');
        await ownButton(content(rootPrefix),'add').last().click();
        const denied=await failed;await delay(100);
        result.requests.push({status:denied.status(),url:denied.url()});
        check('unauthorized-no-insertion',denied.status()===403&&await page.locator('#editor .cv-formset-row').count()===count&&JSON.stringify(await state())===JSON.stringify(stable));
        await context.request.get(`${base}/signin/`);
        for(const width of [390,1280]) {
            await load();await page.setViewportSize({width,height:900});
            await page.locator(`#editor [name="${rootPrefix}-0-title"]`).fill('REJECT');
            const previous=await state();
            const response=page.waitForResponse(r=>r.request().method()==='POST');
            await page.locator('#editor').evaluate(form=>HTMLFormElement.prototype.submit.call(form));
            const invalid=await response;await page.waitForLoadState('load');
            result.requests.push({status:invalid.status(),url:invalid.url(),body:await invalid.text()});
            const input=page.locator(`#editor [name="${rootPrefix}-0-title"]`);
            await input.focus();
            const errorState=await input.evaluate(el=>{
                const row=el.closest('.cv-formset-row'),set=row.closest('.cv-formset-content');
                const visible=selector=>[...row.querySelectorAll(selector)].every(e=>e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden');
                return {field:row.textContent.includes('Field correction required'),hidden:row.textContent.includes('Hidden proof correction'),
                    nonfield:row.textContent.includes('Row correction required'),formset:!!set.querySelector(':scope > .alert'),
                    feedbackVisible:visible('.invalid-feedback,.alert'),focus:document.activeElement===el,
                    value:el.value,proof:row.querySelector('input[name$="-proof"]').value,compact:row.classList.contains('cv-formset-row-compact')};
            });
            const unchanged=await state();
            check(`invalid-${width}`,invalid.status()===422&&Object.entries(errorState).filter(([k])=>!['value','proof'].includes(k)).every(([,v])=>v)&&errorState.value==='REJECT'&&errorState.proof==='retained proof'&&['events','books','notes','memos','scores','leaves'].every(key=>JSON.stringify(unchanged[key])===JSON.stringify(previous[key])),errorState);
            measured=await compactMeasurements(page);assert(measured.geometry,JSON.stringify(measured.failures));
            await compactCapture(page,result,`invalid-${width}`,width,{...measured,errorState});
        }
        await load();
        const management=await post('#editor',c.url,{[`${rootPrefix}-TOTAL_FORMS`]:null});
        check('management-error',management.status===422&&management.body.includes('ManagementForm')&&management.body.includes('TOTAL_FORMS'));
        for(const edge of ['blank','zero','extra-zero','no-controls','delete-absent']) {
            await load(`/compact/${edge}/stock/${c.pk}/`);
            const observation=await content(rootPrefix).evaluate(el=>{
                const form=el.closest('form'),data=[...new FormData(form)],rows=[...el.querySelectorAll(':scope > .cv-formset-row')];
                return {data,rows:rows.length,initial:Number(el.querySelector('input[name$="-INITIAL_FORMS"]').value),total:Number(el.querySelector('input[name$="-TOTAL_FORMS"]').value),
                    headings:el.querySelectorAll(':scope > .cv-formset-compact-headings').length,add:el.querySelectorAll('.cv-form-ctrl-add').length,
                    controls:el.querySelectorAll('.cv-form-ctrl button').length,
                    extraDelete:rows.slice(Number(el.querySelector('input[name$="-INITIAL_FORMS"]').value)).some(r=>r.querySelector('[name$="-DELETE"]'))};
            });
            result.edges.push({edge,...observation});
            let correct=observation.total===observation.rows&&observation.headings===1&&new Set(observation.data.map(([name])=>name)).size===observation.data.length;
            if(edge==='blank')correct&&=observation.initial===0&&observation.total===1;
            if(edge==='zero')correct&&=observation.total===0&&observation.add===0;
            if(edge==='no-controls')correct&&=observation.controls===0;
            if(edge==='delete-absent')correct&&=!observation.extraDelete;
            if(edge==='extra-zero') {
                const response=page.waitForResponse(r=>r.url().includes('template='));
                await ownButton(content(rootPrefix),'add').last().click();const empty=await response;
                const body=await empty.text();await delay(50);
                // Existing template() indexes forms[0]; extra=0 has no AJAX template row.
                correct&&=empty.status()===500&&body.includes('IndexError')&&await content(rootPrefix).locator(':scope > .cv-formset-row').count()===observation.rows;
                observation.fragment={status:empty.status(),limitation:'Existing extra=0 template IndexError; no insertion or recovery control.'};
            }
            check(`edge-${edge}`,correct,observation);
        }
        for(const width of [390,1280]) {
            await load();await page.setViewportSize({width,height:900});
            measured=await compactMeasurements(page);assert(measured.geometry,JSON.stringify(measured.failures));
            await compactCapture(page,result,`saved-${width}`,width,measured);
        }
        check('captures',result.captures.length===4);
        result.limitations=['Human grouping review pending; no physical-device or screen-reader session.', 'Existing AJAX failure has no visible error or retry UI. Zero-total/extra=0 retains existing add limitations.'];
        return;
    }
    if (c.id === 'compact-presentation') {
        result.captures = []; result.humanReview = 'pending';
        for (const composition of compositions) {
            await load(`${c.url}?composition=${composition}`);
            const first = page.locator('#editor .cv-formset-row-compact input:not([type=hidden]):not([disabled])').first();
            await first.fill('8');
            await first.evaluate(el => {
                window.retainedCompactInput=el;
                window.retainedCompactFields=[...document.querySelectorAll('#editor input,#editor select')].map(input=>({input,value:input.value,id:input.id,name:input.name}));
            });
            for (const width of widths) {
                await page.setViewportSize({width, height: 900});
                const retained=await first.evaluate(el=>el===document.activeElement&&retainedCompactFields.every(({input,value,id,name})=>input.isConnected&&input.value===value&&input.id===id&&input.name===name));
                const measurements = await compactMeasurements(page);
                const key = `${composition}:${width}`;
                check(`${key}:assets`, measurements.assets.bootstrap && measurements.assets.compact && measurements.assets.grid);
                check(`${key}:geometry`, measurements.geometry, measurements.failures);
                check(`${key}:labels`, measurements.labels && measurements.required && measurements.help && measurements.denseSchema && measurements.textWrap, measurements);
                check(`${key}:nesting`, measurements.depth >= 3 && measurements.childInsets && measurements.parentBorders);
                // Compare classic row computed properties to a genuinely unopted baseline at this width.
                const baseline = await context.newPage();
                await baseline.setViewportSize({width, height:900});
                await baseline.goto(base + `${c.url}?composition=classic-classic`);
                const classic = await classicStyles(page), original = await classicStyles(baseline);
                check(`${key}:classic-isolation`, classic.every(style => original.some(other => JSON.stringify(other) === JSON.stringify(style))), classic);
                await baseline.close();
                const name = await first.getAttribute('name');
                const accessible = await first.ariaSnapshot();
                await page.keyboard.press('Tab');
                const tab = await page.evaluate(name => {
                    const all=[...document.querySelectorAll('#editor input:not([type=hidden]), #editor select, #editor button, #editor a[href]')]
                        .filter(el => !el.disabled && el.getClientRects().length && el.tabIndex >= 0);
                    const index=all.findIndex(el => el.name===name);
                    return document.activeElement === all[index+1];
                }, name);
                const selectName=await page.locator('#editor .cv-formset-compact-fields select').first().ariaSnapshot();
                check(`${key}:keyboard`, tab && /textbox "/.test(accessible) && /combobox "/.test(selectName), {accessible,selectName,tab});
                await first.focus();
                check(`${key}:resize-identity`, retained && await first.evaluate(el => el===window.retainedCompactInput && el===document.activeElement && el.value==='8'));
                await compactCapture(page, result, `${composition}-${width}`, width, measurements);
                check(`${key}:capture`, true);
            }
        }
        return;
    }
    const outer = page.locator('#editor input[name="outer"]');
    const inner = page.locator('#editor input[name="inner"]');
    const contact = page.locator('#editor input[name="contact"]');
    const detail = page.locator('#editor input[name="detail"]');
    async function sync() { await delay(60); }
    async function change(name, checked) {
        await page.evaluate(({name,checked}) => { const el=document.querySelector(`#editor [name="${name}"]`); el.checked=checked; el.dispatchEvent(new Event('change',{bubbles:true})); }, {name,checked});
        await sync();
    }
    async function presentation() {
        return page.evaluate(() => {
            const form=document.getElementById('editor'), outer=form.elements.outer, contact=form.elements.contact;
            const group=form.querySelector('[cv-data-toggle-field="outer"]');
            return {checked:outer.checked, defaultChecked:outer.defaultChecked, value:contact.value, defaultValue:contact.defaultValue,
                hidden:getComputedStyle(group).display==='none', disabled:contact.disabled, baseline:form.elements.baseline.disabled,
                other:document.querySelector('#other [name="contact"]').value,
                rows:form.querySelectorAll('.cv-formset-row').length,
                management:[...form.querySelectorAll('input[name$="-TOTAL_FORMS"]')].map(el=>[el.name,el.value])};
        });
    }
    if (c.id === 'gap-capability') {
        const initialUrl=`/capability/initial/${c.theme}/${c.pk}/`;
        const emptyUrl=`/capability/all-extra/${c.theme}/${c.emptyPk}/`;
        await load(initialUrl);
        let prefix=`books-memos-${c.pk}-0-0-${c.book}-1`;
        const row = index => page.locator(`#editor input[name="${prefix}-${index}-text"]`).locator('xpath=ancestor::div[contains(@class,"cv-formset-row")][1]');
        const presence=await row(1).evaluate(el=>({deleteInputs:el.querySelectorAll('[name$="-DELETE"]').length,deleteButtons:el.querySelectorAll('.cv-form-ctrl-delete').length}));
        presence.initialDeleteInputs=await row(0).locator('input[name$="-DELETE"]').count();
        check('native-delete-presence',presence.initialDeleteInputs===1&&presence.deleteInputs===0&&presence.deleteButtons===0,presence);
        const eventBefore=await page.evaluate(()=>widgetEvents.length);
        const body=await add(row(1).locator('.cv-form-ctrl-add'));
        check('add-once',body.rows.length===1&&await page.evaluate(()=>widgetEvents.length)===eventBefore+1&&await row(2).locator('input[name$="-DELETE"]').count()===0);
        await row(1).locator('input[name$="-text"]').fill('Capability first extra');
        await row(2).locator('input[name$="-text"]').fill('Capability second extra');
        await row(1).locator('.cv-form-ctrl-up').click();
        check('extra-before-initial',await row(1).evaluate(el=>el.previousElementSibling===null||!el.previousElementSibling.classList.contains('cv-formset-row')));
        await row(0).locator('.cv-form-ctrl-delete').click();
        check('stable-initial-delete',await row(0).locator('input[name$="-DELETE"]').inputValue()==='1');
        const saved=await post('#editor',initialUrl);
        const final=await state();
        result.capability={prefix,initialPrefix:`${prefix}-0`,extraPrefix:`${prefix}-1`,presence,state:final};
        const memos=final.memos.filter(m=>m.book_id===c.book);
        check('ordered-post-persisted',saved.status===200&&memos.length===2&&memos.find(m=>m.text==='Capability first extra')?.order===0&&memos.find(m=>m.text==='Capability second extra')?.order===1,{status:saved.status,memos});
        await load(emptyUrl);
        prefix=`books-memos-${c.emptyPk}-0-0-${c.emptyBook}-1`;
        const extra=await add(row(0).locator('.cv-form-ctrl-add'));
        await row(0).locator('input[name$="-text"]').fill('All extra first');
        await row(1).locator('input[name$="-text"]').fill('All extra moved');
        await row(1).locator('.cv-form-ctrl-up').click();
        const allSaved=await post('#editor',emptyUrl);
        const allState=await state();result.allExtra={rows:extra.rows,state:allState};
        check('all-extra-add-order-post',allSaved.status===200&&await page.locator(`#editor input[name^="${prefix}"][name$="-DELETE"]`).count()===0&&allState.memos.some(m=>m.book_id===c.emptyBook&&m.text==='All extra moved'&&m.order===0),{status:allSaved.status,memos:allState.memos.filter(m=>m.book_id===c.emptyBook)});
        await load();
        const beforeInvalid=await state();
        const invalid=[];
        for(const identity of [null,String(c.foreign),String(c.filtered)]) {
            const response=await post('#editor',c.url+'?reclean=1',{[`books-${c.pk}-0-0-id`]:identity,name:'Must not save'});
            invalid.push({status:response.status,generic:response.body.includes('Invalid row.')});
        }
        const editOnly=await post('#editor',c.url+'?policy=edit&reclean=1',{[`books-${c.pk}-0-1-title`]:'Forbidden extra',name:'Must not save'});
        invalid.push({status:editOnly.status,generic:editOnly.body.includes('Additions are not allowed.')});
        const rejected=await state();result.reclean={invalid,eventsBefore:beforeInvalid.events.length,eventsAfter:rejected.events.length};
        check('reclean-policy-zero-saves',invalid.every(r=>r.status===422&&r.generic)&&rejected.events.length===beforeInvalid.events.length,result.reclean);
        const host=await page.evaluate(()=>({viewport:document.querySelector('meta[name="viewport"]')?.content,container:!!document.querySelector('main.container'),icons:!!document.querySelector('link[href*="font-awesome/6.7.2"]')}));
        check('host-assets',host.viewport==='width=device-width, initial-scale=1'&&host.container&&host.icons,host);
    } else if (c.id === 'gap-ambiguity') {
        const offState=()=>page.locator('#editor').evaluate(f=>({valid:f.checkValidity(),disabled:f.elements.contact.disabled,
            hidden:getComputedStyle(f.querySelector('[cv-data-toggle-field="outer"]')).display==='none',
            contactSent:new FormData(f).has('contact'),management:[...new FormData(f).keys()].some(k=>k.endsWith('-TOTAL_FORMS'))}));
        await contact.evaluate(el=>{el.required=true;el.value='';});
        await outer.uncheck();await sync();
        const off=await offState();
        check('bound-off-native-valid',off.valid&&off.disabled&&off.hidden&&!off.contactSent&&off.management,off);
        await page.evaluate(()=>{const f=document.getElementById('editor');window.oldToggle=f.elements.outer;
            const copy=oldToggle.cloneNode(true);copy.removeAttribute('id');copy.dataset.fixture='duplicate-toggle';f.prepend(copy);cv.initConditional(f);});
        const ambiguous=await offState();
        check('ambiguous-retains-state',ambiguous.valid&&ambiguous.disabled&&ambiguous.hidden&&!ambiguous.contactSent,ambiguous);
        await page.evaluate(()=>{oldToggle.checked=true;oldToggle.dispatchEvent(new Event('change',{bubbles:true}));});await sync();
        check('no-arbitrary-checkbox-follow',(await offState()).hidden&&result.diagnostics.some(text=>text.includes('ambiguous conditional toggle')));
        const detached=await page.evaluate(()=>{const f=document.getElementById('editor');f.elements.inner.checked=false;
            oldToggle.dispatchEvent(new Event('change',{bubbles:true}));
            const unchanged=f.querySelector('[cv-data-toggle-field="inner"]').style.display!=='none';
            f.elements.inner.checked=true;oldToggle.remove();cv.initConditional(f);return unchanged;});
        check('obsolete-listener-detached',detached);
        await page.locator('#editor input[name="outer"]').check();await sync();
        check('unique-recovery',!await contact.isDisabled()&&!((await offState()).hidden));
        await contact.evaluate(el=>{el.disabled=true;});await sync();
        await page.locator('#editor input[name="outer"]').uncheck();await page.locator('#editor input[name="outer"]').check();await sync();
        check('independent-owner-retained',await contact.isDisabled());
        await page.evaluate(()=>{const f=document.getElementById('editor'),copy=f.elements.inner.cloneNode(true);copy.removeAttribute('id');copy.dataset.fixture='duplicate-inner';f.querySelector('[cv-data-toggle-field="outer"]').prepend(copy);cv.initConditional(f);});
        await page.locator('#editor input[name="outer"]').uncheck();await sync();
        check('ancestor-owner-retained',await detail.isDisabled()&&(await offState()).hidden);
        check('other-form-unaffected',await page.locator('#other input[name="outer"]').isChecked()&&!await page.locator('#other input[name="contact"]').isDisabled());
        await page.locator('#editor [data-fixture="duplicate-inner"]').evaluate(el=>el.remove());
        await page.locator('#editor .native-reset').focus();await page.keyboard.press('Enter');await sync();
        check('native-reset-focus',await page.locator('#editor input[name="outer"]').isChecked()&&await contact.isDisabled()&&await page.locator('#editor .native-reset').evaluate(el=>document.activeElement===el));
        await load(`/harness/${c.theme}/${c.pk}/`);
        await page.locator('#launch').focus();await page.keyboard.press('Enter');await page.locator('#editor').waitFor();await delay(c.theme==='stock'?400:60);
        await page.locator('#editor input[name="name"]').fill('');
        const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(c.url));
        await page.locator('#editor [type="submit"]').first().focus();await page.keyboard.press('Enter');
        const actual=await response;await actual.finished();await page.waitForFunction(()=>loadedCount===2);await sync();
        result.requests.push({status:actual.status(),url:actual.url()});
        const focused=await page.locator('#editor input[name="name"]').evaluate(el=>document.activeElement===el&&!el.disabled&&el.getClientRects().length>0);
        await page.locator('#editor input[name="contact"]').evaluate(el=>{el.required=true;el.value='';});
        await page.locator('#editor input[name="outer"]').uncheck();
        await page.locator('#editor input[name="name"]').focus();
        await page.evaluate(()=>{const f=document.getElementById('editor'),copy=f.elements.outer.cloneNode(true);copy.removeAttribute('id');copy.dataset.fixture='modal-duplicate';f.prepend(copy);cv.initConditional(f);});
        const modal=await offState();
        check('modal-422-ambiguity-focus',actual.status()===422&&focused&&modal.disabled&&modal.hidden&&!modal.contactSent&&await page.locator('#editor input[name="name"]').evaluate(el=>document.activeElement===el),modal);
        await page.locator('#editor [data-fixture="modal-duplicate"]').evaluate(el=>el.remove());
        await page.locator('#editor .native-reset').focus();await page.keyboard.press('Enter');await sync();
        check('modal-reset-focus',await page.locator('#editor input[name="outer"]').isChecked()&&!await page.locator('#editor input[name="contact"]').isDisabled()&&await page.locator('#editor .native-reset').evaluate(el=>document.activeElement===el));
        result.captures=[];
        if(c.theme==='stock') {
            const directory='.planning/ui-reviews/06.4-gap-repair';fs.mkdirSync(directory,{recursive:true});
            for(const device of [{id:'desktop',width:1440,height:900,isMobile:false,hasTouch:false,deviceScaleFactor:1},
                {id:'mobile',width:375,height:812,isMobile:true,hasTouch:true,deviceScaleFactor:1},
                {id:'tablet',width:768,height:1024,isMobile:false,hasTouch:false,deviceScaleFactor:1}]) {
                const captureContext=await context.browser().newContext({ignoreHTTPSErrors:true,viewport:{width:device.width,height:device.height},
                    isMobile:device.isMobile,hasTouch:device.hasTouch,deviceScaleFactor:device.deviceScaleFactor});
                try {
                    await captureContext.addCookies(await context.cookies());const capturePage=await captureContext.newPage();
                    const response=await capturePage.goto(base+c.url);assert.equal(response.status(),200);
                    await capturePage.evaluate(()=>document.fonts.ready);
                    // Force the actual configured font resource; a blank/missing remote asset fails capture.
                    await capturePage.evaluate(()=>document.fonts.load('900 16px "Font Awesome 6 Free"'));
                    const observation=await capturePage.evaluate(()=>({
                        document:{clientWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,innerWidth},
                        viewport:document.querySelector('meta[name="viewport"]').content,
                        icons:{loaded:document.fonts.check('900 16px "Font Awesome 6 Free"')&&[...document.fonts].some(f=>f.family.includes('Font Awesome 6 Free')&&f.status==='loaded'),
                            glyphs:[...document.querySelectorAll('.cv-form-ctrl button i')].map(el=>({content:getComputedStyle(el,'::before').content,
                                family:getComputedStyle(el,'::before').fontFamily,width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height})).filter(g=>g.content!=='none'&&g.content!=='normal'&&g.content!=='""'&&g.width>0&&g.height>0)}
                    }));
                    const screenshot=`${directory}/${device.id}.png`;
                    cp.execFileSync('git',['check-ignore',screenshot]); // NOSONAR S4036: test harness
                    await capturePage.screenshot({path:screenshot,fullPage:true});
                    result.captures.push({path:screenshot,sha256:digest(screenshot),device,...observation});
                } finally {await captureContext.close();}
            }
        }
        check('responsive-containment',result.captures.every(capture=>capture.document.clientWidth===capture.document.scrollWidth),result.captures.map(capture=>({device:capture.device,...capture.document})));
        check('loaded-rendered-glyphs',result.captures.every(capture=>capture.icons.loaded&&capture.icons.glyphs.length>0));
        check('screenshot-provenance',result.captures.every(capture=>capture.sha256===digest(capture.path)));
        result.humanReview={H1:'pending',H2:'pending',limitations:'Headless Chromium on Linux; mobile viewport/touch emulation only, no physical device or screen reader. Fixture duplicate forms and reset buttons are test-host surfaces. No human acceptance inferred.'};
        check('human-review-pending',result.humanReview.H1==='pending'&&result.humanReview.H2==='pending');
    } else if (c.id === 'fragment-raw-balance') {
        // Same actual selected child declarations as the full editor; inspect raw bytes before DOM proof.
        const memos = page.locator('#editor .cv-formset-content').filter({has: page.locator(`input[name="books-memos-${c.pk}-0-0-${c.book}-1-TOTAL_FORMS"]`)}).last();
        const body = await add(memos.locator('.cv-form-ctrl-add').first());
        const balanced = rawBalance(body.html);
        assert.throws(()=>rawBalance(body.html+'</div>'));
        assert.throws(()=>rawBalance('<div><fieldset></div></fieldset>'));
        check('raw-wrapper-stack-balanced', balanced);
        check('rows-only-outer-wrapper-absent', !body.html.includes(`name="books-memos-${c.pk}-0-0-${c.book}-1-TOTAL_FORMS"`));
        const prefix = body.rows[0];
        check('parsed-nesting-correct', await page.locator(`#editor input[name="${prefix}-text"]`).evaluate(el=>el.closest('.cv-formset-content').getAttribute('cv-data-formset-prefix')===el.name.replace(/-\d+-text$/, '')));
        await page.locator(`#editor input[name="${prefix}-text"]`).fill('Second sibling browser memo');
        const response = await post(); assert.equal(response.status,200,response.body.slice(0,200));
        const final = await state(); result.state=final;
        check('second-sibling-post-persisted', final.memos.some(m=>m.book_id===c.book&&m.text==='Second sibling browser memo'));
    } else if (c.id === 'inline-file-clear-unchanged') {
        await load(c.filesUrl);
        const response = await post('#editor', c.filesUrl);
        assert.equal(response.status,200,response.body.slice(0,400));
        const final = await state(); result.referenceState=final;
        const observed=final.observed.slice(before.observed.length).find(o=>o.pk===c.record);
        const row=final.records.find(r=>r.id===c.record);
        check('file-has-changed-false', observed?.changed===false && !observed.changed_data.includes('attachment'), observed);
        check('image-has-changed-false', observed?.changed===false && !observed.changed_data.includes('image'));
        check('actual-inline-save', final.events.slice(before.events.length).filter(e=>e.model==='BrowserConditionalRecord'&&e.pk===c.record).length===1);
        check('file-reference-cleared', row.attachment==='');
        check('image-reference-cleared', row.image==='');
        check('stored-content-retained', Object.values(c.references).every(p=>final.storage.includes(p)&&final.storageContent[p]===before.storageContent[p]));
        check('disabled-reference-retained', row.protected===c.references.protected);
        check('explicit-none-retained', row.unchanged===c.references.unchanged);
        check('untouched-extra-not-created', final.records.filter(r=>r.parent_id===c.profile).length===1);
        const upload=await post('#editor',c.filesUrl,{__upload:`records-${c.profile}-0-0-attachment`});
        assert.equal(upload.status,200,upload.body.slice(0,400));
        const uploaded=await state(); result.uploadState=uploaded;
        const received=uploaded.received.at(-1).files[`records-${c.profile}-0-0-attachment`];
        check('file-upload-received', received?.name==='off-upload.txt'&&received.size===24,received);
        check('off-file-upload-discarded', uploaded.records.find(r=>r.id===c.record).attachment==='');
        check('uploaded-file-not-stored', JSON.stringify(uploaded.storage)===JSON.stringify(final.storage)&&!uploaded.storage.some(p=>p.includes('off-upload')));
        result.imageBoundary='Real ImageField stored references only; no image bytes or dimension hooks. Separate real multipart FileField upload.';
    } else if (c.id === 'native-reset-user-default') {
        await add(page.locator('#editor .cv-form-ctrl-add').first());
        await page.locator('#other input[name="contact"]').fill('other form preserved');
        const initial=await presentation();
        await contact.fill('unsaved contact'); await outer.uncheck();
        await page.locator('#editor .native-reset').click(); await sync();
        const clicked=await presentation(); result.click=clicked;
        check('click-default-reset', clicked.checked===clicked.defaultChecked&&clicked.value===clicked.defaultValue&&!clicked.hidden&&!clicked.disabled);
        await contact.fill('keyboard change'); await outer.uncheck();
        await page.locator('#editor .native-reset').focus(); await page.keyboard.press('Enter'); await sync();
        const keyboard=await presentation(); result.keyboard=keyboard;
        check('keyboard-default-reset', keyboard.checked&&keyboard.value==='default contact'&&!keyboard.hidden&&!keyboard.disabled);
        check('post-task-default-state', keyboard.checked===keyboard.defaultChecked&&keyboard.value===keyboard.defaultValue&&keyboard.baseline);
        check('other-form-unchanged', keyboard.other==='other form preserved'&&clicked.other===keyboard.other);
        check('dynamic-rows-retained', initial.rows===clicked.rows&&initial.rows===keyboard.rows&&JSON.stringify(initial.management)===JSON.stringify(keyboard.management));
    } else if (c.id === 'native-reset-user-cancelled') {
        await contact.fill('retain on cancelled reset'); await outer.uncheck();
        await page.evaluate(()=>{ window.cancelledResets=0; document.getElementById('editor').addEventListener('reset',e=>{e.preventDefault();window.cancelledResets++;}); });
        const initial=await presentation();
        await page.locator('#editor .native-reset').click(); await sync(); const clicked=await presentation();
        check('later-listener-cancels-click', await page.evaluate(()=>cancelledResets)===1&&JSON.stringify(initial)===JSON.stringify(clicked));
        await page.locator('#editor .native-reset').focus(); await page.keyboard.press('Space'); await sync();
        const keyboard=await presentation(); result.initial=initial; result.final=keyboard;
        check('later-listener-cancels-keyboard', await page.evaluate(()=>cancelledResets)===2);
        check('values-and-state-unchanged', JSON.stringify(initial)===JSON.stringify(keyboard));
    } else if (c.id === 'disabled-same-value-ownership') {
        await outer.uncheck();
        const forbidden=[];
        const capture=r=>{if(r.url().includes('template='))forbidden.push(r.url());};page.on('request',capture);
        const initialRows=await page.locator('#editor .cv-formset-row').count();
        await page.locator('#editor .cv-form-ctrl-add').first().evaluate(el=>el.dispatchEvent(new MouseEvent('click',{bubbles:true})));
        await sync();page.off('request',capture);
        check('inactive-row-action-rejected',forbidden.length===0&&await page.locator('#editor .cv-formset-row').count()===initialRows&&
            await page.locator('#editor .cv-form-ctrl-add').first().isDisabled()&&!await page.locator(`#editor input[name="books-${c.pk}-0-TOTAL_FORMS"]`).isDisabled());
        await contact.evaluate(el=>{el.disabled=true;}); await sync();
        check('external-true-while-already-disabled', await contact.isDisabled());
        await outer.check(); await sync(); await outer.uncheck(); await outer.check(); await sync();
        check('independent-true-survives-off-on', await contact.isDisabled());
        await outer.uncheck(); await contact.evaluate(el=>{el.disabled=false;}); await sync();
        check('external-false-still-conditionally-disabled', await contact.isDisabled());
        await page.evaluate(()=>{cv.initConditional(document);cv.initConditional(document.getElementById('editor'));});
        await outer.check(); await sync();
        check('external-false-released-on-active', !await contact.isDisabled());
        await contact.evaluate(el=>el.setAttribute('disabled','')); await sync();
        await page.evaluate(()=>cv.initConditional(document));
        await outer.uncheck(); await outer.check(); await sync();
        const retained=await contact.isDisabled();
        await contact.evaluate(el=>el.removeAttribute('disabled')); await sync();
        check('reinit-preserves-owners', retained&&!await contact.isDisabled());
        result.final=await presentation();
    } else if (c.id === 'conditional-focus') {
        await outer.focus(); await page.keyboard.press('Space'); await page.keyboard.press('Space'); await page.keyboard.press('Tab');
        check('keyboard-checkbox-tab', await contact.evaluate(el=>document.activeElement===el));
        await contact.fill('retained unsaved'); await outer.uncheck(); await outer.check();
        check('retained-off-on-text', await contact.inputValue()==='retained unsaved');
        await contact.focus(); await change('outer',false);
        check('focus-toggle-fallback', await outer.evaluate(el=>document.activeElement===el));
        await outer.check(); await detail.focus();
        await inner.evaluate(el=>{el.disabled=true;}); await change('inner',false);
        check('focus-ancestor-fallback', await outer.evaluate(el=>document.activeElement===el));
        await page.evaluate(()=>{const f=document.getElementById('editor');f.elements.outer.disabled=true;f.elements.inner.disabled=false;f.elements.inner.checked=true;f.elements.inner.dispatchEvent(new Event('change',{bubbles:true}));});
        await detail.focus(); await change('outer',false);
        check('focus-owning-form-fallback', await page.locator('#editor').evaluate(el=>document.activeElement===el&&el.getAttribute('tabindex')==='-1'));
        await page.locator('#other input[name="contact"]').focus(); await change('outer',true);
        check('outside-focus-unchanged', await page.locator('#other input[name="contact"]').evaluate(el=>document.activeElement===el));
        check('two-form-isolation', await page.locator('#other input[name="outer"]').isChecked()&&!await page.locator('#other input[name="contact"]').isDisabled());
    } else if (c.id === 'lifecycle') {
        await load(`/harness/${c.theme}/${c.pk}/`);
        await page.locator('#launch').focus();
        await page.evaluate(native=>{window.earlyFocus=false;window.hiddenEvents=0;
            document.addEventListener(native?'close':'hidden.bs.modal',e=>{if(e.target.id==='cv-modal')hiddenEvents++;},true);
            document.addEventListener('cv:modal:loaded',()=>{const m=document.getElementById('cv-modal');if(!m.getClientRects().length&&m.contains(document.activeElement))earlyFocus=true;});
        },c.theme==='native');
        await page.keyboard.press('Enter'); await page.locator('#editor').waitFor(); await delay(c.theme==='stock'?400:60);
        check('no-early-focus', await page.evaluate(()=>!earlyFocus));
        await page.locator('#editor input[name="name"]').fill('');
        const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(c.url));
        await page.locator('#editor [type="submit"]').first().focus(); await page.keyboard.press('Enter');
        const actual=await response; await actual.finished(); await page.waitForFunction(()=>loadedCount===2); await sync();
        result.requests.push({status:actual.status(),url:actual.url(),body:await actual.text()});
        check('real-422', actual.status()===422);
        const focus=await page.evaluate(()=>{const el=document.activeElement;return {name:el.name,tag:el.tagName,id:el.id,inModal:!!el.closest('#cv-modal'),visible:el.getClientRects().length>0,disabled:el.disabled};});
        check('422-focus-usable', focus.name==='name'&&focus.inModal&&focus.visible&&!focus.disabled,focus);
        check('unload-before-replacement', await page.evaluate(()=>unloadAttached===true));
        await page.evaluate(()=>{cv.initConditional(document);cv.initFormsets(document);cv.initFormsets(document.getElementById('editor'));});
        const body=await add(page.locator('#editor .cv-form-ctrl-add').first());
        await page.locator(`#editor input[name="${body.rows[0]}-title"]`).fill('Modal added');
        const nested=page.locator(`#editor [cv-data-formset-form-prefix="${body.rows[0]}"]`).filter({has:page.locator(`input[name="${body.rows[0]}-title"]`)}).first();
        const memoAdd=nested.locator('.cv-formset-content[cv-data-formset-prefix^="books-memos-"] .cv-form-ctrl-add').first();
        const memo=await add(memoAdd);
        await page.locator(`#editor input[name="${memo.rows[0]}-text"]`).fill('nested widget memo');
        await page.locator('#editor input[name="name"]').fill('Valid modal parent');
        // Initial note Delete and memo ordering are actual native controls, serialized after owner reorder.
        await page.locator('#editor .cv-formset-content[cv-data-formset-prefix^="books-notes-"] .cv-form-ctrl-delete').first().click();
        const memoRow=page.locator(`#editor input[name="${memo.rows[0]}-text"]`).locator('xpath=ancestor::div[contains(@class,"cv-formset-row")][1]');
        await memoRow.locator('.cv-form-ctrl-up').click();
        const payload=await page.locator('#editor').evaluate(f=>{f.dispatchEvent(new Event('submit',{bubbles:false,cancelable:true}));return [...new FormData(f)].map(([k,v])=>[k,typeof v==='string'?v:v.name]);});
        result.payload=payload;
        check('reinitialized-once', await page.evaluate(()=>widgetEvents.length===2));
        check('delete-reorder-management', payload.some(([k,v])=>k.endsWith('-DELETE')&&v==='1')&&payload.some(([k])=>k.endsWith('-ORDER'))&&payload.some(([k,v])=>k.endsWith('-TOTAL_FORMS')&&v==='3'),payload);
        check('widgets-once', await page.evaluate(()=>widgetEvents.length===2&&widgetEvents.every(e=>!e.duplicate&&e.count>0)));
        // Recoverable invalid response invoked zero main/sibling/nested saves.
        const invalidState=await state(); assert.equal(invalidState.events.length,before.events.length);
        await page.locator('#cv-modal > [data-cv-modal-dismiss], #cv-modal-content > [data-cv-modal-dismiss]').first().focus();
        await page.keyboard.press('Enter'); await page.waitForFunction(()=>hiddenEvents===1); await sync();
        const closedFocus=await page.evaluate(()=>({id:document.activeElement.id,tag:document.activeElement.tagName,hiddenEvents}));
        check('completed-close-restores-opener', !await page.locator('#cv-modal').isVisible()&&closedFocus.id==='launch',closedFocus);
        await page.locator('#launch').focus(); await page.keyboard.press('Enter'); await page.locator('#editor').waitFor(); await delay(c.theme==='stock'?400:60);
        await page.locator('#editor [name="cancel"]').focus(); await page.keyboard.press('Enter');
        await page.waitForFunction(()=>hiddenEvents===2); await sync();
        check('cancel-restores-opener', await page.locator('#launch').evaluate(el=>document.activeElement===el));
        await page.locator('#launch').focus(); await page.keyboard.press('Enter');
        await page.locator('#editor').waitFor(); await delay(c.theme==='stock'?400:60);
        const savedRow=await add(page.locator('#editor .cv-form-ctrl-add').first());
        await page.locator(`#editor input[name="${savedRow.rows[0]}-title"]`).fill('Persisted modal book');
        const savedNested=page.locator(`#editor input[name="${savedRow.rows[0]}-title"]`).locator('xpath=ancestor::div[contains(@class,"cv-formset-row")][1]');
        const savedMemo=await add(savedNested.locator('.cv-formset-content[cv-data-formset-prefix^="books-memos-"] .cv-form-ctrl-add').first());
        await page.locator(`#editor input[name="${savedMemo.rows[0]}-text"]`).fill('Persisted nested modal memo');
        await page.locator('#editor .cv-formset-content[cv-data-formset-prefix^="books-notes-"] .cv-form-ctrl-delete').first().click();
        const successful=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(c.url));
        await page.locator('#editor [type="submit"]').first().focus(); await page.keyboard.press('Enter');
        const success=await successful; await page.waitForURL(base+c.url);
        const persisted=await state();result.persistedState=persisted;result.requests.push({status:success.status(),url:success.url()});
        const book=persisted.books.find(b=>b.publisher_id===c.pk&&b.title==='Persisted modal book');
        check('authorized-modal-persistence',success.status()===204&&!!book&&persisted.memos.some(m=>m.book_id===book.id&&m.text==='Persisted nested modal memo')&&
            !persisted.notes.some(n=>n.book_id===c.book),{status:success.status(),book});
    } else if (c.id === 'tampered-post') {
        const cases=[['edit-only-extra','edit'],['missing-id',''],['foreign-id',''],['filtered-id','']];
        const errors=[];
        for (const [id,policy] of cases) {
            await load(c.url+(policy?'?policy=edit':''));
            const prefix=`books-${c.pk}-0`;
            const mutate = id==='edit-only-extra' ? {[`${prefix}-TOTAL_FORMS`]:'2',[`${prefix}-1-title`]:'Forged extra'} : {[`${prefix}-0-id`]:id==='missing-id'?null:String(c[id==='foreign-id'?'foreign':'filtered'])};
            const response=await post('#editor',c.url+(policy?'?policy=edit':''),mutate);
            check(id,response.status===422,response.body.match(/(?:Invalid row\.|Additions are not allowed\.)/g));
            errors.push({id,generic:response.body.includes(id==='edit-only-extra'?'Additions are not allowed.':'Invalid row.')});
        }
        const noJs=await page.context().browser().newContext({javaScriptEnabled:false});
        const cookies=await context.cookies(); await noJs.addCookies(cookies);
        const direct=await noJs.newPage(); await direct.goto(base+c.url);
        const form=await direct.locator('#editor').evaluate(f=>Object.fromEntries(new FormData(f)));
        delete form[`books-${c.pk}-0-0-id`];
        const response=await noJs.request.post(base+c.url,{form}); result.direct={status:response.status()};
        check('js-disabled-direct-post', response.status()===422&&(await response.text()).includes('Invalid row.'));
        await noJs.close();
        const final=await state(); result.state=final;
        check('invalid-zero-saves', final.events.length===before.events.length);
        check('generic-policy-errors', errors.every(e=>e.generic));
    } else if (c.id === 'late-init') {
        const roots=await page.evaluate(()=>{
            const f=document.getElementById('editor'), fragment=document.createDocumentFragment();
            const box=document.createElement('div');box.innerHTML='<input type="checkbox" name="late" checked><div cv-data-toggle-group cv-data-toggle-field="late"><input name="late-value" value="retained"></div>';
            fragment.append(box);cv.initConditional(fragment);cv.initFormsets(fragment);f.append(fragment);cv.initConditional(box);cv.initFormsets(box);
            const first=!f.elements['late-value'].disabled;
            f.elements.late.checked=false;f.elements.late.dispatchEvent(new Event('change',{bubbles:true}));
            return first&&f.elements['late-value'].disabled;
        });
        check('fragment-element-roots',roots);
        const retry=await page.evaluate(()=>{
            const f=document.getElementById('editor'), group=document.createElement('div');group.setAttribute('cv-data-toggle-group','');group.setAttribute('cv-data-toggle-field','late-check');group.innerHTML='<input name="retry-value">';f.append(group);cv.initConditional(group);
            const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.name='late-check';f.prepend(checkbox);cv.initConditional(checkbox);return f.elements['retry-value'].disabled;
        });
        check('late-checkbox-retry',retry);
        // Load the shipped script after readiness into a fresh real page with the earlier script absent.
        const late=await context.newPage(); await late.goto(base+c.url+'?late=1');
        assert(await late.evaluate(()=>document.readyState==='complete'&&typeof cv.initConditional==='undefined'));
        await late.addScriptTag({url:base+'/static/crud_views/js/toggle.js'});
        await late.locator('#editor input[name="outer"]').uncheck(); await delay(50);
        check('late-script-ready',await late.locator('#editor input[name="contact"]').isDisabled()); await late.close();
        await page.evaluate(()=>{for(let i=0;i<4;i++){cv.initConditional(document);cv.initFormsets(document);}});
        const initial=await page.evaluate(()=>widgetEvents.length);
        const otherTotal=await page.locator(`#other input[name="books-${c.pk}-0-TOTAL_FORMS"]`).inputValue();
        await add(page.locator('#editor .cv-form-ctrl-add').first());
        check('reinit-single-action',await page.evaluate(()=>widgetEvents.length)===initial+1&&await page.locator(`#other input[name="books-${c.pk}-0-TOTAL_FORMS"]`).inputValue()===otherTotal);
    } else throw Error(`Unknown required case ${c.id}`);
}
async function classicStyles(page) {
    return page.locator('#editor .cv-formset-fieldset:not(.cv-formset-compact)').evaluateAll(nodes => nodes.flatMap(node =>
        [...node.querySelectorAll(':scope > .cv-formset-content > .cv-formset-row > .cv-formset-form label')].map(label => {
            const style=getComputedStyle(label), rowStyle=getComputedStyle(label.closest('.cv-formset-row'));
            return {position:style.position,clip:style.clip,display:style.display,margin:rowStyle.marginLeft,padding:rowStyle.paddingLeft};
        })));
}
async function compactMeasurements(page) {
    return page.evaluate(() => {
        const form=document.querySelector('#editor'), desktop=innerWidth>=768;
        const nodes=[...form.querySelectorAll('.cv-formset-compact')], failures=[];
        let labels=true, childInsets=true, parentBorders=true, depth=0;
        const rows=[];
        for (const node of nodes) {
            const content=node.querySelector(':scope > .cv-formset-content');
            const heading=content.querySelector(':scope > .cv-formset-compact-headings');
            if ((getComputedStyle(heading).display==='none')===desktop) failures.push('heading visibility');
            if (content.querySelectorAll(':scope > .cv-formset-compact-headings').length!==1) failures.push('heading count');
            if (node.classList.contains('cv-formset-compact-child')) childInsets &&= getComputedStyle(node).paddingLeft==='8px';
            let d=0; for(let p=node;p;p=p.parentElement) if(p.classList.contains('cv-formset-fieldset')) d++;
            depth=Math.max(depth,d);
            for (const row of content.querySelectorAll(':scope > .cv-formset-row')) {
                const grid=row.querySelector(':scope > .cv-formset-form > .cv-formset-compact-fields');
                if(!grid) { failures.push('missing grid'); continue; }
                parentBorders &&= parseFloat(getComputedStyle(row).borderLeftWidth)===1;
                const cells=[...grid.children], heads=[...heading.children], gr=grid.getBoundingClientRect();
                const rects=[];
                cells.forEach((cell,i) => {
                    const r=cell.getBoundingClientRect(), hr=heads[i].getBoundingClientRect();
                    const span=Number(cell.className.match(/col-md-(\d+)/)?.[1]);
                    const input=cell.querySelector('input:not([type=hidden]),select,button');
                    const left=input?.getBoundingClientRect().left;
                    if(desktop && (Math.abs(r.left-hr.left)>2 || Math.abs(r.width-gr.width*span/12)>2 ||
                        (left!==undefined && Math.abs(left-(hr.left+parseFloat(getComputedStyle(heads[i]).paddingLeft)))>2))) failures.push({prefix:row.getAttribute('cv-data-formset-form-prefix'),i,left,heading:hr.left,cell:r.left,width:r.width,grid:gr.width,span});
                    if(!desktop && getComputedStyle(cell).display!=='none' && Math.abs(r.width-gr.width)>2) failures.push('mobile full width');
                    rects.push({left:r.left,width:r.width,headingLeft:hr.left,span,inputLeft:left});
                    for(const control of cell.querySelectorAll('input:not([type=hidden]),select')) {
                        const label=[...form.querySelectorAll('label')].filter(l=>l.htmlFor===control.id);
                        if(label.length!==1 || !label[0].textContent.trim() || form.querySelectorAll(`[id="${control.id}"]`).length!==1) {labels=false;continue;}
                        const s=getComputedStyle(label[0]);
                        labels &&= s.display!=='none' && s.visibility!=='hidden' && !label[0].hasAttribute('aria-hidden') &&
                            (desktop ? s.position==='absolute' && s.width==='1px' : s.position==='static' && label[0].getBoundingClientRect().height>1);
                    }
                });
                rows.push({prefix:row.getAttribute('cv-data-formset-form-prefix'),cells:rects});
            }
        }
        const help=form.querySelector('.cv-formset-compact-fields .form-text');
        const dense=form.querySelector('[cv-data-formset-key="scores"] .cv-formset-compact-fields');
        const denseSchema=!!dense && JSON.stringify([...dense.children].map(cell=>Number(cell.className.match(/col-md-(\d+)/)?.[1])))===JSON.stringify([3,1,1,1,1,1,1,1,2]) &&
            !!dense.querySelector('select[name$="-taster"]') && dense.querySelector('[name$="-overall"]').disabled &&
            !dense.querySelector('[name$="-sweetness"]').required;
        const longLabel=dense?.querySelector('label');
        const textWrap=!!help&&help.scrollWidth<=help.clientWidth+1 && (!desktop ? longLabel.getBoundingClientRect().height>parseFloat(getComputedStyle(longLabel).lineHeight) : true);
        const grid=form.querySelector('.cv-formset-compact-fields');
        const scroll={width:document.documentElement.scrollWidth,client:document.documentElement.clientWidth};
        if(scroll.width>scroll.client) failures.push(scroll);
        return {assets:{bootstrap:[...document.styleSheets].some(s=>s.href?.includes('bootstrap.min.css')),
            compact:[...document.styleSheets].some(s=>s.href?.includes('formset.css')) && ['8px','16px'].includes(getComputedStyle(nodes[0].querySelector('.cv-formset-row')).paddingLeft),
            grid:getComputedStyle(grid).display==='flex'},geometry:failures.length===0,failures,labels,childInsets,parentBorders,depth,rows,scroll,
            denseSchema,textWrap,required:!!form.querySelector('.cv-formset-compact-label .asteriskField'),
            help:!!help && help.getBoundingClientRect().height>0 && getComputedStyle(help.parentElement.parentElement).overflowWrap==='anywhere'};
    });
}
async function compactCapture(page, result, name, width, measurements) {
    const capturePath=`${compactPhase}/browser-captures/${result.id}/${name}.png`;
    assert.equal(cp.spawnSync('git', ['check-ignore', '--no-index', capturePath]).status, 0, 'Compact PNG must be ignored');
    fs.mkdirSync(path.dirname(capturePath), {recursive:true});
    await page.screenshot({path:capturePath,fullPage:true});
    result.captures.push({path:capturePath,sha256:digest(capturePath),width,measurements});
}
(argv.includes('--check-evidence') ? Promise.resolve().then(()=>checkEvidence(option('--check-evidence'))) : main()).catch(error => { console.error(error); process.exitCode = 1; });
