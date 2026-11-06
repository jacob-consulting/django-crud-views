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
    return ['native-first-page', 'required-recovery-page'];
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
    const context = await browser.newContext({javaScriptEnabled: false, viewport: {width: 375, height: 844}, serviceWorkers: 'block'});
    context.setDefaultTimeout(10000);
    await context.route('**/*', async route => {
        const url = route.request().url();
        if (url.startsWith(base + '/')) return route.continue();
        try {
            const asset = assetFor(assets, url);
            await route.fulfill({status: 200, body: asset.body, contentType: url.endsWith('.css') ? 'text/css' : url.endsWith('.js') ? 'text/javascript' : 'font/woff2', headers: {'access-control-allow-origin': '*'}});
            report.assets.push({url, status: 200, sha256: asset.sha256, source: asset.file});
        } catch (error) {report.failures.push(error.message); await route.abort();}
    });
    try {
        assert.equal((await context.request.get(base + '/signin/')).status(), 200);
        for (const id of requiredCases(opts.case)) {
            const page = await context.newPage(), posts = [];
            page.on('pageerror', error => report.failures.push(error.message));
            page.on('response', response => {
                if (response.request().method() === 'POST') posts.push({url: response.url(), status: response.status(),
                    fields: Object.fromEntries(new URLSearchParams(response.request().postData()))});
            });
            const observe = async () => (await context.request.get(`${base}/observe/${id}/`)).json();
            try {
                assert.equal((await page.goto(`${base}/workflow/${id}/`)).status(), 200);
                const before = await observe(), initial = await inspect(page);
                assert.deepEqual(initial.actions.map(item => item.name), ['wf_activate', 'wf_cancel_new']);
                assert(initial.actions.every(item => !item.disabled));
                const name = id === 'native-first-page' ? 'wf_activate' : 'wf_cancel_new';
                let invalid;
                if (id === 'required-recovery-page') {
                    await page.locator('[name=comment]').fill('   ');
                    await Promise.all([page.waitForNavigation(), page.locator(`button[value=${name}]`).click()]);
                    invalid = await inspect(page);
                    assert(invalid.errors.some(error => error.text.includes('Comment is required')));
                    assert.equal(posts[0].status, 200); assert.deepEqual((await observe()).history, []);
                    await page.locator('[name=comment]').fill('  Approved by browser  ');
                }
                await Promise.all([page.waitForNavigation(), page.locator(`button[value=${name}]`).click()]);
                const after = await observe();
                assert.equal(after.history.length, 1); assert.equal(after.history[0].transition, name);
                assert.equal(after.state, name === 'wf_activate' ? 'active' : 'canceled');
                assert.equal(posts.at(-1).fields.transition, name); assert.equal(posts.at(-1).status, 302);
                report.cases.push({id, passed: true, javaScriptEnabled: false, initial, invalid, before, after, posts});
            } finally {await page.close();}
        }
    } finally {await context.close();}
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
