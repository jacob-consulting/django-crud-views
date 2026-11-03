// Real HTTP acceptance for signed cancellation. Never fetch or install browser assets.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const compare = (left, right) => left.localeCompare(right, 'en');
function sequence(values, operation) {
    return [...values].reduce((previous, value) => previous.then(() => operation(value)), Promise.resolve());
}
function options(argv) {
    const result = {case: 'all'};
    for (let i = 0; i < argv.length; i += 2) {
        assert(['--case', '--output'].includes(argv[i]), `Unknown option: ${argv[i]}`);
        assert(argv[i + 1] && !argv[i + 1].startsWith('--'), `Missing ${argv[i]}`);
        result[argv[i].slice(2)] = argv[i + 1];
    }
    assert(['all', 'smoke'].includes(result.case), 'Use --case all|smoke');
    result.output ??= path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'cv-cancel-browser-')), 'report.json');
    return result;
}
function declarations() {
    const html = fs.readFileSync(path.join(root, 'tests/test1/app/templates/app/base.html'), 'utf8');
    return [...html.matchAll(/<(?:link|script)\b[^>]*?(?:href|src)="(https:[^"]+)"[^>]*>/gs)].map(([tag, url]) => ({
        url, integrity: tag.match(/integrity="([^"]+)"/)?.[1] ?? null, css: url.endsWith('.css'),
    }));
}
function readAsset(dir, manifest, spec) {
    const entry = manifest.assets[spec.url];
    assert(entry, `Missing declared asset: ${spec.url}`);
    assert(typeof entry.file === 'string' && !path.isAbsolute(entry.file), 'Asset containment: relative file required');
    let filename = path.resolve(dir, entry.file);
    assert(filename.startsWith(dir + path.sep), `Asset containment: ${entry.file}`);
    filename = fs.realpathSync(filename);
    assert(filename.startsWith(dir + path.sep), `Asset containment: ${entry.file}`);
    const body = fs.readFileSync(filename);
    assert.equal(sha(body), entry.sha256, `SHA-256 mismatch: ${spec.url}`);
    if (spec.integrity) {
        assert(spec.integrity.split(/\s+/).some(sri => {
            const [algorithm, digest] = sri.split('-');
            return ['sha256', 'sha384', 'sha512'].includes(algorithm) &&
                crypto.createHash(algorithm).update(body).digest('base64') === digest;
        }), `SRI mismatch: ${spec.url}`);
    }
    return {body, file: filename, sha256: sha(body), integrity: spec.integrity ?? null};
}
function cssDependencies(body, base) {
    return [...body.toString().matchAll(/url\(\s*['"]?([^'"\s)]+)['"]?\s*\)/g)]
        .map(match => match[1]).filter(url => !url.startsWith('data:') && !url.startsWith('#'))
        .map(value => {const url = new URL(value, base).href; return {url, css: url.endsWith('.css')};});
}
function loadAssets(directory, declared = declarations()) {
    assert(directory, 'CV_CANCEL_ASSETS_DIR must name a local directory containing assets.json');
    const dir = fs.realpathSync(directory);
    const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'assets.json'), 'utf8'));
    assert.equal(manifest.version, 1, 'Unsupported assets.json version');
    assert(manifest.assets && typeof manifest.assets === 'object', 'Invalid assets.json mapping');
    const pending = [...declared], result = new Map();
    for (const spec of pending) {
        if (result.has(spec.url)) continue;
        const asset = readAsset(dir, manifest, spec);
        result.set(spec.url, asset);
        if (spec.css) pending.push(...cssDependencies(asset.body, spec.url));
    }
    for (const url of Object.keys(manifest.assets)) assert(result.has(url), `Undeclared manifest URL: ${url}`);
    return result;
}
function assetFor(assets, url) {
    assert(assets.has(url), `Undeclared external request: ${url}`);
    return assets.get(url);
}
function cached(directory, suffix) {
    return fs.existsSync(directory) ? fs.readdirSync(directory).sort(compare).reverse().map(name => path.join(directory, name, suffix)) : [];
}
function runtime(variable, candidates, executable = false) {
    const filename = process.env[variable] ?? candidates.find(file => fs.existsSync(file));
    assert(filename && fs.existsSync(filename), `Missing ${variable}: ${filename ?? 'no cached runtime'}`);
    if (executable) fs.accessSync(filename, fs.constants.X_OK);
    return path.resolve(filename); // Preserve Python venv symlink identity.
}
async function stopOwned(child) {
    if (child?.exitCode !== null || child.signalCode !== null) return;
    const exited = new Promise(resolve => child.once('exit', resolve));
    child.kill('SIGTERM');
    await Promise.race([exited, delay(1500)]);
    if (child.exitCode === null && child.signalCode === null) {child.kill('SIGKILL'); await exited;}
}
function validateExecutable(filename) {
    assert(path.isAbsolute(filename), 'Executable must be an absolute path');
    const resolved = fs.realpathSync(filename), stat = fs.statSync(resolved);
    assert(stat.isFile(), 'Executable must be a regular file');
    assert.equal(stat.mode & 0o022, 0, 'Executable must not be group or world writable');
    fs.accessSync(resolved, fs.constants.X_OK);
    return resolved;
}
function gitExecutable() {
    return validateExecutable(runtime('CV_CANCEL_GIT', ['/usr/bin/git', '/bin/git'], true));
}
function sourceHashes() {
    const files = cp.execFileSync(gitExecutable(), ['ls-files', 'src', 'tests/test1', 'tests/browser/cancel*'], {cwd: root, encoding: 'utf8'})
        .trim().split('\n');
    files.push('tests/browser/cancel_navigation_server.py', 'tests/browser/cancel_fixture_http.py');
    return Object.fromEntries([...new Set(files)].sort(compare).map(file => [file, sha(fs.readFileSync(path.join(root, file)))]));
}
function waitForReady(child, logs, timeout = 30000) {
    return new Promise((resolve, reject) => {
        const finish = (error, ready) => {
            clearTimeout(timer);
            child.stdout.off('data', inspect);
            child.off('exit', exited);
            child.off('error', failed);
            if (error) reject(error); else resolve(ready);
        };
        const inspect = () => {
            const line = logs().stdout.split('\n').slice(0, -1).find(value => value.startsWith('{"ready":'));
            if (!line) return;
            try {finish(null, JSON.parse(line));} catch (error) {finish(error);}
        };
        const exited = () => finish(new Error(`Fixture startup failed: ${logs().stderr}`));
        const failed = error => finish(error);
        const timer = setTimeout(() => finish(new Error(`Fixture startup timed out: ${logs().stderr}`)), timeout);
        child.stdout.on('data', inspect);
        child.once('exit', exited);
        child.once('error', failed);
        if (child.exitCode !== null || child.signalCode !== null) exited(); else inspect();
    });
}
async function startServer(python) {
    const child = cp.spawn(python, ['tests/browser/cancel_navigation_server.py'], {
        cwd: root, env: {...process.env, PYTHONPATH: `${root}/src:${root}`, PYTHONUNBUFFERED: '1'},
        stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '', stderr = '';
    child.stdout.on('data', bytes => {stdout += bytes;});
    child.stderr.on('data', bytes => {stderr += bytes;});
    const logs = () => ({stdout, stderr});
    try {
        const ready = await waitForReady(child, logs);
        return {child, ready, logs};
    } catch (error) {await stopOwned(child); throw error;}
}
function normalized(url) {
    const parsed = new URL(url);
    parsed.searchParams.delete('cv_from_restore');
    return {path: parsed.pathname, query: [...parsed.searchParams]};
}
function assetContentType(url) {
    const types = {'.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2'};
    return types[path.extname(new URL(url).pathname)] ?? 'font/ttf';
}
function modalCases() {
    return ['delete', 'contact'].flatMap(key => ['', 'x=&x=%3Cscript%3E%26%22'].map(query => ({key, query})));
}
function isModalPost(response) {
    return response.request().method() === 'POST' && response.request().headers()['x-cv-modal'] === 'true';
}
async function browserScenarios(browser, assets, report, base, opts) {
        const pending = [], contexts = [];
        async function context(tag = 'button', limited = false) {
            const ctx = await browser.newContext({serviceWorkers: 'block'});
            contexts.push(ctx);
            ctx.setDefaultTimeout(10000);
            await ctx.addCookies([{name: 'cancel_tag', value: tag, url: base}]);
            await ctx.route('**/*', async route => {
                const url = route.request().url();
                if (new URL(url).origin === base) return route.continue();
                try {
                    const asset = assetFor(assets, url);
                    const contentType = assetContentType(url);
                    await route.fulfill({status: 200, body: asset.body, contentType,
                        headers: {'access-control-allow-origin': '*'}});
                } catch (error) {report.failures.push(error.message); await route.abort('blockedbyclient');}
            });
            ctx.on('response', response => {
                const url = response.url();
                if (!assets.has(url) && !url.includes('/static/')) return;
                pending.push((async () => {
                    const body = await response.body();
                    const relative = new URL(url).pathname.replace(/^\/static\//, '');
                    const file = assets.get(url)?.file ?? path.join(root, 'src', relative.split('/')[0], 'static', relative);
                    const expected = fs.readFileSync(file);
                    assert.equal(response.status(), 200, url);
                    assert.equal(sha(body), sha(expected), `Loaded bytes differ from source: ${url}`);
                    report.responses.push({url, status: response.status(), file, sha256: sha(body)});
                })().catch(error => report.failures.push(error.message)));
            });
            ctx.on('page', page => {
                page.on('pageerror', error => report.failures.push(error.message));
                page.on('requestfailed', req => report.failures.push(`${req.url()}: ${req.failure()?.errorText}`));
            });
            const auth = await ctx.request.get(base + '/__signin/?limited=' + Number(limited));
            assert.equal(auth.status(), 200, await auth.text());
            const ids = await auth.json();
            return {ctx, ids, page: await ctx.newPage()};
        }
        async function state(ctx) {const response = await ctx.request.get(base + '/__snapshot/'); assert.equal(response.status(), 200); return response.json();}
        async function goto(page, target) {
            const response = await page.goto(new URL(target, base).href);
            assert.equal(response.status(), 200, `Page failed: ${target}`);
            await page.waitForFunction(() => globalThis.bootstrap?.Modal.VERSION === '5.3.3' && globalThis.jQuery?.fn.jquery === '3.7.1' &&
                typeof cvGetConfig === 'function' && typeof cvModalOpen === 'function' && !!globalThis.cv?.adapters?.modal);
            return response;
        }
        async function openAction(page, pathname, modal = false) {
            const link = page.locator(`a[href^="${pathname}"]`).first();
            const href = await link.getAttribute('href');
            assert(new URL(href, base).searchParams.has('cv_from_cancel'), `Real action lacks capture: ${href}`);
            // Row menus use real Bootstrap dropdowns. Opening them is part of the interaction.
            if (!await link.isVisible()) await link.locator('xpath=ancestor::*[contains(@class,"dropdown")][1]').locator('[data-bs-toggle="dropdown"]').click();
            if (modal) {
                const waiting = page.waitForResponse(r => r.url() === new URL(href, base).href && r.request().headers()['x-cv-modal'] === 'true');
                await link.click(); const response = await waiting; assert.equal(response.status(), 200);
                await page.locator('#cv-modal.show form').waitFor(); return response;
            }
            const waiting = page.waitForNavigation(); await link.click(); const response = await waiting;
            assert.equal(response.status(), 200); return response;
        }
        async function owner(page, response, tag, modal = false) {
            const scope = modal ? page.locator('#cv-modal') : page;
            assert.equal(await scope.locator('form.cv-form').count(), 1);
            assert.equal(await scope.locator('form.cv-form form').count(), 0);
            assert.equal(await scope.locator('form.cv-form [name="csrfmiddlewaretoken"]').count(), 1);
            const cancel = scope.getByRole(tag === 'a' ? 'link' : 'button', {name: 'Cancel', exact: true});
            assert.equal(await cancel.count(), 1);
            const url = await cancel.getAttribute(tag === 'a' ? 'href' : 'data-cv-cancel-url');
            const copied = response.headers()['x-cancel-copy'];
            assert(copied, 'Guarded copied-template evidence absent');
            const copiedURL = await page.evaluate(html => new DOMParser().parseFromString(html, 'text/html').querySelector('a')?.getAttribute('href'), copied);
            assert.equal(copiedURL, url, 'Copied helper parity');
            assert(!copied.includes('<script>'), 'Unescaped copied template');
            return cancel;
        }
        async function cancel(page, ctx, control, expected, record, icon = false) {
            const before = await state(ctx), events = [];
            const listener = request => events.push({method: request.method(), url: request.url()});
            page.on('request', listener);
            const destination = await control.getAttribute('href') ?? await control.getAttribute('data-cv-cancel-url');
            assert.deepEqual(normalized(new URL(destination, base)), normalized(new URL(expected, base)));
            const waiting = page.waitForNavigation();
            await (icon ? control.locator('i, svg, span').first() : control).click();
            assert.equal((await waiting).status(), 200);
            page.off('request', listener);
            assert.deepEqual(normalized(page.url()), normalized(new URL(expected, base)));
            const after = await state(ctx);
            assert.deepEqual(after.rows, before.rows, 'Cancel mutated model rows');
            assert(events.every(req => req.method === 'GET'), 'Cancel sent non-GET');
            const audit = after.requests.slice(before.requests.length);
            assert(audit.length > 0 && audit.every(req => req.method === 'GET' && req.writes.length === 0), 'Cancel wrote app tables');
            record.cancels.push({destination, final: page.url(), events, audit, rowsSha256: sha(JSON.stringify(after.rows))});
        }
        async function run(id, fn) {
            const record = {id, cancels: [], passed: false}; report.cases.push(record);
            await fn(record); record.passed = true;
        }
        const initial = await context();
        report.initialization = {bootstrap: '5.3.3', jquery: '3.7.1', cancel: 'cvGetConfig plus delegated clicks', modal: 'cvModalOpen plus real modal replacement'};
        await sequence(opts.case === 'smoke' ? ['button'] : ['button', 'a'], async tag => {
            const {ctx, ids, page} = tag === 'button' ? initial : await context(tag);
            const flows = opts.case === 'smoke' ? [['list', 'update']] : [['list', 'update'], ['detail', 'update'], ['list', 'create'], ['list', 'delete'], ['detail', 'delete']];
            await sequence(flows, ([origin, key]) => run(`${tag}-${origin}-${key}`, async record => {
                const source = origin === 'list' ? '/publisher/?name=Alpha&x=&x=two&sort=name&page=1' : `/publisher/${ids.publisher}/detail/?x=&x=detail`;
                await goto(page, source);
                const target = key === 'create' ? '/publisher/create/' : `/publisher/${ids.publisher}/${key}/`;
                const response = await openAction(page, target);
                const control = await owner(page, response, tag);
                const form = page.locator('form.cv-form');
                await form.evaluate(form => {form.noValidate = false; const input = form.querySelector('input:not([type="hidden"])');
                    input.required = true; if (input.type === 'checkbox') input.checked = false; else input.value = '';});
                assert.equal(await form.evaluate(form => form.checkValidity()), false, 'Fixture must have browser-invalid fields');
                await cancel(page, ctx, control, source, record, tag === 'button');
                // Repeated Cancel destination GETs cannot turn into mutations.
                const before = await state(ctx);
                await sequence([1, 2], async () => {
                    assert.equal((await ctx.request.get(new URL(record.cancels[0].destination, base).href)).status(), 200);
                });
                const after = await state(ctx); assert.deepEqual(after.rows, before.rows);
                assert(after.requests.slice(before.requests.length).every(req => !req.writes.length));
            }));
            if (opts.case === 'smoke') return;
            await sequence(['x=&x=A&name=Alpha', ''], query => run(`${tag}-independent-tabs-${query ? 'filtered' : 'empty'}`, async record => {
                const second = await ctx.newPage();
                try {
                    // Explicit empty capture starts from a fresh session, then tab B remembers filters.
                    if (!query) await ctx.request.get(base + '/publisher/?cv_from_restore=1');
                    const source = '/publisher/' + (query ? '?' + query : '');
                    await goto(page, source); const response = await openAction(page, `/publisher/${ids.publisher}/update/`);
                    const control = await owner(page, response, tag);
                    await goto(second, '/publisher/?name=Beta&x=B');
                    const secondResponse = await openAction(second, `/publisher/2/update/`);
                    const secondControl = await owner(second, secondResponse, tag);
                    await cancel(page, ctx, control, source, record);
                    await goto(page, '/publisher/');
                    assert.deepEqual(normalized(page.url()), normalized(new URL(source, base)), 'Bare list must remember restored state');
                    await cancel(second, ctx, secondControl, '/publisher/?name=Beta&x=B', record);
                } finally {await second.close();}
            }));
            await run(`${tag}-nested-parent-captures`, async record => {
                const second = await ctx.newPage();
                try {
                    await goto(page, ids.book_list + '?x=&x=parentA');
                    const response = await openAction(page, ids.book_update), control = await owner(page, response, tag);
                    await goto(second, ids.other_book_list + '?x=parentB');
                    const responseB = await openAction(second, ids.other_book_update), controlB = await owner(second, responseB, tag);
                    await cancel(page, ctx, control, ids.book_list + '?x=&x=parentA', record);
                    await cancel(second, ctx, controlB, ids.other_book_list + '?x=parentB', record);
                } finally {await second.close();}
            });
            await sequence(modalCases(), ({key, query}) =>
                run(`${tag}-modal-${key}-${query ? 'filtered' : 'empty'}`, async record => {
                    await ctx.request.get(base + '/author_modal/?cv_from_restore=1');
                    const source = '/author_modal/' + (query ? '?' + query : '');
                    await goto(page, source);
                    let response = await openAction(page, `/author_modal/${ids.author}/${key}/`, true);
                    await owner(page, response, tag, true);
                    await sequence([1, 2], async () => {
                        const waiting = page.waitForResponse(isModalPost);
                        await page.locator('#cv-modal form [type="submit"]').click(); response = await waiting;
                        assert.equal(response.status(), 422);
                        await page.locator('#cv-modal form .invalid-feedback').first().waitFor();
                        await owner(page, response, tag, true);
                    });
                    const control = await owner(page, response, tag, true);
                    await cancel(page, ctx, control, source, record, tag === 'button');
                })
            );
            await run(`${tag}-protected-delete-no-form`, async record => {
                await goto(page, `/author_origin/${ids.protected}/delete/?cv_from=list`);
                assert.equal(await page.locator('form.cv-form').count(), 0);
                assert.equal(await page.getByRole('button', {name: 'Cancel', exact: true}).count(), 0);
                assert.equal(await page.getByRole('link', {name: 'Cancel', exact: true}).count(), 0);
                record.protection = await page.getByText('This author is protected.').count(); assert(record.protection);
            });
            await run(`${tag}-hidden-cancel-authorized-submit`, async record => {
                const limited = await context(tag, true);
                try {
                    const response = await goto(limited.page, `/publisher/${ids.publisher}/update/`);
                    assert.equal(response.headers()['x-cancel-copy'], '');
                    assert.equal(await limited.page.getByRole('button', {name: 'Cancel', exact: true}).count(), 0);
                    assert.equal(await limited.page.getByRole('link', {name: 'Cancel', exact: true}).count(), 0);
                    assert.equal(await limited.page.locator('form.cv-form [name="csrfmiddlewaretoken"]').count(), 1);
                    await limited.page.locator('[name="name"]').fill('Authorized ' + tag);
                    const waiting = limited.page.waitForResponse(r => r.request().method() === 'POST');
                    const savedNavigation = limited.page.waitForNavigation();
                    await limited.page.locator('form.cv-form [type="submit"]').click();
                    const saved = await waiting; assert.equal(saved.status(), 302);
                    await savedNavigation;
                    const after = await state(limited.ctx);
                    assert.equal(after.rows.Publisher.find(row => row.id === ids.publisher).name, 'Authorized ' + tag);
                    record.submit = {status: saved.status(), location: saved.headers().location};
                    // Restore fixture using another authorized real POST so subsequent cases stay deterministic.
                    await goto(limited.page, `/publisher/${ids.publisher}/update/`);
                    await limited.page.locator('[name="name"]').fill('Alpha');
                    const restored = limited.page.waitForResponse(r => r.request().method() === 'POST');
                    const restoredNavigation = limited.page.waitForNavigation();
                    await limited.page.locator('form.cv-form [type="submit"]').click(); assert.equal((await restored).status(), 302);
                    await restoredNavigation;
                } finally {await limited.ctx.close();}
            });
        });
        await Promise.all(pending);
        for (const spec of declarations()) assert(report.responses.some(r => r.url === spec.url), `Required asset never loaded: ${spec.url}`);
        for (const name of ['viewset.js', 'modal.js', 'adapters.js']) assert(report.responses.some(r => r.file.endsWith('/' + name)), `Required package script never loaded: ${name}`);
        assert(report.responses.some(r => r.url.endsWith('fa-solid-900.woff2')), 'Real icon font never loaded');
        assert.deepEqual(report.failures, []);
        report.finalAudit = await state(initial.ctx);
        await sequence(contexts, ctx => ctx.close());
}
async function main() {
    const opts = options(process.argv.slice(2));
    // Validate explicit executables first, even if the asset prerequisite is absent.
    const python = runtime('CV_CANCEL_PYTHON', [path.join(root, '.nox/tests-3-12-django-5-2/bin/python')], true);
    const playwright = runtime('CV_CANCEL_PLAYWRIGHT', cached(`${process.env.HOME}/.npm/_npx`, 'node_modules/playwright'));
    const chromium = runtime('CV_CANCEL_CHROMIUM', cached(`${process.env.HOME}/.cache/ms-playwright`, 'chrome-linux64/chrome'), true);
    const assets = loadAssets(process.env.CV_CANCEL_ASSETS_DIR);
    const started = Date.now();
    const report = {status: 'running', captured: new Date().toISOString(), command: [process.execPath, __filename, ...process.argv.slice(2)],
        revision: cp.execFileSync(gitExecutable(), ['rev-parse', 'HEAD'], {cwd: root, encoding: 'utf8'}).trim(), sourceHashes: sourceHashes(),
        runtime: {node: process.version, nodePath: process.execPath, playwrightPath: playwright,
            playwright: require(path.join(playwright, 'package.json')).version, chromiumPath: chromium},
        manifest: {path: path.resolve(process.env.CV_CANCEL_ASSETS_DIR, 'assets.json'),
            sha256: sha(fs.readFileSync(path.join(process.env.CV_CANCEL_ASSETS_DIR, 'assets.json')))},
        declaredAssets: [...assets].map(([url, {body, ...entry}]) => ({url, ...entry})),
        responses: [], cases: [], failures: [], cleanup: {}, humanAcceptance: 'pending; no screen-reader or visual certification'};
    let server, browser;
    try {
        server = await startServer(python);
        const base = `http://127.0.0.1:${server.ready.ready}`;
        Object.assign(report.runtime, server.ready.runtime);
        assert(report.runtime.packagePath.startsWith(root + '/src/'));
        assert.match(report.runtime.django, /^(4\.2|5\.2|6\.0)\./);
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true, args: ['--disable-background-networking']});
        report.runtime.chromium = browser.version();
        await browserScenarios(browser, assets, report, base, opts);
        report.status = 'passed';
    } catch (error) {report.status = 'failed'; report.error = error.stack; process.exitCode = 1;}
    finally {
        function cleanupError(stage, error) {
            report.cleanupErrors ??= [];
            report.cleanupErrors.push({stage, error: error.stack});
            report.status = 'failed';
            report.error ??= error.stack;
            process.exitCode = 1;
        }
        // Cleanup stages are independent: a rejected browser close must not retain
        // the owned fixture/database or prevent recording the original failure.
        try {if (browser) await browser.close();}
        catch (error) {cleanupError('browser.close', error);}
        if (server) {
            try {await stopOwned(server.child);}
            catch (error) {cleanupError('server.stop', error);}
            try {
                report.cleanup = {pid: server.child.pid, exitCode: server.child.exitCode, signal: server.child.signalCode,
                    stopped: server.child.exitCode !== null || server.child.signalCode !== null, databaseRemoved: !fs.existsSync(server.ready.database)};
                report.serverLogs = server.logs();
            } catch (error) {cleanupError('server.report', error);}
        }
        report.durationSeconds = (Date.now() - started) / 1000;
        try {fs.writeFileSync(path.resolve(opts.output), JSON.stringify(report, null, 2) + '\n');}
        catch (error) {cleanupError('report.write', error);}
        console.log(JSON.stringify({status: report.status, cases: report.cases.length, output: path.resolve(opts.output),
            error: report.error, cleanupErrors: report.cleanupErrors}));
    }
}
module.exports = {loadAssets, assetFor, options, stopOwned, runtime, sequence, validateExecutable, waitForReady};
if (require.main === module) main().catch(error => {console.error(error.stack); process.exitCode = 1;});
