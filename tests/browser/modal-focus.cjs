// Real HTTP/browser regression. Reuses installed runtimes; never installs packages.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const net = require('node:net');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
process.chdir(root);
const phase = '.planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282';
const runtime = JSON.parse(fs.readFileSync('.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json'));
const node = process.env.CV_FOCUS_NODE || runtime.node.path;
if (fs.realpathSync(process.execPath) !== fs.realpathSync(node)) {
    const result = cp.spawnSync(node, [__filename, ...process.argv.slice(2)], {stdio: 'inherit'});
    if (result.error) console.error(result.error);
    process.exit(result.status ?? 1);
}
const argv = process.argv.slice(2);
function option(name, fallback) { const i = argv.indexOf(name); return i < 0 ? fallback : argv[i + 1]; }
const output = option('--output', `${phase}/19-evidence/browser-results.json`);
const base = 'http://127.0.0.1:8143';
const screenshotDir = '.planning/ui-reviews/06.3-focus';
const inputs = [
    'src/crud_views/static/crud_views/js/modal.js', 'src/crud_views/static/crud_views/js/adapters.js',
    'tests/js/modal.test.js', 'tests/js/adapters.test.js', 'CHANGELOG.md', 'docs/migrating-1.0.md',
    'src/crud_views/lib/deletion.py', 'src/crud_views/lib/views/delete.py',
    'src/crud_views/templates/crud_views/view_delete.content.html', 'tests/test1/app/templates/app/base.html',
    'tests/browser/modal-focus.cjs', 'docs/reference/javascript.md', 'docs/reference/modals.md',
    `${phase}/17-evidence/server.py`, 'src/crud_views/templates/crud_views/modal/shell.html',
    'src/crud_views/templates/crud_views/modal/content.html', 'package-lock.json',
];
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const hashes = () => Object.fromEntries(inputs.map(file => [file, digest(file)]));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

const CASE_IDS = ['unchecked', 'blocked', 'close', 'escape', 'removed-opener', 'disabled-opener', 'hidden-opener', 'repeated-open', 'native-dialog', 'controls'];
function checkEvidence(file) {
    const record = JSON.parse(fs.readFileSync(file));
    assert(record.completed && record.passed && !record.error, 'Run incomplete or failed');
    assert.deepEqual(Object.keys(record.sourceHashes).sort(), inputs.slice().sort(), 'Wrong source input set');
    assert.deepEqual(record.sourceHashes, hashes(), 'Stale source hashes');
    assert(record.runtime.node && record.runtime.browser && record.runtime.python && record.runtime.playwrightPath && record.runtime.chromiumPath, 'Missing runtime');
    assert(Array.isArray(record.command) && record.command.length >= 2 && record.revision && record.captured, 'Missing command/revision');
    assert(Array.isArray(record.pageErrors) && record.pageErrors.length === 0, 'Page errors');
    assert.deepEqual(record.cases.map(c => c.id).sort(), CASE_IDS.slice().sort(), 'Missing/duplicate case');
    for (const result of record.cases) {
        assert(result.passed && result.assertions.length >= 2 && result.assertions.every(a => a.passed === true && a.name), `Failed assertions: ${result.id}`);
        const names = result.assertions.map(a => a.name);
        const required = ['no page errors'];
        if (['unchecked', 'native-dialog'].includes(result.id)) required.push('real HTTP status', 'invalid confirmation retains keyboard focus', 'one visible form and field error', 'row retained and zero custom callbacks');
        if (result.id === 'blocked') required.push('real protection added', 'real HTTP status', 'blocked response focuses Close', 'blocked focus remains visible', 'both notices remain and form is absent', 'filtered hidden label stays hidden', 'row retained and zero custom callbacks');
        if (result.id === 'controls') required.push('Tab stays inside modal', 'Cancel navigates to configured URL', 'row retained and zero custom callbacks', 'Space checks confirmation', 'real HTTP status', 'confirmed Delete removes row and calls real custom handler');
        else required.push('completed dismissal hides dialog', 'exact usable return target', 'return focus is visible and outside dialog', 'hidden event observes completed hiding', 'restore after completed hide');
        assert(required.every(name => names.includes(name)), `Missing required assertion: ${result.id}`);
        if (['unchecked', 'blocked', 'native-dialog'].includes(result.id)) assert.deepEqual(result.statuses, [422]);
        if (result.id === 'controls') assert.deepEqual(result.statuses, [204]);
        if (result.id === 'repeated-open') {
            assert.equal(result.hideEvents.length, 5);
            assert(names.includes('rapid reopen survives the previous hide transition') && names.includes('reopened session still recovers replacement focus'));
        }
        if (result.id === 'native-dialog') assert.equal(result.hideEvents.length, 2);
        assert(result.screenshots.length > 0, `No screenshots: ${result.id}`);
        for (const shot of result.screenshots) assert.equal(digest(shot.path), shot.sha256, `Missing/stale screenshot ${shot.path}`);
    }
    console.log('FOCUS_EVIDENCE_OK');
}
async function main() {
    const record = {captured: new Date().toISOString(), revision: cp.execFileSync('git', ['rev-parse', 'HEAD'], {encoding: 'utf8'}).trim(),
        sourceHashes: hashes(), command: [process.execPath, __filename, ...argv], runtime: {node: process.version, nodePath: process.execPath},
        completed: false, passed: false, cases: [], pageErrors: []};
    let child, browser;
    fs.mkdirSync(path.dirname(output), {recursive: true});
    fs.mkdirSync(screenshotDir, {recursive: true});
    try {
        // Refuse an occupied port; never attach to or kill an unrelated host.
        await new Promise((resolve, reject) => {
            const probe = net.createServer(); probe.once('error', reject);
            probe.listen(8143, '127.0.0.1', () => probe.close(resolve));
        });
        const python = process.env.CV_FOCUS_PYTHON || path.join(root, '.nox/crispy_floor-3-12-django-6-0/bin/python');
        const playwright = process.env.CV_FOCUS_PLAYWRIGHT || '/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
        const chromium = process.env.CV_FOCUS_CHROMIUM || '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
        for (const file of [python, playwright, chromium]) assert(fs.existsSync(file), `Missing runtime: ${file}`);
        record.runtime.python = cp.execFileSync(python, ['-c', 'import sys,django; print(sys.version); print(django.get_version())'], {encoding: 'utf8'}).trim();
        record.runtime.pythonPath = python; record.runtime.playwrightPath = playwright; record.runtime.chromiumPath = chromium;
        const log = fs.openSync(output + '.server.log', 'w');
        child = cp.spawn(python, [`${phase}/17-evidence/server.py`], {cwd: root,
            env: {...process.env, PYTHONPATH: `${root}/src:${root}`, PYTHONUNBUFFERED: '1'}, stdio: ['ignore', log, log]});
        fs.closeSync(log);
        let spawnError; child.on('error', error => { spawnError = error; });
        let ready = false;
        for (let i = 0; i < 150; i++) {
            if (spawnError) throw spawnError;
            assert(child.exitCode === null && child.signalCode === null, `Fixture exited ${child.exitCode}`);
            try { ready = (await fetch(base + '/cases/', {signal: AbortSignal.timeout(1000)})).ok; } catch (_) { /* startup */ }
            if (ready) break;
            await delay(200);
        }
        assert(ready, 'Fixture readiness timeout');
        browser = await require(playwright).chromium.launch({headless: true, executablePath: chromium, args: ['--no-sandbox']});
        record.runtime.browser = browser.version();
        const context = await browser.newContext({ignoreHTTPSErrors: true});
        const page = await context.newPage();
        page.setDefaultTimeout(15000);
        page.on('pageerror', error => record.pageErrors.push(error.message));
        await page.goto(base + '/signin/');
        const cases = await (await context.request.get(base + '/cases/')).json();
        if (argv.includes('--visual')) {
            record.results = [];
            for (const c of cases.filter(c => ['partial', 'blocked'].includes(c.mode))) {
                await context.addCookies([{name: 'review_language', value: c.language, url: base}]);
                for (const viewport of [{width: 1440, height: 900}, {width: 768, height: 1024}, {width: 375, height: 812}]) {
                    await page.setViewportSize(viewport);
                    for (const mode of ['page', 'modal']) {
                        if (mode === 'page') assert.equal((await page.goto(base + c.url)).status(), 200);
                        else {
                            await page.goto(base + '/harness/?target=' + encodeURIComponent(c.url));
                            await page.waitForFunction(() => typeof bootstrap === 'object' && typeof cv.cvModalOpen === 'function');
                            await page.locator('#launch').focus(); await page.keyboard.press('Enter');
                            await page.locator('#cv-modal').waitFor({state: 'visible'}); await delay(400);
                        }
                        const region = page.locator(mode === 'page' ? 'main' : '#cv-modal');
                        const text = await region.innerText();
                        assert(text.includes(c.language === 'de' ? 'Diese Vorschau ist unvollständig.' : 'This preview is incomplete.'));
                        assert(text.includes('München 東京 <escaped>') && text.includes('Nested 0 — 雪'));
                        assert(!text.includes('HIDDEN-CONTRACT'));
                        assert.equal(await region.locator('form.cv-form').count(), c.mode === 'blocked' ? 0 : 1);
                        const stem = `${screenshotDir}/visual-${c.language}-${c.mode}-${mode}-${viewport.width}x${viewport.height}`;
                        const file = stem + '.png'; await page.screenshot({path: file, fullPage: true});
                        const item = {case: c, viewport, mode, screenshots: [{path: file, sha256: digest(file)}],
                            ...await region.evaluate(el => ({text: el.innerText, scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
                                scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
                                alerts: [...el.querySelectorAll('[role="alert"]')].map(e => e.innerText),
                                controls: [...el.querySelectorAll('input,button,a')].map(e => ({tag: e.tagName, name: e.name, text: e.innerText})),
                                font: getComputedStyle(el).fontFamily}))};
                        if (c.mode === 'partial') {
                            const confirm = region.locator('input[name="confirm"]'); await confirm.scrollIntoViewIfNeeded();
                            item.confirmationAccessible = await confirm.isVisible(); assert(item.confirmationAccessible);
                            const scrolled = stem + '-confirmation.png'; await page.screenshot({path: scrolled}); item.screenshots.push({path: scrolled, sha256: digest(scrolled)});
                        }
                        record.results.push(item);
                        if (mode === 'modal') {
                            await page.locator('#cv-modal [data-cv-modal-dismiss]').focus(); await page.keyboard.press('Enter');
                            await page.waitForFunction(() => !document.querySelector('.modal-backdrop'));
                        }
                    }
                }
            }
            assert.equal(record.pageErrors.length, 0);
        } else {
        const requested = option('--case', 'all');
        const ids = requested === 'all' ? CASE_IDS : [requested];
        assert(ids.every(id => CASE_IDS.includes(id)), 'Unknown case');
        async function snapshot() {
            return page.evaluate(() => {
                const el = document.activeElement, style = getComputedStyle(el);
                return {tag: el.tagName, id: el.id, name: el.name, connected: el.isConnected,
                    visible: !!el.getClientRects().length && style.visibility !== 'hidden',
                    focusVisible: el.matches(':focus-visible'), inModal: !!el.closest('#cv-modal'),
                    main: el.matches('main, [role="main"]'), outline: style.outline, boxShadow: style.boxShadow};
            });
        }
        for (const id of ids) {
            const result = {id, passed: false, assertions: [], screenshots: [], observations: []}; record.cases.push(result);
            const check = (name, condition) => { result.assertions.push({name, passed: Boolean(condition)}); assert(condition, `${id}: ${name}`); };
            const c = cases.find(c => c.mode === (id === 'blocked' ? 'stale' : 'partial') && c.language === 'en');
            const native = id === 'native-dialog';
            async function capture(label) {
                const state = await snapshot(); result.observations.push({label, ...state});
                const file = `${screenshotDir}/${path.basename(output, '.json')}-${id}-${label}.png`;
                await page.screenshot({path: file}); result.screenshots.push({path: file, sha256: digest(file)});
                return state;
            }
            async function open(target = c, trigger = '#launch', fresh = true) {
                if (fresh) {
                    await page.goto(base + '/harness/?target=' + encodeURIComponent(target.url));
                    await page.waitForFunction(() => typeof bootstrap === 'object' && typeof cv.cvModalOpen === 'function');
                    if (native) {
                        const docs = fs.readFileSync('docs/reference/javascript.md', 'utf8').split('## A non-Bootstrap modal')[1].split('## A non-Bootstrap tooltip')[0];
                        const shell = docs.match(/```html\n([\s\S]*?)```/)[1];
                        const code = docs.match(/```javascript\n([\s\S]*?)```/)[1];
                        await page.evaluate(({shell, code}) => {
                            document.getElementById('cv-modal').outerHTML = shell;
                            // Execute the published adapter, with no Bootstrap involvement.
                            new Function('cv', code)(cv); window.bootstrap = undefined;
                        }, {shell, code});
                    }
                    await page.evaluate(native => {
                        window.focusEvents = [];
                        document.addEventListener(native ? 'close' : 'hidden.bs.modal', event => {
                            if (event.target.id === 'cv-modal') focusEvents.push({kind: 'hidden', visible: !!event.target.getClientRects().length});
                        }, true);
                        document.addEventListener('focusin', event => {
                            if (event.target.id === 'launch' || event.target.id === 'alternate' || event.target.matches('main'))
                                focusEvents.push({kind: 'return', id: event.target.id, main: event.target.matches('main')});
                        });
                    }, native);
                }
                await page.locator(trigger).focus(); await page.keyboard.press('Enter');
                await page.locator('#cv-modal').waitFor({state: 'visible'}); await delay(native ? 50 : 400);
                await page.evaluate(() => { focusEvents = []; });
            }
            async function dismiss(key = 'Enter', expected = 'launch') {
                if (key === 'Enter') await page.locator('#cv-modal [data-cv-modal-dismiss]').focus();
                await page.keyboard.press(key);
                await page.waitForFunction(() => focusEvents.some(e => e.kind === 'hidden'));
                const state = await capture(`dismiss-${result.observations.length}`);
                const events = await page.evaluate(() => focusEvents);
                result.hideEvents = [...(result.hideEvents || []), events];
                check('completed dismissal hides dialog', !await page.locator('#cv-modal').isVisible());
                check('exact usable return target', expected === 'main' ? state.main : state.id === expected);
                check('return focus is visible and outside dialog', state.connected && state.visible && state.focusVisible && !state.inModal);
                // Native dialog may itself restore focus while closing, before its queued close event.
                const hidden = events.findIndex(e => e.kind === 'hidden');
                check('hidden event observes completed hiding', hidden >= 0 && events[hidden].visible === false);
                check('restore after completed hide', native || (hidden === 0 && events.length === 2 && events[1].kind === 'return'));
            }
            async function submit(target, expectedStatus) {
                await page.locator('#cv-modal [type="submit"]').focus();
                const response = page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes(target.url));
                await page.keyboard.press('Enter'); const actual = (await response).status();
                result.statuses = [...(result.statuses || []), actual]; check('real HTTP status', actual === expectedStatus);
            }
            async function noWrites(target) {
                const state = await (await context.request.get(`${base}/state/${target.pk}/`)).json();
                result.state = state; check('row retained and zero custom callbacks', state.exists && state.events.length === 0);
            }
            await open();
            if (['unchecked', 'native-dialog'].includes(id)) {
                await submit(c, 422);
                await page.waitForFunction(() => document.querySelector('#cv-modal .invalid-feedback'));
                const state = await capture('unchecked');
                check('invalid confirmation retains keyboard focus', state.name === 'confirm' && state.inModal && state.visible && state.focusVisible);
                check('one visible form and field error', await page.locator('#cv-modal form.cv-form').count() === 1 && await page.locator('#cv-modal .invalid-feedback').first().isVisible());
                await noWrites(c); await dismiss();
                if (native) { await open(c, '#launch', false); await dismiss('Escape'); }
            } else if (id === 'blocked') {
                await page.locator('#cv-modal input[name="confirm"]').focus(); await page.keyboard.press('Space');
                check('real protection added', (await context.request.post(`${base}/protect/${c.pk}/`)).status() === 200);
                await submit(c, 422); await page.locator('#cv-modal form.cv-form').waitFor({state: 'detached'});
                const state = await capture('blocked'); const text = await page.locator('#cv-modal').innerText();
                check('blocked response focuses Close', await page.locator('#cv-modal [data-cv-modal-dismiss]').evaluate(el => el === document.activeElement));
                check('blocked focus remains visible', state.inModal && state.visible && state.focusVisible);
                check('both notices remain and form is absent', text.includes('This preview is incomplete.') && text.includes('Deletion is blocked by protected relationships') && await page.locator('#cv-modal form').count() === 0);
                check('filtered hidden label stays hidden', !text.includes('HIDDEN-CONTRACT'));
                await noWrites(c); await dismiss();
            } else if (id === 'close' || id === 'escape') {
                await dismiss(id === 'escape' ? 'Escape' : 'Enter');
            } else if (['removed-opener', 'disabled-opener', 'hidden-opener'].includes(id)) {
                await page.locator('#launch').evaluate((el, kind) => {
                    if (kind === 'removed-opener') el.remove();
                    if (kind === 'disabled-opener') el.setAttribute('aria-disabled', 'true');
                    if (kind === 'hidden-opener') el.hidden = true;
                }, id);
                await dismiss('Enter', 'main');
            } else if (id === 'repeated-open') {
                await dismiss();
                await page.locator('#launch').evaluate(el => { const other = el.cloneNode(true); other.id = 'alternate'; other.innerHTML = '<span>Alternate opener</span>'; el.after(other); });
                for (const trigger of ['#alternate', '#launch', '#alternate']) { await open(c, trigger, false); await dismiss('Escape', trigger.slice(1)); }
                await open(c, '#launch', false);
                await page.evaluate(url => {
                    cv.adapters.modal.hide(document.getElementById('cv-modal'));
                    cv.cvModalOpen(url, '', document.getElementById('alternate'));
                }, c.url);
                await delay(800);
                check('rapid reopen survives the previous hide transition', await page.locator('#cv-modal').isVisible());
                await page.evaluate(() => { focusEvents = []; });
                await submit(c, 422); await page.waitForFunction(() => document.querySelector('#cv-modal .invalid-feedback'));
                check('reopened session still recovers replacement focus', (await snapshot()).name === 'confirm');
                await dismiss('Escape', 'alternate');
            } else if (id === 'controls') {
                for (let i = 0; i < 8; i++) { await page.keyboard.press('Tab'); check('Tab stays inside modal', (await snapshot()).inModal); }
                const cancel = page.locator('#cv-modal [data-cv-cancel-url]'); const url = await cancel.getAttribute('data-cv-cancel-url');
                await cancel.focus(); await page.keyboard.press('Enter'); await page.waitForURL(base + url);
                check('Cancel navigates to configured URL', page.url() === base + url); await noWrites(c);
                const success = cases.find(c => c.mode === 'success' && c.language === 'en'); await open(success);
                await page.locator('#cv-modal input[name="confirm"]').focus(); await page.keyboard.press('Space');
                check('Space checks confirmation', await page.locator('#cv-modal input[name="confirm"]').isChecked()); await capture('confirmed');
                await submit(success, 204); await page.waitForURL(url => !url.pathname.includes('/harness/'));
                const state = await (await context.request.get(`${base}/state/${success.pk}/`)).json(); result.deletedState = state;
                check('confirmed Delete removes row and calls real custom handler', !state.exists && state.events.length > 0);
            }
            check('no page errors', record.pageErrors.length === 0); result.passed = true;
        }
        }
        record.completed = true; record.passed = true;
    } catch (error) { record.error = error.stack; record.completed = true; throw error; }
    finally {
        try {
            if (browser) await browser.close();
        } catch (error) {
            record.passed = false; record.cleanupError = error.stack; process.exitCode = 1;
        } finally {
            try {
                if (child && child.exitCode === null && child.signalCode === null) {
                    child.kill('SIGTERM');
                    await Promise.race([new Promise(resolve => child.once('exit', resolve)), delay(3000)]);
                    if (child.exitCode === null && child.signalCode === null) {
                        child.kill('SIGKILL'); await new Promise(resolve => child.once('exit', resolve));
                    }
                }
            } finally {
                fs.writeFileSync(output, JSON.stringify(record, null, 2) + '\n');
            }
        }
    }
    assert(record.passed, 'Browser cleanup failed');
    console.log('FOCUS_BROWSER_OK');
}
(argv.includes('--check-evidence') ? Promise.resolve().then(() => checkEvidence(option('--check-evidence'))) : main()).catch(error => { console.error(error); process.exitCode = 1; });
