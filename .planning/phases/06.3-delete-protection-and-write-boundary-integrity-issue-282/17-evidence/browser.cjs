// Uses the already-cached Playwright module and Chromium. No package installation.
const {chromium} = require('/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('fs');
const assert = require('assert/strict');
const path = require('path');
const base = 'http://127.0.0.1:8143';
const out = path.resolve('.planning/ui-reviews/06.3-gap-review');
const durable = path.resolve('.planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/17-evidence');
fs.mkdirSync(out, {recursive: true});

(async () => {
    const browser = await chromium.launch({headless: true,
        executablePath: '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
        args: ['--no-sandbox']});
    const errors = [], results = [], keyboard = [];
    const ctx = await browser.newContext({ignoreHTTPSErrors: true});
    const page = await ctx.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base + '/signin/');
    const cases = await (await ctx.request.get(base + '/cases/')).json();
    const viewports = [{width: 1440, height: 900}, {width: 768, height: 1024}, {width: 375, height: 812}];
    async function focus(label) {
        keyboard.push({label, ...await page.evaluate(() => {
            const e = document.activeElement, s = getComputedStyle(e);
            return {tag: e.tagName, id: e.id, text: e.innerText?.slice(0, 90),
                modal: !!e.closest('#cv-modal'), focusVisible: e.matches(':focus-visible'),
                outline: s.outline, boxShadow: s.boxShadow};
        })});
    }
    async function open(c) {
        await page.goto(base + '/harness/?target=' + encodeURIComponent(c.url));
        await page.waitForFunction(() => typeof bootstrap === 'object' && typeof cv.cvModalOpen === 'function');
        await page.locator('#launch').focus();
        await page.keyboard.press('Enter');
        await page.locator('#cv-modal').waitFor({state: 'visible'});
        await page.waitForTimeout(400);
    }
    for (const c of cases.filter(c => ['partial', 'blocked'].includes(c.mode))) {
        await ctx.addCookies([{name: 'review_language', value: c.language, url: base}]);
        for (const viewport of viewports) {
            await page.setViewportSize(viewport);
            for (const mode of ['page', 'modal']) {
                if (mode === 'page') {
                    assert.equal((await page.goto(base + c.url)).status(), 200);
                } else await open(c);
                const root = page.locator(mode === 'modal' ? '#cv-modal' : 'main');
                const text = await root.innerText();
                const warning = c.language === 'de' ? 'Diese Vorschau ist unvollständig.' : 'This preview is incomplete.';
                assert(text.includes(warning));
                assert(text.includes('München 東京 <escaped>'));
                assert(text.includes('Nested 0 — 雪'));
                assert(!text.includes('HIDDEN-CONTRACT'));
                assert.equal(await root.locator('form.cv-form').count(), c.mode === 'blocked' ? 0 : 1);
                const filename = `${c.language}-${c.mode}-${mode}-${viewport.width}x${viewport.height}.png`;
                await page.screenshot({path: path.join(out, filename), fullPage: true});
                results.push({case: c, viewport, mode, filename, ...await root.evaluate(e => ({
                    scrollWidth: e.scrollWidth, clientWidth: e.clientWidth, text: e.innerText,
                    alerts: [...e.querySelectorAll('[role="alert"]')].map(a => a.innerText),
                    controls: [...e.querySelectorAll('input,button,a')].map(a => ({tag: a.tagName, text: a.innerText, name: a.name}))
                }))});
                if (mode === 'modal') {
                    await root.locator('[data-cv-modal-dismiss]').first().click();
                    await root.waitFor({state: 'hidden'});
                }
            }
        }
    }
    await ctx.addCookies([{name: 'review_language', value: 'en', url: base}]);
    await page.setViewportSize(viewports[0]);
    const c = cases.find(c => c.mode === 'stale' && c.language === 'en');
    await open(c);
    const modal = page.locator('#cv-modal');
    await focus('keyboard Enter opens modal');
    for (let i = 0; i < 6; i++) { await page.keyboard.press('Tab'); await focus(`initial Tab ${i + 1}`); }
    const form = modal.locator('form.cv-form');
    const initialAttributes = await form.evaluate(e => ({noValidate: e.noValidate, html: e.outerHTML}));
    // The real rendered form already has noValidate=true (recorded below). This idempotent assignment
    // retains that behavior while observing the server's unchecked-confirmation 422 via keyboard Enter.
    await form.evaluate(e => { e.noValidate = true; });
    await modal.locator('[type="submit"]').focus();
    const invalid = page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes(c.url));
    await page.keyboard.press('Enter');
    assert.equal((await invalid).status(), 422);
    await page.waitForTimeout(400);
    await focus('after unchecked 422 replacement');
    assert.equal(await modal.locator('input[name="confirm"]').count(), 1);
    await page.screenshot({path: path.join(out, 'keyboard-after-unchecked-422.png')});
    for (let i = 0; i < 6; i++) { await page.keyboard.press('Tab'); await focus(`after 422 Tab ${i + 1}`); }
    await modal.locator('input[name="confirm"]').focus();
    await page.keyboard.press('Space');
    assert(await modal.locator('input[name="confirm"]').isChecked());
    await focus('checkbox toggled using Space');
    await page.screenshot({path: path.join(out, 'keyboard-confirm-focused.png')});
    assert.equal((await ctx.request.post(base + '/protect/' + c.pk + '/')).status(), 200);
    await modal.locator('[type="submit"]').focus();
    const blocked = page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes(c.url));
    await page.keyboard.press('Enter');
    assert.equal((await blocked).status(), 422);
    await modal.locator('form.cv-form').waitFor({state: 'detached'});
    await focus('after blocked 422 replacement');
    assert((await modal.innerText()).includes('This preview is incomplete.'));
    assert((await modal.innerText()).includes('Deletion is blocked by protected relationships'));
    await page.screenshot({path: path.join(out, 'keyboard-after-blocked-422.png')});
    await page.keyboard.press('Tab'); await focus('first Tab after blocked replacement');
    await modal.locator('[data-cv-modal-dismiss]').first().focus();
    await page.keyboard.press('Enter');
    await modal.waitFor({state: 'hidden'});
    await focus('Close via keyboard');
    const partial = cases.find(c => c.mode === 'partial' && c.language === 'en');
    await open(partial);
    const cancel = modal.locator('[data-cv-cancel-url]');
    const cancelUrl = await cancel.getAttribute('data-cv-cancel-url');
    await cancel.focus(); await page.keyboard.press('Enter');
    await page.waitForURL(base + cancelUrl);
    keyboard.push({label: 'Cancel via keyboard', url: page.url()});
    const success = cases.find(c => c.mode === 'success' && c.language === 'en');
    await open(success);
    await modal.locator('input[name="confirm"]').focus(); await page.keyboard.press('Space');
    await modal.locator('[type="submit"]').focus();
    const submitted = page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes(success.url));
    await page.keyboard.press('Enter');
    const response = await submitted;
    assert.equal(response.status(), 204);
    await page.waitForTimeout(400);
    const state = await (await ctx.request.get(base + '/state/' + success.pk + '/')).json();
    assert.equal(state.exists, false); assert(state.events.length > 0);
    keyboard.push({label: 'Confirmed Delete via keyboard', status: response.status(), state});
    const record = {captured: new Date().toISOString(), browser: browser.version(),
        source: 'bc5a56a8c8b9254bfe0e87d893a74ff57e72e38f85646b31b6206e1222717a12',
        sourceRevision: require('child_process').execFileSync('git', ['rev-parse', 'HEAD'], {encoding: 'utf8'}).trim(),
        screenshotDirectory: path.relative(process.cwd(), out), initialAttributes, results, keyboard, pageErrors: errors};
    fs.writeFileSync(path.join(durable, 'browser-results.json'), JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify({screenshots: results.length + 3, browser: browser.version(), keyboard, pageErrors: errors}, null, 2));
    await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
