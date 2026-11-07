// Dedicated real-browser acceptance. Port rejection precedes runtime discovery.
const portText = process.env.CV_PRESENTATION_PORT ?? '8145';
const port = Number(portText);
if (!/^[0-9]+$/.test(portText) || port < 1024 || port > 65535 || [8143, 8144].includes(port)) {
    console.error('CV_PRESENTATION_PORT must be decimal 1024..65535; reserved ports: 8143, 8144');
    process.exit(1);
}
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
process.chdir(root);
const node = process.env.CV_FOCUS_NODE ?? process.execPath;
assert(fs.existsSync(node), `Missing CV_FOCUS_NODE: ${node}`);
if (fs.realpathSync(node) !== fs.realpathSync(process.execPath)) {
    const result = cp.spawnSync(node, [__filename, ...process.argv.slice(2)], {stdio: 'inherit'});
    process.exit(result.status ?? 1);
}
const crypto = require('node:crypto');
const net = require('node:net');
const argv = process.argv.slice(2);
function option(name, fallback) {
    const index = argv.indexOf(name);
    if (index < 0) return fallback;
    assert(argv[index + 1] && !argv[index + 1].startsWith('--'), `Missing ${name}`);
    return argv[index + 1];
}
const requested = option('--case', 'all');
assert(['tabs', 'all'].includes(requested), 'Use --case tabs|all');
const output = option('--output', '.planning/phases/06.5-remaining-presentation-contracts-and-decided-cleanup/08-browser-results.json');
const base = `http://127.0.0.1:${port}`;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function filesIn(dir) {
    return fs.readdirSync(dir, {withFileTypes: true}).flatMap(e => e.isDirectory() ? filesIn(`${dir}/${e.name}`) : [`${dir}/${e.name}`]);
}
function runtimePath(variable, candidates) {
    const selected = process.env[variable] ?? candidates.find(p => fs.existsSync(p));
    assert(selected && fs.existsSync(selected), `Missing ${variable}: ${selected ?? 'no cached runtime found'}`);
    return path.resolve(selected); // Keep venv symlinks: resolving Python's executable loses its environment.
}
function cached(directory, relative) {
    return fs.existsSync(directory) ? fs.readdirSync(directory).sort().reverse().map(name => path.join(directory, name, relative)) : [];
}
const home = process.env.HOME;
const assetSource = fs.readFileSync('tests/test1/app/templates/app/base.html', 'utf8');
const requiredAssets = [...assetSource.matchAll(/<(?:link|script)\b[^>]*?(?:href|src)="(https:[^"]+)"[^>]*>/gs)].map(([tag, url]) => ({
    requestedURL: url, integrity: tag.match(/integrity="([^"]+)"/)?.[1] ?? null,
    crossorigin: tag.match(/crossorigin="([^"]+)"/)?.[1] ?? null,
    version: url.includes('bootstrap') ? '5.3.3' : url.includes('jquery') ? '3.7.1' : '6.7.2',
}));
requiredAssets.push({requestedURL: 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/webfonts/fa-solid-900.woff2',
    integrity: null, crossorigin: null, version: '6.7.2'});
assert.equal(requiredAssets.length, 5);
function check(record, id, condition, observed) {
    record.assertions.push({id, passed: !!condition, ...(observed === undefined ? {} : {observed})});
    assert(condition, `${record.id}: ${id}: ${JSON.stringify(observed)}`);
}
async function bounded(promise, ms, message) {
    let timer;
    try {return await Promise.race([promise, new Promise((_, reject) => {timer = setTimeout(() => reject(Error(message)), ms);})]);}
    finally {clearTimeout(timer);}
}
async function preflight(page, url, report) {
    const responses = new Map();
    const failures = [];
    const pending = [];
    const responseListener = response => {
        let request = response.request();
        while (request.redirectedFrom()) request = request.redirectedFrom();
        const declared = requiredAssets.find(a => a.requestedURL === request.url());
        if (!declared || response.status() >= 300 && response.status() < 400) return;
        pending.push((async () => {
            const body = await response.body();
            responses.set(declared.requestedURL, {...declared, finalURL: response.url(), status: response.status(),
                sha256: sha(body), integrityAccepted: !declared.integrity || declared.integrity.split(/\s+/).some(sri => {
                    const split = sri.indexOf('-');
                    return crypto.createHash(sri.slice(0, split)).update(body).digest('base64') === sri.slice(split + 1);
                })});
        })().catch(error => failures.push({url: declared.requestedURL, reason: error.message})));
    };
    const failureListener = request => failures.push({url: request.url(), reason: request.failure()?.errorText});
    page.on('response', responseListener);
    page.on('requestfailed', failureListener);
    try {
        await bounded((async () => {
            const response = await page.goto(url, {waitUntil: 'load', timeout: 29000});
            if (response.status() !== 200) {
                const error = Error(`Fixture page returned HTTP ${response.status()}`);
                error.applicationFailure = true;
                throw error;
            }
            await page.waitForFunction(() => globalThis.bootstrap?.Tab.VERSION === '5.3.3' && globalThis.jQuery?.fn.jquery === '3.7.1');
            report.font = await page.evaluate(async () => {
                const loaded = await document.fonts.load('900 16px "Font Awesome 6 Free"');
                const icon = document.querySelector('.fa-user');
                const style = getComputedStyle(icon, '::before');
                return {loaded: loaded.length > 0 && document.fonts.check('900 16px "Font Awesome 6 Free"'),
                    family: style.fontFamily, weight: style.fontWeight, glyph: style.content};
            });
            assert(report.font.loaded && report.font.family.includes('Font Awesome 6 Free') && report.font.glyph.includes('\uf007'), 'Required rendered Font Awesome glyph');
            await Promise.all(pending);
            for (const declared of requiredAssets) {
                const actual = responses.get(declared.requestedURL);
                assert(actual?.status === 200 && actual.integrityAccepted && actual.sha256, `Required asset unavailable or integrity failed: ${declared.requestedURL}`);
            }
            assert.equal(failures.length, 0, JSON.stringify(failures));
        })(), 30000, 'Required browser asset preflight exceeded 30 seconds');
    } finally {
        page.off('response', responseListener);
        page.off('requestfailed', failureListener);
        report.assets = [...responses.values()];
        report.assetFailures = failures;
        report.missingAssets = requiredAssets.filter(a => !responses.has(a.requestedURL)).map(a => a.requestedURL);
    }
}
async function tabState(page, container, count, index, record, label, focused = true) {
    // Bootstrap's fade transition completes after aria-selected/active changes.
    await page.waitForFunction(({container, index}) => {
        const tabs = [...document.querySelector(container).querySelectorAll('[role="tab"]')];
        return tabs.every((tab, i) => document.getElementById(tab.getAttribute('aria-controls')).classList.contains('show') === (i === index));
    }, {container, index});
    const state = await page.locator(container).evaluate(root => ({
        focus: document.activeElement.id,
        tabs: [...root.querySelectorAll('[role="tab"]')].map(t => {
            const p = document.getElementById(t.getAttribute('aria-controls'));
            return {id: t.id, name: t.textContent.trim(), selected: t.getAttribute('aria-selected'),
                tabIndex: t.tabIndex, active: t.classList.contains('active'), target: t.getAttribute('data-bs-target'),
                panel: p && {id: p.id, label: p.getAttribute('aria-labelledby'), visible: !!p.getClientRects().length,
                    active: p.classList.contains('active'), shown: p.classList.contains('show'), tabIndex: p.tabIndex}};
        }),
    }));
    check(record, label, state.tabs.length === count && state.tabs.every((t, i) =>
        t.name && t.panel && t.target === '#' + t.panel.id && t.panel.label === t.id && t.panel.tabIndex === 0 &&
        t.selected === String(i === index) && t.active === (i === index) && t.tabIndex === (i === index ? 0 : -1) &&
        t.panel.visible === (i === index) && t.panel.active === (i === index) && t.panel.shown === (i === index)) &&
        (!focused || state.focus === state.tabs[index].id), state);
}
async function tabs(page, container, count, links, record, modal = false) {
    const controls = page.locator(`${container} [role="tab"]`);
    await tabState(page, container, count, 0, record, 'first-paint', false);
    await controls.first().focus();
    // This is deliberately the first interaction with the newly inserted tablist.
    for (const [key, selected] of [['ArrowDown', count - 1], ['ArrowDown', 0], ['ArrowUp', count - 1], ['Home', 0], ['End', count - 1]]) {
        await page.keyboard.press(key);
        await tabState(page, container, count, selected, record, `keyboard-${record.assertions.length}-${key}`);
    }
    for (let selected = 0; selected < count; selected++) {
        await controls.nth(selected).click();
        await tabState(page, container, count, selected, record, `click-${selected}`);
        const panel = await controls.nth(selected).getAttribute('aria-controls');
        await page.keyboard.press('Tab');
        check(record, `tab-panel-${selected}`, await page.evaluate(id => document.activeElement.id === id, panel), panel);
        await page.keyboard.press('Tab');
        const destination = links ? `#${panel} a[href="/panel-link/"]` : modal ? '#modal-after-tabs' : '#after-tabs';
        check(record, `tab-exit-${selected}`, await page.locator(destination).evaluate(el => el === document.activeElement), destination);
    }
}
async function runTabs(page, detail, report) {
    for (const count of [1, 2]) for (const links of [false, true]) {
        const url = base + detail + `?count=${count}&links=${Number(links)}`;
        assert.equal((await page.goto(url)).status(), 200);
        for (const modal of [false, true]) {
            const record = {id: `tabs-${count}-${links ? 'link' : 'plain'}-${modal ? 'modal' : 'page'}`, assertions: [], passed: false};
            report.cases.push(record);
            if (modal) {
                await page.locator('#launch').focus();
                await page.keyboard.press('Enter');
                await page.waitForFunction(() => document.querySelector('#cv-modal.show [role="tab"]') && !document.querySelector('#cv-modal').classList.contains('cv-loading'));
                await delay(350);
            }
            await tabs(page, modal ? '#cv-modal' : '#primary', count, links, record, modal);
            if (modal) {
                // Real HTTP replacement while visible; retain the accepted opener explicitly.
                const replacement = page.waitForResponse(r => r.url() === url && r.request().headers()['x-cv-modal'] === 'true');
                await page.evaluate(url => new Promise(resolve => {
                    document.getElementById('cv-modal').addEventListener('cv:modal:loaded', () => resolve(), {once: true});
                    cv.cvModalOpen(url, '', document.getElementById('launch'));
                }), url);
                check(record, 'replacement-real-http', (await replacement).status() === 200);
                await tabState(page, '#cv-modal', count, 0, record, 'replacement-first-paint', false);
                await page.locator('#cv-modal [data-cv-modal-dismiss]').click();
                await page.waitForFunction(() => document.activeElement.id === 'launch' && !document.querySelector('#cv-modal').classList.contains('show'));
                check(record, 'completed-close-restores-opener', await page.locator('#launch').evaluate(el => el === document.activeElement));
                await page.keyboard.press('Enter');
                await page.locator('#cv-modal.show [role="tab"]').first().waitFor();
                await delay(350);
                await page.locator('#cv-modal [role="tab"]').first().focus();
                await page.keyboard.press('ArrowDown');
                await tabState(page, '#cv-modal', count, count - 1, record, 'reopened-keyboard');
                await page.locator('#cv-modal [data-cv-modal-dismiss]').click();
                await page.waitForFunction(() => document.activeElement.id === 'launch');
            }
            record.passed = true;
        }
    }
}
async function accordionState(page, container, count, selected, record, label) {
    // Wait for every panel, including the previously selected one, to finish transitioning.
    await page.waitForFunction(selector => !document.querySelector(selector).querySelector('.collapsing'), container);
    const state = await page.locator(container).evaluate(root => [...root.querySelectorAll('.accordion-button')].map(control => {
        const panel = document.getElementById(control.getAttribute('aria-controls'));
        return {expanded: control.getAttribute('aria-expanded'), collapsed: control.classList.contains('collapsed'),
            shown: panel.classList.contains('show'), visible: panel.getBoundingClientRect().height > 0,
            contained: root.contains(panel), label: panel.getAttribute('aria-labelledby') === control.id,
            target: control.getAttribute('data-bs-target') === '#' + panel.id};
    }));
    check(record, label, state.length === count && state.every((item, index) =>
        item.expanded === String(index === selected) && item.collapsed === (index !== selected) &&
        item.shown === (index === selected) && item.visible === (index === selected) &&
        item.contained && item.label && item.target), state);
}
async function runIdentity(page, detail, report) {
    const record = {id: 'identity-isolation', assertions: [], passed: false};
    report.cases.push(record);
    await page.goto(base + detail + '?expanded=1');
    check(record, 'two-independent-page-tablists', await page.locator('main [role="tablist"]').count() === 2,
        await page.locator('main [role="tablist"]').count());
    await page.locator('#primary [role="tab"]').last().click();
    await tabState(page, '#primary', 2, 1, record, 'primary-switched');
    await tabState(page, '#sibling', 2, 0, record, 'sibling-unaffected', false);
    await page.locator('#sibling [role="tab"]').first().focus();
    await page.keyboard.press('ArrowDown');
    await tabState(page, '#sibling', 2, 1, record, 'sibling-keyboard');
    await tabState(page, '#primary', 2, 1, record, 'primary-unaffected', false);
    await openModal(page);
    await page.locator('#cv-modal [role="tab"]').first().focus();
    await page.keyboard.press('ArrowDown');
    await tabState(page, '#cv-modal', 2, 1, record, 'modal-independent-keyboard');
    await page.keyboard.press('Home');
    await tabState(page, '#cv-modal', 2, 0, record, 'modal-home');
    await tabState(page, '#primary', 2, 1, record, 'page-unaffected-by-modal', false);
    await tabState(page, '#sibling', 2, 1, record, 'sibling-unaffected-by-modal', false);
    const allIds = await page.locator('[id]').evaluateAll(nodes => nodes.map(n => n.id));
    check(record, 'page-modal-all-ids-unique', new Set(allIds).size === allIds.length);
    await closeModal(page);
    const parents = await page.locator('.accordion').evaluateAll(nodes => nodes.map(root => ({
        id: root.id, controls: [...root.querySelectorAll('.accordion-button')].map(c => {
            const panel = document.getElementById(c.getAttribute('aria-controls'));
            return {control: c.id, title: [...c.childNodes].filter(n => n.nodeType === Node.TEXT_NODE).map(n => n.textContent).join('').trim(), panel: panel.id, target: c.getAttribute('data-bs-target'),
                parent: panel.getAttribute('data-bs-parent'), label: panel.getAttribute('aria-labelledby'), contained: root.contains(panel)};
        }),
    })));
    check(record, 'two-scoped-accordions', parents.length === 2 && parents.every(p => p.controls.length === 5 &&
        p.controls.every(c => c.parent === '#' + p.id && c.target === '#' + c.panel && c.label === c.control && c.contained)), parents);
    check(record, 'arbitrary-repeated-titles', parents.every(p => JSON.stringify(p.controls.map(c => c.title)) === JSON.stringify(['Repeated', 'Repeated', '', 'A !?', '日本語'])));
    for (const [index, parent] of parents.entries()) {
        for (const [position, control] of parent.controls.entries()) {
            const icon = await inspectIcon(page, '#' + control.control);
            check(record, `accordion-${index}-icon-${position}`, icon.children.length === (position === 1 ? 1 : 0) &&
                icon.host.content.includes('\uf007') === (position === 0) &&
                (position !== 1 || icon.children[0].content.includes('\uf007')));
        }
    }
    for (const [index, parent] of parents.entries()) {
        await accordionState(page, '#' + parent.id, 5, 0, record, `accordion-${index}-first-paint`);
        for (const [position, control] of parent.controls.entries()) {
            if (position === 0) continue; // First group is already open on first paint.
            await page.locator('#' + control.control).click();
            await accordionState(page, '#' + parent.id, 5, position, record, `accordion-${index}-switch-${position}`);
        }
        await page.locator('#' + parent.controls.at(-1).control).click();
        await accordionState(page, '#' + parent.id, 5, -1, record, `accordion-${index}-close-all`);
        const sibling = parents[1 - index];
        await accordionState(page, '#' + sibling.id, 5, index === 0 ? 0 : -1, record, `accordion-${index}-sibling-unaffected`);
    }
    record.passed = true;
}
async function openModal(page) {
    await page.locator('#launch').focus();
    await page.keyboard.press('Enter');
    await page.locator('#cv-modal.show [role="tab"]').first().waitFor();
    await delay(350);
}
async function closeModal(page) {
    await page.locator('#cv-modal [data-cv-modal-dismiss]').click();
    await page.waitForFunction(() => document.activeElement.id === 'launch' && !document.querySelector('#cv-modal').classList.contains('show'));
}
async function identitySnapshot(page, container) {
    return page.locator(`${container} [role="tab"]`).evaluateAll(nodes => nodes.map(n => ({
        id: n.id, panel: n.getAttribute('aria-controls'), title: n.textContent.trim(),
    })));
}
async function runTranslation(page, detail, report) {
    const record = {id: 'stable-translated-identities', assertions: [], passed: false};
    report.cases.push(record);
    let stable, modalStable, generated;
    for (const [iteration, query] of ['lang=en', 'lang=en', 'lang=de', 'lang=de&reverse=1', 'lang=en'].entries()) {
        await page.goto(base + detail + '?expanded=1&' + query);
        const current = await identitySnapshot(page, '#primary');
        const ids = current.map(t => [t.id, t.panel]).sort();
        const expectedIds = token => ['january', 'february'].map(key => [
            `cvod-c${token.length}-${token}-s${key.length}-${key}-control`,
            `cvod-c${token.length}-${token}-s${key.length}-${key}-panel`,
        ]).sort(); // NOSONAR S2871: test harness
        check(record, `exact-supplied-page-targets-${iteration}`, JSON.stringify(ids) === JSON.stringify(expectedIds('author-page')));
        if (!stable) stable = ids;
        check(record, `stable-page-${iteration}`, JSON.stringify(ids) === JSON.stringify(stable), current);
        const expected = query.includes('lang=de') ? ['Januar', 'Februar'] : ['January', 'February'];
        if (query.includes('reverse')) expected.reverse();
        check(record, `real-translated-titles-${iteration}`, JSON.stringify(current.map(t => t.title)) === JSON.stringify(expected), current);
        const fresh = await page.locator('.accordion [id], .accordion[id]').evaluateAll(nodes => nodes.map(n => n.id));
        check(record, `generated-distinct-${iteration}`, fresh.length > 10 && new Set(fresh).size === fresh.length && (!generated || fresh.every(id => !generated.includes(id))));
        generated = fresh;
        await openModal(page);
        const modal = await identitySnapshot(page, '#cv-modal');
        const modalIds = modal.map(t => [t.id, t.panel]).sort();
        check(record, `exact-supplied-modal-targets-${iteration}`, JSON.stringify(modalIds) === JSON.stringify(expectedIds('author-modal')));
        if (!modalStable) modalStable = modalIds;
        check(record, `stable-modal-${iteration}`, JSON.stringify(modalIds) === JSON.stringify(modalStable) && modalIds.flat().every(id => !ids.flat().includes(id)), modal);
        check(record, `modal-translation-${iteration}`, JSON.stringify(modal.map(t => t.title)) === JSON.stringify(expected));
        await closeModal(page);
    }
    record.passed = true;
}
async function inspectIcon(page, selector) {
    return page.locator(selector).evaluate(host => {
        const icons = [...host.querySelectorAll('i')];
        const glyph = el => {const style = getComputedStyle(el, '::before'); return {content: style.content, font: style.fontFamily};};
        return {tag: host.tagName, text: host.textContent.trim(), classes: [...host.classList], host: glyph(host),
            children: icons.map(el => ({classes: [...el.classList], hidden: el.getAttribute('aria-hidden'), ...glyph(el)}))};
    });
}
async function runIcons(page, detail, report) {
    const record = {id: 'mixed-heading-icons', assertions: [], passed: false};
    report.cases.push(record);
    for (const icon of ['host', 'element', 'empty', 'disabled']) for (const size of ['default', 'replace', 'remove']) {
        await page.goto(base + detail + `?icon=${icon}&size=${size}&heading=2`);
        await openModal(page);
        for (const [selector, level, defaultSize] of [['main h2', 'H2', 'h3'], ['#cv-modal .modal-title', 'H2', 'h5']]) {
            const state = await inspectIcon(page, selector);
            const glyphs = [state.host, ...state.children].filter(g => g.content.includes('\uf007'));
            check(record, `${icon}-${size}-${defaultSize}-placement`, state.tag === level && state.text.length > 0 &&
                glyphs.length === (['host', 'element'].includes(icon) ? 1 : 0) &&
                state.children.length === (icon === 'element' ? 1 : 0) &&
                (icon !== 'host' || state.classes.includes('fa-user')) &&
                state.children.every(c => c.hidden === 'true') &&
                glyphs.every(g => g.font.includes('Font Awesome 6 Free')), state);
            check(record, `${icon}-${size}-${defaultSize}-sizing`, size === 'default' ? state.classes.includes(defaultSize) :
                !state.classes.includes(defaultSize) && state.classes.includes('native-title-size') === (size === 'replace'));
            check(record, `${icon}-${size}-${defaultSize}-accessible`, await page.getByRole('heading', {level: Number(level.slice(1))}).filter({hasText: new RegExp('^\\s*' + state.text + '\\s*$')}).count() === 1);
        }
        for (const scope of ['#primary', '#cv-modal']) {
            const host = await inspectIcon(page, `${scope} [role="tab"]:first-child`);
            const element = await inspectIcon(page, `${scope} [role="tab"]:last-child`);
            check(record, `${icon}-${size}-${scope}-group-icons`, host.classes.includes('fa-user') && host.children.length === 0 &&
                host.host.content.includes('\uf007') && element.children.length === 1 && element.children[0].content.includes('\uf007') &&
                element.children[0].hidden === 'true' && !element.classes.includes('fa-user'));
            check(record, `${icon}-${size}-${scope}-tab-accessible-names`, await page.locator(scope).getByRole('tab', {name: /January/}).count() === 1 &&
                await page.locator(scope).getByRole('tab', {name: /February/}).count() === 1);
        }
        await closeModal(page);
    }
    record.passed = true;
}
async function runNative(page, detail, report) {
    const record = {id: 'native-projection-escaping', assertions: [], passed: false};
    report.cases.push(record);
    const requests = [];
    const capture = request => requests.push(request.url());
    page.on('request', capture);
    try {
        const response = await page.goto(base + detail + '?theme=native');
        check(record, 'native-http-rendered', response.status() === 200);
        const state = await page.evaluate(() => {
            const group = document.querySelector('.native-group');
            return {title: group?.querySelector('h2')?.textContent, groupId: group?.dataset.groupId, root: group?.dataset.root,
                panel: group?.id, properties: [...document.querySelectorAll('dd')].map(el => ({...el.dataset, text: el.textContent.trim()})),
                badges: [...document.querySelectorAll('.status')].map(el => ({...el.dataset, text: el.textContent, classes: [...el.classList]})),
                attack: globalThis.presentationAttack, scripts: document.querySelectorAll('script,link[rel="stylesheet"], [onclick]').length,
                bootstrap: document.querySelectorAll('.badge, .card, [data-bs-toggle], [role="tab"]').length};
        });
        record.observed = state;
        const hostile = '<script>window.presentationAttack=1</script> & "value"';
        check(record, 'escaped-original-group', state.title === hostile && state.groupId === 'native' &&
            state.root === 'cvod-c11-author-page-root' && state.panel === 'cvod-c11-author-page-s6-native-panel');
        check(record, 'original-resolved-properties', state.properties.length === 3 && state.properties.slice(0, 2).every(p =>
            p.originalPath === 'first_name' && p.originalValue === hostile && p.text === hostile) && state.properties[2].text === 'Author');
        check(record, 'native-semantic-color-pill', state.badges.length === 2 && state.badges[0].color === 'brand-custom' &&
            state.badges[0].pill === 'True' && state.badges[0].classes.includes('status-brand') && state.badges[0].classes.includes('status-pill') &&
            state.badges[1].color === 'custom" onclick="attack' && state.badges[1].pill === 'False' && !state.badges[1].classes.includes('status-pill'));
        check(record, 'original-value-prop-settings-context', state.badges.every(b => b.value === hostile && b.path === 'first_name' &&
            b.newline === 'linebreaksbr' && b.text === hostile), state.badges);
        check(record, 'no-script-attribute-injection', !state.attack && state.scripts === 0);
        check(record, 'no-bootstrap-assets-or-markup', state.bootstrap === 0 && requests.every(url => url.startsWith(base)), requests);
    } finally {page.off('request', capture);}
    // The native loader context must not leak into a following stock response.
    await page.goto(base + detail);
    check(record, 'stock-after-native', await page.locator('#primary [role="tab"]').count() === 2 && await page.locator('.native-group').count() === 0);
    record.passed = true;
}
async function main() {
    const sourceFiles = ['tests/browser/presentation.cjs', 'tests/browser/presentation_server.py',
        'tests/browser/presentation-config.test.cjs', 'tests/test1/app/templates/app/base.html',
        ...filesIn('tests/browser/templates/presentation'), ...filesIn('src/crud_views/static/crud_views/js'),
        ...filesIn('src/crud_views_object_detail/static'),
        ...filesIn('src/crud_views_object_detail/templates'), 'src/crud_views_object_detail/lib/mixins.py',
        'src/crud_views/lib/icons.py', 'src/crud_views/lib/button_classes.py', 'src/crud_views/templatetags/crud_views.py',
        'src/crud_views/templates/crud_views/modal/content.html',
        'src/crud_views_object_detail/lib/presentation.py', 'src/crud_views_object_detail/lib/resolvers.py',
        'src/crud_views_object_detail/templatetags/crud_views_object_detail.py'];
    const report = {captured: new Date().toISOString(), command: [process.execPath, __filename, ...argv], scope: requested,
        revision: cp.execFileSync('git', ['rev-parse', 'HEAD'], {encoding: 'utf8'}).trim(), // NOSONAR S4036: test harness
        sourceHashes: Object.fromEntries(sourceFiles.sort().map(file => [file, sha(fs.readFileSync(file))])), // NOSONAR S2871: test harness
        runtime: {node: process.version, nodePath: process.execPath}, cases: [], pageErrors: [], consoleErrors: [], cleanup: {},
        coverageLimits: ['No human visual acceptance', 'No screen-reader or assistive-technology certification',
            'Native case is bounded projection/escaping, not native tabs or a full alternative theme'],
        status: 'running', passed: false};
    let child, childExit, browser, serverLog = '', assetGate = false;
    try {
        const python = runtimePath('CV_FOCUS_PYTHON', ['.nox/tests-3-12-django-5-2/bin/python', '.venv/bin/python']);
        const playwright = runtimePath('CV_FOCUS_PLAYWRIGHT', cached(`${home}/.npm/_npx`, 'node_modules/playwright'));
        const chromium = runtimePath('CV_FOCUS_CHROMIUM', cached(`${home}/.cache/ms-playwright`, 'chrome-linux64/chrome'));
        Object.assign(report.runtime, {pythonPath: python, playwrightPath: playwright, chromiumPath: chromium,
            playwright: require(`${playwright}/package.json`).version}, JSON.parse(cp.execFileSync(python, ['-c',
            'import json,sys,django,crud_views; print(json.dumps({"python":sys.version,"django":django.get_version(),"packagePath":crud_views.__file__}))'],
            {encoding: 'utf8', env: {...process.env, PYTHONPATH: `${root}/src:${root}`}})));
        assert(report.runtime.packagePath.startsWith(root + '/src/'));
        assert(/^(4\.2|5\.2|6\.0)\./.test(report.runtime.django), 'Use a supported Django series');
        await new Promise((resolve, reject) => {const probe = net.createServer(); probe.once('error', reject); probe.listen(port, '127.0.0.1', () => probe.close(resolve));});
        child = cp.spawn(python, ['tests/browser/presentation_server.py'], {cwd: root, env: {...process.env,
            CV_PRESENTATION_PORT: String(port), PYTHONPATH: `${root}/src:${root}`, PYTHONUNBUFFERED: '1'}, stdio: ['ignore', 'pipe', 'pipe']});
        child.stdout.on('data', data => {serverLog += data;}); child.stderr.on('data', data => {serverLog += data;});
        childExit = new Promise((resolve, reject) => {child.once('exit', (code, signal) => resolve({code, signal})); child.once('error', reject);});
        await bounded((async () => {
            while (!serverLog.includes('"ready"')) {
                assert(child.exitCode === null, `Fixture exited: ${serverLog}`);
                await delay(100);
            }
        })(), 15000, 'Fixture readiness timed out');
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true});
        report.runtime.chromium = browser.version();
        const context = await browser.newContext();
        const page = await context.newPage();
        page.setDefaultTimeout(5000);
        page.on('pageerror', error => report.pageErrors.push(error.message));
        page.on('console', message => {if (message.type() === 'error') report.consoleErrors.push(message.text());});
        const login = await context.request.get(base + '/signin/');
        assert.equal(login.status(), 200);
        const {detail} = await login.json();
        assetGate = true;
        await preflight(page, base + detail, report);
        assetGate = false;
        await runTabs(page, detail, report);
        if (requested === 'all') {
            await runIdentity(page, detail, report);
            await runTranslation(page, detail, report);
            await runIcons(page, detail, report);
            await runNative(page, detail, report);
        }
        assert.equal(report.cases.length, requested === 'all' ? 12 : 8);
        assert(report.cases.every(c => c.passed && c.assertions.length > 0 && c.assertions.every(a => a.passed)));
        assert.deepEqual(report.pageErrors, []);
        assert.deepEqual(report.consoleErrors, []);
        report.status = 'passed'; report.passed = true;
    } catch (error) {
        report.status = assetGate && !error.applicationFailure ? 'infrastructure_prerequisite_failed' : 'failed';
        report.error = error.stack;
        process.exitCode = report.status === 'infrastructure_prerequisite_failed' ? 2 : 1;
    } finally {
        const cleanupFailed = error => {
            report.cleanup.error = [report.cleanup.error, error.message].filter(Boolean).join('; ');
            report.passed = false; report.status = 'failed'; process.exitCode = 1;
        };
        try {
            if (browser) await bounded(browser.close(), 5000, 'Browser cleanup timed out');
            report.cleanup.browserClosed = true;
        } catch (error) {cleanupFailed(error);}
        // Fixture ownership is independent of whether Chromium closed successfully.
        try {
            if (child && child.exitCode === null && child.signalCode === null) child.kill('SIGTERM');
            if (childExit) { // NOSONAR S6544: test harness
                try {report.cleanup.serverExit = await bounded(childExit, 5000, 'Fixture cleanup timed out');}
                catch (error) {
                    child.kill('SIGKILL');
                    report.cleanup.serverExit = await childExit;
                    report.cleanup.reaped = true;
                    throw error; // NOSONAR S1143: test harness
                }
            }
            report.cleanup.reaped = true;
        } catch (error) {cleanupFailed(error);}
        report.serverLog = serverLog;
        report.completed = report.passed && report.cleanup.reaped;
        fs.mkdirSync(path.dirname(output), {recursive: true});
        if (fs.existsSync(output)) {
            const previous = JSON.parse(fs.readFileSync(output));
            if (previous.status === 'infrastructure_prerequisite_failed') {
                fs.copyFileSync(output, output + `.failed-${previous.captured.replace(/[^0-9]/g, '')}.json`);
            }
        }
        fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
        console.log(`${report.status}: ${report.cases.length} cases; ${output}`);
        if (report.error) console.error(report.error);
    }
}
main().catch(error => {console.error(error); process.exitCode = 1;});
