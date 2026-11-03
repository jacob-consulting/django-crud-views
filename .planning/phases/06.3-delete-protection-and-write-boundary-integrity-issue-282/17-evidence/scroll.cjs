const {chromium} = require('/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('fs'), path = require('path');
(async () => {
    const base = 'http://127.0.0.1:8143';
    const browser = await chromium.launch({headless: true,
        executablePath: '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome', args: ['--no-sandbox']});
    const ctx = await browser.newContext({ignoreHTTPSErrors: true, viewport: {width: 375, height: 812}});
    const page = await ctx.newPage();
    await page.goto(base + '/signin/');
    await ctx.addCookies([{name: 'review_language', value: 'de', url: base}]);
    const cases = await (await ctx.request.get(base + '/cases/')).json();
    const c = cases.find(c => c.language === 'de' && c.mode === 'partial');
    await page.goto(base + '/harness/?target=' + encodeURIComponent(c.url));
    await page.waitForFunction(() => typeof bootstrap === 'object' && typeof cv.cvModalOpen === 'function');
    await page.locator('#launch').focus(); await page.keyboard.press('Enter');
    const modal = page.locator('#cv-modal'); await modal.waitFor({state: 'visible'});
    await modal.locator('input[name="confirm"]').focus();
    await page.waitForTimeout(400);
    await page.screenshot({path: '.planning/ui-reviews/06.3-gap-review/de-partial-modal-375x812-scrolled-confirm.png'});
    const result = await modal.evaluate(e => {
        const input = e.querySelector('input[name="confirm"]');
        const s = getComputedStyle(input), text = e.querySelector('.modal-body');
        return {active: document.activeElement.id, boxShadow: s.boxShadow,
            font: getComputedStyle(text).fontFamily, scrollTop: e.scrollTop, scrollHeight: e.scrollHeight,
            clientHeight: e.clientHeight, fullText: e.innerText};
    });
    const files = fs.readdirSync('.planning/ui-reviews/06.3-gap-review').filter(f => f.endsWith('.png'));
    const crypto = require('crypto');
    result.screenshots = files.map(file => ({file, sha256: crypto.createHash('sha256').update(
        fs.readFileSync(path.join('.planning/ui-reviews/06.3-gap-review', file))).digest('hex')}));
    fs.writeFileSync('.planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/17-evidence/scroll-results.json', JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify({font: result.font, active: result.active, screenshots: files.length}));
    await browser.close();
})().catch(error => {console.error(error); process.exit(1);});
