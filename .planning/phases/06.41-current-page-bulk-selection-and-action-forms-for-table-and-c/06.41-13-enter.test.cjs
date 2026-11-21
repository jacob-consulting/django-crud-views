// Acceptance evidence runner: use an existing Playwright installation, browser and seeded server.
const {chromium} = require(process.env.CV_BULK_PLAYWRIGHT);
const assert = require('node:assert/strict');
const test = require('node:test');

test('Enter on a bulk checkbox never submits with JavaScript disabled', async () => {
    const browser = await chromium.launch({executablePath: process.env.CV_BULK_CHROMIUM, headless: true});
    try {
        const page = await browser.newPage({
            javaScriptEnabled: false,
            storageState: process.env.CV_BULK_BROWSER_AUTH,
        });
        await page.goto(process.env.CV_BULK_BROWSER_URL);
        const initial = page.url();
        const posts = [];
        page.on('request', request => { if (request.method() === 'POST') posts.push(request.url()); });
        const checkbox = page.getByRole('checkbox', {name: 'Select Document 01', exact: true});
        await checkbox.check();
        await checkbox.focus();
        await page.keyboard.press('Enter');
        await page.waitForTimeout(400);
        assert.deepEqual(posts, [], 'Enter must not submit the first configured action');
        assert.equal(page.url(), initial);
        assert.equal(await checkbox.isChecked(), true);
    } finally {
        await browser.close();
    }
});
