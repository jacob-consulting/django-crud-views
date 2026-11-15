'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const {runtime, stopOwned} = require('./cancel-navigation.cjs');
const root = path.resolve(__dirname, '../..');
const sha = body => crypto.createHash('sha256').update(body).digest('hex');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const cached = (directory, suffix) => fs.existsSync(directory) ? fs.readdirSync(directory).sort().reverse().map(name => path.join(directory, name, suffix)) : [];
const cacheDefault = path.join(os.homedir(), '.cache/django-crud-views/cancel-assets-06.7');
const CSP = "default-src 'none'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self'; form-action 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'";

function declarations() {
    return [...fs.readFileSync(path.join(__dirname, 'templates/manage/page.html'), 'utf8')
        .matchAll(/<(?:link|script)\b[^>]*?(?:href|src)="(https:[^"]+)"[^>]*>/gs)]
        .map(([tag, url]) => ({url, integrity: tag.match(/integrity="([^"]+)"/)[1]}));
}
function assetFor(assets, url) {
    assert(assets.has(url), `Undeclared external request: ${url}`);
    return assets.get(url);
}
function preflight(directory = cacheDefault) {
    const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'assets.json'), 'utf8'));
    const result = new Map(), pending = declarations();
    for (const spec of pending) {
        if (result.has(spec.url)) continue;
        assert(['cdn.jsdelivr.net', 'cdnjs.cloudflare.com'].includes(new URL(spec.url).hostname));
        const entry = manifest.assets[spec.url];
        assert(entry, `Missing cached asset: ${spec.url}`);
        const file = fs.realpathSync(path.resolve(directory, entry.file));
        assert(file.startsWith(fs.realpathSync(directory) + path.sep), 'Asset outside owned cache');
        const body = fs.readFileSync(file);
        assert.equal(sha(body), entry.sha256, `Cache digest mismatch: ${spec.url}`);
        if (spec.integrity) {
            const [algorithm, expected] = spec.integrity.split('-');
            assert.equal(crypto.createHash(algorithm).update(body).digest('base64'), expected, `SRI mismatch: ${spec.url}`);
        }
        result.set(spec.url, {body, file, sha256: sha(body), integrity: spec.integrity ?? null});
        if (spec.url.endsWith('.css')) {
            for (const [, value] of body.toString().matchAll(/url\(['"]?([^'"\s)]+)['"]?\)/g)) {
                if (value.startsWith('data:')) continue;
                const url = new URL(value, spec.url).href;
                assert(url.startsWith('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/webfonts/'), `Undeclared font: ${url}`);
                pending.push({url});
            }
        }
    }
    return result;
}
async function startOwned(executable, args, timeout = 30000) {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-manage-'));
    const child = cp.spawn(executable, [...args, '--directory', directory], {cwd: root,
        env: {...process.env, PYTHONUNBUFFERED: '1'}, stdio: ['ignore', 'pipe', 'pipe']});
    let stdout = '', stderr = '', spawnError;
    child.once('error', error => {spawnError = error;});
    child.stdout.on('data', data => {stdout += data;});
    child.stderr.on('data', data => {stderr += data;});
    const server = {child, directory, logs: () => ({stdout, stderr})};
    try {
        const deadline = Date.now() + timeout;
        while (Date.now() < deadline) {
            if (spawnError) throw spawnError;
            assert(child.exitCode === null && child.signalCode === null, `Fixture startup failed: ${stderr}`);
            const line = stdout.split('\n').find(line => line.startsWith('{"ready":'));
            if (line) {server.ready = JSON.parse(line); return server;}
            await delay(25);
        }
        throw new Error(`Fixture startup timed out: ${stderr}`);
    } catch (error) {
        error.cleanup = await cleanupServer(server); error.logs = server.logs(); throw error;
    }
}
async function cleanupServer(server) {
    if (server.child.pid) await stopOwned(server.child);
    const stopped = !server.child.pid || server.child.exitCode !== null || server.child.signalCode !== null;
    assert(stopped, 'Owned process did not stop');
    fs.rmSync(server.directory, {recursive: true, force: true});
    return {pid: server.child.pid ?? null, stopped, directory: server.directory, databaseRemoved: !fs.existsSync(server.directory)};
}
function requiredCases(selection) {
    const smoke = ['core-normal-390', 'guardian-normal-390', 'ordinary-denied'];
    if (selection === 'smoke') return smoke;
    return [...smoke, ...['core', 'guardian'].flatMap(kind => [
        ...[390, 1280].flatMap(width => ['en', 'de'].map(language => `${kind}-layout-${language}-${width}`)),
        ...['errors', 'errors-1280', 'empty', 'no-holders', 'holders0', 'holders1', 'holders20', 'holders21', 'hidden', 'zero-defaults', 'no-js', 'missing-js'].map(state => `${kind}-${state}`),
        ...[0, 1, 3].flatMap(count => ['en', 'de'].map(language => `${kind}-collections${count}-${language}`)),
    ]), ...['resource', 'resource-nested'].flatMap(kind => [390, 1280].flatMap(width =>
        ['en', 'de'].flatMap(language => ['layout', 'empty', 'none', 'no-holders'].map(state => `${kind}-${state}-${language}-${width}`)))),
    'nested-ancestors', 'hierarchy-resource', 'documentation-failure'];
}
function validateAssets(required, observed) {
    assert(required.length > 0, 'No required assets');
    for (const url of required) {
        const item = observed.find(value => value.url === url);
        assert(item, `Missing required asset: ${url}`);
        assert.equal(item.status, 200, `Failed required asset: ${url}`);
        assert.match(item.sha256, /^[a-f0-9]{64}$/, 'Missing asset digest');
    }
}
function validateEvidence(report, selection) {
    for (const id of requiredCases(selection)) assert(report.cases.some(item => item.id === id && item.passed), `Missing case: ${id}`);
    assert.equal(report.preflight.status, 'passed');
    assert.equal(report.csp, CSP);
    assert.deepEqual(report.failures, []);
    validateAssets(report.requiredAssets, report.assets);
    assert.equal(report.cleanup.length, 1);
    assert(report.cleanup[0].stopped && report.cleanup[0].databaseRemoved, 'Owned cleanup incomplete');
    assert(Object.keys(report.sources.files).length > 10, 'Missing source fingerprints');
    if (selection === 'all') {
        for (const id of uiIds()) {
            const mapping = report.ui?.[id];
            assert(mapping?.length && mapping.every(caseId => report.cases.some(item => item.id === caseId && item.passed)), `Unproven UI mapping: ${id}`);
            assert.deepEqual(mapping, uiMappings()[id], `Unrelated criterion mapping: ${id}`);
            for (const caseId of mapping) {
                const proof = report.cases.find(item => item.id === caseId).criteria?.[id];
                validateCriterion(id, caseId, proof);
            }
        }
        assert.equal(Object.keys(report.ui).length, 52);
        for (const item of report.cases.filter(item => item.id !== 'ordinary-denied')) {
            assert(item.facts && Object.keys(item.facts).length > 0, `Missing DOM facts: ${item.id}`);
            assert(report.screenshots.some(shot => shot.case === item.id && /^[a-f0-9]{64}$/.test(shot.sha256)), `Missing screenshot: ${item.id}`);
        }
    }
}
function uiIds() {
    return ['permissions', 'views', 'presentation', 'facts', 'checks', 'defaults'].flatMap(surface =>
        ['empty', 'loading', 'error', 'populated', 'partial', 'overflow', 'zero-one-many', 'long-text'].map(state => `${surface}.${state}`))
        .concat(['loading', 'error', 'overflow', 'long-text'].map(state => `help.${state}`));
}
function uiMappings() {
    const both = (...states) => ['core', 'guardian'].flatMap(kind => states.map(state => `${kind}-${state}`));
    const collections = both(...[0, 1, 3].flatMap(n => ['en', 'de'].map(language => `collections${n}-${language}`)));
    const layouts = both('layout-en-390', 'layout-de-390', 'layout-en-1280', 'layout-de-1280');
    const loading = both('no-js', 'missing-js');
    // Explicit surface ownership. Passing a case for one surface proves nothing about another.
    const surfaces = {
        permissions: {empty: both('empty', 'no-holders'), loading, error: ['ordinary-denied'], populated: layouts,
            partial: ['guardian-layout-en-390'], overflow: layouts,
            'zero-one-many': both('holders0', 'holders1', 'holders20', 'holders21'), 'long-text': layouts},
        views: {empty: both('empty'), loading, error: ['ordinary-denied'], populated: layouts,
            partial: layouts, overflow: layouts, 'zero-one-many': collections, 'long-text': layouts},
        presentation: {empty: both('empty'), loading, error: both('errors'), populated: layouts,
            partial: both('errors'), overflow: layouts, 'zero-one-many': collections, 'long-text': layouts},
        facts: {empty: both('empty'), loading, error: ['ordinary-denied'], populated: ['nested-ancestors', 'hierarchy-resource'],
            partial: ['hierarchy-resource'], overflow: layouts, 'zero-one-many': collections, 'long-text': layouts},
        checks: {empty: both('empty'), loading, error: both('errors'), populated: both('errors'),
            partial: both('errors'), overflow: both('errors', 'errors-1280'), 'zero-one-many': collections, 'long-text': both('errors', 'errors-1280')},
        defaults: {empty: both('zero-defaults'), loading, error: loading, populated: layouts,
            partial: loading, overflow: layouts, 'zero-one-many': collections, 'long-text': layouts},
        help: {loading, error: ['documentation-failure'], overflow: layouts, 'long-text': layouts},
    };
    return Object.fromEntries(Object.entries(surfaces).flatMap(([surface, states]) =>
        Object.entries(states).map(([state, cases]) => [`${surface}.${state}`, cases])));
}

function validateCriterion(id, caseId, proof) {
    assert(proof && proof.surface === id.split('.')[0] && proof.measurements && Object.keys(proof.measurements).length,
        `Missing criterion measurements: ${id}/${caseId}`);
    assert(Array.isArray(proof.assertions) && proof.assertions.length && proof.assertions.every(item =>
        typeof item.name === 'string' && item.name && Object.hasOwn(item, 'actual') && Object.hasOwn(item, 'expected') &&
        JSON.stringify(item.actual) === JSON.stringify(item.expected)), `Failed criterion assertion: ${id}/${caseId}`);
    if (id.endsWith('.zero-one-many')) {
        const expected = Number(caseId.match(/(?:collections|holders)(\d+)/)?.[1]);
        assert.equal(proof.measurements.count, expected, `Wrong criterion cardinality: ${id}/${caseId}`);
    }
}

async function criterionProofs(page, caseId, facts) {
    const proofs = {};
    for (const [id, cases] of Object.entries(uiMappings())) {
        if (!cases.includes(caseId)) continue;
        const [surface, state] = id.split('.');
        const measurements = await page.evaluate(surface => {
            const selectors = {permissions: '#cv-manage-permissions', views: '#cv-manage-views', presentation: '#cv-manage-presentation',
                facts: '#cv-manage-viewset, #cv-manage-hierarchy, #cv-manage-urls', checks: '#cv-manage-checks-clean, #cv-manage-checks-issues',
                defaults: '[data-cv-defaults-control], [data-cv-default-count]', help: '[data-cv-manage-help]'};
            const nodes = [...document.querySelectorAll(selectors[surface])];
            const text = nodes.map(el => el.textContent).join(' ');
            const root = document.querySelector('[data-cv-manage]');
            const rects = nodes.map(el => {const r = el.getBoundingClientRect(), wrapper = el.closest('.table-responsive');
                return {left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height,
                    localScroll: !!wrapper && wrapper.getAttribute('role') === 'region' && wrapper.tabIndex === 0 && !!wrapper.getAttribute('aria-label')};});
            const count = selector => document.querySelectorAll(selector).length;
            const rows = [...document.querySelectorAll('#cv-manage-views details')].map(el => ({id: el.id, top: el.getBoundingClientRect().top, bottom: el.getBoundingClientRect().bottom}));
            const children = [...document.querySelectorAll('[data-manage-child]')].map(el => ({text: el.textContent, links: el.querySelectorAll('a').length, top: el.getBoundingClientRect().top, bottom: el.getBoundingClientRect().bottom}));
            return {text, rects, width: innerWidth, documentWidth: document.documentElement.scrollWidth, nodes: nodes.length,
                views: rows, children, buttons: count('#cv-manage-presentation tbody tr[data-cv-config-row] td:nth-child(4)'),
                presentationSections: count('#cv-manage-presentation tbody'),
                checks: Number(document.querySelector('#cv-manage-checks-clean')?.textContent.match(/\d+/)?.[0] ?? 0),
                issues: count('#cv-manage-checks-issues li'), defaults: count('[data-cv-default-row]'), hidden: count('[data-cv-default-row][hidden]'),
                users: count('[data-manage-users] tr[data-holder-id]'), remainder: count('[data-manage-users-overflow] tr[data-holder-id]'),
                overflowDisclosures: count('[data-manage-users-overflow]'), actor: count('[data-manage-actor]'),
                cells: [...document.querySelectorAll('[data-manage-actor] td')].map(el => ({key: el.dataset.permission, text: el.textContent})),
                controls: count('[data-cv-show-defaults]'), controlHidden: !document.querySelector('[data-cv-defaults-control]')?.getBoundingClientRect().height,
                configRows: count('[data-cv-config-row]'), help: [...document.querySelectorAll('[data-cv-manage-help]')].map(el => ({href: el.href, target: el.target, label: el.getAttribute('aria-label')})),
                htmlLanguage: document.documentElement.lang, csp: window.manageCspViolations ?? [], root: !!root};
        }, surface);
        const assertions = [];
        const check = (name, actual, expected = true) => {assert.deepEqual(actual, expected, `${id}/${caseId}: ${name}`); assertions.push({name, actual, expected});};
        check('surface present', measurements.nodes > 0);
        if (state === 'zero-one-many') {
            const n = Number(caseId.match(/(?:collections|holders)(\d+)/)[1]);
            const counts = {permissions: measurements.users + measurements.remainder, views: measurements.views.length,
                presentation: measurements.buttons, facts: measurements.children.length, checks: measurements.checks, defaults: measurements.defaults};
            measurements.count = counts[surface]; check('collection cardinality', measurements.count, n);
            if (surface === 'permissions') {
                check('first users', measurements.users, Math.min(n, 20)); check('remainder users', measurements.remainder, Math.max(n - 20, 0));
                check('overflow disclosure', measurements.overflowDisclosures, Number(n > 20));
                check('superuser plural count', measurements.text.includes(`${Math.min(n, 2)} active superuser${n === 1 ? ' holds' : 's hold'}`));
            }
            if (surface === 'views' || surface === 'facts') {
                const items = surface === 'views' ? measurements.views : measurements.children;
                check('vertical stacking', items.every((item, i) => !i || item.top >= items[i - 1].bottom));
            }
            if (surface === 'checks') check('plural-aware check count', measurements.text.includes(measurements.htmlLanguage === 'de'
                ? `${n} Systemprüfung${n === 1 ? ' für' : 'en für'}` : `${n} system check${n === 1 ? ' for' : 's for'}`));
            if (surface === 'defaults') {
                check('hidden default rows', measurements.hidden, n);
                check('plural-aware hidden count', measurements.text.includes(measurements.htmlLanguage === 'de'
                    ? `${n} Standardwert${n === 1 ? ' ausgeblendet' : 'e ausgeblendet'}` : `${n} default${n === 1 ? ' hidden' : 's hidden'}`));
            }
        } else if (state === 'empty') {
            const empty = {permissions: measurements.actor === 1 && /No permissions configured|No direct permission holders/.test(measurements.text),
                views: measurements.views.length === 0 && measurements.text.includes('No views registered.'),
                presentation: measurements.buttons === 0 && measurements.text.includes('No context buttons configured.'),
                facts: measurements.children.length === 0 && measurements.text.includes('top level') && measurements.text.includes('icon_header'),
                checks: measurements.issues === 0 && measurements.text.includes('no issues'), defaults: measurements.defaults === 0 && measurements.controls === 1};
            check('specific empty state', empty[surface]);
        } else if (state === 'loading' || (surface === 'defaults' && ['error', 'partial'].includes(state))) {
            check('server rendered surface', facts.raw.surfaces[surface] > 0);
            check('all configuration rows readable', measurements.hidden, 0);
            check('uninitialized control hidden', measurements.controlHidden);
            if (surface === 'help') check('native help links', measurements.help.every(link => link.href.includes('#') && link.target === '_blank' && !!link.label));
        } else if (['error', 'partial', 'populated'].includes(state)) {
            if (surface === 'presentation' && state !== 'populated') check('missing target fallback', measurements.text.includes('Target unavailable; review'));
            else if (surface === 'checks') {
                check('visible scoped issue', measurements.issues, 1);
                check('severity and ID', measurements.text.includes('Warning') && measurements.text.includes('fixture.W001'));
                check('silenced issue absent', !measurements.text.includes('fixture.W002'));
            } else if (surface === 'permissions') {
                check('actor row', measurements.actor, 1); check('permission cells', measurements.cells.length > 0);
                if (state === 'partial') {
                    const cell = key => measurements.cells.find(item => item.key === key).text;
                    check('combined grant', /model/.test(cell('view')) && /object/.test(cell('view')));
                    check('object-only grant', !/model/.test(cell('change')) && /object/.test(cell('change')));
                    check('model-only grant', /model/.test(cell('add')) && !/object/.test(cell('add')));
                    check('no grant dash', cell('delete').includes('—'));
                }
            } else if (surface === 'views') {
                check('view disclosures', measurements.views.length > 1);
                check('annotation fallback', /not declared|nicht deklariert/.test(measurements.text));
            } else if (surface === 'presentation') check('context and template sections', measurements.presentationSections === 4 && measurements.buttons > 0 && /extends/.test(measurements.text));
            else if (surface === 'facts') {
                check('identity and route facts', measurements.text.includes('pk_name') && measurements.text.includes('browser_'));
                if (caseId === 'hierarchy-resource') check('unlinked resource route', measurements.children.some(item => item.text.includes('browser_resource-manage') && item.text.includes('/parent/<browser_parent_pk>/resource-child/manage/') && item.links === 0));
                if (caseId === 'nested-ancestors') check('complete ancestor chain', measurements.text.includes('browser_parent') && measurements.text.includes('browser_child'));
            } else if (surface === 'defaults') check('toggle exercised with defaults', facts.keyboard && measurements.defaults > 0 && measurements.hidden === 0);
            else if (surface === 'help') check('documentation failure leaves source usable', facts.originalPageUnchanged);
        } else if (['overflow', 'long-text'].includes(state)) {
            check('document containment', measurements.documentWidth <= measurements.width + 1);
            check('surface containment or labeled local scroll', measurements.rects.every(r => r.height === 0 || r.localScroll || (r.left >= -1 && r.right <= measurements.width + 1)));
            const geometry = facts.opened ?? facts;
            if (surface === 'permissions') check('long holder wrapping', geometry.holders.some(item => item.textLength > 80) && geometry.holders.every(item => item.width <= 193 && (item.textLength < 80 || item.lines > 1)));
            if (surface === 'checks') check('long issue preserved', measurements.text.includes('Berechtigungsverwaltungszuständigkeitsüberprüfung'.repeat(3)));
            if (surface === 'views') check('long class path preserved', measurements.text.includes('Berechtigungsdiagnose' + 'Berechtigungsverwaltungszuständigkeitsüberprüfung'.repeat(3)));
            if (['facts', 'presentation'].includes(surface)) check('long route preserved', measurements.text.includes('permission_configuration_review_'.repeat(6)));
            if (surface === 'help') check('help target geometry', geometry.help.every(item => item.width === 32 && item.height === 32 && !item.overlap));
            check('no CSP violations', measurements.csp, []);
        }
        proofs[id] = {surface, measurements, assertions};
        validateCriterion(id, caseId, proofs[id]);
    }
    return proofs;
}
function sources() {
    const files = [...cp.execFileSync('git', ['ls-files', 'src/crud_views', 'src/crud_views_guardian'], {cwd: root, encoding: 'utf8'}).trim().split('\n'),
        'tests/browser/manage_presentation_server.py', 'tests/browser/manage-presentation.cjs',
        'tests/browser/templates/manage/page.html', 'tests/test1/app/models.py', 'tests/test1/conftest.py'];
    return {head: cp.execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root, encoding: 'utf8'}).trim(),
        files: Object.fromEntries(files.map(file => [file, sha(fs.readFileSync(path.join(root, file)))]))};
}
async function signin(context, base, ordinary = false) {
    const credentials = await (await context.request.get(base + '/signin/')).json();
    const response = await context.request.post(base + '/signin/', {form: {
        username: ordinary ? 'ordinary' : credentials.username, password: 'fixture-only', csrfmiddlewaretoken: credentials.csrf,
    }});
    assert.equal(response.status(), 200, 'Real fixture authentication failed');
}
async function openContext(browser, base, report, assets, options = {}) {
    const context = await browser.newContext({viewport: {width: options.width ?? 390, height: 900},
        serviceWorkers: 'block', javaScriptEnabled: options.javascript !== false});
    context.setDefaultTimeout(10000);
    const observed = [], failures = [], pending = [];
    await context.route('https://**/*', async route => {
        try {
            const asset = assetFor(assets, route.request().url());
            await route.fulfill({body: asset.body, status: 200,
                contentType: route.request().url().endsWith('.css') ? 'text/css' : route.request().url().endsWith('.js') ? 'text/javascript' : 'font/woff2',
                headers: {'access-control-allow-origin': '*'}});
        } catch (error) {failures.push(error.message); await route.abort();}
    });
    if (options.missing) await context.route('**/crud_views/js/manage.js', route => route.abort('failed'));
    await context.addInitScript(() => {
        window.manageCspViolations = [];
        document.addEventListener('securitypolicyviolation', event => window.manageCspViolations.push({directive: event.effectiveDirective, blocked: event.blockedURI}));
    });
    context.on('response', response => {
        const url = response.url();
        if (response.request().resourceType() === 'document') return;
        if (!url.includes('/static/') && !url.startsWith('https:') && !url.endsWith('/jquery.js')) return;
        const record = {url, status: response.status()}; observed.push(record);
        pending.push((async () => {
            record.sha256 = sha(await response.body());
            const file = url.startsWith('https:') ? assetFor(assets, url).file : url.endsWith('/jquery.js') ? path.join(root, 'node_modules/jquery/dist/jquery.min.js') :
                path.join(root, 'src', new URL(url).pathname.split('/')[2], 'static', new URL(url).pathname.slice('/static/'.length));
            record.source = file;
            assert.equal(record.sha256, sha(fs.readFileSync(file)), `Served asset differs from source: ${url}`);
        })().catch(error => failures.push(error.message)));
    });
    const page = await context.newPage();
    page.on('request', request => {
        if (['xhr', 'fetch'].includes(request.resourceType())) failures.push(`Unexpected asynchronous card request: ${request.url()}`);
    });
    page.on('pageerror', error => failures.push(error.message));
    page.on('console', message => {
        if (message.type() === 'error' && !(options.missing && message.location().url.endsWith('/manage.js'))) failures.push(message.text());
    });
    page.on('requestfailed', request => {
        if (!(options.missing && request.url().endsWith('/crud_views/js/manage.js'))) failures.push(`${request.url()}: ${request.failure()?.errorText}`);
    });
    await signin(context, base);
    return {context, page, observed, failures, pending};
}
async function inspect(page) {
    const facts = await page.evaluate(() => {
        const root = document.querySelector('[data-cv-manage]');
        return {width: innerWidth, documentWidth: document.documentElement.scrollWidth,
            overflow: [...root.querySelectorAll('*')].filter(el => {
                if (el.closest('.table-responsive') || !el.getBoundingClientRect().height) return false;
                const range = document.createRange(); range.selectNodeContents(el);
                return range.getBoundingClientRect().right > innerWidth + 1;
            }).map(el => ({tag: el.tagName, text: el.textContent.slice(0, 100), width: el.scrollWidth})),
            root: !!root, controls: root.querySelectorAll('[data-cv-show-defaults]').length,
            views: root.querySelectorAll('#cv-manage-views details').length,
            csp: window.manageCspViolations ?? [],
            tables: [...root.querySelectorAll('.table-responsive')].map(el => ({label: el.getAttribute('aria-label'), role: el.getAttribute('role'), tab: el.tabIndex})),
            defaults: root.querySelectorAll('[data-cv-default-row]').length,
            hiddenDefaults: root.querySelectorAll('[data-cv-default-row][hidden]').length,
            inline: [...root.querySelectorAll('*')].filter(el => el.tagName === 'STYLE' || (el.tagName === 'SCRIPT' && !el.src) ||
                [...el.attributes].some(a => a.name === 'style' || /^on/i.test(a.name) || /^javascript:/i.test(a.value))).length};
    });
    assert(facts.root && facts.controls === 1 && facts.views > 0);
    assert(facts.documentWidth <= facts.width + 1, `Document overflow: ${JSON.stringify(facts)}`);
    assert(facts.tables.every(el => el.label && el.role === 'region' && el.tab === 0));
    assert.deepEqual(facts.csp, []);
    assert(facts.defaults > 0 && facts.hiddenDefaults === facts.defaults);
    return facts;
}
async function capture(page, report, opts, id, facts) {
    const criteria = await criterionProofs(page, id, facts);
    const relative = `manage-screenshots/${id}.png`, file = path.resolve(path.dirname(opts.output), relative);
    fs.mkdirSync(path.dirname(file), {recursive: true});
    await page.screenshot({path: file, fullPage: true});
    report.screenshots.push({case: id, path: relative, sha256: sha(fs.readFileSync(file))});
    report.cases.push({id, passed: true, facts, criteria});
    console.log(`passed: ${id}`);
}
async function runSmoke(browser, base, report, assets, opts) {
    const owned = await openContext(browser, base, report, assets);
    try {
        for (const kind of ['core', 'guardian']) {
            const response = await owned.page.goto(`${base}/case/${kind}/normal/`);
            assert.equal(response.status(), 200);
            assert.equal(response.headers()['content-security-policy'], CSP);
            await owned.page.evaluate(() => document.fonts.ready);
            const facts = await inspect(owned.page);
            facts.codeColors = await owned.page.locator('[data-cv-manage] code').evaluateAll(elements => elements.map(el => ({
                color: getComputedStyle(el).color, parent: getComputedStyle(el.parentElement).color,
            })));
            assert(facts.codeColors.length && facts.codeColors.every(item => item.color === item.parent), 'Diagnostic code must inherit neutral theme text');
            const headingColor = await owned.page.locator('h1').evaluate(el => getComputedStyle(el).color);
            await owned.context.route('**/manage-theme.css', route => route.fulfill({contentType: 'text/css', body: '[data-cv-manage] code { color: rgb(20, 30, 40); }'}));
            const theme = await owned.page.addStyleTag({url: base + '/manage-theme.css'});
            assert(await owned.page.locator('[data-cv-manage] code').evaluateAll(elements => elements.every(el => getComputedStyle(el).color === 'rgb(20, 30, 40)')));
            assert.equal(await owned.page.locator('h1').evaluate(el => getComputedStyle(el).color), headingColor);
            await theme.evaluate(el => el.remove());
            facts.themeOverride = true;
            const required = await owned.page.locator('link[rel=stylesheet],script[src]').evaluateAll(elements => elements.map(el => el.href || el.src));
            report.requiredAssets.push(...required);
            await capture(owned.page, report, opts, `${kind}-normal-390`, facts);
        }
        await signin(owned.context, base, true);
        const denied = [];
        for (const kind of ['core', 'guardian', 'nested']) {
            const response = await owned.context.request.get(`${base}/case/${kind}/normal/`);
            assert.equal(response.status(), 403);
            assert(!(await response.text()).includes('data-cv-manage'));
            denied.push({kind, status: response.status(), diagnostics: false});
        }
        report.cases.push({id: 'ordinary-denied', passed: true, facts: {denied}, criteria: Object.fromEntries(
            ['permissions', 'views', 'facts'].map(surface => [`${surface}.error`, {surface, measurements: {denied},
                assertions: denied.map(item => ({name: `${item.kind} denies protected diagnostics`, actual: [item.status, item.diagnostics], expected: [403, false]}))}]))});
        await Promise.all(owned.pending);
        report.assets.push(...owned.observed); report.failures.push(...owned.failures);
    } finally {await owned.context.close();}
}

async function geometry(page) {
    const facts = await page.evaluate(() => {
        const root = document.querySelector('[data-cv-manage]');
        const visible = el => !!el.getBoundingClientRect().height && getComputedStyle(el).visibility !== 'hidden' && !el.closest('.visually-hidden,[hidden]');
        const rgb = color => (color.match(/[\d.]+/g) ?? []).map(Number);
        const blend = (front, back) => front.slice(0, 3).map((value, i) => value * (front[3] ?? 1) + back[i] * (1 - (front[3] ?? 1)));
        const background = el => {
            if (!el) return [255, 255, 255];
            const c = rgb(getComputedStyle(el).backgroundColor);
            return blend(c, background(el.parentElement));
        };
        const luminance = c => c.slice(0, 3).map(value => value / 255).map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
            .reduce((total, value, i) => total + value * [.2126, .7152, .0722][i], 0);
        const texts = [...root.querySelectorAll('*')].filter(el => visible(el) && [...el.childNodes].some(node => node.nodeType === 3 && node.textContent.trim()));
        const textStyles = texts.map(el => {
            const style = getComputedStyle(el), bg = background(el), fg = blend(rgb(style.color), bg), a = luminance(bg), b = luminance(fg);
            return {tag: el.tagName, text: el.textContent.trim().slice(0, 80), size: parseFloat(style.fontSize), weight: Number(style.fontWeight),
                ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05), foreground: style.color, background: bg};
        });
        const wrappers = [...root.querySelectorAll('.table-responsive')].filter(visible).map(el => {
            el.scrollLeft = 200;
            const result = {width: el.clientWidth, scrollWidth: el.scrollWidth, scroll: el.scrollLeft, label: el.getAttribute('aria-label'), role: el.getAttribute('role'), tab: el.tabIndex};
            el.scrollLeft = 0; return result;
        });
        const help = [...root.querySelectorAll('[data-cv-manage-help]')].filter(visible).map(el => {
            const rect = el.getBoundingClientRect(), header = el.parentElement, title = header.querySelector('h2,h3');
            const titleRect = title?.getBoundingClientRect();
            return {width: rect.width, height: rect.height, margin: parseFloat(getComputedStyle(el).marginInlineStart), label: el.getAttribute('aria-label'),
                target: el.target, rel: el.rel, title: el.getAttribute('title') || el.getAttribute('data-bs-original-title'),
                overlap: !!titleRect && rect.left < titleRect.right && rect.right > titleRect.left && rect.top < titleRect.bottom && rect.bottom > titleRect.top};
        });
        return {width: innerWidth, documentWidth: document.documentElement.scrollWidth, textStyles, wrappers, help,
            holders: [...root.querySelectorAll('#cv-manage-permissions th[scope=row]')].filter(visible).map(el => {
                const range = document.createRange(); range.selectNodeContents(el);
                return {width: el.getBoundingClientRect().width, wrap: getComputedStyle(el).overflowWrap,
                    textLength: el.textContent.trim().length, lines: new Set([...range.getClientRects()].map(rect => rect.top)).size};
            }),
            heading: {size: parseFloat(getComputedStyle(document.querySelector('h1')).fontSize), weight: getComputedStyle(document.querySelector('h1')).fontWeight},
            keys: [...root.querySelectorAll('.cv-manage-config th[scope=row]')].filter(visible).map(el => ({width: el.getBoundingClientRect().width, wrap: getComputedStyle(el).whiteSpace})),
            summaries: [...root.querySelectorAll('summary')].filter(visible).map(el => ({height: el.getBoundingClientRect().height, controls: el.querySelectorAll('a,button,input,select').length})),
            scopes: [...root.querySelectorAll('th')].every(el => ['row', 'col', 'rowgroup', 'colgroup'].includes(el.scope)),
            csp: window.manageCspViolations ?? [],
            counts: {defaults: root.querySelectorAll('[data-cv-default-row]').length, hidden: root.querySelectorAll('[data-cv-default-row][hidden]').length,
                users: root.querySelectorAll('[data-manage-users] tr[data-holder-id]').length, overflow: root.querySelectorAll('[data-manage-users-overflow] tr[data-holder-id]').length},
            text: root.textContent};
    });
    assert(facts.documentWidth <= facts.width + 1, `Overflow: ${facts.documentWidth}/${facts.width}`);
    assert(facts.holders.every(el => el.width <= 193 && el.wrap === 'anywhere' && (el.textLength < 80 || el.lines > 1)), `Holder labels must wrap: ${JSON.stringify(facts.holders)}`);
    assert(facts.scopes && facts.wrappers.every(el => el.label && el.role === 'region' && el.tab === 0));
    assert(facts.wrappers.every(el => el.scrollWidth <= el.width + 1 || el.scroll > 0), 'Table cannot scroll locally');
    assert(facts.keys.every(el => el.width >= 191 && el.wrap === 'nowrap'));
    assert(facts.summaries.every(el => el.height >= 44 && el.controls === 0));
    assert(facts.help.every(el => el.width === 32 && el.height === 32 && el.margin >= 8 && !el.overlap && el.label && el.title && el.target === '_blank' && el.rel === 'noopener'), 'Help target geometry/semantics');
    assert(facts.textStyles.every(item => [14, 16, 24].includes(item.size) && [400, 600].includes(item.weight)), `Typography: ${JSON.stringify(facts.textStyles.filter(item => ![14,16,24].includes(item.size) || ![400,600].includes(item.weight)))}`);
    assert(facts.textStyles.every(item => item.ratio >= 4.5), `Contrast: ${JSON.stringify(facts.textStyles.filter(item => item.ratio < 4.5))}`);
    // The inherited Bootstrap host heading is responsive below1200px; new manage content
    // has its exact14/16px roles above. Record the shell separately, preserving its behavior.
    assert(facts.heading.size <= 24 && facts.heading.size >= 20 && facts.heading.weight === '600');
    assert.deepEqual(facts.csp, []);
    return facts;
}
async function rawContract(response, page) {
    const html = await response.text();
    const facts = await page.evaluate(html => {
        const document = new DOMParser().parseFromString(html, 'text/html');
        const root = document.querySelector('[data-cv-manage]');
        return {violations: [...document.querySelectorAll('*')].filter(el => el.tagName === 'STYLE' || (el.tagName === 'SCRIPT' && !el.src) ||
            [...el.attributes].some(attr => attr.name === 'style' || /^on/i.test(attr.name) || /^javascript:/i.test(attr.value))).length,
            rows: root.querySelectorAll('[data-cv-config-row]').length, hiddenRows: root.querySelectorAll('[data-cv-config-row][hidden]').length,
            controlHidden: root.querySelector('[data-cv-defaults-control]').hasAttribute('hidden'),
            surfaces: Object.fromEntries(Object.entries({permissions: '[data-manage-actor]', views: '#cv-manage-views details',
                presentation: '#cv-manage-presentation [data-cv-config-row]', facts: '#cv-manage-viewset tr',
                checks: '#cv-manage-checks-clean, #cv-manage-checks-issues', defaults: '[data-cv-default-row]', help: '[data-cv-manage-help]'}).map(([key, selector]) => [key, root.querySelectorAll(selector).length])),
            badgeTitles: [...root.querySelectorAll('[data-cv-tooltip]')].every(el => el.title && el.tagName !== 'A'),
            descriptions: [...root.querySelectorAll('#cv-manage-views summary')].every(el => document.getElementById(el.getAttribute('aria-describedby'))?.textContent.trim())};
    }, html);
    assert.equal(facts.violations, 0, 'Inline server markup');
    assert(facts.hiddenRows === 0 && facts.controlHidden && facts.badgeTitles && facts.descriptions);
    assert.equal(response.headers()['content-security-policy'], CSP);
    return facts;
}
async function openDetails(page) {
    const summaries = page.locator('[data-cv-manage] details > summary');
    for (let i = 0; i < await summaries.count(); i++) {
        const summary = summaries.nth(i);
        await summary.focus(); await summary.press('Enter');
        assert(await summary.evaluate(el => el.parentElement.open && document.activeElement === el));
        await summary.press('Space');
        assert(await summary.evaluate(el => !el.parentElement.open && document.activeElement === el));
        await summary.press('Enter');
    }
}
async function toggleDefaults(page) {
    const control = page.locator('[data-cv-show-defaults]');
    assert(!await control.isChecked());
    const before = await page.locator('[data-cv-default-row]').count();
    assert.equal(await page.locator('[data-cv-default-row][hidden]').count(), before);
    await control.focus(); await control.press('Space');
    assert(await control.isChecked());
    assert(await control.evaluate(el => document.activeElement === el));
    assert(await control.evaluate(el => getComputedStyle(el).outlineStyle !== 'none' || getComputedStyle(el).boxShadow !== 'none'), 'Switch focus indicator');
    assert.equal(await page.locator('[data-cv-default-row][hidden]').count(), 0);
    // Tab naturally advances from the switch to its neighboring help link.
    await control.press('Tab');
    assert(await page.evaluate(() => document.activeElement.matches('[data-cv-manage-help][href$="#views"]')));
    await control.focus(); await control.press('Space');
    assert.equal(await page.locator('[data-cv-default-row][hidden]').count(), before);
    return before;
}
async function runAll(browser, base, report, assets, opts) {
    const owned = await openContext(browser, base, report, assets);
    const page = owned.page;
    try {
        for (const kind of ['core', 'guardian']) {
            for (const count of [0, 1, 3]) for (const language of ['en', 'de']) {
                const response = await page.goto(`${base}/case/${kind}/collections${count}/?language=${language}`);
                assert.equal(response.status(), 200);
                const raw = await rawContract(response, page);
                assert.equal(await page.locator('#cv-manage-views details').count(), count);
                assert.equal(await page.locator('#cv-manage-views details[open]').count(), 0);
                await openDetails(page);
                assert.equal(await toggleDefaults(page), count);
                const facts = await geometry(page);
                await capture(page, report, opts, `${kind}-collections${count}-${language}`, {raw, ...facts});
            }
            for (const width of [390, 1280]) for (const language of ['en', 'de']) {
                await page.setViewportSize({width, height: 900});
                const response = await page.goto(`${base}/case/${kind}/normal/?language=${language}`);
                assert.equal(response.status(), 200);
                await page.evaluate(() => document.fonts.ready);
                const raw = await rawContract(response, page);
                assert.equal(await page.locator('[data-cv-manage] details[open]').count(), 0);
                assert(await page.locator('#cv-manage-presentation > [data-cv-manage-help]').isVisible());
                const closed = await geometry(page);
                if (language === 'de') assert(closed.text.includes('Standardwerte anzeigen') && closed.text.includes('Darstellung'));
                assert(closed.text.includes('contact_author') && closed.text.includes('Berechtigungsverwaltungszuständigkeitsüberprüfung'));
                assert.equal(await page.locator('#cv-manage-guardian').count(), kind === 'guardian' ? 1 : 0);
                await openDetails(page);
                const defaults = await toggleDefaults(page);
                assert(defaults > 0 && await page.locator('span[data-cv-default-count]:visible').count() > 0);
                const control = page.locator('[data-cv-show-defaults]'); await control.press('Space');
                const opened = await geometry(page);
                assert(opened.text.includes('browser_annotation') && opened.text.includes(language === 'de' ? 'nicht deklariert' : 'not declared'));
                assert(opened.text.includes('x'.repeat(199)) && !opened.text.includes('x'.repeat(250)), 'Diagnostic repr must be bounded');
                const scrollable = page.locator('.table-responsive').filter({visible: true});
                for (let i = 0; i < await scrollable.count(); i++) {
                    const wrapper = scrollable.nth(i);
                    if (await wrapper.evaluate(el => el.scrollWidth > el.clientWidth + 2)) {
                        await wrapper.focus(); await wrapper.press('ArrowRight'); await page.waitForTimeout(150);
                        assert(await wrapper.evaluate(el => el.scrollLeft > 0 && document.activeElement === el));
                        break;
                    }
                }
                if (kind === 'guardian') {
                    const cells = await page.locator('[data-manage-actor] td').evaluateAll(cells => cells.map(el => ({key: el.dataset.permission, text: el.textContent})));
                    const view = cells.find(cell => cell.key === 'view'), change = cells.find(cell => cell.key === 'change');
                    assert(/model|Modell/.test(view.text) && /object|Objekt/.test(view.text));
                    assert(!/model|Modell/.test(change.text) && /object|Objekt/.test(change.text));
                    const add = cells.find(cell => cell.key === 'add');
                    assert(/model|Modell/.test(add.text) && !/object|Objekt/.test(add.text));
                }
                for (const label of language === 'de' ? ['0 Mitglieder', '1 Mitglied', '2 Mitglieder'] : ['0 members', '1 member', '2 members']) assert(opened.text.includes(label));
                const badge = page.locator('#cv-manage-views summary [data-cv-tooltip]').first();
                assert(await badge.evaluate(el => !!bootstrap.Tooltip.getInstance(el)));
                await badge.hover(); await page.locator('.tooltip.show').waitFor();
                assert((await page.locator('.tooltip.show').innerText()).length > 0);
                await page.mouse.move(0, 0); await page.waitForTimeout(250);
                assert.deepEqual(await page.evaluate(() => window.manageCspViolations), []);
                await capture(page, report, opts, `${kind}-layout-${language}-${width}`, {raw, closed, opened, tooltip: true, keyboard: true});
            }
            await page.setViewportSize({width: 390, height: 900});
            for (const scenario of ['errors', 'empty', 'no-holders', 'holders0', 'holders1', 'holders20', 'holders21', 'hidden', 'zero-defaults']) {
                const response = await page.goto(`${base}/case/${kind}/${scenario}/`);
                assert.equal(response.status(), 200, `${kind}/${scenario}`);
                const raw = await rawContract(response, page);
                await openDetails(page);
                const facts = await geometry(page);
                const html = await response.text();
                if (scenario.startsWith('holders')) {
                    const n = Number(scenario.slice(7));
                    assert.equal(facts.counts.users, Math.min(n, 20)); assert.equal(facts.counts.overflow, Math.max(n - 20, 0));
                    assert.equal(await page.locator('[data-manage-users-overflow]').count(), n > 20 ? 1 : 0);
                    assert(facts.text.includes(`${Math.min(n, 2)} active superuser`));
                }
                if (scenario === 'errors') {
                    assert(facts.text.includes('fixture.W001') && !facts.text.includes('fixture.W002'));
                    assert(facts.text.includes('Target unavailable; review'));
                    assert.equal(await page.locator('#cv-manage-checks-issues').count(), 1);
                    assert.equal(await page.locator('#cv-manage-checks-clean').count(), 0);
                    assert(html.includes('&lt;unsafe&gt;') && !html.includes('<unsafe>'));
                } else assert(facts.text.includes('no issues'));
                if (scenario === 'empty') {
                    assert.equal(await page.locator('[data-manage-actor]').count(), 1, 'Empty vocabulary retains the actor');
                    assert(facts.text.includes('No permissions configured.') && facts.text.includes('No views registered.') && facts.text.includes('No context buttons configured.'));
                    assert(facts.text.includes('No child ViewSets') && facts.text.includes('top level') && facts.text.includes('icon_header'));
                }
                if (scenario === 'no-holders') assert(facts.text.includes('No direct permission holders') && facts.text.includes('No groups hold these permissions.') && facts.text.includes('No users hold these permissions directly.'));
                if (scenario === 'hidden') assert(!html.includes('holder-00-') && !html.includes('super-0-') && !html.includes('data-manage-users'));
                if (scenario === 'zero-defaults') assert.equal(await toggleDefaults(page), 0);
                await capture(page, report, opts, `${kind}-${scenario}`, {raw, ...facts});
                if (scenario === 'errors') {
                    await page.setViewportSize({width: 1280, height: 900});
                    await capture(page, report, opts, `${kind}-errors-1280`, {raw, ...await geometry(page)});
                    await page.setViewportSize({width: 390, height: 900});
                }
            }
            for (const mode of ['no-js', 'missing-js']) {
                const plain = await openContext(browser, base, report, assets, {javascript: mode !== 'no-js', missing: mode === 'missing-js'});
                try {
                    const response = await plain.page.goto(`${base}/case/${kind}/normal/`);
                    const raw = await rawContract(response, plain.page);
                    assert(!await plain.page.locator('[data-cv-defaults-control]').isVisible());
                    assert.equal(await plain.page.locator('[data-cv-default-row][hidden]').count(), 0);
                    await openDetails(plain.page);
                    const facts = await geometry(plain.page);
                    await capture(plain.page, report, opts, `${kind}-${mode}`, {raw, ...facts});
                    await Promise.all(plain.pending);
                    report.assets.push(...plain.observed); report.failures.push(...plain.failures);
                } finally {await plain.context.close();}
            }
        }
        for (const kind of ['nested', 'hierarchy']) {
            const response = await page.goto(`${base}/case/${kind}/normal/`);
            assert.equal(response.status(), 200);
            const facts = await geometry(page);
            if (kind === 'nested') {
                assert.equal(await page.locator('#cv-manage-hierarchy a:not([data-cv-manage-help])').count(), 2);
                assert(facts.text.includes('browser_parent') && facts.text.includes('browser_child') && facts.text.includes('nearest:'));
                for (const href of await page.locator('#cv-manage-hierarchy a:not([data-cv-manage-help])').evaluateAll(links => links.map(el => el.href))) {
                    assert.equal((await owned.context.request.get(href)).status(), 200);
                }
            } else {
                assert(facts.text.includes('browser_resource-manage') && facts.text.includes('/parent/<browser_parent_pk>/resource-child/manage/') && facts.text.includes('browser_child'));
                assert.equal(await page.locator('#cv-manage-hierarchy [data-manage-child] a').count(), 0);
            }
            await capture(page, report, opts, kind === 'nested' ? 'nested-ancestors' : 'hierarchy-resource', facts);
        }
        for (const kind of ['resource', 'resource-nested']) for (const width of [390, 1280]) for (const language of ['en', 'de']) {
            await page.setViewportSize({width, height: 900});
            for (const state of ['layout', 'empty', 'none', 'no-holders']) {
                const response = await page.goto(`${base}/case/${kind}/${state === 'layout' ? 'normal' : state}/?language=${language}`);
                assert.equal(response.status(), 200, `${kind}/${state}/${language}`);
                const raw = await rawContract(response, page);
                const closed = await geometry(page);
                await openDetails(page);
                assert(await toggleDefaults(page) > 0);
                await page.locator('[data-cv-show-defaults]').press('Space');
                const opened = await geometry(page);
                assert(opened.text.includes('BrowserResource') && opened.text.includes('resource_permissions'));
                const links = await page.locator('#cv-manage-hierarchy a:not([data-cv-manage-help])').evaluateAll(els => els.map(el => el.href));
                assert.equal(links.length, kind === 'resource-nested' ? 1 : 0);
                for (const href of links) assert.equal((await owned.context.request.get(href)).status(), 200);
                const matrix = page.locator('#cv-manage-permissions');
                const text = await matrix.innerText();
                const badges = await matrix.locator('.badge.bg-info.text-dark').evaluateAll(els => els.map(el => ({
                    text: el.textContent.trim(), background: getComputedStyle(el).backgroundColor, color: getComputedStyle(el).color,
                })));
                if (state === 'layout') {
                    assert.equal(opened.counts.users, 20); assert.equal(opened.counts.overflow, 1);
                    assert.equal(await page.locator('[data-manage-users-overflow] details[open], details[data-manage-users-overflow][open]').count(), 1);
                    assert(badges.length >= 24 && badges.every(badge => badge.text === (language === 'de' ? 'Ressource' : 'resource') && badge.background === 'rgb(13, 202, 240)' && badge.color === 'rgb(33, 37, 41)'));
                    assert(text.includes(language === 'de'
                        ? 'Ressource: explizit zugeordnete Django-Berechtigung; keine Berechtigungen für einzelne Elemente.'
                        : 'resource: explicitly mapped Django permission; no per-item grants.'));
                } else if (state === 'empty' || state === 'none') {
                    assert.equal(await matrix.locator('[data-permission]').count(), 0);
                    assert(text.includes(language === 'de' ? 'Keine Ressourcen-Berechtigungen deklariert' : 'No Resource permissions declared'));
                    assert(text.includes(language === 'de' ? 'View-Einschränkungen gelten gesondert.' : 'custom view restrictions apply separately.'));
                    assert(!text.includes('No permissions configured.') && !text.includes('Keine Berechtigungen konfiguriert.'));
                    assert.equal(badges.length, 0);
                } else {
                    assert(text.includes('delete_author'));
                    assert(text.includes(language === 'de' ? 'Keine direkten Berechtigungsinhaber' : 'No direct permission holders'));
                    assert.equal(opened.counts.users, 0); assert.equal(opened.counts.overflow, 0);
                }
                await capture(page, report, opts, `${kind}-${state}-${language}-${width}`, {raw, closed, opened, badges, links, keyboard: true});
            }
        }
        const before = page.url();
        // Simulate an unavailable documentation host without making a network request.
        await owned.context.route('https://django-crud-views.readthedocs.io/**', route => route.fulfill({status: 503, body: 'Documentation temporarily unavailable'}));
        const popupPromise = owned.context.waitForEvent('page');
        await page.locator('[data-cv-manage-help]').first().click();
        const popup = await popupPromise; await popup.waitForLoadState();
        assert((await popup.locator('body').innerText()).includes('temporarily unavailable'));
        assert.equal(page.url(), before); assert(await page.locator('[data-cv-manage]').isVisible()); await popup.close();
        await capture(page, report, opts, 'documentation-failure', {originalPageUnchanged: true});
        await Promise.all(owned.pending);
        report.assets.push(...owned.observed); report.failures.push(...owned.failures);
        report.ui = uiMappings();
    } finally {await owned.context.close();}
}
async function main(argv = process.argv.slice(2)) {
    const opts = {case: 'all', output: '/tmp/cv-0633-manage-browser.json', python: '.nox/tests-3-12-django-6-0/bin/python'};
    for (let i = 0; i < argv.length; i += 2) {
        assert(['--case', '--output', '--python'].includes(argv[i]) && argv[i + 1], 'Use --python PATH --case smoke|all --output FILE');
        opts[argv[i].slice(2)] = argv[i + 1];
    }
    assert(['smoke', 'all'].includes(opts.case));
    const report = {command: [process.execPath, __filename, ...argv], started: new Date().toISOString(),
        cases: [], failures: [], assets: [], requiredAssets: [], cleanup: [], screenshots: [], csp: CSP};
    let browser, server;
    try {
        let assets;
        try {
            assets = preflight(process.env.CV_MANAGE_ASSETS_DIR ?? cacheDefault);
            report.preflight = {status: 'passed', assets: [...assets].map(([url, value]) => ({url, file: value.file, sha256: value.sha256, integrity: value.integrity}))};
        } catch (error) {report.preflight = {status: 'environment-blocked', error: error.message}; throw error;}
        report.sources = sources();
        const playwright = runtime('CV_MANAGE_PLAYWRIGHT', cached(path.join(os.homedir(), '.npm/_npx'), 'node_modules/playwright'));
        const chromium = runtime('CV_MANAGE_CHROMIUM', cached(path.join(os.homedir(), '.cache/ms-playwright'), 'chrome-linux64/chrome'), true);
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true, args: ['--no-sandbox']});
        report.browser = {playwright, chromium, version: browser.version()};
        server = await startOwned(path.resolve(opts.python), ['tests/browser/manage_presentation_server.py']);
        report.server = server.ready;
        for (const file of Object.values(server.ready.modules)) assert(file.startsWith(root + '/src/'), `Stale package: ${file}`);
        const base = `http://127.0.0.1:${server.ready.ready}`;
        await runSmoke(browser, base, report, assets, opts);
        if (opts.case === 'all') await runAll(browser, base, report, assets, opts);
        assert.deepEqual(sources(), report.sources, 'Sources changed during browser run');
        report.cleanup.push(await cleanupServer(server)); report.logs = server.logs(); server = null;
        validateEvidence(report, opts.case); report.status = 'passed';
    } catch (error) {
        report.status = report.preflight?.status === 'environment-blocked' ? 'environment-blocked' : 'failed';
        report.error = error.stack;
        if (error.cleanup) report.startupCleanup = error.cleanup;
        if (error.logs) report.startupLogs = error.logs;
        process.exitCode = 1;
    } finally {
        if (browser) await browser.close();
        if (server) {report.cleanup.push(await cleanupServer(server)); report.logs = server.logs();}
        report.finished = new Date().toISOString();
        fs.mkdirSync(path.dirname(path.resolve(opts.output)), {recursive: true});
        fs.writeFileSync(opts.output, JSON.stringify(report, null, 2) + '\n');
        console.log(`${report.status}: ${report.cases.length} cases; ${opts.output}`);
        if (report.error) console.error(report.error);
    }
    return report;
}
if (require.main === module) main().catch(error => {console.error(error); process.exitCode = 1;});
module.exports = {CSP, preflight, declarations, assetFor, validateEvidence, validateAssets, requiredCases, uiIds, uiMappings, startOwned, cleanupServer};
