'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const {runtime, stopOwned} = require('./cancel-navigation.cjs');
const root = path.resolve(__dirname, '../..');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const cached = (directory, suffix) => fs.existsSync(directory) ? fs.readdirSync(directory).sort().reverse().map(name => path.join(directory, name, suffix)) : [];
const states = ['normal', 'wide', 'no-history', 'terminal', 'neither', 'invalid'];
const badges = ['custom', 'missing', 'empty', 'none', 'restored'];
function requiredCases(selection) {
    return ['stock', 'tabler'].flatMap(theme => selection === 'smoke' ? [`${theme}-normal-390`, `${theme}-invalid-390`] :
        [...[390, 1280].flatMap(width => states.map(state => `${theme}-${state}-${width}`)),
            ...badges.map(badge => `${theme}-badge-${badge}`), `${theme}-modal`, `${theme}-submit`]);
}
function validateEvidence(report, selection) {
    for (const id of requiredCases(selection)) assert(report.cases.some(item => item.id === id && item.passed), `Missing case: ${id}`);
    assert.deepEqual(report.failures, []);
    assert.equal(report.cleanup.length, 2);
    for (const item of report.cleanup) assert(item.stopped && item.databaseRemoved, 'Owned cleanup incomplete');
}
function validateAssets(required, observed) {
    for (const url of required) {
        const item = observed.find(item => item.url === url);
        assert(item, `Missing required asset: ${url}`);
        assert.equal(item.status, 200, `Failed required asset: ${url}`);
    }
}
async function startOwned(executable, args, timeout = 30000) {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-workflow-'));
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
        error.cleanup = await cleanupServer(server);
        error.logs = server.logs();
        throw error;
    }
}
async function cleanupServer(server) {
    if (server.child.pid) await stopOwned(server.child);
    const stopped = !server.child.pid || server.child.exitCode !== null || server.child.signalCode !== null;
    assert(stopped, 'Owned process did not stop');
    fs.rmSync(server.directory, {recursive: true, force: true});
    return {pid: server.child.pid ?? null, stopped, directory: server.directory,
        databaseRemoved: !fs.existsSync(server.directory)};
}
function sources(companion) {
    const upstreamFiles = ['src/crud_views/lib/button_classes.py', 'src/crud_views/apps.py',
        'src/crud_views/templates/crud_views/snippets/form_frame.html',
        ...cp.execFileSync('git', ['ls-files', 'src/crud_views_workflow'], {cwd: root, encoding: 'utf8'}).trim().split('\n'),
        'tests/browser/workflow_presentation_server.py', 'tests/browser/workflow-presentation.cjs',
        'tests/browser/templates/conditional_formsets/page.html', 'tests/test1/app/models.py', 'tests/test1/app/views.py'];
    const companionFiles = ['src/crud_views_tabler/apps.py', 'src/crud_views_tabler/buttons.py',
        'src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css',
        'src/crud_views_tabler/templates/crud_views/snippets/form_frame.html',
        'src/crud_views_tabler/templates/crud_views_tabler/page.html',
        'src/django_tabler/templates/django_tabler/base.html', 'src/django_tabler/templates/django_tabler/layouts/app.html',
        'src/django_tabler/static/django_tabler/django_tabler.css'];
    return [[root, upstreamFiles], [companion, companionFiles]].map(([directory, files]) => ({directory,
        head: cp.execFileSync('git', ['rev-parse', 'HEAD'], {cwd: directory, encoding: 'utf8'}).trim(),
        files: Object.fromEntries(files.map(file => [file, sha(fs.readFileSync(path.join(directory, file)))])),
        scopedDiff: cp.execFileSync('git', ['diff', 'HEAD', '--', ...files], {cwd: directory, encoding: 'utf8'})}));
}
function declarations(theme, companion) {
    const file = theme === 'stock' ? path.join(root, 'tests/browser/templates/conditional_formsets/page.html') :
        path.join(companion, 'src/django_tabler/templates/django_tabler/base.html');
    return [...fs.readFileSync(file, 'utf8').matchAll(/<(?:link|script)\b[^>]*?(?:href|src)="(https:[^"]+)"[^>]*>/gs)]
        .map(([tag, url]) => ({url, integrity: tag.match(/integrity="([^"]+)"/)?.[1] ?? null}));
}
async function inspect(page, expected, theme) {
    const result = await page.evaluate(() => {
        const forms = [...document.querySelectorAll('form.cv-form')];
        const table = document.querySelector('table');
        const wrapper = table?.parentElement;
        const heading = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].find(el => el.textContent.trim() === 'Workflow History');
        const actionHeading = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].find(el => el.textContent.trim() === 'Workflow Action');
        const content = wrapper?.parentElement;
        const contentStyle = content && getComputedStyle(content);
        let geometry = null;
        if (wrapper) {
            wrapper.scrollLeft = 100;
            geometry = {wrapper: wrapper.clientWidth, scrollWidth: wrapper.scrollWidth, scrollDelta: wrapper.scrollLeft,
                table: table.getBoundingClientRect().width, display: getComputedStyle(table).display,
                overflowX: getComputedStyle(wrapper).overflowX,
                available: content.clientWidth - parseFloat(contentStyle.paddingLeft) - parseFloat(contentStyle.paddingRight),
                children: [...wrapper.children].map(el => el.tagName), headers: table.querySelectorAll('th[scope=col]').length,
                headingOutside: !!heading && !wrapper.contains(heading),
                actionOutside: forms.every(form => !wrapper.contains(form)) && (!actionHeading || !wrapper.contains(actionHeading)),
                historyBeforeActions: !actionHeading || !!(wrapper.compareDocumentPosition(actionHeading) & Node.DOCUMENT_POSITION_FOLLOWING)};
            wrapper.scrollLeft = 0;
        }
        return {forms: forms.length, tokens: document.querySelectorAll('form.cv-form [name=csrfmiddlewaretoken]').length,
            ownership: forms.map(form => ({tokens: form.querySelectorAll('[name=csrfmiddlewaretoken]').length,
                submits: [...form.querySelectorAll('button[type=submit],input[type=submit]')].filter(el => el.form === form).length,
                method: form.getAttribute('method'), nested: form.querySelectorAll('form').length,
                inCard: !!form.closest('.card-body'), headingInCard: !!actionHeading && actionHeading.parentElement === form.parentElement})),
            actionHeading: !!actionHeading, empty: document.body.textContent.includes('There are no workflow steps available from the current state.'),
            error: document.body.textContent.includes('Comment is required for this transition'),
            table: !!table, geometry, documentWidth: document.documentElement.scrollWidth, viewport: innerWidth,
            font: getComputedStyle(document.body).fontFamily,
            badges: table ? [...table.querySelectorAll('td span')].map(el => ({text: el.textContent, classes: el.getAttribute('class'), children: el.children.length})) : []};
    });
    const choices = !['terminal', 'neither'].includes(expected);
    assert.equal(result.forms, choices ? 1 : 0);
    assert.equal(result.tokens, choices ? 1 : 0);
    assert.equal(result.actionHeading, choices);
    assert.equal(result.empty, !choices);
    assert.equal(result.table, !['no-history', 'neither'].includes(expected));
    if (choices) {
        assert.equal(result.ownership[0].tokens, 1); assert.equal(result.ownership[0].submits, 1);
        assert.equal(result.ownership[0].nested, 0); assert.equal(result.ownership[0].method, 'post');
        if (theme === 'tabler') assert(result.ownership[0].inCard && result.ownership[0].headingInCard);
    }
    assert(result.documentWidth <= result.viewport + 1, `Page overflow: ${JSON.stringify(result)}`);
    if (result.geometry) {
        const g = result.geometry;
        assert(Math.abs(g.wrapper - g.available) <= 2, `Wrapper width: ${JSON.stringify(g)}`);
        assert(g.table >= g.wrapper - 2, `Shrinking table: ${JSON.stringify(g)}`);
        assert.equal(g.display, 'table'); assert.equal(g.headers, 6); assert.deepEqual(g.children, ['TABLE']);
        assert(g.headingOutside && g.actionOutside && g.historyBeforeActions);
        if (expected === 'normal' && result.viewport === 1280) assert(Math.abs(g.table - g.wrapper) <= 2);
        if (expected === 'wide' || g.scrollWidth > g.wrapper + 1) {
            assert(g.scrollWidth > g.wrapper && g.scrollDelta > 0 && ['auto', 'scroll'].includes(g.overflowX));
        }
    }
    if (expected === 'invalid') assert(result.error);
    return result;
}
async function runTheme(browser, theme, companion, opts, report, assetCache) {
    const python = runtime(theme === 'stock' ? 'CV_WORKFLOW_PYTHON' : 'CV_WORKFLOW_THEME_PYTHON',
        [theme === 'stock' ? path.join(root, '.nox/tests-3-12-django-5-2/bin/python') : path.join(companion, '.venv/bin/python')], true);
    let server, context;
    try {
        server = await startOwned(python, ['tests/browser/workflow_presentation_server.py', '--theme', theme, '--companion', companion]);
        report.servers.push({...server.ready, executable: python});
        const origins = server.ready.origins;
        assert.equal(origins['crud_views_workflow/badge.html'], path.join(root, 'src/crud_views_workflow/templates/crud_views_workflow/badge.html'));
        assert.equal(origins['crud_views/snippets/form_frame.html'], path.join(theme === 'stock' ? root : companion,
            `src/${theme === 'stock' ? 'crud_views' : 'crud_views_tabler'}/templates/crud_views/snippets/form_frame.html`));
        for (const [name, filename] of Object.entries(server.ready.modules)) assert(filename.startsWith(path.join(
            ['crud_views', 'crud_views_workflow'].includes(name) ? root : companion, 'src') + '/'), `Stale module ${name}`);
        const base = `http://127.0.0.1:${server.ready.ready}`;
        context = await browser.newContext({viewport: {width: 390, height: 844}, serviceWorkers: 'block'});
        context.setDefaultTimeout(10000);
        const declared = declarations(theme, companion), pending = [], observed = [];
        await context.route('https://**/*', async route => {
            const url = route.request().url();
            try {
                assert(['cdn.jsdelivr.net', 'cdnjs.cloudflare.com'].includes(new URL(url).hostname), `Undeclared asset host: ${url}`);
                if (!assetCache.has(url)) {
                    const cacheFile = path.join(os.homedir(), '.cache/django-crud-views/cancel-assets-06.7', new URL(url).hostname, new URL(url).pathname);
                    const body = fs.existsSync(cacheFile) ? fs.readFileSync(cacheFile) : cp.execFileSync('curl', ['--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], {maxBuffer: 8 * 1024 * 1024});
                    assetCache.set(url, {body, source: fs.existsSync(cacheFile) ? cacheFile : url});
                }
                const asset = assetCache.get(url), integrity = declared.find(item => item.url === url)?.integrity;
                if (integrity) {
                    const [algorithm, digest] = integrity.split('-');
                    assert.equal(crypto.createHash(algorithm).update(asset.body).digest('base64'), digest, `SRI mismatch: ${url}`);
                }
                await route.fulfill({body: asset.body, status: 200,
                    contentType: url.endsWith('.css') ? 'text/css' : url.endsWith('.js') ? 'text/javascript' : 'font/woff2',
                    headers: {'access-control-allow-origin': '*'}});
            } catch (error) {report.failures.push(error.message); await route.abort();}
        });
        context.on('response', response => {
            const url = response.url();
            if (!url.includes('/static/') && !url.startsWith('https:')) return;
            if (observed.some(item => item.url === url)) return;
            const record = {url, status: response.status(), theme}; observed.push(record);
            pending.push((async () => {
                record.sha256 = sha(await response.body());
                if (url.startsWith('https:')) record.source = assetCache.get(url)?.source;
                else {
                    const relative = new URL(url).pathname.replace(/^\/static\//, '');
                    const app = relative.split('/')[0];
                    record.source = path.join(['django_tabler', 'crud_views_tabler'].includes(app) ? companion : root, 'src', app, 'static', relative);
                    assert.equal(record.sha256, sha(fs.readFileSync(record.source)), `Static source mismatch: ${url}`);
                }
            })().catch(error => report.failures.push(error.message)));
        });
        const page = await context.newPage();
        page.on('pageerror', error => report.failures.push(error.message));
        page.on('requestfailed', request => report.failures.push(`${request.url()}: ${request.failure()?.errorText}`));
        assert.equal((await context.request.get(base + '/signin/')).status(), 200);
        async function observation() {
            const response = await context.request.get(base + '/observations/');
            const result = await response.json();
            assert(result.raw.maximum <= 1 && result.raw.depth === 0, 'Raw nested form');
            return result;
        }
        async function visit(state, width = 390, badge = null) {
            await page.setViewportSize({width, height: width === 390 ? 844 : 900});
            const response = await page.goto(`${base}/workflow/${state === 'invalid' ? 'normal' : state}/${badge ? '?badge=' + badge : ''}`);
            assert.equal(response.status(), 200, `Workflow GET failed: ${response.url()}; see server logs`);
            await page.evaluate(() => document.fonts.ready);
            if (state === 'invalid') {
                await page.locator('[name=transition][value=wf_cancel_new]').check();
                const posted = page.waitForResponse(response => response.request().method() === 'POST');
                await page.locator('form.cv-form [type=submit]').click();
                assert.equal((await posted).status(), 200);
                await page.waitForLoadState('load'); await page.evaluate(() => document.fonts.ready);
            }
            return {measurement: await inspect(page, state, theme), observation: await observation()};
        }
        for (const width of opts.case === 'smoke' ? [390] : [390, 1280]) {
            for (const state of opts.case === 'smoke' ? ['normal', 'invalid'] : states) {
                const details = await visit(state, width);
                const expectedClass = theme === 'stock' ? 'badge rounded-pill text-bg-light' : 'badge bg-light-lt';
                assert.equal(details.measurement.badges[0]?.classes ?? expectedClass, expectedClass);
                report.cases.push({id: `${theme}-${state}-${width}`, passed: true, ...details});
                if (opts.case === 'all' && width === 390 && ['normal', 'wide'].includes(state)) {
                    const relative = `screenshots/workflow-${theme}-${state}-390.png`;
                    const filename = path.resolve(path.dirname(opts.output), relative);
                    fs.mkdirSync(path.dirname(filename), {recursive: true});
                    await page.screenshot({path: filename, fullPage: true});
                    report.screenshots.push({path: relative, sha256: sha(fs.readFileSync(filename))});
                }
            }
        }
        if (opts.case === 'all') {
            for (const badge of badges) {
                const details = await visit('normal', 390, badge);
                const first = details.measurement.badges[0];
                const expected = badge === 'custom' ? 'badge custom-purple " <unsafe> {{literal}}' : badge === 'missing' ? 'badge rounded-pill text-bg-purple' :
                    ['empty', 'none'].includes(badge) ? '' : theme === 'stock' ? 'badge rounded-pill text-bg-light' : 'badge bg-light-lt';
                assert.equal(first.classes, expected); assert.equal(first.children, 0);
                if (badge === 'custom') assert.equal(first.text, '<b>State & "quoted"</b>');
                const current = await page.evaluate(html => {
                    const el = new DOMParser().parseFromString(html, 'text/html').body.firstElementChild;
                    return {classes: el.getAttribute('class'), text: el.textContent, children: el.children.length};
                }, details.observation.current_badge);
                assert.deepEqual(current, first);
                report.cases.push({id: `${theme}-badge-${badge}`, passed: true, current, ...details});
            }
            const response = await context.request.get(base + '/workflow/neither/', {headers: {'X-CV-Modal': 'true'}});
            assert.equal(response.status(), 200);
            const html = await response.text(), obs = await observation();
            assert.equal(obs.raw.forms, 1); assert.equal(obs.raw.tokens, 1);
            assert(Object.keys(obs.origins).includes('crud_views/view_custom_form.content.html'));
            assert(!html.includes('class="card"') && !html.includes('Workflow History'));
            const denied = await context.request.post(base + '/workflow/normal/', {form: {transition: 'wf_cancel_new', comment: ''}});
            assert.equal(denied.status(), 403, 'CSRF middleware was bypassed');
            report.cases.push({id: `${theme}-modal`, passed: true, status: response.status(), csrfMissingStatus: denied.status(), observation: obs});
            const formPage = await context.request.get(base + '/workflow/normal/');
            const token = (await formPage.text()).match(/name="csrfmiddlewaretoken" value="([^"]+)"/)[1];
            const submitted = await context.request.post(base + '/workflow/normal/', {
                form: {csrfmiddlewaretoken: token, transition: 'wf_cancel_new', comment: 'Successful submission regression'},
                maxRedirects: 0,
            });
            assert.equal(submitted.status(), 302, 'Successful workflow submission must preserve the redirect');
            const destination = await context.request.get(new URL(submitted.headers().location, base).href);
            assert.equal(destination.status(), 200);
            const history = await context.request.get(base + '/workflow/normal/');
            assert((await history.text()).includes('Successful submission regression'));
            report.cases.push({id: `${theme}-submit`, passed: true, status: submitted.status(), destinationStatus: destination.status()});
        }
        await Promise.all(pending);
        validateAssets(declared.map(item => item.url), observed);
        report.assets.push(...observed);
    } finally {
        if (context) await context.close();
        if (server) {report.cleanup.push(await cleanupServer(server)); report.logs[theme] = server.logs();}
    }
}
async function main(argv = process.argv.slice(2)) {
    const opts = {case: 'all', output: '/tmp/cv-workflow.json'};
    for (let i = 0; i < argv.length; i += 2) {
        assert(['--case', '--output'].includes(argv[i]) && argv[i + 1], 'Use --case smoke|all --output FILE');
        opts[argv[i].slice(2)] = argv[i + 1];
    }
    assert(['smoke', 'all'].includes(opts.case));
    const report = {command: [process.execPath, __filename, ...argv], started: new Date().toISOString(),
        cases: [], failures: [], servers: [], assets: [], cleanup: [], screenshots: [], logs: {}};
    let browser;
    try {
        const companion = path.resolve(process.env.CV_WORKFLOW_COMPANION ?? path.join(root, '../tabler-test'));
        report.sources = sources(companion);
        const playwright = runtime('CV_WORKFLOW_PLAYWRIGHT', cached(path.join(os.homedir(), '.npm/_npx'), 'node_modules/playwright'));
        const chromium = runtime('CV_WORKFLOW_CHROMIUM', cached(path.join(os.homedir(), '.cache/ms-playwright'), 'chrome-linux64/chrome'), true);
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true, args: ['--no-sandbox']});
        report.browser = {playwright, version: require(path.join(playwright, 'package.json')).version, chromium, versionChromium: browser.version()};
        const cache = new Map();
        for (const theme of ['stock', 'tabler']) await runTheme(browser, theme, companion, opts, report, cache);
        assert.deepEqual(sources(companion), report.sources, 'Sources changed during browser run');
        validateEvidence(report, opts.case); report.status = 'passed';
    } catch (error) {
        report.status = 'failed'; report.error = error.stack;
        if (error.cleanup) report.startupCleanup = error.cleanup;
        if (error.logs) report.startupLogs = error.logs;
        process.exitCode = 1;
    } finally {
        if (browser) await browser.close();
        report.finished = new Date().toISOString();
        fs.mkdirSync(path.dirname(path.resolve(opts.output)), {recursive: true});
        fs.writeFileSync(opts.output, JSON.stringify(report, null, 2) + '\n');
        console.log(`${report.status}: ${report.cases.length} cases; ${opts.output}`);
        if (report.error) console.error(report.error);
    }
    return report;
}
if (require.main === module) main().catch(error => {console.error(error); process.exitCode = 1;});
module.exports = {validateEvidence, validateAssets, requiredCases, startOwned, cleanupServer};
