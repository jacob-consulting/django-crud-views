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
    'tests/browser/modal-focus.cjs', 'docs/reference/javascript.md', 'docs/reference/modals.md',
    `${phase}/17-evidence/server.py`, 'src/crud_views/templates/crud_views/modal/shell.html',
    'src/crud_views/templates/crud_views/modal/content.html', 'package-lock.json',
];
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const hashes = () => Object.fromEntries(inputs.map(file => [file, digest(file)]));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

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
        const c = cases.find(c => c.mode === 'partial' && c.language === 'en');
        const result = {id: 'unchecked', passed: false, assertions: [], screenshots: []}; record.cases.push(result);
        const check = (name, condition) => { result.assertions.push({name, passed: Boolean(condition)}); assert(condition, name); };
        await page.goto(base + '/harness/?target=' + encodeURIComponent(c.url));
        await page.waitForFunction(() => typeof bootstrap === 'object' && typeof cv.cvModalOpen === 'function');
        await page.locator('#launch').focus(); await page.keyboard.press('Enter');
        await page.locator('#cv-modal').waitFor({state: 'visible'}); await delay(400);
        await page.evaluate(() => {
            window.focusEvents = [];
            document.getElementById('cv-modal').addEventListener('hidden.bs.modal', () => focusEvents.push('hidden'));
            document.getElementById('launch').addEventListener('focus', () => focusEvents.push('opener'));
        });
        await page.locator('#cv-modal [type="submit"]').focus();
        const response = page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes(c.url));
        await page.keyboard.press('Enter'); result.status = (await response).status();
        await page.waitForFunction(() => document.querySelector('#cv-modal .invalid-feedback'));
        await delay(100);
        result.focus = await page.evaluate(() => {
            const el = document.activeElement;
            return {tag: el.tagName, id: el.id, name: el.name, connected: el.isConnected, visible: !!el.getClientRects().length,
                focusVisible: el.matches(':focus-visible'), inModal: !!el.closest('#cv-modal')};
        });
        const shot = `${screenshotDir}/unchecked.png`; await page.screenshot({path: shot});
        result.screenshots.push({path: shot, sha256: digest(shot)});
        check('real 422', result.status === 422);
        check('invalid confirmation retains visible keyboard focus', result.focus.name === 'confirm' && result.focus.inModal && result.focus.visible && result.focus.focusVisible);
        check('exactly one form', await page.locator('#cv-modal form.cv-form').count() === 1);
        result.state = await (await context.request.get(`${base}/state/${c.pk}/`)).json();
        check('invalid request does not delete or call custom handler', result.state.exists && result.state.events.length === 0);
        await page.locator('#cv-modal [data-cv-modal-dismiss]').focus(); await page.keyboard.press('Enter');
        await page.locator('#cv-modal').waitFor({state: 'hidden'}); await delay(100);
        result.close = await page.evaluate(() => ({id: document.activeElement.id, events: focusEvents}));
        check('completed hide returns exact opener', result.close.id === 'launch' && result.close.events.join(',') === 'hidden,opener');
        check('no page errors', record.pageErrors.length === 0);
        result.passed = true;
        record.completed = true; record.passed = true;
    } catch (error) { record.error = error.stack; record.completed = true; throw error; }
    finally {
        if (browser) await browser.close();
        if (child && child.exitCode === null && child.signalCode === null) {
            child.kill('SIGTERM');
            await Promise.race([new Promise(resolve => child.once('exit', resolve)), delay(3000)]);
            if (child.exitCode === null && child.signalCode === null) { child.kill('SIGKILL'); await new Promise(resolve => child.once('exit', resolve)); }
        }
        fs.writeFileSync(output, JSON.stringify(record, null, 2) + '\n');
    }
    console.log('FOCUS_BROWSER_OK');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
