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
function options(argv) {
    const result = {case: 'all', output: '/tmp/cv-action-tooltips.json'};
    for (let i = 0; i < argv.length; i += 2) {
        assert(['--case', '--output'].includes(argv[i]), `Unknown option: ${argv[i]}`);
        assert(argv[i + 1] && !argv[i + 1].startsWith('--'), `Missing ${argv[i]}`);
        result[argv[i].slice(2)] = argv[i + 1];
    }
    assert(['smoke', 'all'].includes(result.case), 'Use --case smoke|all');
    return result;
}
function cached(directory, suffix) {
    return fs.existsSync(directory) ? fs.readdirSync(directory).sort().reverse().map(name => path.join(directory, name, suffix)) : [];
}
function identity(actual, mode, kind = 'action-leaf') {
    assert.equal(actual, mode === 'custom' ? kind : null, 'Recipe root identity mismatch');
}
function recipeHashes() {
    const text = fs.readFileSync(path.join(root, 'docs/reference/buttons.md'), 'utf8');
    return Object.fromEntries(['action-leaf', 'menu-leaf', 'raw-context'].map(name => {
        const matches = [...text.matchAll(new RegExp(`^<!-- tooltip-recipe: ${name} -->\\n\x60\x60\x60django\\n([\\s\\S]*?)\\n\x60\x60\x60(?=\\n|$)`, 'gm'))];
        assert.equal(matches.length, 1); return [name, sha(matches[0][1])];
    }));
}
const matrix = ['mixed-context', 'mixed-list', ...['icon', 'label', 'both'].flatMap(mode => ['context', 'list', 'card'].map(location => `menu-${mode}-${location}`)),
    'permissions-context', 'permissions-list', 'missing-icon', 'strict-restoration', 'empty-short', 'both-empty', 'empty-full', 'escaping', 'custom-label', 'post', 'link', 'modal'];
function validateEvidence(report, selection = 'smoke', output = '/tmp/cv-action-tooltips.json') {
    const required = ['stock-smoke', 'custom-smoke', 'stock-repeat'];
    if (selection === 'all') for (const mode of ['stock', 'custom']) required.push(...matrix.map(name => `${mode}-${name}`));
    for (const id of required) {
        const item = report.cases.find(item => item.id === id);
        assert(item && item.passed && item.controls > 0, `Missing case: ${id}`);
        const expected = id.includes('-mixed-') || id.endsWith('-modal') || id.includes('-menu-') ? 3 : 1;
        assert.equal(item.controls, expected, `Incorrect control count: ${id}`);
    }
    assert.equal(report.failures.length, 0);
    assert(report.cleanup.stopped && report.cleanup.databaseRemoved, 'Owned cleanup incomplete');
    if (selection === 'all') {
        for (const mode of ['stock', 'custom']) {
            const modal = report.cases.find(item => item.id === `${mode}-modal`);
            for (const key of ['initial', 'replacement', 'reopened', 'disposed', 'hide']) assert(modal[key] > 0, `Zero modal ${key}`);
            for (const name of ['tooltip', 'menu', 'modal']) {
                const relative = `screenshots/${mode}-${name}.png`, item = report.screenshots?.find(item => item.path === relative);
                assert(item, `Missing screenshot ${relative}`);
                assert.equal(sha(fs.readFileSync(path.resolve(path.dirname(output), relative))), item.sha256, `Screenshot hash mismatch ${relative}`);
            }
        }
        for (const item of report.cases) if (item.strict) assert.equal(item.strict, item.id.endsWith('-missing-icon') ? 'False' : 'True', 'Strict scope leaked');
    }
}
async function cleanup(browser, server, report) {
    const fail = (stage, error) => {
        report.status = 'failed'; report.error ??= error.stack;
        (report.cleanupErrors ??= []).push({stage, error: error.stack});
    };
    try {if (browser) await browser.close();} catch (error) {fail('browser.close', error);}
    try {if (server) await stopOwned(server.child);} catch (error) {fail('server.stop', error);}
    if (server) {
        report.cleanup = {pid: server.child.pid, stopped: server.child.exitCode !== null || server.child.signalCode !== null,
            databaseRemoved: !fs.existsSync(server.ready.database)};
        report.serverLogs = server.logs();
    }
}
async function startServer(python) {
    const child = cp.spawn(python, ['tests/browser/action_tooltips_server.py'], {cwd: root,
        env: {...process.env, PYTHONPATH: `${root}/src:${root}`, PYTHONUNBUFFERED: '1'}, stdio: ['ignore', 'pipe', 'pipe']});
    let stdout = '', stderr = '', spawnError;
    // OS launch errors arrive asynchronously, outside spawn()'s try/catch.
    // Consume the event immediately and pass it through main's evidence writer.
    child.once('error', error => {spawnError = error;});
    child.stdout.on('data', data => {stdout += data;}); child.stderr.on('data', data => {stderr += data;});
    try {
        for (let i = 0; i < 300; i++) {
            if (spawnError) throw spawnError;
            assert(child.exitCode === null && child.signalCode === null, `Fixture startup failed: ${stderr}`);
            const line = stdout.split('\n').find(line => line.startsWith('{"ready":'));
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
function sourceHashes() {
    const files = cp.execFileSync('git', ['ls-files', 'src', 'tests/test1', 'docs/reference/buttons.md'], {cwd: root, encoding: 'utf8'}).trim().split('\n');
    files.push('tests/browser/action-tooltips.cjs', 'tests/browser/action_tooltips_server.py', 'tests/browser/action-tooltips.test.cjs', 'tests/browser/cancel-navigation.cjs');
    return Object.fromEntries(files.sort().map(file => [file, sha(fs.readFileSync(path.join(root, file)))]));
}
async function main(argv = process.argv.slice(2)) {
    const opts = options(argv), started = Date.now();
    const report = {status: 'running', command: [process.execPath, __filename, ...argv], captured: new Date().toISOString(),
        revision: cp.execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root, encoding: 'utf8'}).trim(), sourceHashes: sourceHashes(),
        runtime: {node: process.version}, cases: [], responses: [], failures: [], cleanup: {}, humanAcceptance: 'pending; no screen-reader testing'};
    let server, browser;
    try {
        const python = runtime('CV_CANCEL_PYTHON', [path.join(root, '.nox/tests-3-12-django-5-2/bin/python')], true);
        assert(fs.statSync(python).isFile(), 'CV_CANCEL_PYTHON must be an executable regular file');
        const playwright = runtime('CV_CANCEL_PLAYWRIGHT', cached(`${process.env.HOME}/.npm/_npx`, 'node_modules/playwright'));
        const chromium = runtime('CV_CANCEL_CHROMIUM', cached(`${process.env.HOME}/.cache/ms-playwright`, 'chrome-linux64/chrome'), true);
        const assets = loadAssets(process.env.CV_CANCEL_ASSETS_DIR);
        report.manifest = {path: path.resolve(process.env.CV_CANCEL_ASSETS_DIR, 'assets.json'), sha256: sha(fs.readFileSync(path.join(process.env.CV_CANCEL_ASSETS_DIR, 'assets.json')))};
        report.assets = [...assets].map(([url, {body, ...item}]) => ({url, ...item}));
        server = await startServer(python);
        Object.assign(report.runtime, server.ready.runtime, {playwright: require(path.join(playwright, 'package.json')).version,
            playwrightPath: playwright, chromiumPath: chromium, vitest: require(path.join(root, 'node_modules/vitest/package.json')).version,
            declaredVitest: require(path.join(root, 'package.json')).devDependencies.vitest});
        report.recipes = server.ready.recipes;
        assert.deepEqual(report.recipes, recipeHashes(), 'Exact documentation recipe bytes differ');
        assert(report.runtime.packagePath.startsWith(root + '/src/'));
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true, args: ['--disable-background-networking']});
        report.runtime.chromium = browser.version();
        report.fontEnvironment = {fontconfigPath: process.env.FONTCONFIG_PATH ?? null,
            fontconfigFile: process.env.FONTCONFIG_FILE ?? null,
            matches: Object.fromEntries(['system-ui', 'sans-serif', 'Arial'].map(family => {
                const result = cp.spawnSync('fc-match', ['-f', '%{family}\n%{file}\n', family], {encoding: 'utf8'});
                return [family, {status: result.status, output: result.stdout ?? '', error: result.error?.message ?? null}];
            }))};
        const base = `http://127.0.0.1:${server.ready.ready}`, pending = [];
        const ctx = await browser.newContext({serviceWorkers: 'block', viewport: {width: 1280, height: 900}});
        ctx.setDefaultTimeout(10000);
        await ctx.route('**/*', async route => {
            const url = route.request().url();
            if (new URL(url).origin === base) return route.continue();
            try {
                const asset = assetFor(assets, url);
                await route.fulfill({status: 200, body: asset.body, contentType: url.endsWith('.css') ? 'text/css' : url.endsWith('.js') ? 'text/javascript' : 'font/woff2', headers: {'access-control-allow-origin': '*'}});
            } catch (error) {report.failures.push(error.message); await route.abort();}
        });
        const observedAssets = new Set();
        ctx.on('response', response => {
            const url = response.url();
            if (!assets.has(url) && !url.includes('/static/')) return;
            // Hash each loaded asset once, before leaving its first document. Later
            // navigations may invalidate Chromium's response body handles.
            if (observedAssets.has(url)) return;
            observedAssets.add(url);
            pending.push((async () => {
                const relative = new URL(url).pathname.replace(/^\/static\//, '');
                const file = assets.get(url)?.file ?? path.join(root, 'src', relative.split('/')[0], 'static', relative);
                const body = await response.body(); assert.equal(sha(body), sha(fs.readFileSync(file)), `Loaded source mismatch ${url}`);
                report.responses.push({url, file, sha256: sha(body)});
            })().catch(error => report.failures.push(error.message)));
        });
        const auth = await ctx.request.get(base + '/__signin/'); assert.equal(auth.status(), 200);
        const ids = await auth.json(), page = await ctx.newPage();
        const cdp = await ctx.newCDPSession(page);
        await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
        page.on('pageerror', error => report.failures.push(error.stack));
        async function goto(target, mode, scenario = 'smoke') {
            await ctx.addCookies([{name: 'tooltip_mode', value: mode, url: base}, {name: 'tooltip_scenario', value: scenario, url: base}]);
            const response = await page.goto(base + target); assert.equal(response.status(), 200);
            assert.equal(response.headers()['x-tooltip-mode'], mode);
            assert.equal(response.headers()['x-tooltip-strict'], scenario === 'missing-icon' ? 'False' : 'True');
            await page.waitForFunction(() => bootstrap?.Tooltip.VERSION === '5.3.3' && typeof cv?.initTooltips === 'function' && !!cv?.adapters?.tooltip);
            await Promise.all(pending);
            return response;
        }
        async function tooltip(control, short, full, mode, response, selector = '[cv-key="update"][data-cv-tooltip="context"]', location = 'context') {
            identity(await control.getAttribute('data-tooltip-recipe'), mode);
            const raw = await page.evaluate(({html, selector}) => {
                const el = new DOMParser().parseFromString(html, 'text/html').querySelector(selector);
                return {title: el.getAttribute('title'), marker: el.getAttribute('data-cv-tooltip'), hidden: el.querySelector('.visually-hidden')?.textContent};
            }, {html: await response.text(), selector});
            assert.equal(raw.title, short); assert.equal(raw.marker, location); assert.equal(raw.hidden.trim(), full);
            assert.equal(await control.evaluate(el => !!bootstrap.Tooltip.getInstance(el)), true);
            await control.hover(); await page.locator('.tooltip.show .tooltip-inner').waitFor();
            assert.equal(await page.locator('.tooltip.show .tooltip-inner').textContent(), short);
            const accessible = full || short;
            assert.equal(await control.and(page.getByRole('link', {name: accessible, exact: true})).count(), 1, 'Full accessible name changed');
            await page.mouse.move(0, 0); await control.blur(); await page.locator('.tooltip.show').waitFor({state: 'hidden'});
            // Keep focus inside a live modal; clicking the page would dismiss its backdrop.
            await control.focus(); await page.keyboard.press('Shift+Tab');
            for (let i = 0; i < 100 && !await control.evaluate(el => el === document.activeElement); i++) await page.keyboard.press('Tab');
            assert(await control.evaluate(el => el === document.activeElement), 'Keyboard did not reach control');
            await page.locator('.tooltip.show .tooltip-inner').waitFor();
            assert.equal(await page.locator('.tooltip.show .tooltip-inner').textContent(), short);
            return raw;
        }
        for (const [id, mode] of [['stock-smoke', 'stock'], ['custom-smoke', 'custom'], ['stock-repeat', 'stock']]) {
            const record = {id, controls: 1, passed: false}; report.cases.push(record);
            const response = await goto(`/author/${ids.author}/detail/`, mode);
            record.raw = await tooltip(page.locator('[cv-key="update"][data-cv-tooltip="context"]'), 'Update', `Update author ${ids.name}`, mode, response);
            record.strict = response.headers()['x-tooltip-strict']; record.passed = true;
        }
        async function run(id, fn) {
            const record = {id, controls: 0, passed: false}; report.cases.push(record);
            await fn(record); assert(record.controls > 0); record.passed = true;
        }
        async function screenshot(mode, kind) {
            const relative = `screenshots/${mode}-${kind}.png`, file = path.resolve(path.dirname(opts.output), relative);
            if (kind !== 'menu') await page.waitForFunction(() => {
                const tip = document.querySelector('.tooltip.show');
                return tip && Number(getComputedStyle(tip).opacity) >= 0.89;
            });
            fs.mkdirSync(path.dirname(file), {recursive: true}); await page.screenshot({path: file});
            (report.screenshots ??= []).push({path: relative, sha256: sha(fs.readFileSync(file))});
            // Computed CSS alone cannot identify the font Chromium actually draws.
            // CDP reports the platform fonts and glyph counts for these exact nodes.
            const {root: documentNode} = await cdp.send('DOM.getDocument');
            const selectors = kind === 'menu' ? ['body', '.dropdown-item[cv-key="detail"]'] :
                kind === 'modal' ? ['body', '#cv-modal .modal-title', '#cv-modal label', '.tooltip.show .tooltip-inner'] :
                    ['body', '[cv-list-container] [cv-key="detail"] span', '.tooltip.show .tooltip-inner'];
            const samples = [];
            for (const selector of selectors) {
                const {nodeId} = await cdp.send('DOM.querySelector', {nodeId: documentNode.nodeId, selector});
                assert(nodeId, `Font diagnostic node missing: ${selector}`);
                const computed = await page.locator(selector).first().evaluate(el => {
                    const css = getComputedStyle(el);
                    return {text: el.textContent.trim().slice(0, 100), fontFamily: css.fontFamily,
                        fontSize: css.fontSize, fontWeight: css.fontWeight, lineHeight: css.lineHeight};
                });
                const {fonts} = await cdp.send('CSS.getPlatformFontsForNode', {nodeId});
                // body owns the declared font stack but has no directly rendered text.
                if (selector !== 'body') assert(fonts.length > 0, `No rendered font evidence: ${selector}`);
                samples.push({selector, computed, platformFonts: fonts});
            }
            (report.fontDiagnostics ??= []).push({mode, kind, samples});
        }
        async function rawControls(response, selector) {
            return page.evaluate(({html, selector}) => [...new DOMParser().parseFromString(html, 'text/html').querySelectorAll(selector)].map(el => ({
                key: el.getAttribute('cv-key'), title: el.getAttribute('title'), marker: el.getAttribute('data-cv-tooltip'),
                text: el.textContent.trim(), hidden: el.querySelector('.visually-hidden')?.textContent.trim(),
                recipe: el.getAttribute('data-tooltip-recipe')})), {html: await response.text(), selector});
        }
        async function suppressed(control, raw, mode, kind = 'action-leaf') {
            identity(raw.recipe, mode, kind); assert.equal(raw.title, null); assert.equal(raw.marker, null);
            assert.equal(await control.evaluate(el => bootstrap.Tooltip.getInstance(el)), null);
            assert(await control.isVisible()); await control.hover(); await control.focus();
            assert.equal(await page.locator('.tooltip.show').count(), 0);
        }
        const selectors = {context: '[cv-context-container]', list: '[cv-list-container]', card: '.card .d-flex.gap-2'};
        const urls = {context: `/author/${ids.author}/detail/`, list: '/author/', card: '/author/card/'};
        if (opts.case === 'all') for (const mode of ['stock', 'custom']) {
            for (const location of ['context', 'list']) await run(`${mode}-mixed-${location}`, async record => {
                const response = await goto(urls[location], mode, 'mixed'), scope = selectors[location];
                const raw = await rawControls(response, `${scope} [cv-key]`);
                assert.deepEqual(raw.map(item => item.key), ['detail', 'update', 'delete']);
                for (const key of ['detail', 'delete']) await suppressed(page.locator(`${scope} [cv-key="${key}"]`), raw.find(item => item.key === key), mode);
                record.raw = await tooltip(page.locator(`${scope} [cv-key="update"]`), 'Update', `Update author ${ids.name}`, mode, response, `${scope} [cv-key="update"]`, location);
                record.controls = raw.length; record.strict = response.headers()['x-tooltip-strict'];
                if (location === 'list') await screenshot(mode, 'tooltip');
            });
            for (const inline of ['icon', 'label', 'both']) for (const location of ['context', 'list', 'card']) await run(`${mode}-menu-${inline}-${location}`, async record => {
                const response = await goto(urls[location], mode, `menu-${inline}`), scope = page.locator(selectors[location]);
                const toggle = scope.locator('[data-bs-toggle="dropdown"]'); assert.equal(await toggle.count(), 1);
                assert.equal(await toggle.getAttribute('title'), null); assert.equal(await toggle.getAttribute('data-cv-tooltip'), null);
                await toggle.click();
                const items = scope.locator('.dropdown-item'), raw = await rawControls(response, `${selectors[location]} .dropdown-item`);
                assert.deepEqual(raw.map(item => item.key), ['detail', 'delete']);
                for (let i = 0; i < 2; i++) await suppressed(items.nth(i), raw[i], mode, 'menu-leaf');
                assert.deepEqual(raw.map(item => item.text), ['Detail', 'Delete']);
                if (location === 'context') assert.equal(await items.first().getAttribute('aria-current'), 'page');
                if (inline === 'icon' && location === 'context') await screenshot(mode, 'menu');
                record.controls = raw.length; record.keys = raw.map(item => item.key); record.labels = raw.map(item => item.text);
                await page.keyboard.press('Escape');
                await ctx.request.get(base + '/__signin/?limited=1');
                const deniedResponse = await goto(urls[location], mode, `menu-${inline}-denied`);
                const deniedScope = page.locator(selectors[location]), denied = deniedScope.locator('.dropdown-item');
                await deniedScope.locator('[data-bs-toggle="dropdown"]').click();
                assert.equal(await denied.count(), 1); assert(await denied.isDisabled());
                assert.equal(await denied.getAttribute('cv-key'), 'update');
                const deniedRaw = (await rawControls(deniedResponse, `${selectors[location]} .dropdown-item`))[0];
                identity(deniedRaw.recipe, mode, 'menu-leaf'); assert.equal(deniedRaw.title, null); assert.equal(deniedRaw.marker, null);
                assert.equal(await denied.evaluate(el => bootstrap.Tooltip.getInstance(el)), null);
                for (const attr of ['href', 'data-cv-action', 'data-cv-target', 'data-cv-modal']) assert.equal(await denied.getAttribute(attr), null);
                assert.equal(await deniedScope.locator('[cv-key="delete"]').count(), 0);
                record.disabledControls = 1; record.controls++; await ctx.request.get(base + '/__signin/');
            });
            await ctx.request.get(base + '/__signin/?limited=1');
            for (const location of ['context', 'list']) await run(`${mode}-permissions-${location}`, async record => {
                const response = await goto(urls[location], mode, 'permissions'), scope = page.locator(selectors[location]);
                const control = scope.locator('[cv-key="update"]'); assert.equal(await control.count(), 1);
                assert(await control.isDisabled()); assert.equal(await control.getAttribute('data-cv-disabled'), 'permission');
                for (const attr of ['href', 'data-cv-modal', 'data-cv-action', 'data-cv-target']) assert.equal(await control.getAttribute(attr), null);
                assert.equal(await scope.locator('[cv-key="delete"]').count(), 0);
                identity(await control.getAttribute('data-tooltip-recipe'), mode);
                record.raw = await rawControls(response, `${selectors[location]} [cv-key="update"]`);
                assert.equal(record.raw[0].title, 'Update'); record.controls = 1;
            });
            await ctx.request.get(base + '/__signin/');
            await run(`${mode}-missing-icon`, async record => {
                const response = await goto(urls.context, mode, 'missing-icon'), selector = '[cv-context-container] [cv-key="update"]';
                record.raw = (await rawControls(response, selector))[0];
                await suppressed(page.locator(selector), record.raw, mode); assert.equal(record.raw.text, 'Update');
                record.strict = response.headers()['x-tooltip-strict']; record.controls = 1;
            });
            await run(`${mode}-strict-restoration`, async record => {
                await goto(urls.context, mode);
                await ctx.addCookies([{name: 'tooltip_scenario', value: 'failed-render', url: base}]);
                const failed = await ctx.request.get(base + '/__failed/'); assert.equal(failed.status(), 500);
                const response = await goto(urls.context, mode); record.strict = response.headers()['x-tooltip-strict']; record.controls = 1;
            });
            for (const name of ['empty-short', 'both-empty', 'empty-full', 'escaping']) await run(`${mode}-${name}`, async record => {
                const response = await goto(urls.context, mode, name), selector = '[cv-context-container] [cv-key="update"]', control = page.locator(selector);
                const raw = (await rawControls(response, selector))[0];
                if (name === 'both-empty') {
                    await suppressed(control, raw, mode); assert.equal(raw.hidden, '');
                    assert.equal(await control.evaluate(el => bootstrap.Tooltip.getInstance(el)), null);
                    assert.equal(await control.getAttribute('aria-label'), null); assert.equal(raw.text, '');
                    assert.equal(await control.and(page.getByRole('link', {name: '', exact: true})).count(), 1);
                } else {
                    const short = name === 'empty-short' ? 'Full fallback' : name === 'empty-full' ? 'Short only' : ids.payload;
                    const full = name === 'empty-short' ? short : name === 'empty-full' ? '' : `Full ${ids.payload} end`;
                    await tooltip(control, short, full, mode, response, selector);
                    if (name === 'empty-full') assert.equal(await control.getAttribute('aria-label'), short);
                    assert.equal(await control.locator('img, script, [onerror]').count(), 0);
                }
                record.raw = raw; record.controls = 1;
            });
            await run(`${mode}-custom-label`, async record => {
                const response = await goto(urls.context, mode, 'custom-label'), selector = '[cv-context-container] [data-cv-tooltip="context"]';
                await tooltip(page.locator(selector), 'Custom caption', 'Custom caption', mode, response, selector);
                record.controls = 1;
            });
            await run(`${mode}-post`, async record => {
                await goto(urls.context, mode, 'post'); const control = page.locator('[cv-context-container] [cv-key="ping"]');
                identity(await control.getAttribute('data-tooltip-recipe'), mode);
                assert.equal(await control.getAttribute('data-cv-action'), 'submit-form');
                const [submitted] = await Promise.all([page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes('/ping/')), control.click()]);
                assert.equal(submitted.status(), 302);
                record.status = submitted.status(); record.controls = 1;
            });
            await run(`${mode}-link`, async record => {
                await goto(urls.context, mode); const control = page.locator('[cv-context-container] [cv-key="update"]');
                const [response] = await Promise.all([page.waitForNavigation(), control.click()]); assert.equal(response.status(), 200);
                assert(new URL(page.url()).pathname.endsWith('/update/')); record.controls = 1;
            });
            await run(`${mode}-modal`, async record => {
                await goto('/author_modal/', mode, 'modal');
                const trigger = page.locator(`[cv-list-container] [cv-key="contact"][data-cv-modal="true"]`);
                assert.equal(await trigger.count(), 1); assert.equal(new URL(await trigger.getAttribute('href'), base).pathname, `/author_modal/${ids.author}/contact/`);
                await page.evaluate(() => {
                    window.tooltipObservations = {dispose: [], hide: []};
                    for (const name of ['dispose', 'hide']) {
                        const original = cv.adapters.tooltip[name];
                        cv.adapters.tooltip[name] = function(el) {
                            const instance = bootstrap.Tooltip.getInstance(el);
                            tooltipObservations[name].push({node: el, live: !!instance, attached: el.isConnected, shown: !!instance?.tip?.classList.contains('show')});
                            return original.apply(this, arguments);
                        };
                    }
                });
                async function open() {
                    const [response] = await Promise.all([page.waitForResponse(r => r.url().includes('/contact/') && r.request().headers()['x-cv-modal'] === 'true'), trigger.click()]);
                    assert.equal(response.status(), 200);
                    await page.locator('#cv-modal.show form').waitFor(); return response;
                }
                const selector = '#cv-modal [cv-key="detail"][data-cv-tooltip="context"]';
                async function modalTooltip(response) {
                    const control = page.locator(selector); assert.equal(await control.count(), 1);
                    // Raw modal response has no outer #cv-modal wrapper.
                    await tooltip(control, 'Inspect', `Full modal author ${ids.name}`, mode, response, '[cv-key="detail"][data-cv-tooltip="context"]');
                    return control;
                }
                await modalTooltip(await open()); record.initial = 1; await screenshot(mode, 'modal');
                assert.equal(await page.locator('#app-owned').getAttribute('data-bs-original-title'), 'Application hint');
                assert.equal(await page.locator('#cv-modal form [type="submit"]').getAttribute('data-bs-original-title'), 'Application submit hint');
                assert.equal(await page.locator('#cv-modal form [type="submit"]').textContent().then(text => text.trim()), 'Send');
                await page.evaluate(() => {window.oldTooltipNode = document.querySelector('#cv-modal [cv-key="detail"]');});
                const [replaced] = await Promise.all([page.waitForResponse(r => r.request().method() === 'POST' && r.request().headers()['x-cv-modal'] === 'true'), page.locator('#cv-modal form [type="submit"]').click()]);
                assert.equal(replaced.status(), 422);
                await page.locator('#cv-modal .invalid-feedback').first().waitFor();
                assert(await page.evaluate(() => !oldTooltipNode.isConnected && !bootstrap.Tooltip.getInstance(oldTooltipNode) && oldTooltipNode !== document.querySelector('#cv-modal [cv-key="detail"]')));
                const control = await modalTooltip(replaced); record.replacement = 1;
                const [navigated] = await Promise.all([page.waitForResponse(r => r.url().includes('/detail/') && r.request().headers()['x-cv-modal'] === 'true'), control.click()]);
                assert.equal(navigated.status(), 200);
                await page.locator('#cv-modal form').waitFor({state: 'detached'}); await page.locator('.tooltip.show').waitFor({state: 'hidden'});
                record.disposed = await page.evaluate(() => tooltipObservations.dispose.filter(item => item.live && item.attached).length);
                record.hide = await page.evaluate(() => tooltipObservations.hide.filter(item => item.live && item.shown).length);
                assert(record.disposed > 0 && record.hide > 0);
                await page.locator('#cv-modal [data-cv-modal-dismiss]').click(); await page.locator('#cv-modal.show').waitFor({state: 'hidden'});
                await modalTooltip(await open()); record.reopened = 1; record.controls = 3;
            });
        }
        await Promise.all(pending);
        for (const asset of report.assets.filter(item => item.integrity)) assert(report.responses.some(item => item.url === asset.url), `Declared asset not loaded ${asset.url}`);
        assert(report.responses.some(item => item.url.endsWith('fa-solid-900.woff2')), 'Icon font not loaded');
        for (const name of ['tooltip.js', 'adapters.js', 'modal.js', 'viewset.js']) assert(report.responses.some(item => item.file.endsWith('/' + name)), `Required script missing ${name}`);
        assert.deepEqual(report.failures, []);
        report.status = 'passed';
    } catch (error) {
        report.status = 'failed'; report.error = error.stack;
        if (error.fixtureCleanup) report.cleanup = error.fixtureCleanup;
    }
    finally {
        await cleanup(browser, server, report);
        if (report.status === 'passed') {
            try {validateEvidence(report, opts.case, opts.output);} catch (error) {report.status = 'failed'; report.error = error.stack;}
        }
        report.durationSeconds = (Date.now() - started) / 1000;
        fs.writeFileSync(path.resolve(opts.output), JSON.stringify(report, null, 2) + '\n');
        console.log(JSON.stringify({status: report.status, cases: report.cases.length, output: opts.output, error: report.error}));
        if (report.status !== 'passed') process.exitCode = 1;
    }
}
module.exports = {options, identity, validateEvidence, cleanup, main, matrix};
if (require.main === module) main().catch(error => {console.error(error.stack); process.exitCode = 1;});
