'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const {loadAssets: readAssets, assetFor, runtime} = require('./cancel-navigation.cjs');
const {startOwned, cleanupServer} = require('./workflow-presentation.cjs');
const root = path.resolve(__dirname, '../..');
const host = 'tests/browser/templates/workflow_validation/page.html';
const sha = body => crypto.createHash('sha256').update(body).digest('hex');
const cached = (directory, suffix) => fs.existsSync(directory) ? fs.readdirSync(directory).sort().reverse().map(name => path.join(directory, name, suffix)) : [];

function declarations() {
    return [...fs.readFileSync(path.join(root, host), 'utf8').matchAll(/<(?:link|script)\b[^>]*?(?:href|src)="(https:[^"]+)"[^>]*>/gs)]
        .map(([tag, url]) => ({url, integrity: tag.match(/integrity="([^"]+)"/)?.[1], css: url.endsWith('.css')}));
}
function loadAssets(directory, declared = declarations()) {
    assert(directory, 'CV_WORKFLOW_ASSETS_DIR must name a local assets.json directory');
    return readAssets(directory, declared);
}

function requiredCases(selection) {
    assert(['smoke', 'all'].includes(selection));
    const smoke = ['native-first-page', 'required-recovery-page'];
    return selection === 'smoke' ? smoke : [...smoke,
        ...['label-safety', 'empty', 'one', 'all-none', 'optional', 'mixed', 'initial-blockers',
            'post-blockers', 'late-refusal', 'invalid-choice', 'custom-errors', 'cancel-omitted'].flatMap(name => ['page', 'modal'].map(mode => `${name}-${mode}`)),
        'implicit-submit-custom-input-page', 'textarea-enter-page', 'modal-lifecycle', 'radio-custom-page',
        'repeated-forms-page', 'cancel-page', 'keyboard-page',
        ...['page', 'modal'].flatMap(mode => [375, 1440].map(width => `long-${mode}-${width}`))];
}
function validateEvidence(report, selection) {
    for (const id of requiredCases(selection)) assert(report.cases.some(item => item.id === id && item.passed), `Missing case: ${id}`);
    assert.deepEqual(report.failures, []);
    assert(report.cleanup.stopped && report.cleanup.databaseRemoved, 'Owned cleanup incomplete');
    const manifest = report.assetManifest;
    assert(manifest && path.isAbsolute(manifest.directory ?? '') && path.isAbsolute(manifest.path ?? ''), 'Resolved asset provenance missing');
    assert.equal(manifest.path, path.join(manifest.directory, 'assets.json'));
    assert(manifest.suppliedDirectory && /^[a-f0-9]{64}$/.test(manifest.sha256), 'Manifest input/hash missing');
    assert.equal(report.environment?.CV_WORKFLOW_ASSETS_DIR, manifest.suppliedDirectory, 'Asset invocation environment missing');
    assert(Array.isArray(report.command) && report.command.length >= 4, 'Actual command missing');
    assert(report.sources && Object.keys(report.sources).length > 0, 'Source hashes missing');
}

function sources() {
    const files = cp.execFileSync('git', ['ls-files', 'src/crud_views', 'src/crud_views_workflow', 'tests/test1'], {cwd: root, encoding: 'utf8'}).trim().split('\n');
    files.push(host, 'tests/browser/workflow_validation_server.py', 'tests/browser/workflow-validation.cjs',
        'tests/browser/workflow-validation.test.cjs', 'tests/browser/cancel-navigation.cjs', 'tests/browser/workflow-presentation.cjs');
    return Object.fromEntries([...new Set(files)].sort().map(file => [file, sha(fs.readFileSync(path.join(root, file)))]));
}
async function inspect(page, scope = 'form.cv-form') {
    const result = await page.locator(scope).evaluate(form => {
        const group = form.querySelector('[role=group]');
        const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
        const refs = [...form.querySelectorAll('[aria-describedby]')].flatMap(el => el.getAttribute('aria-describedby').split(/\s+/));
        return {tokens: form.querySelectorAll('[name=csrfmiddlewaretoken]').length, nested: form.querySelectorAll('form').length,
            ownership: [...form.querySelectorAll('input,textarea,button')].every(el => el.form === form),
            actions: [...form.querySelectorAll('button[name=transition]')].map(el => ({name: el.value, disabled: el.disabled, label: el.textContent})),
            group: group && {name: group.getAttribute('aria-label'), classes: group.className},
            duplicateIds: ids.filter((id, index) => ids.indexOf(id) !== index),
            unresolved: refs.filter(id => document.querySelectorAll(`[id="${CSS.escape(id)}"]`).length !== 1),
            width: form.getBoundingClientRect().width, viewport: innerWidth, documentWidth: document.documentElement.scrollWidth,
            errors: [...form.querySelectorAll('.invalid-feedback')].map(el => ({text: el.textContent.trim(),
                width: el.getBoundingClientRect().width, height: el.getBoundingClientRect().height,
                display: getComputedStyle(el).display, visibility: getComputedStyle(el).visibility}))};
    });
    assert.equal(result.tokens, 1); assert.equal(result.nested, 0); assert(result.ownership);
    assert.deepEqual(result.duplicateIds, []); assert.deepEqual(result.unresolved, []);
    if (result.group) assert(!/\bform-(control|select)\b/.test(result.group.classes));
    for (const error of result.errors) assert(error.width > 0 && error.height > 0 && error.display !== 'none' && error.visibility === 'visible', `Hidden error: ${JSON.stringify(error)}`);
    return result;
}

async function runCases(browser, assets, server, report, opts) {
    const base = `http://127.0.0.1:${server.ready.ready}`;
    async function newContext(modal, width) {
        const context = await browser.newContext({javaScriptEnabled: modal, viewport: {width, height: 844}, serviceWorkers: 'block'});
        context.setDefaultTimeout(10000);
        if (modal) await context.addInitScript(() => {
            window.workflowModalEvents = [];
            document.addEventListener('cv:modal:loaded', () => window.workflowModalEvents.push('loaded'));
        });
        await context.route('**/*', async route => {
        const url = route.request().url();
        if (url.startsWith(base + '/')) return route.continue();
        try {
            const asset = assetFor(assets, url);
            await route.fulfill({status: 200, body: asset.body, contentType: url.endsWith('.css') ? 'text/css' : url.endsWith('.js') ? 'text/javascript' : 'font/woff2', headers: {'access-control-allow-origin': '*'}});
            report.assets.push({url, status: 200, sha256: asset.sha256, source: asset.file});
        } catch (error) {report.failures.push(error.message); await route.abort();}
        });
        assert.equal((await context.request.get(base + '/signin/')).status(), 200);
        return context;
    }
    for (const id of requiredCases(opts.case)) {
        const modal = id.includes('modal'), width = id.endsWith('1440') ? 1440 : 375;
        const context = await newContext(modal, width);
        try {
            const page = await context.newPage(), posts = [];
            page.on('pageerror', error => report.failures.push(error.message));
            page.on('response', response => {
                if (response.request().method() === 'POST' && response.url().includes('/workflow/')) posts.push({url: response.url(), status: response.status(),
                    redirect: response.headers()['x-cv-redirect'], fields: Object.fromEntries(new URLSearchParams(response.request().postData()))});
            });
            const observe = async () => (await context.request.get(`${base}/observe/${id}/`)).json();
            try {
                const url = `${base}/workflow/${id}/`;
                const scope = modal ? '#cv-modal-content form.cv-form' : 'main form.cv-form';
                const form = page.locator(scope);
                const details = {id, passed: true, javaScriptEnabled: modal, width};
                if (id === 'repeated-forms-page') {
                    await page.goto(`${base}/repeated/`);
                    assert.equal(await form.count(), 3);
                    details.forms = [];
                    for (let i = 0; i < 3; i++) details.forms.push(await inspect(page, `main form.cv-form:nth-of-type(${i + 1})`));
                    assert.equal(await page.locator('button[name=prefixed-transition]').count(), 2);
                    assert.equal(await page.locator('form.cv-form a[id$="-cancel"]').count(), 3);
                    report.cases.push(details); continue;
                }
                if (modal) {
                    assert.equal((await page.goto(`${base}/launch/${id}/`)).status(), 200);
                    for (const name of ['cv-config', 'cv-modal', 'cv-modal-dialog', 'cv-modal-content']) assert.equal(await page.locator(`#${name}`).count(), 1);
                    const loaded = page.waitForResponse(response => response.url() === url && response.request().headers()['x-cv-modal'] === 'true');
                    await page.locator('#launch').click(); assert.equal((await loaded).status(), 200);
                    await page.waitForFunction(() => window.workflowModalEvents.length === 1);
                    await page.locator('#cv-modal.show').waitFor();
                    details.loadedStatus = 200;
                } else assert.equal((await page.goto(url)).status(), 200);
                const before = await observe(); details.before = before;
                if (id.startsWith('empty-')) {
                    assert.equal(await form.count(), modal ? 1 : 0);
                    assert.equal(await page.locator('button[name=transition]').count(), 0);
                    if (!modal) assert((await page.locator('main').innerText()).includes('There are no workflow steps available'));
                    details.after = await observe(); report.cases.push(details); continue;
                }
                await page.evaluate(() => document.fonts.ready);
                const initial = await inspect(page, scope); details.initial = initial;
                async function submit(name, success = false, action = null) {
                    const count = modal ? await page.evaluate(() => window.workflowModalEvents.length) : 0;
                    const response = page.waitForResponse(r => r.url() === url && r.request().method() === 'POST');
                    // A failed click may outlast this timeout. Attach a rejection
                    // handler immediately so finally still owns process cleanup.
                    response.catch(() => {});
                    const click = action ?? (() => form.locator(`button[value=${name}]`).click());
                    if (!modal || success) await Promise.all([page.waitForNavigation(), click()]); else await click();
                    const result = await response;
                    if (modal && !success) await page.waitForFunction(count => window.workflowModalEvents.length > count, count);
                    if (!modal || success) await page.waitForLoadState('load');
                    return result;
                }
                async function success(name, action) {
                    const response = await submit(name, true, action);
                    assert.equal(response.status(), modal ? 204 : 302);
                    if (modal) assert.equal(response.headers()['x-cv-redirect'], url.replace(base, ''));
                    const after = await observe();
                    posts.at(-1).fields = after.request.fields;
                    assert.equal(after.history.length, 1); assert.equal(after.history[0].transition, name);
                    assert.equal(after.state, name === 'wf_cancel_new' ? 'canceled' : 'active');
                    assert.equal(posts.at(-1).fields.transition, name);
                    details.after = after;
                }
                async function invalid(name = 'wf_cancel_new', action) {
                    const response = await submit(name, false, action);
                    assert.equal(response.status(), modal ? 422 : 200);
                    const dom = await inspect(page, scope); assert(dom.errors.length > 0);
                    const observation = await observe();
                    posts.at(-1).fields = observation.request.fields;
                    assert.equal(observation.state, 'new'); assert.deepEqual(observation.history, []);
                    details.invalid = dom; details.after = observation;
                    assert(!await page.locator('.alert-success').count());
                    return dom;
                }
                if (id.startsWith('long-')) {
                    assert.equal(initial.actions.length, 8);
                    assert(initial.actions.every(item => item.disabled && item.label.includes(server.ready.token)));
                    const longText = server.ready.long_text + server.ready.token;
                    assert.equal(initial.group.name, longText);
                    const group = form.locator('[role=group]');
                    for (const action of initial.actions) {
                        const caption = server.ready.long_text + action.name + server.ready.token;
                        const suffix = action.name === 'wf_cancel_new' ? ' *Comment required' : '';
                        assert.equal(action.label, caption + suffix);
                        assert.equal(await form.getByRole('button', {name: caption + (suffix ? ' Comment required' : ''), exact: true}).count(), 1);
                    }
                    assert(initial.documentWidth <= width + 1, 'Workflow content causes horizontal overflow');
                    const measurement = await form.evaluate(form => {
                        const root = form.getBoundingClientRect();
                        const elements = [...form.querySelectorAll('button, label, .form-text, li, textarea, a[id$="-cancel"]')];
                        return {bounds: elements.map(el => ({tag: el.tagName, left: el.getBoundingClientRect().left, right: el.getBoundingClientRect().right,
                            ownerLeft: root.left, ownerRight: root.right})), clipped: [...form.querySelectorAll('[role=group], [role=group] *')].filter(el =>
                                // The specified accessible suffix is deliberately visually hidden, never visible content.
                                !(el.matches('button > span.visually-hidden') && el.textContent === 'Comment required') &&
                                ['hidden', 'scroll', 'auto'].includes(getComputedStyle(el).overflowY)).length,
                            reasons: [...form.querySelectorAll('[role=group] li')].map(el => el.textContent)};
                    });
                    assert.equal(measurement.reasons.length, 16); assert.equal(measurement.clipped, 0);
                    assert(measurement.bounds.every(item => item.left >= item.ownerLeft - 1 && item.right <= item.ownerRight + 1), 'Workflow element exceeds owner');
                    assert.deepEqual(measurement.reasons, initial.actions.flatMap(() => [longText, server.ready.reasons[1] + server.ready.token]));
                    assert.equal(await form.locator('b, script, em').count(), 0);
                    const guidance = form.locator('[role=group]').locator('xpath=preceding-sibling::*[1]');
                    assert.equal(await guidance.textContent(), longText);
                    assert.deepEqual(await group.locator('[id$="-help"]').allTextContents(), initial.actions.map(() => longText));
                    assert.equal(await form.locator('label[for$="-comment"]').textContent().then(value => value.trim()), longText);
                    assert.equal(await form.locator('[id$="-comment_helptext"]').textContent(), longText);
                    const cancel = form.locator('a[id$="-cancel"]'); await cancel.scrollIntoViewIfNeeded();
                    assert(await cancel.isVisible());
                    assert.equal(await form.getByRole('link', {name: server.ready.cancel_caption, exact: true}).count(), 1);
                    assert.equal((await cancel.textContent()).trim(), server.ready.cancel_caption);
                    const rawComment = '  ' + longText.repeat(2) + '  ';
                    await form.locator('[name=comment]').fill(rawComment);
                    await invalid(null, () => form.evaluate(form => form.requestSubmit()));
                    assert.equal(await form.locator('[name=comment]').inputValue(), rawComment);
                    assert(details.invalid.documentWidth <= width + 1);
                    const destination = await cancel.getAttribute('href');
                    details.geometry = measurement;
                    const filename = path.join(path.dirname(path.resolve(opts.output)), `dcv-phase06131-${id}.png`);
                    await page.screenshot({path: filename, fullPage: true});
                    report.screenshots.push({case: id, path: filename, sha256: sha(fs.readFileSync(filename))});
                    const count = posts.length;
                    await Promise.all([page.waitForNavigation(), cancel.click()]);
                    assert.equal(new URL(page.url()).pathname, new URL(destination, base).pathname);
                    assert.equal(posts.length, count);
                    assert.equal((await observe()).state, 'new'); assert.deepEqual((await observe()).history, []);
                } else if (id.startsWith('initial-blockers-') || id.startsWith('mixed-')) {
                    assert.deepEqual(initial.actions.map(item => item.disabled), id.startsWith('mixed-') ? [true, false] : [true, true]);
                    const items = await form.locator('[role=group] li').allTextContents();
                    assert.deepEqual(items, id.startsWith('mixed-') ? server.ready.reasons : [...server.ready.reasons, ...server.ready.reasons]);
                    assert(!await form.locator('script, blocker').count());
                    assert(!await page.getByText('There are no workflow steps available', {exact: false}).count());
                    details.after = await observe();
                } else if (id.startsWith('one-') || id.startsWith('all-none-') || id.startsWith('optional-')) {
                    assert.equal(initial.actions.length, id.startsWith('one-') ? 1 : 2);
                    assert.equal(await form.locator('[role=group] button [aria-hidden=true]').count(), 0);
                    assert.equal(await form.locator('.asteriskField').count(), 1);
                    assert.equal(await form.locator('textarea[name=comment]').count(), id.startsWith('optional-') ? 1 : 0);
                    if (!id.startsWith('optional-')) assert.equal(await form.locator('[id$="-comment"].mb-3').count(), 0);
                    assert.equal(await form.locator('[id$="-help"], [id$="_helptext"]').count(), 0);
                    await success('wf_activate');
                } else if (id.startsWith('cancel-omitted-')) {
                    assert.equal(await form.locator('a[id$="-cancel"], [data-cv-cancel-url]').count(), 0);
                    details.after = await observe();
                } else if (id === 'cancel-page') {
                    const cancel = form.locator('a[id$="-cancel"]'); assert.equal(await cancel.count(), 1);
                    const destination = await cancel.getAttribute('href');
                    await Promise.all([page.waitForNavigation(), cancel.click()]);
                    assert.equal(new URL(page.url()).pathname, new URL(destination, base).pathname); assert.equal(posts.length, 0);
                    assert.deepEqual((await observe()).history, []); details.destination = page.url();
                } else if (id.startsWith('label-safety-')) {
                    assert.equal(initial.group.name, server.ready.label); assert(initial.actions.every(item => !item.disabled));
                    const label = form.locator('[role=group]').locator('xpath=../label');
                    assert.equal(await label.getAttribute('for'), null);
                    const brokenLabels = await form.locator('label[for]').evaluateAll(labels => labels.filter(el => !document.getElementById(el.htmlFor) || document.getElementById(el.htmlFor).type === 'submit').length);
                    assert.equal(brokenLabels, 0); const priorUrl = page.url();
                    await label.click(); await page.waitForTimeout(150);
                    assert.equal(page.url(), priorUrl); assert.equal(posts.length, 0); assert.deepEqual((await observe()).history, []);
                    await form.locator('[name=comment]').fill('Chosen second action'); await success('wf_cancel_new');
                } else if (id === 'implicit-submit-custom-input-page') {
                    assert.deepEqual(initial.actions.map(item => item.name), ['wf_activate', 'wf_cancel_new']);
                    const first = form.locator('[type=submit]').first(); assert.equal(await first.getAttribute('value'), 'wf_activate');
                    assert(await first.isEnabled());
                    const input = form.locator('input[type=text][name=extra]'); await input.fill('Valid custom input');
                    await success('wf_activate', () => input.press('Enter')); assert.equal(posts.length, 1);
                    details.activation = 'Enter on required single-line input; first submit in tree order';
                } else if (id === 'textarea-enter-page') {
                    const textarea = form.locator('[name=comment]'); await textarea.fill('First line');
                    const priorUrl = page.url(); await textarea.press('End'); await textarea.press('Enter');
                    assert.equal(await textarea.inputValue(), 'First line\n'); await page.waitForTimeout(150);
                    assert.equal(page.url(), priorUrl); assert.equal(posts.length, 0);
                    assert.deepEqual((await observe()).history, []); assert.equal((await observe()).state, 'new');
                    details.textareaValue = await textarea.inputValue();
                } else if (id.startsWith('invalid-choice-')) {
                    for (const value of [null, 'forged']) {
                        const button = form.locator('button[type=submit]').first();
                        await button.evaluate((el, value) => {if (value === null) el.removeAttribute('name'); else el.value = value;}, value);
                        await invalid(null, () => button.click());
                        assert((await inspect(page, scope)).group.classes.includes('is-invalid'));
                    }
                } else if (id.startsWith('post-blockers-') || id.startsWith('late-refusal-')) {
                    const raw = '  <b>Retained & {{ comment }}</b>  ';
                    await form.locator('[name=comment]').fill(raw);
                    if (id.startsWith('post-')) {
                        const token = await form.locator('[name=csrfmiddlewaretoken]').inputValue();
                        assert.equal((await context.request.post(`${base}/change/${id}/`, {headers: {'X-CSRFToken': token}})).status(), 200);
                    } else await form.locator('[name=extra]').fill('  <em>Raw custom value</em>  ');
                    const dom = await invalid('wf_activate'); assert(dom.group.classes.includes('is-invalid'));
                    assert(dom.errors.some(error => server.ready.reasons.every(reason => error.text.includes(reason))));
                    assert.equal(await form.locator('[name=comment]').inputValue(), raw);
                    if (id.startsWith('late-')) {
                        assert.equal(await form.locator('[name=extra]').inputValue(), '  <em>Raw custom value</em>  ');
                        assert.equal(details.after.request.clean_calls, 1); assert.equal(details.after.name, id);
                        assert.equal(details.after.request.context_state, 'new');
                    }
                    assert.equal(await form.locator('b, em').count(), 0);
                } else if (id.startsWith('custom-errors-') || id === 'radio-custom-page') {
                    const raw = '  Kept <value> & {{ text }}  '; await form.locator('[name=comment]').fill(raw);
                    if (id.startsWith('radio')) {
                        assert.equal(await form.locator('input[type=radio][name=transition]').count(), 2);
                        await form.locator('input[value=wf_activate]').check();
                        await invalid(null, () => form.locator('button[name=submit]').click());
                    } else await invalid('wf_activate');
                    assert(details.invalid.errors.some(error => error.text.includes('This field is required')));
                    assert.equal(await form.locator('[name=comment]').inputValue(), raw);
                    await form.locator('[name=extra]').fill('Now valid');
                    if (id.startsWith('radio')) await success('wf_activate', () => form.locator('button[name=submit]').click());
                    else await success('wf_activate');
                } else if (id === 'keyboard-page') {
                    await form.locator('button[value=wf_activate]').focus();
                    assert.equal(await page.evaluate(() => document.activeElement.value), 'wf_activate');
                    details.focus = await page.evaluate(() => ({outline: getComputedStyle(document.activeElement).outlineStyle, boxShadow: getComputedStyle(document.activeElement).boxShadow}));
                    await success('wf_activate', () => page.keyboard.press('Enter'));
                } else if (id === 'required-recovery-page' || id === 'modal-lifecycle') {
                    assert(initial.actions.every(item => !item.disabled));
                    await page.locator('[name=comment]').fill('   ');
                    const dom = await invalid(); assert(dom.errors.some(error => error.text.includes('Comment is required')));
                    await form.locator('[name=comment]').fill('  Approved by browser  '); await success('wf_cancel_new');
                } else {
                    assert.equal(id, 'native-first-page'); await success('wf_activate');
                }
                details.posts = posts;
                if (!details.after) details.after = await observe();
                assert(details.after.checks.every(check => check.name !== 'wf_secret'));
                report.cases.push(details);
            } catch (error) {
                report.cases.push({id, passed: false, error: error.stack, posts});
                throw error;
            } finally {await page.close();}
        } finally {await context.close();}
    }
}

async function main(argv = process.argv.slice(2)) {
    const opts = {case: 'all', output: '/tmp/dcv-phase06131-browser.json'};
    for (let i = 0; i < argv.length; i += 2) {
        assert(['--case', '--output'].includes(argv[i]) && argv[i + 1], 'Use --case smoke|all --output FILE');
        opts[argv[i].slice(2)] = argv[i + 1];
    }
    const environment = Object.fromEntries(['CV_WORKFLOW_ASSETS_DIR', 'CV_WORKFLOW_PYTHON', 'CV_WORKFLOW_PLAYWRIGHT', 'CV_WORKFLOW_CHROMIUM']
        .filter(name => process.env[name] !== undefined).map(name => [name, process.env[name]]));
    const report = {command: [process.execPath, __filename, ...argv], environment, started: new Date().toISOString(), cases: [], failures: [], assets: [], screenshots: []};
    let browser, server;
    try {
        requiredCases(opts.case); report.sources = sources();
        report.stage = 'environment-assets';
        const assets = loadAssets(environment.CV_WORKFLOW_ASSETS_DIR), directory = fs.realpathSync(environment.CV_WORKFLOW_ASSETS_DIR);
        report.assetManifest = {suppliedDirectory: environment.CV_WORKFLOW_ASSETS_DIR, directory,
            path: path.join(directory, 'assets.json'), sha256: sha(fs.readFileSync(path.join(directory, 'assets.json')))};
        report.validatedAssets = [...assets].map(([url, asset]) => ({url, sha256: asset.sha256, source: asset.file}));
        report.stage = 'environment-runtime';
        const playwright = runtime('CV_WORKFLOW_PLAYWRIGHT', cached(path.join(os.homedir(), '.npm/_npx'), 'node_modules/playwright'));
        const chromium = runtime('CV_WORKFLOW_CHROMIUM', cached(path.join(os.homedir(), '.cache/ms-playwright'), 'chrome-linux64/chrome'), true);
        const python = runtime('CV_WORKFLOW_PYTHON', [path.join(root, '.nox/tests-3-12-django-5-2/bin/python')], true);
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true, args: ['--no-sandbox']});
        report.runtime = {playwright, playwrightVersion: require(path.join(playwright, 'package.json')).version, chromium, chromiumVersion: browser.version(), python};
        report.stage = 'fixture-startup';
        server = await startOwned(python, ['tests/browser/workflow_validation_server.py']); report.server = server.ready;
        for (const filename of Object.values(server.ready.modules)) assert(filename.startsWith(root + '/src/'), 'Stale imported source');
        assert.equal(server.ready.host, path.join(root, host));
        report.stage = 'browser-cases';
        await runCases(browser, assets, server, report, opts);
        assert.deepEqual(sources(), report.sources, 'Source drift during browser run');
    } catch (error) {
        report.failures.push(error.stack); report.environmentFailure = report.stage?.startsWith('environment-');
        if (error.cleanup) report.cleanup = error.cleanup;
        if (error.logs) report.logs = error.logs;
    } finally {
        if (browser) await browser.close();
        if (server) {report.cleanup = await cleanupServer(server); report.logs = server.logs();}
        try {validateEvidence(report, opts.case); report.status = 'passed';}
        catch (error) {report.status = 'failed'; report.failures.push(error.message); process.exitCode = 1;}
        report.finished = new Date().toISOString();
        fs.mkdirSync(path.dirname(path.resolve(opts.output)), {recursive: true});
        fs.writeFileSync(opts.output, JSON.stringify(report, null, 2) + '\n');
        console.log(`${report.status}: ${report.cases.length} cases; ${opts.output}`);
        if (report.status !== 'passed') console.error(report.failures.join('\n'));
    }
    return report;
}
if (require.main === module) main().catch(error => {console.error(error); process.exitCode = 1;});
module.exports = {requiredCases, validateEvidence, loadAssets, assetFor};
