'use strict';
// Synthetic computed-style proof; Django rendering tests separately prove emitted classes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const {preflight} = require('./manage-presentation.cjs');
const {runtime} = require('./cancel-navigation.cjs');
const root = path.resolve(__dirname, '../..');
const revision = '04f95c30a6b368697ad92248071fec0477689186';
const baselineHashes = {
    'src/crud_views/static/crud_views/css/manage.css': 'da593f9dc2f3c69385a96fd13ef734f5d6549292b388a9d4659beff7c0f09808',
    'src/crud_views/static/crud_views/css/formset.css': 'a874e3f1a8f26520087adcdc5e4839f2befaccea462350a75d04e88f2231a630',
    'src/crud_views/templates/crud_views/formsets/compact_headings.html': '2f4b3b5133ee315a8c25c99e20bb6c4ad034c2d7a223d5daccdd7d55fe6ccfd0',
    'src/crud_views/lib/formsets/compact.py': '28fd041d458042c08d9921ed45ce5d124fd975ab28a28b4de9959be227c4d5a4',
};
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const cached = (dir, suffix) => fs.existsSync(dir) ? fs.readdirSync(dir).sort().reverse().map(n => path.join(dir, n, suffix)) : [];
const tokens = ['secondary-color', 'secondary-text-emphasis', 'body-bg', 'border-color', 'border-radius', 'tertiary-bg'];
// Each entry identifies exactly one consumer and its independently expected token slot.
const consumers = [
    ['th', '[data-cv-manage] th', 'color', 1],
    ['default', '.cv-manage-default td', 'color', 0],
    ['help', '[data-cv-manage-help]', 'color', 1],
    ['card-border', '.cv-formset-row-card', 'borderTopColor', 0],
    ['card-radius', '.cv-formset-row-card', 'borderTopLeftRadius', 4],
    ['card-bg', '.cv-formset-row-card', 'backgroundColor', 2],
    ['compact-radius', '.cv-formset-row-compact', 'borderTopLeftRadius', 4],
    ['compact-bg', '.cv-formset-row-compact', 'backgroundColor', 2],
    ['compact-border', '.cv-formset-row-bordered', 'borderTopColor', 3],
    ['child-bg', '.cv-formset-compact-child', 'backgroundColor', 5],
    ['child-border', '.cv-formset-compact-child', 'borderTopColor', 3],
    ['child-radius', '.cv-formset-compact-child', 'borderTopLeftRadius', 4],
];
const literal = ['rgb(108, 117, 125)', 'rgb(73, 80, 87)', 'rgb(255, 255, 255)', 'rgb(222, 226, 230)', '6px', 'rgb(248, 249, 250)'];
const outer = ['rgb(11, 22, 33)', 'rgb(44, 55, 66)', 'rgb(77, 88, 99)', 'rgb(111, 122, 133)', '10px', 'rgb(144, 155, 166)'];
const inner = ['rgb(21, 32, 43)', 'rgb(54, 65, 76)', 'rgb(87, 98, 109)', 'rgb(121, 132, 143)', '14px', 'rgb(154, 165, 176)'];

function fixture(changed) {
    const grid = kind => `<div class="row ${changed ? 'gx-3 ' : ''}cv-formset-compact-${kind}"><div class="col-6">Name</div><div class="col-6">Value</div></div>`;
    const content = `<div data-cv-manage><table><tbody><tr class="cv-manage-default"><th scope="row">Setting</th><td>Default</td></tr></tbody></table><button class="btn btn-sm btn-outline-secondary" data-cv-manage-help>?</button></div>
        <div class="cv-formset-row-card">Card</div><div class="cv-formset-row-compact cv-formset-row-bordered">${grid('headings')}${grid('fields')}</div><div class="cv-formset-compact-child">Child</div>`;
    return `<section id="light">${content}<section id="dark" data-bs-theme="dark" data-demo-theme="dark">${content}</section></section>`;
}
function mapping(rootOnly = false) {
    const values = list => tokens.map((t, i) => `--demo-${t}: ${list[i]};`).join('');
    const aliases = tokens.map(t => `--cv-${t}: var(--demo-${t});`).join('');
    return `:root {${values(outer)}} [data-demo-theme="dark"] {${values(inner)}}
        ${rootOnly ? ':root' : ':root, [data-demo-theme]'} {${aliases}}`;
}
async function measure(page, mode, selected, grids) {
    return page.evaluate(({mode, selected, grids}) => {
        const section = document.getElementById(mode);
        const one = selector => {
            const nodes = [...section.querySelectorAll(selector)].filter(el => el.closest('section') === section);
            if (nodes.length !== 1) throw new Error(`${mode}: expected one ${selector}, got ${nodes.length}`);
            return nodes[0];
        };
        const values = Object.fromEntries(selected.map(([id, selector, prop]) => [id, getComputedStyle(one(selector))[prop]]));
        const box = node => {const r = node.getBoundingClientRect(); return {x: r.x, y: r.y, width: r.width, height: r.height};};
        const rows = grids ? Object.fromEntries(['headings', 'fields'].map(kind => {
            const node = one(`.cv-formset-compact-${kind}`), css = getComputedStyle(node);
            return [kind, {gutter: css.getPropertyValue('--bs-gutter-x').trim(), align: css.alignItems,
                display: css.display, marginLeft: css.marginLeft, marginRight: css.marginRight, box: box(node),
                columns: [...node.children].map(child => ({paddingLeft: getComputedStyle(child).paddingLeft,
                    paddingRight: getComputedStyle(child).paddingRight, box: box(child)}))}];
        })) : {};
        return {values, rows};
    }, {mode, selected, grids});
}
async function main(argv = process.argv.slice(2)) {
    const opts = {case: 'all'};
    for (let i = 0; i < argv.length; i += 2) {
        assert(['--case', '--output'].includes(argv[i]) && argv[i + 1], 'Use --case manage|all --output FILE');
        opts[argv[i].slice(2)] = argv[i + 1];
    }
    assert(['manage', 'all'].includes(opts.case) && opts.output, 'Use --case manage|all --output FILE');
    const selected = opts.case === 'manage' ? consumers.slice(0, 3) : consumers;
    const grids = opts.case === 'all';
    const expectedCases = [1280, 390].flatMap(w => ['light', 'dark'].map(m => `stock-${m}-${w}`))
        .concat('theme-root-mapping', grids ? ['literal-fallback'] : []);
    const report = {selection: opts.case, expectedCases, cases: [], started: new Date().toISOString(), status: 'failed'};
    let browser;
    try {
        const original = {}, current = {}, hashes = {};
        for (const [file, digest] of Object.entries(baselineHashes)) {
            original[file] = cp.execFileSync('git', ['show', `${revision}:${file}`], {cwd: root});
            assert.equal(sha(original[file]), digest, `Baseline mismatch: ${file}`);
            current[file] = fs.readFileSync(path.join(root, file)); hashes[file] = sha(current[file]);
        }
        report.baseline = {revision, hashes: baselineHashes}; report.current = hashes;
        report.runnerHash = sha(fs.readFileSync(__filename));
        const assets = preflight(process.env.CV_MANAGE_ASSETS_DIR);
        const bootstrap = [...assets].find(([url]) => url.endsWith('/bootstrap@5.3.3/dist/css/bootstrap.min.css'));
        assert(bootstrap, 'Missing Bootstrap 5.3.3'); report.bootstrapHash = bootstrap[1].sha256;
        const playwright = runtime('CV_MANAGE_PLAYWRIGHT', cached(path.join(os.homedir(), '.npm/_npx'), 'node_modules/playwright'));
        const chromium = runtime('CV_MANAGE_CHROMIUM', cached(path.join(os.homedir(), '.cache/ms-playwright'), 'chrome-linux64/chrome'), true);
        browser = await require(playwright).chromium.launch({executablePath: chromium, headless: true, args: ['--no-sandbox']});
        report.runtime = {node: process.version, nodePath: process.execPath, playwright, chromium, browser: browser.version(),
            playwrightVersion: require(path.join(playwright, 'package.json')).version};
        const load = async (changed, width, extra = '', stock = true) => {
            const page = await browser.newPage({viewport: {width, height: 1000}});
            await page.route('**/*', route => route.abort());
            const source = changed ? current : original;
            const css = Object.entries(source).filter(([f]) => f.endsWith('.css')).map(([, bytes]) => bytes.toString()).join('\n');
            await page.setContent(`<style>${stock ? bootstrap[1].body : ''}\n${css}\nhtml {font-size:16px} section {padding:16px} ${extra}</style>${fixture(changed)}`);
            return page;
        };
        for (const width of [1280, 390]) {
            const before = await load(false, width), after = await load(true, width);
            const beforeModes = {};
            try {
                for (const mode of ['light', 'dark']) {
                    const id = `stock-${mode}-${width}`;
                    const expected = await measure(before, mode, selected, grids), actual = await measure(after, mode, selected, grids);
                    beforeModes[mode] = expected;
                    assert.equal(Object.keys(actual.values).length, grids ? 12 : 3);
                    assert.deepEqual(actual, expected, id);
                    if (grids) {
                        assert.equal(Object.keys(actual.rows).length, 2);
                        assert.equal(actual.rows.headings.display, width === 390 ? 'none' : 'flex');
                        assert(actual.rows.fields.box.width > 0 && actual.rows.fields.box.height > 0);
                        if (width === 1280) assert(actual.rows.headings.box.width > 0 && actual.rows.headings.box.height > 0);
                    }
                    report.cases.push({id, passed: true, actual, expected});
                }
                assert.notEqual(beforeModes.light.values.th, beforeModes.dark.values.th, 'Dark section must change text');
                if (grids) assert.notEqual(beforeModes.light.values['card-bg'], beforeModes.dark.values['card-bg'], 'Dark section must change backgrounds');
            } finally {await before.close(); await after.close();}
        }
        const mapped = await load(true, 1280, mapping()), rootOnly = await load(true, 1280, mapping(true));
        try {
            const results = {};
            for (const [mode, values] of [['light', outer], ['dark', inner]]) {
                const actual = (await measure(mapped, mode, selected, false)).values;
                const expected = Object.fromEntries(selected.map(([id, , , slot]) => [id, values[slot]]));
                results[mode] = {actual, expected};
                assert.deepEqual(actual, expected, `theme-root-mapping/${mode}`);
            }
            const actual = (await measure(rootOnly, 'dark', selected, false)).values;
            const expected = Object.fromEntries(selected.map(([id, , , slot]) => [id, outer[slot]]));
            assert.deepEqual(actual, expected, 'Root-only aliases must retain outer computed values');
            results.rootOnly = {actual, expected};
            report.cases.push({id: 'theme-root-mapping', passed: true, ...results});
        } finally {await mapped.close(); await rootOnly.close();}
        if (grids) {
            const page = await load(true, 1280, '[data-cv-manage-help] {color:var(--bs-btn-color)}', false);
            try {
                const actual = (await measure(page, 'light', selected, false)).values;
                const expected = Object.fromEntries(selected.map(([id, , , slot]) => [id, literal[slot]]));
                assert.deepEqual(actual, expected, 'literal-fallback');
                report.cases.push({id: 'literal-fallback', passed: true, actual, expected});
            } finally {await page.close();}
        }
        assert.deepEqual(report.cases.map(c => c.id), expectedCases);
        for (const [file, hash] of Object.entries(hashes)) assert.equal(sha(fs.readFileSync(path.join(root, file))), hash, 'Sources changed during run');
        assert.equal(sha(fs.readFileSync(__filename)), report.runnerHash);
        report.status = 'passed';
    } catch (error) {report.error = error.stack; throw error;}
    finally {
        if (browser) await browser.close();
        report.finished = new Date().toISOString();
        fs.mkdirSync(path.dirname(path.resolve(opts.output)), {recursive: true});
        fs.writeFileSync(opts.output, JSON.stringify(report, null, 2) + '\n');
        console.log(`${report.status}: ${report.cases.length} cases; ${opts.output}`);
    }
    return report;
}
if (require.main === module) main().catch(error => {console.error(error); process.exitCode = 1;});
module.exports = {main};
