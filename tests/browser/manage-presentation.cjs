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
        ...['errors', 'empty', 'no-holders', 'holders0', 'holders1', 'holders20', 'holders21', 'hidden', 'zero-defaults', 'no-js', 'missing-js'].map(state => `${kind}-${state}`),
    ]), 'nested-ancestors', 'hierarchy-resource', 'documentation-failure'];
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
    const categories = {
        empty: ['core-empty', 'guardian-empty', 'core-no-holders', 'guardian-no-holders', 'core-zero-defaults', 'hierarchy-resource'],
        loading: ['core-no-js', 'guardian-no-js', 'core-missing-js', 'guardian-missing-js'],
        error: ['core-errors', 'guardian-errors', 'ordinary-denied', 'documentation-failure'],
        populated: ['core-layout-en-1280', 'guardian-layout-en-1280', 'nested-ancestors', 'hierarchy-resource'],
        partial: ['guardian-layout-en-390', 'core-errors', 'core-hidden', 'guardian-hidden', 'hierarchy-resource'],
        overflow: ['core-layout-en-390', 'guardian-layout-en-390', 'core-layout-de-1280', 'guardian-layout-de-1280'],
        'zero-one-many': ['core-holders0', 'core-holders1', 'core-holders20', 'core-holders21', 'guardian-holders0', 'guardian-holders1', 'guardian-holders20', 'guardian-holders21', 'core-zero-defaults'],
        'long-text': ['core-layout-de-390', 'guardian-layout-de-390', 'core-errors', 'guardian-errors'],
    };
    return Object.fromEntries(uiIds().map(id => [id, categories[id.split('.')[1]]]));
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
    const relative = `manage-screenshots/${id}.png`, file = path.resolve(path.dirname(opts.output), relative);
    fs.mkdirSync(path.dirname(file), {recursive: true});
    await page.screenshot({path: file, fullPage: true});
    report.screenshots.push({case: id, path: relative, sha256: sha(fs.readFileSync(file))});
    report.cases.push({id, passed: true, facts});
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
            const required = await owned.page.locator('link[rel=stylesheet],script[src]').evaluateAll(elements => elements.map(el => el.href || el.src));
            report.requiredAssets.push(...required);
            await capture(owned.page, report, opts, `${kind}-normal-390`, facts);
        }
        await signin(owned.context, base, true);
        for (const kind of ['core', 'guardian', 'nested']) {
            assert.equal((await owned.context.request.get(`${base}/case/${kind}/normal/`)).status(), 403);
        }
        report.cases.push({id: 'ordinary-denied', passed: true});
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
            } else assert(facts.text.includes('Resource, no manage page') && facts.text.includes('browser_child'));
            await capture(page, report, opts, kind === 'nested' ? 'nested-ancestors' : 'hierarchy-resource', facts);
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
