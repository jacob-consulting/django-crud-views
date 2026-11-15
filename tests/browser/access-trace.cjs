'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const {CSP, preflight, assetFor, validateAssets, startOwned, cleanupServer} = require('./manage-presentation.cjs');
const {runtime} = require('./cancel-navigation.cjs');
const root = path.resolve(__dirname, '../..');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const requiredInputs = ['tests/browser/access-trace.cjs', 'tests/browser/access_trace_server.py', 'tests/browser/access-trace.test.cjs',
    'tests/browser/manage-presentation.cjs', 'tests/browser/manage_presentation_server.py', 'tests/browser/templates/manage/page.html',
    'tests/browser/cancel-navigation.cjs', 'tests/test1/conftest.py', 'tests/test1/app/models.py', 'tests/conftest.py'];
function sources(directory = root) {
    const paths = cp.execFileSync('git', ['ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', 'src/crud_views', 'src/crud_views_guardian'], {cwd: directory}).toString().split('\0').filter(Boolean);
    return {files: Object.fromEntries([...new Set([...paths, ...requiredInputs])].sort().map(file => [file, sha(fs.readFileSync(path.join(directory, file)))]))};
}
function requiredCases(selection) {
    const smoke = ['core-viewset-en-390-js', 'guardian-viewset-en-390-js', 'hosting-authorization'];
    if (selection === 'smoke') return smoke;
    return [...new Set([...smoke, ...['core', 'guardian'].flatMap(kind => [390, 1280].flatMap(width => ['en', 'de'].flatMap(language =>
        ['viewset', 'path'].flatMap(mode => ['js', 'nojs'].map(js => `${kind}-${mode}-${language}-${width}-${js}`))))),
    ...['core', 'guardian'].flatMap(kind => ['default-off', 'needs-pk', 'username-collision-viewset', 'username-collision-path',
        'pk-viewset', 'pk-path', 'unknown-viewset', 'unknown-path', 'error', 'not-found', 'no-route', 'hostile', 'registry-override', 'help'].map(state => `${kind}-${state}`)),
    'viewer-parent-denied-actor-allowed', 'nested-parent-coordinates'])];
}
function validateEvidence(report) {
    for (const id of requiredCases(report.selection)) {
        const item = report.cases.find(item => item.id === id);
        assert(item?.passed, `Missing case: ${id}`);
        assert(item.assertions?.length && item.assertions.every(a => a.name && JSON.stringify(a.actual) === JSON.stringify(a.expected)), `False assertions: ${id}`);
        const f = item.facts;
        assert(f && f.documentWidth <= f.width + 1 && f.inline === 0 && f.labels === true, `False measurements: ${id}`);
        assert.deepEqual(f.csp, [], `CSP violations: ${id}`);
        for (const key of ['outcomeFirst', 'boundaryOnce', 'errorLinked', 'resultSpacing'])
            assert.equal(f.presentation?.[key], true, `False presentation measurement ${key}: ${id}`);
        assert(report.screenshots.some(s => s.case === id && s.path && /^[a-f0-9]{64}$/.test(s.sha256)), `Missing capture: ${id}`);
    }
    assert.equal(report.preflight.status, 'passed'); assert.equal(report.csp, CSP); assert.deepEqual(report.failures, []);
    assert.equal(report.cleanup.length, 1); assert(report.cleanup[0].stopped && report.cleanup[0].databaseRemoved, 'Owned cleanup failed');
    for (const file of requiredInputs) assert.match(report.sources.files[file] ?? '', /^[a-f0-9]{64}$/, `Missing source: ${file}`);
    validateAssets(report.requiredAssets, report.assets);
}
function verifyReceipt(report, directory = root, receiptDirectory = root, validate = true) {
    if (validate) {assert.equal(report.status, 'passed'); validateEvidence(report);}
    assert.deepEqual(sources(directory), report.sources, 'Current source bytes/path set differ from receipt');
    for (const capture of report.screenshots) {
        const file = path.resolve(receiptDirectory, capture.path);
        assert(file.startsWith(path.resolve(receiptDirectory) + path.sep), 'Capture outside receipt directory');
        assert.equal(sha(fs.readFileSync(file)), capture.sha256, `Stale capture: ${capture.path}`);
    }
}
async function signin(context, base, username = 'developer') {
    const credentials = await (await context.request.get(base + '/signin/')).json();
    const result = await context.request.post(base + '/signin/', {form: {username, password: 'fixture-only', csrfmiddlewaretoken: credentials.csrf}});
    assert.equal(result.status(), 200);
}
async function openContext(browser, base, assets, javascript) {
    const context = await browser.newContext({viewport: {width: 390, height: 900}, javaScriptEnabled: javascript, serviceWorkers: 'block'});
    context.setDefaultTimeout(15000);
    const failures = [], observed = [], pending = [];
    await context.route('**/*', async route => {
        const url = route.request().url();
        try {
            if (url.startsWith(base + '/')) return await route.continue();
            if (url.startsWith('https://django-crud-views.readthedocs.io/')) return await route.fulfill({status: 200, contentType: 'text/html', body: '<h1 id="access-check">Access check documentation</h1>'});
            const asset = assetFor(assets, url);
            await route.fulfill({body: asset.body, status: 200, contentType: url.endsWith('.css') ? 'text/css' : url.endsWith('.js') ? 'text/javascript' : 'font/woff2', headers: {'access-control-allow-origin': '*'}});
        } catch (error) {failures.push(error.message); await route.abort();}
    });
    await context.addInitScript(() => {
        window.accessCsp = [];
        document.addEventListener('securitypolicyviolation', e => window.accessCsp.push({directive: e.effectiveDirective, blocked: e.blockedURI}));
    });
    context.on('response', response => {
        if (response.request().resourceType() === 'document') return;
        const url = response.url(), record = {url, status: response.status()}; observed.push(record);
        pending.push((async () => {
            const bytes = await response.body(); record.sha256 = sha(bytes);
            const file = url.startsWith('https:') ? assetFor(assets, url).file : url.endsWith('/jquery.js') ? path.join(root, 'node_modules/jquery/dist/jquery.min.js') :
                path.join(root, 'src', new URL(url).pathname.split('/')[2], 'static', new URL(url).pathname.slice('/static/'.length));
            record.source = file; assert.equal(record.status, 200); assert.equal(record.sha256, sha(fs.readFileSync(file)), `Served bytes mismatch: ${url}`);
        })().catch(error => failures.push(error.message)));
    });
    const page = await context.newPage();
    page.on('pageerror', e => failures.push(e.message));
    page.on('console', m => {if (m.type() === 'error') failures.push(m.text());});
    page.on('requestfailed', r => failures.push(`${r.url()}: ${r.failure()?.errorText}`));
    page.on('request', r => {if (['fetch', 'xhr'].includes(r.resourceType())) failures.push(`Unexpected fetch: ${r.url()}`);});
    await signin(context, base);
    return {context, page, pending, failures, observed};
}
async function facts(page, response) {
    const html = await response.text(); assert.equal(response.status(), 200); assert.equal(response.headers()['content-security-policy'], CSP);
    const result = await page.evaluate(html => {
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const inputs = [...doc.querySelectorAll('#cv-manage-access-trace input:not([type="hidden"])')];
        const inline = [...doc.querySelectorAll('*')].filter(el => el.tagName === 'STYLE' || (el.tagName === 'SCRIPT' && !el.src) || [...el.attributes].some(a => a.name === 'style' || /^on/i.test(a.name) || /^javascript:/i.test(a.value))).length;
        const card = document.querySelector('#cv-manage-access-trace');
        const traces = [...document.querySelectorAll('[data-cv-access-trace]')];
        const errors = [...document.querySelectorAll('#cv-manage-access-trace [role="alert"]')];
        return {width: innerWidth, documentWidth: document.documentElement.scrollWidth, inline,
            presentation: {
                outcomeFirst: traces.every(el => el.firstElementChild?.matches('[data-cv-trace-outcome]')),
                boundaryOnce: traces.filter(el => el.querySelector('[data-cv-trace-outcome] [data-cv-trace-result="allowed"]')).every(el => {
                    const notice = el.querySelector('[data-cv-trace-outcome] > p:nth-child(2)')?.textContent.trim();
                    return Boolean(notice) && el.textContent.split(notice).length === 2;
                }),
                errorLinked: errors.every(el => el.id && el.closest('form')?.querySelectorAll(`[aria-invalid="true"][aria-describedby="${el.id}"]`).length === 1 && parseFloat(getComputedStyle(el).marginTop) >= 16),
                resultSpacing: !card || parseFloat(getComputedStyle(card.querySelector('[data-cv-access-results]')).marginTop) >= 16,
            },
            labels: inputs.every(el => el.id && doc.querySelectorAll(`[id="${el.id}"]`).length === 1 && doc.querySelectorAll(`label[for="${el.id}"]`).length === 1),
            csp: window.accessCsp ?? [], language: document.documentElement.lang,
            text: document.querySelector('#cv-manage-access-trace')?.textContent ?? '',
            regions: [...document.querySelectorAll('[role="region"]')].map(el => ({label: el.getAttribute('aria-label'), tab: el.tabIndex, width: el.clientWidth, scrollWidth: el.scrollWidth})),
            outcomes: [...document.querySelectorAll('[data-cv-trace-result]')].map(el => ({result: el.dataset.cvTraceResult, text: el.textContent, classes: el.className}))};
    }, html);
    assert(result.documentWidth <= result.width + 1, `Page overflow: ${result.documentWidth} > ${result.width}`);
    assert.equal(result.inline, 0); assert(result.labels); assert.deepEqual(result.csp, []);
    assert(result.regions.every(r => r.label && r.tab === 0));
    assert(Object.values(result.presentation).every(Boolean), 'Reviewed presentation measurements failed');
    assert(!result.text.includes('PRIVATE_'), 'Object content leaked');
    return result;
}
async function run(browser, base, server, assets, opts, report) {
    for (const javascript of [true, false]) {
        if (!javascript && opts.case === 'smoke') continue;
        const owned = await openContext(browser, base, assets, javascript);
        const {page, context} = owned;
        const capture = async (id, response, assertions, viewer = 'developer') => {
            const observed = await facts(page, response);
            const identity = await (await context.request.get(base + '/identity/')).json();
            assert.equal(identity.username, viewer);
            assertions.push({name: 'viewer retained', actual: identity.username, expected: viewer});
            const relative = `06.34-browser-captures/${id}.png`, file = path.resolve(path.dirname(opts.output), relative);
            fs.mkdirSync(path.dirname(file), {recursive: true}); await page.screenshot({path: file, fullPage: true});
            report.screenshots.push({case: id, path: relative, sha256: sha(fs.readFileSync(file))});
            report.cases.push({id, passed: true, facts: observed, assertions}); console.log(`passed: ${id}`);
        };
        const check = (arr, name, actual, expected = true) => {assert.deepEqual(actual, expected, name); arr.push({name, actual, expected});};
        const submit = async (kind, mode, language = 'en', username = 'reader', value = '', enabled = 'on') => {
            await page.goto(`${base}/case/${kind}/${enabled}/${language}/`);
            await page.locator(`#cv-access-${mode}-user`).fill(username);
            await page.locator(mode === 'path' ? '#cv-access-path' : '#cv-access-pk').fill(value);
            const form = page.locator('#cv-manage-access-trace form').nth(mode === 'viewset' ? 0 : 1);
            const response = page.waitForResponse(r => r.request().isNavigationRequest() && r.url().startsWith(base + '/case/'));
            await form.locator('button').click();
            const submitted = await response;
            await page.waitForURL(url => url.searchParams.get('cv_access_mode') === mode && url.searchParams.get('cv_access_user') === username);
            await page.waitForLoadState('load');
            return submitted;
        };
        try {
            for (const kind of ['core', 'guardian']) for (const width of [390, 1280]) for (const language of ['en', 'de']) for (const mode of ['viewset', 'path']) {
                const id = `${kind}-${mode}-${language}-${width}-${javascript ? 'js' : 'nojs'}`;
                if (!requiredCases(opts.case).includes(id)) continue;
                await page.setViewportSize({width, height: 900});
                let response = await submit(kind, mode, language, 'reader', mode === 'viewset' ? server.object_pk : server.routes[kind].detail);
                const checks = [];
                check(checks, 'locale survives native GET', await page.locator('html').getAttribute('lang'), language);
                check(checks, 'selected actor in trace', (await page.locator('[data-cv-access-trace]').first().textContent()).includes('reader'));
                const matrix = await page.locator('[data-manage-actor]').innerText();
                check(checks, 'matrix actor', matrix.includes(mode === 'viewset' ? 'reader' : 'developer'));
                check(checks, 'actor-neutral matrix explanation', /the access row includes|die Zugriffszeile/i.test(await page.locator('#cv-manage-permissions').innerText()));
                for (const input of await page.locator('#cv-manage-access-trace input:not([type="hidden"])').all()) {
                    await input.focus(); check(checks, 'input focus and visible indicator', await input.evaluate(e => e === document.activeElement &&
                        (getComputedStyle(e).boxShadow !== 'none' || getComputedStyle(e).outlineStyle !== 'none')));
                }
                const region = page.locator('[role="region"]').first();
                await region.focus(); check(checks, 'scroll region keyboard focus', await region.evaluate(e => e === document.activeElement));
                if (await region.evaluate(e => e.scrollWidth > e.clientWidth + 2)) {
                    await region.press('ArrowRight'); await page.waitForTimeout(200);
                    check(checks, 'local keyboard scrolling', await region.evaluate(e => e.scrollLeft > 0));
                }
                if (mode === 'viewset') {
                    check(checks, 'collapsed denied summary shows recorded permission',
                        (await page.locator('[data-cv-access-row="delete"] summary [data-cv-trace-summary]').innerText()).includes('app.delete_author'));
                    const errorSummary = (await page.locator('[data-cv-access-row="error"] summary [data-cv-trace-summary]').innerText()).trim();
                    check(checks, 'collapsed error summary retains recorded explanation', errorSummary.length > 0 &&
                        (await page.locator('[data-cv-access-row="error"] [data-cv-access-trace]').textContent()).includes(errorSummary));
                    if (kind === 'guardian') check(checks, 'collapsed strict list summary shows actual counts',
                        /(?:sees 1 of 2 objects|sieht 1 von 2 Objekten)/i.test(await page.locator('[data-cv-access-row="list"] summary [data-cv-trace-summary]').innerText()));
                    const rows = await page.locator('[data-cv-access-row]').evaluateAll(es => es.map(e => e.dataset.cvAccessRow));
                    check(checks, 'complete route inventory', rows, server.view_keys[kind]);
                    const details = page.locator('[data-cv-access-row="detail"]'), summary = details.locator('summary');
                    await summary.focus(); check(checks, 'summary focused', await summary.evaluate(e => e === document.activeElement));
                    await page.keyboard.press('Enter'); check(checks, 'Enter opens native details', await details.getAttribute('open'), '');
                    await page.keyboard.press('Space'); check(checks, 'Space closes native details', await details.getAttribute('open'), null);
                    for (const el of await page.locator('details[data-cv-access-row]').all()) await el.locator('summary').click();
                    const text = await page.locator('[data-cv-access-row="extra"]').innerText();
                    check(checks, 'extra args instruction', /path|Pfad/.test(text));
                    check(checks, 'POST-only limitation', (await page.locator('[data-cv-access-row="post_only"]').innerText()).includes('GET'));
                    check(checks, 'denied and error outcomes', await page.locator('[data-cv-trace-result="denied"]').count() > 0 && await page.locator('[data-cv-trace-result="error"]').count() > 0);
                    check(checks, 'unreached and unevaluated', await page.locator('[data-cv-trace-result="not_reached"]').count() > 0 && await page.locator('[data-cv-trace-result="not_evaluated"]').count() > 0);
                    if (kind === 'guardian') check(checks, 'actual strict list counts', /(?:sees 1 of 2 objects|sieht 1 von 2 Objekten)/i.test(await page.locator('[data-cv-access-row="list"]').innerText()));
                } else check(checks, 'allowed path outcome', await page.locator('[data-cv-trace-result="allowed"]').count(), 1);
                const url = page.url(); response = await page.goto(url);
                check(checks, 'copied result URL', page.url(), url);
                if (mode === 'viewset') for (const el of await page.locator('details[data-cv-access-row]').all()) await el.locator('summary').click();
                await capture(id, response, checks);
            }
            if (javascript) {
                await page.setViewportSize({width: 390, height: 900});
                for (const kind of ['core', 'guardian']) {
                    if (opts.case !== 'all') continue;
                    for (const mode of ['viewset', 'path']) for (const [state, username, expected] of [
                        ['username-collision', '22', '22'], ['pk', String(server.actors.developer), 'developer'], ['unknown', 'absent-user', null],
                    ]) {
                        const response = await submit(kind, mode, 'en', username, mode === 'path' ? server.routes[kind].detail : server.object_pk), checks = [];
                        if (expected === null) {
                            check(checks, 'unknown input feedback', await page.locator('#cv-manage-access-trace [role="alert"]').count(), 1);
                            check(checks, 'unknown has no trace', await page.locator('[data-cv-access-trace]').count(), 0);
                            check(checks, 'unknown error belongs to selected user field',
                                await page.locator(`#cv-access-${mode}-user`).getAttribute('aria-describedby'), `cv-access-${mode}-error`);
                        } else {
                            const text = await page.locator('[data-cv-access-trace]').first().textContent();
                            check(checks, 'selected actor identity', text.includes(`${expected} (pk ${server.actors[expected]},`));
                        }
                        await capture(`${kind}-${state}-${mode}`, response, checks);
                    }
                    let response = await page.goto(`${base}/case/${kind}/off/en/?cv_access_mode=path&cv_access_user=reader&cv_access_path=/missing/`), checks = [];
                    check(checks, 'default off hides card', await page.locator('#cv-manage-access-trace').count(), 0);
                    check(checks, 'default off retains viewer row', (await page.locator('[data-manage-actor]').innerText()).includes('developer'));
                    await capture(`${kind}-default-off`, response, checks);
                    response = await submit(kind, 'viewset'); checks = [];
                    check(checks, 'missing pk instructions', (await page.locator('[data-cv-access-row="detail"]').innerText()).includes('needs an object pk'));
                    await capture(`${kind}-needs-pk`, response, checks);
                    for (const [state, target, username, result] of [
                        ['error', server.routes[kind].error, 'reader', 'error'],
                        ['not-found', server.routes[kind].detail.replace(server.object_pk, '00000000-0000-0000-0000-000000000000'), 'reader', 'not_found'],
                        ['no-route', '/' + 'missing_long_path_'.repeat(30), 'reader', 'no_such_route'],
                        ['hostile', server.routes[kind].error, server.hostile, 'error'],
                        ['registry-override', server.routes[kind].detail, 'reader', 'allowed'],
                    ]) {
                        response = await submit(kind, 'path', 'en', username, target, state === 'registry-override' ? 'override' : 'on'); checks = [];
                        check(checks, `expected ${state} outcome ${result}: ${await page.locator('#cv-manage-access-trace').innerText()}`, await page.locator(`[data-cv-trace-result="${result}"]`).count() > 0);
                        check(checks, 'escaped hostile markup', await page.locator('unsafe').count(), 0);
                        if (state === 'registry-override') check(checks, 'registry override classes', await page.locator('[data-cv-trace-result]').evaluateAll(es => es.every(e => e.classList.contains('fixture-trace-override'))));
                        await capture(`${kind}-${state}`, response, checks);
                    }
                    response = await page.goto(`${base}/case/${kind}/on/de/`); checks = [];
                    const help = page.locator('#cv-manage-access-trace [data-cv-manage-help]');
                    check(checks, 'help anchor', (await help.getAttribute('href')).endsWith('#access-check'));
                    check(checks, 'new tab', await help.getAttribute('target'), '_blank');
                    check(checks, 'noopener', (await help.getAttribute('rel')).includes('noopener'));
                    check(checks, 'translated labels', (await help.getAttribute('aria-label')).includes('Zugriffs') && (await help.getAttribute('title')).length > 0);
                    const popupPromise = context.waitForEvent('page'); await help.click(); const popup = await popupPromise;
                    await popup.waitForLoadState(); check(checks, 'local docs response', await popup.locator('h1').innerText(), 'Access check documentation'); await popup.close();
                    await capture(`${kind}-help`, response, checks);
                }
                let response = await page.goto(`${base}/case/core/on/en/`), checks = [];
                const ordinary = await browser.newContext(); await signin(ordinary, base, 'ordinary');
                check(checks, 'nonmember hosting denied', (await ordinary.request.get(`${base}/case/core/on/en/`)).status(), 403); await ordinary.close();
                const anonymous = await browser.newContext(); check(checks, 'anonymous hosting redirects', (await anonymous.request.get(`${base}/case/core/on/en/`, {maxRedirects: 0})).status(), 302); await anonymous.close();
                await capture('hosting-authorization', response, checks);
                if (opts.case === 'all') {
                    checks = []; check(checks, 'viewer cannot open parent-scoped manage', (await context.request.get(base + server.routes.nested_manage)).status(), 403);
                    response = await submit('core', 'path', 'en', 'reader', server.routes.nested);
                    check(checks, 'independent actor may open nested target', await page.locator('[data-cv-trace-result="allowed"]').count(), 1);
                    await capture('viewer-parent-denied-actor-allowed', response, checks);
                    // The reader is not a developer: prove hosting remains denied even with target grants.
                    const reader = await browser.newContext(); await signin(reader, base, 'reader');
                    checks = []; check(checks, 'actor still cannot use nested manage', (await reader.request.get(base + server.routes.nested_manage)).status(), 403); await reader.close();
                    await signin(context, base, 'nested-developer');
                    await page.goto(base + server.routes.nested_form);
                    await page.locator('#cv-access-viewset-user').fill('reader');
                    const pending = page.waitForResponse(r => r.request().isNavigationRequest() && r.url().startsWith(base + '/nested-case/'));
                    await page.locator('#cv-manage-access-trace form').first().locator('button').click(); response = await pending;
                    check(checks, 'nested hosting URL retained', new URL(page.url()).pathname, server.routes.nested_form);
                    check(checks, 'actual parent coordinate in trace', (await page.locator('[data-cv-access-trace]').first().textContent()).includes('trace_parent'));
                    check(checks, 'nested selected actor row', (await page.locator('[data-manage-actor]').innerText()).includes('reader'));
                    await capture('nested-parent-coordinates', response, checks, 'nested-developer');
                }
            }
        } finally {
            await Promise.all(owned.pending); report.assets.push(...owned.observed); report.failures.push(...owned.failures);
            await context.close().catch(error => report.failures.push(error.message));
        }
    }
}
async function main(argv = process.argv.slice(2)) {
    if (argv[0] === '--verify') {
        assert.equal(argv.length, 2); const file = path.resolve(argv[1]); verifyReceipt(JSON.parse(fs.readFileSync(file)), root, path.dirname(file));
        console.log('Verified current source bytes, complete observations, captures and cleanup'); return;
    }
    const opts = {case: 'all', python: '.nox/tests-3-12-django-6-0/bin/python', output: '/tmp/cv-0634-browser.json'};
    for (let i = 0; i < argv.length; i += 2) {assert(['--case', '--python', '--output'].includes(argv[i]) && argv[i + 1]); opts[argv[i].slice(2)] = argv[i + 1];}
    assert(['all', 'smoke'].includes(opts.case));
    const report = {command: [process.execPath, __filename, ...argv], started: new Date().toISOString(), selection: opts.case, cases: [], screenshots: [], assets: [], requiredAssets: [], cleanup: [], failures: [], csp: CSP};
    let browser, server;
    try {
        let assets;
        try {assets = preflight(process.env.CV_MANAGE_ASSETS_DIR); report.preflight = {status: 'passed', assets: [...assets].map(([url, a]) => ({url, sha256: a.sha256, file: a.file}))};}
        catch (error) {report.preflight = {status: 'environment-blocked', error: error.message}; throw error;}
        report.sources = sources();
        const cached = (dir, suffix) => fs.existsSync(dir) ? fs.readdirSync(dir).sort().reverse().map(name => path.join(dir, name, suffix)) : [];
        const playwright = runtime('CV_MANAGE_PLAYWRIGHT', cached(path.join(os.homedir(), '.npm/_npx'), 'node_modules/playwright'));
        const chromium = runtime('CV_MANAGE_CHROMIUM', cached(path.join(os.homedir(), '.cache/ms-playwright'), 'chrome-linux64/chrome'), true);
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true, args: ['--no-sandbox']});
        report.browser = {playwright, chromium, version: browser.version()};
        server = await startOwned(path.resolve(opts.python), ['tests/browser/access_trace_server.py']); report.server = server.ready;
        for (const file of Object.values(server.ready.modules)) assert(file.startsWith(root + '/src/'), `Stale module: ${file}`);
        for (const file of Object.values(server.ready.origins)) assert(file.startsWith(root + '/src/') || file === path.join(root, 'tests/browser/templates/manage/page.html'), `Stale template: ${file}`);
        assert(server.ready.versions.Django.startsWith('6.0.'));
        const base = `http://127.0.0.1:${server.ready.ready}`;
        report.requiredAssets = [base + '/static/crud_views/css/manage.css', base + '/static/crud_views/js/manage.js', ...assets.keys()].filter(url => !url.includes('/webfonts/'));
        await run(browser, base, server.ready, assets, opts, report);
        assert.deepEqual(sources(), report.sources, 'Sources changed during run');
        report.cleanup.push(await cleanupServer(server)); report.logs = server.logs(); server = null;
        validateEvidence(report); report.status = 'passed';
    } catch (error) {report.status = report.preflight?.status === 'environment-blocked' ? 'environment-blocked' : 'failed'; report.error = error.stack; if (error.cleanup) report.startupCleanup = error.cleanup; if (error.logs) report.startupLogs = error.logs; process.exitCode = 1;}
    finally {
        if (browser) await browser.close();
        if (server) {report.cleanup.push(await cleanupServer(server)); report.logs = server.logs();}
        report.finished = new Date().toISOString(); fs.mkdirSync(path.dirname(path.resolve(opts.output)), {recursive: true}); fs.writeFileSync(opts.output, JSON.stringify(report, null, 2) + '\n');
        console.log(`${report.status}: ${report.cases.length} cases; ${opts.output}`); if (report.error) console.error(report.error);
    }
}
if (require.main === module) main().catch(error => {console.error(error); process.exitCode = 1;});
module.exports = {CSP, requiredInputs, sources, sha, requiredCases, validateEvidence, verifyReceipt};
