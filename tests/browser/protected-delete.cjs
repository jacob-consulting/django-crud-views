'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const {loadAssets, assetFor, runtime, stopOwned} = require('./cancel-navigation.cjs');
const root = path.resolve(__dirname, '../..');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const scenarios = ['finite-exact', 'finite-over', 'blockers-exhaust', 'hidden-tail', 'unlimited', 'hidden-only', 'preview-off', 'escaping', 'link-off'];
const matrix = ['page-click', 'page-enter', 'modal-click', 'modal-enter', ...['page', 'modal'].flatMap(kind => scenarios.map(scenario => `${kind}-${scenario}`))];
const requiredCases = selection => selection === 'all' ? ['stock', 'custom'].flatMap(mode => matrix.map(name => `${mode}-${name}`)).concat('stock-repeat') : ['stock-page-click', 'custom-page-click', 'stock-repeat'];
function scenarioFor(id) {return scenarios.find(scenario => id.endsWith(`-${scenario}`)) ?? 'finite-exact';}
function expectedPreview(scenario) {
    const hidden = ['hidden-only', 'preview-off'].includes(scenario);
    return {plainProtected: true, displayedCount: hidden ? 0 : scenario === 'blockers-exhaust' ? 2 : scenario === 'finite-over' ? 3 : 4,
        shortenedNoticeCount: ['blockers-exhaust', 'finite-over'].includes(scenario) ? 1 : 0,
        summaryBookCount: scenario === 'preview-off' ? null : 2,
        detailsAbsent: hidden || scenario === 'blockers-exhaust'};
}
function options(argv) {
    const result = {case: 'all', output: '/tmp/cv-protected-delete.json'};
    for (let i = 0; i < argv.length; i += 2) {
        assert(['--case', '--output'].includes(argv[i]), `Unknown option: ${argv[i]}`);
        assert(argv[i + 1] && !argv[i + 1].startsWith('--'), `Missing ${argv[i]}`);
        result[argv[i].slice(2)] = argv[i + 1];
    }
    assert(['smoke', 'all'].includes(result.case), 'Use --case smoke|all');
    return result;
}
function recipes(source = fs.readFileSync(path.join(root, 'docs/migrating-1.0.md'), 'utf8'), expected) {
    assert(!source.includes('\r'), 'Recipes require LF newlines');
    const bodies = {}, hashes = {};
    for (const name of ['content', 'related', 'body']) {
        const marker = `<!-- protected-delete-recipe: ${name} -->`;
        assert.equal(source.split(marker).length - 1, 1, `Expected one ${name} marker`);
        const matches = [...source.matchAll(new RegExp(`^${marker}\\n\x60\x60\x60django\\n([\\s\\S]*?)^\x60\x60\x60$`, 'gm'))];
        assert.equal(matches.length, 1, `Expected adjacent django fence for ${name}`);
        bodies[name] = matches[0][1]; hashes[name] = sha(bodies[name]);
    }
    if (expected) assert.deepEqual(hashes, expected, 'Recipe bytes changed');
    return {bodies, hashes};
}
function sourceHashes() {
    const files = cp.execFileSync('git', ['ls-files', 'src', 'tests/test1', 'docs/migrating-1.0.md'], {cwd: root, encoding: 'utf8'}).trim().split('\n');
    files.push('tests/browser/protected-delete.cjs', 'tests/browser/protected_delete_server.py', 'tests/browser/protected-delete.test.cjs', 'tests/browser/cancel-navigation.cjs');
    return Object.fromEntries([...new Set(files)].sort().map(file => [file, sha(fs.readFileSync(path.join(root, file)))]));
}
function validateEvidence(report, selection = 'smoke', output = '/tmp/cv-protected-delete.json') {
    const required = requiredCases(selection);
    assert.deepEqual(report.cases.map(item => item.id).sort(), [...required].sort(), 'Missing, duplicate or unexpected case IDs');
    for (const item of report.cases) {
        assert.equal(item.passed, true, `Failed case ${item.id}`);
        assert.equal(item.mode, item.id.startsWith('custom-') ? 'custom' : 'stock');
        assert.equal(item.sourceKind, item.id.includes('-modal-') ? 'modal' : 'page');
        for (const key of ['noHiddenLabel', 'noHiddenHref', 'wholeFormAbsent', 'sharedAlert', 'recipeIdentity', 'escapedLabel']) assert.equal(item.dom[key], true, `${item.id}: ${key}`);
        for (const [key, value] of Object.entries(expectedPreview(scenarioFor(item.id)))) assert.equal(item.dom[key], value, `${item.id}: ${key}`);
        if (item.id.endsWith('-click') || item.id.endsWith('-enter') || item.id === 'stock-repeat') {
            assert.equal(item.activation, item.id.endsWith('-enter') ? 'Enter' : 'click');
            assert.equal(item.afterUrl, item.href, 'Navigation must reach actual href');
            assert.notEqual(item.beforeUrl, item.afterUrl, 'Navigation did not occur');
            assert.equal(item.detailStatus, 200); assert.equal(item.detailModalHeader, null);
            assert.equal(item.requestResourceType, 'document');
            assert.equal(item.dom.fullDocument, true); assert.equal(item.dom.sameRow, true);
            assert.equal(item.dom.ordinaryAnchor, true); assert.equal(item.dom.modalCapable, true);
            if (item.activation === 'Enter') {
                assert.equal(item.focusedAnchorBeforeEnter, true, 'Enter requires exact focused anchor');
                assert.equal(item.activeElementTag, 'A'); assert.equal(item.activeElementHref, item.href);
            }
        } else {
            assert.equal(item.activation, 'none'); assert.equal(item.href, null);
            assert.equal(item.beforeUrl, item.afterUrl); assert.equal(item.detailStatus, null);
            assert.equal(item.requestResourceType, null); assert.equal(item.detailModalHeader, null);
            if (item.id.endsWith('link-off')) assert.equal(item.dom.linkDisabledText, true);
            if (item.id.endsWith('preview-off')) assert.equal(item.dom.previewDisabledHidden, true);
        }
    }
    assert.deepEqual(report.sourceHashes, sourceHashes(), 'Stale source hashes');
    assert.deepEqual(report.recipeHashes, recipes().hashes, 'Stale recipe hashes');
    assert.equal(report.failures.length, 0); assert.equal(report.cleanupErrors.length, 0);
    assert(report.cleanup.stopped && report.cleanup.databaseRemoved, 'Owned cleanup incomplete');
    assert.equal(report.status, 'passed');
    if (selection === 'all') for (const mode of ['stock', 'custom']) {
        const relative = `screenshots/protected-${mode}-modal.png`, item = report.screenshots.find(item => item.path === relative);
        assert(item, `Missing screenshot ${relative}`);
        assert.equal(sha(fs.readFileSync(path.resolve(path.dirname(output), relative))), item.sha256, 'Screenshot hash mismatch');
    }
}
async function cleanup(browser, server, report) {
    const fail = (stage, error) => {report.status = 'failed'; report.error ??= error.stack; (report.cleanupErrors ??= []).push({stage, error: error.stack});};
    try {if (browser) await browser.close();} catch (error) {fail('browser.close', error);}
    try {if (server) await stopOwned(server.child);} catch (error) {fail('server.stop', error);}
    if (server) {
        report.cleanup = {pid: server.child.pid, stopped: server.child.exitCode !== null || server.child.signalCode !== null,
            databaseRemoved: !fs.existsSync(server.ready.database), database: server.ready.database};
        report.serverLogs = server.logs();
    }
}
async function startServer(python) {
    const child = cp.spawn(python, ['tests/browser/protected_delete_server.py'], {cwd: root,
        env: {...process.env, PYTHONPATH: `${root}/src:${root}`, PYTHONUNBUFFERED: '1'}, stdio: ['ignore', 'pipe', 'pipe']});
    let stdout = '', stderr = '', spawnError;
    child.once('error', error => {spawnError = error;});
    child.stdout.on('data', data => {stdout += data;}); child.stderr.on('data', data => {stderr += data;});
    try {
        for (let i = 0; i < 300; i++) {
            if (spawnError) throw spawnError;
            assert(child.exitCode === null && child.signalCode === null, `Fixture startup failed: ${stderr}`);
            const line = stdout.split('\n').slice(0, -1).find(line => line.startsWith('{"ready":'));
            if (line) return {child, ready: JSON.parse(line), logs: () => ({stdout, stderr})};
            await delay(100);
        }
        throw Error('Fixture startup timed out');
    } catch (error) {
        if (child.pid) await stopOwned(child);
        error.fixtureCleanup = {stage: 'server.start', pid: child.pid ?? null, spawned: !!child.pid,
            stopped: !child.pid || child.exitCode !== null || child.signalCode !== null};
        throw error;
    }
}
function cached(directory, suffix) {
    return fs.existsSync(directory) ? fs.readdirSync(directory).sort().reverse().map(name => path.join(directory, name, suffix)) : [];
}
async function main(argv = process.argv.slice(2)) {
    const opts = options(argv), started = Date.now();
    const report = {status: 'running', command: [process.execPath, __filename, ...argv], captured: new Date().toISOString(),
        revision: cp.execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root, encoding: 'utf8'}).trim(), sourceHashes: sourceHashes(),
        runtime: {node: process.version}, cases: [], failures: [], screenshots: [], cleanup: {}, cleanupErrors: [], humanAcceptance: 'pending; no assistive-technology testing'};
    let server, browser;
    try {
        const python = runtime('CV_CANCEL_PYTHON', [path.join(root, '.nox/tests-3-12-django-5-2/bin/python')], true);
        assert(fs.statSync(python).isFile(), 'CV_CANCEL_PYTHON must be an executable regular file');
        const playwright = runtime('CV_CANCEL_PLAYWRIGHT', cached(`${process.env.HOME}/.npm/_npx`, 'node_modules/playwright'));
        const chromium = runtime('CV_CANCEL_CHROMIUM', cached(`${process.env.HOME}/.cache/ms-playwright`, 'chrome-linux64/chrome'), true);
        const assets = loadAssets(process.env.CV_CANCEL_ASSETS_DIR);
        report.assets = [...assets].map(([url, {body, ...item}]) => ({url, ...item}));
        report.manifest = {path: path.resolve(process.env.CV_CANCEL_ASSETS_DIR, 'assets.json'), sha256: sha(fs.readFileSync(path.join(process.env.CV_CANCEL_ASSETS_DIR, 'assets.json')))};
        const expectedRecipes = recipes().hashes;
        server = await startServer(python);
        report.recipeHashes = server.ready.recipeHashes;
        assert.deepEqual(report.recipeHashes, expectedRecipes, 'Exact recipe bytes differ before browser launch');
        assert.deepEqual(report.sourceHashes, server.ready.sourceHashes, 'Server source identity differs');
        Object.assign(report.runtime, server.ready.runtime, {playwright: require(path.join(playwright, 'package.json')).version,
            playwrightPath: playwright, chromiumPath: chromium, vitest: require(path.join(root, 'node_modules/vitest/package.json')).version,
            declaredVitest: require(path.join(root, 'package.json')).devDependencies.vitest});
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true, args: ['--disable-background-networking']});
        report.runtime.chromium = browser.version();
        const base = `http://127.0.0.1:${server.ready.ready}`;
        const ctx = await browser.newContext({serviceWorkers: 'block', viewport: {width: 1280, height: 900}});
        ctx.setDefaultTimeout(10000);
        await ctx.route('**/*', async route => {
            const url = route.request().url();
            if (new URL(url).origin === base) return route.continue();
            try {const asset = assetFor(assets, url); await route.fulfill({status: 200, body: asset.body,
                contentType: url.endsWith('.css') ? 'text/css' : url.endsWith('.js') ? 'text/javascript' : 'font/woff2', headers: {'access-control-allow-origin': '*'}});
            } catch (error) {report.failures.push(error.message); await route.abort();}
        });
        const auth = await ctx.request.get(base + '/__signin/'); assert.equal(auth.status(), 200);
        const ids = await auth.json(), page = await ctx.newPage();
        page.on('pageerror', error => report.failures.push(error.stack));
        const detailPath = ids.cascadeDetailPath;
        assert(detailPath && ids.cascadeLabel, 'Missing visible cascade fixture');
        async function show(mode, kind, scenario = 'finite-exact') {
            await ctx.addCookies([{name: 'protected_mode', value: mode, url: base}, {name: 'protected_scenario', value: scenario, url: base}]);
            const target = kind === 'modal' ? '/publisher_modal_protected/' : `/publisher_cascade/${ids.publisher}/delete/`;
            const response = await page.goto(base + target); assert.equal(response.status(), 200);
            assert.equal(response.headers()['x-protected-mode'], mode);
            await page.waitForFunction(() => typeof cv !== 'undefined' && typeof bootstrap !== 'undefined');
            if (kind === 'modal') {
                await page.locator(`[cv-key="delete"][href*="/${ids.publisher}/delete/"]`).click();
                await page.locator('#cv-modal.show .alert-danger').waitFor();
            }
            return kind === 'modal' ? page.locator('#cv-modal') : page.locator('body');
        }
        async function inspect(scope, mode, scenario) {
            const hidden = ['hidden-only', 'preview-off'].includes(scenario);
            const html = await scope.innerHTML(), text = await scope.innerText();
            const details = scope.locator('.alert-warning').filter({hasText: 'Details about the related objects to be deleted:'});
            const summary = scope.locator('.alert-warning').filter({hasText: 'The following related objects will also be deleted:'});
            const bookSummary = (await summary.allInnerTexts()).join('\n').match(/book:\s*(\d+)/i);
            const dom = {
                noHiddenLabel: !html.includes(ids.hiddenLabel) && !html.includes(ids.hiddenCascadeLabel) && !text.includes('(restricted)'),
                noHiddenHref: !html.includes(ids.detailPaths.hidden) && !html.includes(ids.hiddenCascadeDetailPath),
                wholeFormAbsent: await scope.locator('form, [cv-key="cancel"], [data-cv-cancel]').count() === 0,
                sharedAlert: await scope.locator('.alert-danger[role="alert"]').count() === 1,
                recipeIdentity: await scope.locator('[data-protected-delete-recipe="body"]').count() === (mode === 'custom' && !hidden ? 1 : 0),
                escapedLabel: await scope.locator('img[src="x"]').count() === 0 && (hidden || text.includes(ids.payload)),
                plainProtected: await scope.locator('.alert-danger a').count() === 0,
                displayedCount: await scope.locator('.alert-danger li').count() + await details.locator('li').count(),
                shortenedNoticeCount: text.split('This preview is shortened. Additional objects are not shown.').length - 1,
                summaryBookCount: bookSummary ? Number(bookSummary[1]) : null,
                detailsAbsent: await details.count() === 0,
            };
            for (const key of ['noHiddenLabel', 'noHiddenHref', 'wholeFormAbsent', 'sharedAlert', 'recipeIdentity', 'escapedLabel']) assert.equal(dom[key], true, key);
            for (const [key, value] of Object.entries(expectedPreview(scenario))) assert.equal(dom[key], value, key);
            if (!hidden) {
                assert(text.includes(ids.deniedLabel));
                assert.equal(await scope.locator(`a[href="${ids.detailPaths.denied}"]`).count(), 0);
            } else {
                for (const label of [ids.allowedLabel, ids.deniedLabel]) assert(!text.includes(label));
                assert.equal(await scope.locator('a[href*="/contract/"]').count(), 0);
            }
            return dom;
        }
        for (const id of requiredCases(opts.case)) {
            const mode = id.startsWith('custom-') ? 'custom' : 'stock', kind = id.includes('-modal-') ? 'modal' : 'page';
            const navigation = id.endsWith('-click') || id.endsWith('-enter') || id === 'stock-repeat';
            const item = {id, mode, sourceKind: kind, passed: false, activation: navigation ? (id.endsWith('-enter') ? 'Enter' : 'click') : 'none',
                href: null, detailStatus: null, detailModalHeader: null, focusedAnchorBeforeEnter: null, activeElementTag: null,
                activeElementHref: null, requestResourceType: null}; report.cases.push(item);
            const scenario = scenarioFor(id), scope = await show(mode, kind, scenario);
            item.scenario = scenario;
            item.beforeUrl = page.url(); item.dom = await inspect(scope, mode, scenario);
            if (navigation) {
                const anchor = scope.locator(`.alert-warning a[href="${detailPath}"]`);
                assert.equal(await anchor.count(), 1); item.href = await anchor.evaluate(el => el.href);
                item.dom.ordinaryAnchor = await anchor.evaluate(el => el.getAttributeNames().every(name => name === 'href') && !el.target);
                assert(item.dom.ordinaryAnchor);
                if (kind === 'modal' && item.activation === 'click' && opts.case === 'all') {
                    const relative = `screenshots/protected-${mode}-modal.png`, file = path.resolve(path.dirname(opts.output), relative);
                    await page.mouse.move(0, 800);
                    await page.locator('.tooltip.show').waitFor({state: 'hidden'});
                    await page.waitForFunction(() => {
                        const modal = document.querySelector('#cv-modal.show');
                        return modal && getComputedStyle(modal).opacity === '1' &&
                            getComputedStyle(modal.querySelector('.modal-dialog')).transform === 'none';
                    });
                    fs.mkdirSync(path.dirname(file), {recursive: true}); await page.screenshot({path: file});
                    report.screenshots.push({path: relative, sha256: sha(fs.readFileSync(file))});
                }
                if (item.activation === 'Enter') {
                    await anchor.focus();
                    Object.assign(item, await anchor.evaluate(el => ({focusedAnchorBeforeEnter: document.activeElement === el,
                        activeElementTag: document.activeElement.tagName, activeElementHref: document.activeElement.href})));
                    assert(item.focusedAnchorBeforeEnter);
                }
                const responsePromise = page.waitForResponse(response => response.url() === item.href && response.request().isNavigationRequest());
                if (item.activation === 'Enter') await anchor.press('Enter'); else await anchor.click();
                const response = await responsePromise; await page.waitForURL(item.href); await page.waitForLoadState();
                item.detailStatus = response.status(); item.detailModalHeader = response.request().headers()['x-cv-modal'] ?? null;
                item.requestResourceType = response.request().resourceType();
                item.dom.fullDocument = /<html[\s>]/i.test(await response.text()) && /<!doctype html>/i.test(await response.text());
                const detailText = await page.locator('body').innerText();
                item.dom.sameRow = detailText.includes(ids.cascadeLabel) && !detailText.includes(ids.payload) && new URL(page.url()).pathname === detailPath;
                item.dom.modalCapable = response.headers()['x-protected-detail-modal-capable'] === 'true';
            } else if (scenario === 'link-off') {
                item.dom.linkDisabledText = await scope.locator('.cv-related-objects a').count() === 0;
                assert(item.dom.linkDisabledText);
            } else if (scenario === 'preview-off') {
                item.dom.previewDisabledHidden = await scope.locator('.cv-related-objects').count() === 0;
                assert(item.dom.previewDisabledHidden);
            }
            item.afterUrl = page.url(); item.passed = true;
        }
        report.status = 'passed';
    } catch (error) {report.status = 'failed'; report.error = error.stack; report.failures.push(error.message); if (error.fixtureCleanup) report.cleanup = error.fixtureCleanup;
    } finally {
        await cleanup(browser, server, report);
        report.durationSeconds = (Date.now() - started) / 1000;
        if (report.status === 'passed') try {validateEvidence(report, opts.case, opts.output);} catch (error) {report.status = 'failed'; report.error = error.stack; report.failures.push(error.message);}
        fs.mkdirSync(path.dirname(path.resolve(opts.output)), {recursive: true}); fs.writeFileSync(opts.output, JSON.stringify(report, null, 2) + '\n');
    }
    console.log(JSON.stringify({status: report.status, cases: report.cases.length, durationSeconds: report.durationSeconds, output: opts.output, error: report.error}));
    if (report.status !== 'passed') throw Error(`Protected-delete acceptance failed: ${report.error}`);
    return report;
}
module.exports = {validateEvidence, cleanup, main, options, recipes, sourceHashes, requiredCases, startServer};
if (require.main === module) main().catch(error => {console.error(error.stack); process.exitCode = 1;});
