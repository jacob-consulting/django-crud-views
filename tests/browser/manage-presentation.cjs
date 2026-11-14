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
    return ['core-normal-390', 'guardian-normal-390', 'ordinary-denied'];
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
async function runSmoke(browser, base, report, assets) {
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
            report.cases.push({id: `${kind}-normal-390`, passed: true, facts});
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
        await runSmoke(browser, `http://127.0.0.1:${server.ready.ready}`, report, assets);
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
module.exports = {CSP, preflight, declarations, assetFor, validateEvidence, validateAssets, requiredCases, startOwned, cleanupServer};
