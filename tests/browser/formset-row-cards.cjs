// Focused presentation acceptance; owns its loopback host, SQLite database and browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const outputIndex = process.argv.indexOf('--output');
if (outputIndex !== -1) assert(process.argv[outputIndex + 1], '--output requires a path');
const output = path.resolve(root, outputIndex === -1
    ? '.planning/phases/06.30-queryset-driven-conditional-fields-360/evidence/10-row-cards.json'
    : process.argv[outputIndex + 1]);
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const python = process.env.CV_QUERYSET_PYTHON || path.join(root, '.venv/bin/python');
const playwright = process.env.CV_QUERYSET_PLAYWRIGHT || '/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
const chromium = process.env.CV_QUERYSET_CHROMIUM || '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
// Reuse real example views, settings and seeds. The two mixed routes change only their declarations.
const host = String.raw`
import importlib, json, os, platform, sys
from dataclasses import replace
from pathlib import Path
from wsgiref.simple_server import make_server
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
from django.conf import settings
root, temp = Path(os.environ['CV_ROW_ROOT']), Path(os.environ['CV_ROW_TEMP'])
assert temp.name.startswith('cv-row-cards-') and temp.is_dir()
assert Path(importlib.import_module('project.settings').__file__).resolve() == root / 'examples/bootstrap5/project/settings.py'
settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(temp / 'db.sqlite3')}}
settings.MEDIA_ROOT = temp / 'media'
settings.ALLOWED_HOSTS = ['127.0.0.1']
settings.ROOT_URLCONF = '__main__'
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse
from django.urls import include, path, reverse
from django.utils.functional import lazy
from formsets.seed import seed as seed_formsets
from formsets_conditional.seed import seed as seed_conferences
from formsets_conditional.models import Conference
from queryset_conditional.seed import seed as seed_services
from formsets.models import Checklist, Questionnaire
from queryset_conditional.models import RequestBatch
from formsets.views import cv_formsets, cv_compact_formsets, QuestionnaireUpdateView
import crud_views
assert Path(crud_views.__file__).resolve() == root / 'src/crud_views/__init__.py'
call_command('migrate', verbosity=0, interactive=False)
User = get_user_model()
User.objects.create_superuser(username='browser', password='browser-only-password', email='')
for name in ('alice', 'bob'): User.objects.create_user(username=name)
seed_formsets()
seed_conferences()
seed_services()
mixed = cv_formsets.model_copy(deep=True)
mixed['questions'].children['choices'] = cv_compact_formsets['questions'].children['choices'].model_copy(deep=True)
reverse_mixed = cv_compact_formsets.model_copy(deep=True)
reverse_mixed['questions'].children['choices'] = cv_formsets['questions'].children['choices'].model_copy(deep=True)
labelled = cv_formsets.model_copy(deep=True)
labelled['questions'].children['choices'].form_show_labels = True
plain_parent = cv_compact_formsets.model_copy(deep=True)
plain_parent['questions'].row_legend = False
plain_parent['questions'].children['choices'].row_legend = None
plain_classic_parent = mixed.model_copy(deep=True)
plain_classic_parent['questions'].row_legend = False
plain_classic_parent['questions'].children['choices'].row_legend = None
plain_compact_parent = reverse_mixed.model_copy(deep=True)
plain_compact_parent['questions'].row_legend = False
plain_compact_parent['questions'].children['choices'].row_legend = None
variants = {}
for name, parent_border, child_border, legend in [
    ('border-parent', True, False, None), ('border-child', False, True, None),
    ('border-false', True, True, False), ('border-empty', True, True, ''),
    ('border-lazy-empty', True, True, lazy(lambda: '', str)()),
]:
    tree = cv_compact_formsets.model_copy(deep=True)
    parent = tree['questions']
    child = parent.children['choices']
    parent.compact_layout = replace(parent.compact_layout, row_border=parent_border)
    child.compact_layout = replace(child.compact_layout, row_border=child_border)
    parent.row_legend = child.row_legend = legend
    variants[name] = tree
urlpatterns = [
    path('favicon.ico', lambda request: HttpResponse(status=204)),
    path('__mixed/classic-compact/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=mixed)),
    path('__mixed/compact-classic/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=reverse_mixed)),
    path('__mixed/labelled/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=labelled)),
    path('__mixed/plain-parent/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=plain_parent)),
    path('__mixed/plain-classic-parent/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=plain_classic_parent)),
    path('__mixed/plain-compact-parent/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=plain_compact_parent)),
    path('', include('project.urls')),
]
urlpatterns[0:0] = [path(f'__mixed/{name}/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=tree))
    for name, tree in variants.items()]
pk = Questionnaire.objects.get(title='Customer Survey').pk
batch = RequestBatch.objects.get(title='Weekly service requests').pk
checklist = Checklist.objects.get(title='Release checklist').pk
urls = {
    'conference': reverse('conference-update', kwargs={'pk': Conference.objects.get(name='Python Summit').pk}),
    'checklist': reverse('checklist-update', kwargs={'pk': checklist}),
    'questionnaire': reverse('questionnaire-update', kwargs={'pk': pk}),
    'compact': reverse('questionnaire-compact_update', kwargs={'pk': pk}),
    'classic-compact': f'/__mixed/classic-compact/{pk}/',
    'compact-classic': f'/__mixed/compact-classic/{pk}/',
    'labelled': f'/__mixed/labelled/{pk}/',
    'plain-parent': f'/__mixed/plain-parent/{pk}/',
    'plain-classic-parent': f'/__mixed/plain-classic-parent/{pk}/',
    'plain-compact-parent': f'/__mixed/plain-compact-parent/{pk}/',
    'ordinary': reverse('service_batch-update', kwargs={'pk': batch}),
    'service-compact': reverse('service_batch_compact-update', kwargs={'pk': batch}),
}
urls.update({name: f'/__mixed/{name}/{pk}/' for name in variants})
with make_server('127.0.0.1', 0, StaticFilesHandler(get_wsgi_application())) as server:
    print(json.dumps({'port': server.server_port, 'login': reverse('login'), 'urls': urls,
        'runtime': {'python': platform.python_version(), 'django': django.get_version(),
                    'source': str(Path(crud_views.__file__).resolve()), 'settings': 'project.settings'}}), flush=True)
    server.serve_forever()
`;

function fingerprints() {
    const files = cp.execFileSync('git', ['ls-files', '-co', '--exclude-standard', '-z'], {cwd: root})
        .toString().split('\0');
    return Object.fromEntries([...new Set(files)].filter(f => /^(src\/|examples\/bootstrap5\/|package(-lock)?\.json$)/.test(f)
        || f.startsWith('tests/browser/formset-row-cards.')).sort().map(f => [f, digest(fs.readFileSync(path.join(root, f)))]));
}

function waitForReady(child, hostLog, timeout = 60000) {
    return new Promise((resolve, reject) => {
        let stdout = '';
        const finish = (error, ready) => {
            clearTimeout(timer);
            child.stdout.off('data', onData);
            child.off('error', onError);
            child.off('exit', onExit);
            if (error) reject(error);
            else resolve(ready);
        };
        const onError = error => finish(error);
        const onExit = code => finish(Error(`Host exited ${code}: ${hostLog()}`));
        const onData = data => {
            stdout += data;
            const lines = stdout.split('\n');
            stdout = lines.pop(); // A chunk boundary is not a record boundary.
            for (const line of lines) if (line.startsWith('{"port":')) {
                try {finish(null, JSON.parse(line));}
                catch (error) {finish(error);}
                return;
            }
        };
        const timer = setTimeout(() => finish(Error(`Host startup timeout: ${hostLog()}`)), timeout);
        child.stdout.setEncoding('utf8');
        child.once('error', onError);
        child.once('exit', onExit);
        child.stdout.on('data', onData);
    });
}

function validateCompactStyle(style, kind) {
    assert(['bordered', 'borderless', 'plain'].includes(kind));
    assert.equal(style.compact, true);
    assert.equal(style.plain, kind === 'plain');
    assert.equal(style.bordered, kind === 'bordered');
    assert.equal(style.cards, 0);
    assert.equal(style.legends, 0);
    for (const key of ['borders', 'padding', 'margins']) assert.equal(style[key].length, 4);
    assert(style.borders.every(value => kind === 'bordered' ? parseFloat(value) > 0 : value === '0px'));
    assert(style.padding.every(value => kind === 'plain' ? value === '0px' : parseFloat(value) > 0));
    if (kind === 'plain') {
        assert.equal(style.radius, '0px');
        assert.equal(style.background, 'rgba(0, 0, 0, 0)');
    } else {
        assert(parseFloat(style.radius) > 0);
        assert.notEqual(style.background, 'rgba(0, 0, 0, 0)');
    }
}

async function run() {
    for (const file of [python, playwright, chromium]) assert(fs.existsSync(file), `Missing prerequisite ${file}`);
    const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-row-cards-'));
    // Captures survive resource cleanup for review, outside the repository's tracked source.
    const captures = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-row-card-captures-'));
    const record = {scope: 'G-06.30-2 focused frames; prior ordinary scenarios retained', started: new Date().toISOString(), command: process.argv,
        sourceRoot: root, sourceHashes: fingerprints(), scenarios: [], screenshots: [], pageErrors: [], failedRequests: [],
        runtime: {node: process.version, nodePath: process.execPath, pythonPath: python, playwrightPath: playwright,
            playwright: require(path.join(playwright, 'package.json')).version, chromiumPath: chromium},
        isolation: {temporary, database: path.join(temporary, 'db.sqlite3'), media: path.join(temporary, 'media')}};
    let child, browser, failure, hostLog = '';
    const check = (scenario, id, actual, expected = true) => {
        assert.deepEqual(actual, expected, `${scenario.id}: ${id}`);
        scenario.assertions.push({id, actual, expected, passed: true});
    };
    const scenario = id => { const s = {id, assertions: []}; record.scenarios.push(s); console.log(`SCENARIO ${id}`); return s; };
    try {
        child = cp.spawn(python, ['-c', host], {cwd: root, env: {...process.env, PYTHONDONTWRITEBYTECODE: '1',
            PYTHONPATH: `${root}/src:${root}/examples/bootstrap5`, CV_ROW_ROOT: root, CV_ROW_TEMP: temporary}});
        child.stderr.on('data', data => {hostLog += data;});
        const ready = await waitForReady(child, () => hostLog);
        assert.notEqual(ready.port, 9000);
        Object.assign(record.runtime, ready.runtime);
        record.isolation.port = ready.port;
        const base = `http://127.0.0.1:${ready.port}`;
        browser = await require(playwright).chromium.launch({headless: true, executablePath: chromium, args: ['--no-sandbox']});
        record.runtime.chromium = browser.version();
        const context = await browser.newContext({viewport: {width: 1280, height: 900}});
        const page = await context.newPage();
        page.setDefaultTimeout(10000);
        page.on('pageerror', e => record.pageErrors.push(String(e)));
        page.on('requestfailed', r => record.failedRequests.push({url: r.url(), error: r.failure().errorText}));
        page.on('response', r => { if (r.status() >= 400) record.failedRequests.push({url: r.url(), status: r.status()}); });
        await page.goto(base + ready.login);
        await page.locator('[name="username"]').fill('browser');
        await page.locator('[name="password"]').fill('browser-only-password');
        await Promise.all([page.waitForURL(url => url.pathname !== ready.login),
            page.locator('form').filter({has: page.locator('[name="username"]')}).locator('[type="submit"]').click()]);
        const visit = async name => {const response = await page.goto(base + ready.urls[name]); assert.equal(response.status(), 200);};
        const capture = async name => {
            const file = path.join(captures, `${name}.png`);
            await page.screenshot({path: file, fullPage: true});
            record.screenshots.push({path: file, sha256: digest(fs.readFileSync(file))});
        };
        const rows = kind => page.locator(`.cv-formset-row[cv-data-formset-form*='"key": "${({choices: 'questions-choices', speakers: 'sessions-speakers'})[kind] || kind}"']`);
        const ownButton = (row, action) => row.locator(`:scope > .cv-formset-form button.cv-form-ctrl-${action}, :scope > .cv-formset-row-card > .cv-formset-form button.cv-form-ctrl-${action}`);
        const input = (row, suffix) => row.locator(`input[name$="-${suffix}"]`).first();
        const shapes = async () => page.locator('.cv-formset-row').evaluateAll(elements => elements.map(row => ({
            key: JSON.parse(row.getAttribute('cv-data-formset-form')).key.split('-').at(-1),
            compact: row.classList.contains('cv-formset-row-compact'),
            cards: row.querySelectorAll(':scope > .cv-formset-row-card').length,
            legend: row.querySelector(':scope > .cv-formset-row-card > legend')?.textContent.trim() || '',
        })));
        const checkQuestionnaire = async (s, id) => {
            const shape = await shapes();
            check(s, id, shape.length > 0 && shape.every(r => r.key === 'questions'
                ? r.cards === 1 && r.legend === 'Question' : r.cards === 0 && r.legend === ''));
        };
        const submit = async () => {
            const form = page.locator('form').filter({has: page.locator('.cv-formset-content')}).first();
            // Force server validation even for required-field failures covered below.
            await Promise.all([page.waitForNavigation(), form.evaluate(el => {el.noValidate = true; el.requestSubmit();})]);
        };
        const plainRow = async (s, id, row) => {
            // Inspect steady-state frames after the existing insertion/delete highlight finishes.
            await row.evaluate(async el => {await Promise.all(el.getAnimations().map(animation => animation.finished.catch(() => {})));});
            const actual = await row.evaluate(el => {
                const css = getComputedStyle(el);
                return {borders: ['Top', 'Right', 'Bottom', 'Left'].map(side => css[`border${side}Width`]),
                    padding: ['Top', 'Right', 'Bottom', 'Left'].map(side => css[`padding${side}`]),
                    radius: css.borderRadius, background: css.backgroundColor,
                    cards: el.querySelectorAll(':scope > .cv-formset-row-card').length,
                    legends: el.querySelectorAll(':scope > legend, :scope > .cv-formset-row-card > legend').length};
            });
            check(s, id, actual, {borders: ['0px', '0px', '0px', '0px'], padding: ['0px', '0px', '0px', '0px'],
                radius: '0px', background: 'rgba(0, 0, 0, 0)', cards: 0, legends: 0});
        };
        const compactRow = async (s, id, row, kind) => {
            await row.evaluate(async el => {await Promise.all(el.getAnimations().map(a => a.finished.catch(() => {})));});
            const actual = await row.evaluate(el => {
                const css = getComputedStyle(el), sides = ['Top', 'Right', 'Bottom', 'Left'];
                return {borders: sides.map(side => css[`border${side}Width`]),
                    padding: sides.map(side => css[`padding${side}`]), margins: sides.map(side => css[`margin${side}`]),
                    radius: css.borderRadius, background: css.backgroundColor,
                    compact: el.classList.contains('cv-formset-row-compact'),
                    bordered: el.classList.contains('cv-formset-row-bordered'), plain: el.classList.contains('cv-formset-row-plain'),
                    cards: el.querySelectorAll(':scope > .cv-formset-row-card').length,
                    legends: el.querySelectorAll(':scope > legend, :scope > .cv-formset-row-card > legend').length};
            });
            validateCompactStyle(actual, kind);
            check(s, id, {kind, ...actual}, {kind, ...actual});
            return actual;
        };
        const borderedCompactRow = (s, id, row) => compactRow(s, id, row, 'bordered');
        const borderlessCompactRow = (s, id, row) => compactRow(s, id, row, 'borderless');
        const framedRow = async (s, id, row) => check(s, id, await row.evaluate(el => {
            const frame = el.querySelector(':scope > .cv-formset-row-card') || el;
            const css = getComputedStyle(frame);
            return parseFloat(css.borderTopWidth) > 0 && parseFloat(css.paddingLeft) > 0
                && css.backgroundColor !== 'rgba(0, 0, 0, 0)';
        }));
        const checklist = scenario('checklist-lifecycle');
        for (const width of [1280, 390]) {
            await page.setViewportSize({width, height: 900});
            await visit('checklist');
            check(checklist, `note-${width}`, await page.getByText('Compact rows explicitly enable borders with row_border=True.', {exact: false}).first().isVisible());
            check(checklist, `questionnaire-link-${width}`, await page.getByRole('link', {name: 'Questionnaire examples', exact: true}).first().getAttribute('href'), '/formsets/questionnaire/');
            await borderedCompactRow(checklist, `initial-${width}`, rows('items').first());
            // A real computed-style mutation must fail the same predicate used for acceptance.
            const firstItem = rows('items').first();
            await firstItem.evaluate(el => el.classList.remove('cv-formset-row-bordered'));
            try {
                await assert.rejects(() => borderedCompactRow(checklist, `removed-hook-${width}`, firstItem));
                check(checklist, `removed-border-hook-rejected-${width}`, true);
            } finally {await firstItem.evaluate(el => el.classList.add('cv-formset-row-bordered'));}
            check(checklist, `headings-${width}`, await page.locator('.cv-formset-compact-headings').isVisible(), width > 768);
            check(checklist, `mobile-label-${width}`, await input(rows('items').first(), 'label').evaluate(el => {
                const label = el.labels[0];
                return label.textContent.trim().length > 0 && (innerWidth > 768 || label.getBoundingClientRect().height > 1);
            }));
            const count = await rows('items').count();
            await ownButton(rows('items').first(), 'add').click();
            await page.waitForFunction(n => document.querySelectorAll('.cv-formset-row').length === n + 1, count);
            const added = rows('items').nth(1);
            await input(added, 'label').fill(`Added item ${width}`);
            await added.locator('input[type="checkbox"][name$="-done"]').check();
            await borderedCompactRow(checklist, `inserted-${width}`, added);
            await input(rows('items').first(), 'label').fill('');
            await submit();
            await borderedCompactRow(checklist, `invalid-${width}`, rows('items').first());
            check(checklist, `required-error-${width}`, await input(rows('items').first(), 'label').evaluate(el =>
                el.getAttribute('aria-invalid') === 'true' && el.closest('.cv-formset-row').textContent.includes('required')));
            await input(rows('items').first(), 'label').fill(`Corrected item ${width}`);
            await borderedCompactRow(checklist, `corrected-${width}`, rows('items').first());
            await rows('items').first().locator('input[type="checkbox"][name$="-done"]').uncheck();
            await capture(`checklist-invalid-corrected-${width}`);
            await submit();
            check(checklist, `save-redirect-${width}`, new URL(page.url()).pathname !== ready.urls.checklist);
            await visit('checklist');
            await borderedCompactRow(checklist, `reopened-${width}`, rows('items').first());
            const values = await rows('items').evaluateAll(els => els.map(el => ({label: el.querySelector('input[name$="-label"]').value,
                done: el.querySelector('input[type="checkbox"][name$="-done"]').checked})));
            check(checklist, `saved-checked-${width}`, values.some(v => v.label === `Added item ${width}` && v.done));
            check(checklist, `saved-omitted-${width}`, values.some(v => v.label === `Corrected item ${width}` && !v.done));
            await capture(`checklist-reopened-${width}`);
        }
        const conference = scenario('conference-leaf-lifecycle');
        for (const width of [1280, 390]) {
            await page.setViewportSize({width, height: 900});
            await visit('conference');
            await plainRow(conference, `speaker-initial-${width}`, rows('speakers').first());
            await framedRow(conference, `session-initial-${width}`, rows('sessions').first());
            const oldName = await input(rows('speakers').first(), 'name').inputValue();
            const count = await rows('speakers').count();
            await ownButton(rows('speakers').first(), 'add').click();
            await page.waitForFunction(n => [...document.querySelectorAll('.cv-formset-row')].filter(el =>
                JSON.parse(el.getAttribute('cv-data-formset-form')).key === 'sessions-speakers').length === n + 1, count);
            const added = rows('sessions').first().locator('.cv-formset-row').nth(1);
            await input(added, 'name').fill(`New speaker ${width}`);
            await plainRow(conference, `speaker-inserted-${width}`, added);
            await input(rows('speakers').first(), 'name').fill('');
            await submit();
            await plainRow(conference, `speaker-invalid-${width}`, rows('speakers').first());
            await framedRow(conference, `session-invalid-${width}`, rows('sessions').first());
            const speakerAccessibility = await input(rows('speakers').first(), 'name').evaluate(el => {
                const row = el.closest('.cv-formset-row');
                const ids = (el.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
                return {invalid: el.getAttribute('aria-invalid'), error: row.textContent.includes('required'),
                    linkedError: ids.some(id => row.querySelector(`[id="${id}"]`)?.textContent.includes('required')),
                    sectionLabel: row.closest('.cv-formset-fieldset').querySelector(':scope > legend').textContent.trim()};
            });
            check(conference, `speaker-error-and-label-${width}`, speakerAccessibility,
                {invalid: 'true', error: true, linkedError: true, sectionLabel: 'Speakers'});
            await input(rows('speakers').first(), 'name').fill(`Edited speaker ${width}`);
            // Select a different persisted speaker even after the previous viewport's save.
            const otherIndex = await rows('speakers').evaluateAll((els, width) => els.findIndex(el => {
                const name = el.querySelector('input[name$="-name"]').value;
                return name && name !== `Edited speaker ${width}` && name !== `New speaker ${width}`;
            }), width);
            assert(otherIndex >= 0, 'A distinct saved speaker must be available for deletion');
            const otherSpeaker = rows('speakers').nth(otherIndex);
            const deletedName = await input(otherSpeaker, 'name').inputValue();
            await ownButton(otherSpeaker, 'delete').click();
            check(conference, `speaker-delete-control-${width}`, await input(otherSpeaker, 'DELETE').inputValue(), '1');
            await capture(`conference-corrected-${width}`);
            await submit();
            check(conference, `save-redirect-${width}`, new URL(page.url()).pathname !== ready.urls.conference);
            await visit('conference');
            const names = await rows('speakers').locator('input[name$="-name"]').evaluateAll(els => els.map(el => el.value));
            check(conference, `speaker-edit-saved-${width}`, names.includes(`Edited speaker ${width}`) && !names.includes(oldName));
            check(conference, `speaker-add-saved-${width}`, names.includes(`New speaker ${width}`));
            check(conference, `speaker-delete-saved-${width}`, !names.includes(deletedName));
            await plainRow(conference, `speaker-reopened-${width}`, rows('speakers').first());
            await framedRow(conference, `session-reopened-${width}`, rows('sessions').first());
            await capture(`conference-reopened-${width}`);
        }
        await page.locator('input[name="with_sessions"]').uncheck();
        check(conference, 'sessions-off-hidden', await rows('sessions').first().isVisible(), false);
        await submit();
        await visit('conference');
        check(conference, 'sessions-off-reopened', await page.locator('input[name="with_sessions"]').isChecked(), false);
        const purge = JSON.parse(cp.execFileSync(python, ['-c',
            "import json,sqlite3,sys; c=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True); pk=c.execute(\"SELECT id FROM formsets_conditional_conference WHERE name='Python Summit'\").fetchone()[0]; print(json.dumps({'sessions': c.execute('SELECT count(*) FROM formsets_conditional_session WHERE conference_id=?',(pk,)).fetchone()[0], 'speakers': c.execute('SELECT count(*) FROM formsets_conditional_speaker').fetchone()[0]}))",
            record.isolation.database], {encoding: 'utf8'}));
        check(conference, 'sessions-off-cascades-database', purge, {sessions: 0, speakers: 0});
        await visit('questionnaire');
        const asset = scenario('assets');
        const stylesheet = await page.locator('link[href*="/formset.css"]').getAttribute('href');
        check(asset, 'no-preview-suffix', !stylesheet.includes('?'));
        const response = await context.request.get(new URL(stylesheet, base).href);
        check(asset, 'stylesheet-response', response.status(), 200);
        record.servedStylesheet = {url: stylesheet, actualHash: digest(await response.body()),
            expectedHash: digest(fs.readFileSync(path.join(root, 'src/crud_views/static/crud_views/css/formset.css')))};
        check(asset, 'served-stylesheet-identity', record.servedStylesheet.actualHash, record.servedStylesheet.expectedHash);

        const nested = scenario('nested-lifecycle');
        await checkQuestionnaire(nested, 'initial-frames');
        const originalSibling = await input(rows('questions').nth(1), 'text').inputValue();
        const firstChoiceValue = await input(rows('choices').first(), 'label').inputValue();
        const childCount = await rows('choices').count();
        await ownButton(rows('choices').first(), 'add').click();
        await page.waitForFunction(n => [...document.querySelectorAll('.cv-formset-row')].filter(el => JSON.parse(el.getAttribute('cv-data-formset-form')).key === 'questions-choices').length === n + 1, childCount);
        await checkQuestionnaire(nested, 'ajax-child-unframed');
        check(nested, 'child-insert-preserves-sibling', await input(rows('questions').nth(1), 'text').inputValue(), originalSibling);
        // New child follows its insertion owner; initial siblings keep their own names and values.
        const newChild = rows('questions').first().locator('.cv-formset-row').nth(1);
        await input(newChild, 'label').fill('Added child');
        check(nested, 'original-child-preserved', await input(rows('choices').first(), 'label').inputValue(), firstChoiceValue);
        const parentCount = await rows('questions').count();
        await ownButton(rows('questions').first(), 'add').click();
        await page.waitForFunction(n => [...document.querySelectorAll('.cv-formset-row')].filter(el => JSON.parse(el.getAttribute('cv-data-formset-form')).key === 'questions').length === n + 1, parentCount);
        const newParent = rows('questions').nth(1);
        await input(newParent, 'text').fill('Added parent');
        await input(newParent.locator('.cv-formset-row').first(), 'label').fill('Nested answer');
        await checkQuestionnaire(nested, 'ajax-parent-and-children');
        check(nested, 'parent-insert-preserves-sibling', await input(rows('questions').nth(2), 'text').inputValue(), originalSibling);
        check(nested, 'control-row-ownership', await page.locator('button[class*="cv-form-ctrl-"]').evaluateAll(buttons => buttons.length > 0 && buttons.every(button => {
            const row = button.closest('.cv-formset-row');
            return row && button.closest('.cv-formset-form').parentElement.closest('.cv-formset-row') === row;
        })));

        // An existing child with an empty required value must redisplay its own native error.
        await input(rows('choices').first(), 'label').fill('');
        await submit();
        await checkQuestionnaire(nested, 'invalid-redisplay-frames');
        check(nested, 'suppressed-row-error-associated', await input(rows('choices').first(), 'label').evaluate(el => {
            const row = el.closest('.cv-formset-row');
            const ids = (el.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
            return el.getAttribute('aria-invalid') === 'true' && ids.some(id => row.querySelector(`[id="${id}"]`)?.textContent.includes('required'));
        }));
        await input(rows('choices').first(), 'label').fill(firstChoiceValue);
        await ownButton(rows('choices').first(), 'delete').click();
        check(nested, 'delete-owned-child', await rows('choices').first().locator('input[name$="-DELETE"]').inputValue(), '1');
        // Django redisplay groups initial rows before extras; find the inserted row by its value.
        const addedParent = rows('questions').filter({has: page.locator('input[name$="-text"][value="Added parent"]')});
        for (let i = 0; i < await rows('questions').count() - 1; i++) await ownButton(addedParent, 'up').click();
        check(nested, 'reordered-parent-value', await input(rows('questions').first(), 'text').inputValue(), 'Added parent');
        await submit();
        check(nested, 'save-redirect', new URL(page.url()).pathname !== ready.urls.questionnaire);
        await visit('questionnaire');
        await checkQuestionnaire(nested, 'saved-reopened-frames');
        check(nested, 'reopened-parent-order', await input(rows('questions').first(), 'text').inputValue(), 'Added parent');
        check(nested, 'reopened-nested-value', await input(rows('questions').first().locator('.cv-formset-row').first(), 'label').inputValue(), 'Nested answer');
        const labels = await rows('choices').locator('input[name$="-label"]').evaluateAll(els => els.map(el => el.value));
        check(nested, 'deleted-child-absent', !labels.includes(firstChoiceValue));
        check(nested, 'added-child-saved', labels.includes('Added child'));

        const presentation = scenario('presentation');
        for (const width of [1280, 390]) {
            await page.setViewportSize({width, height: 900});
            await visit('questionnaire');
            await checkQuestionnaire(presentation, `frames-${width}`);
            check(presentation, `card-boundary-${width}`, await page.locator('.cv-formset-row-card').first().evaluate(el => {
                const css = getComputedStyle(el), rect = el.getBoundingClientRect();
                return parseFloat(css.borderTopWidth) >= 1 && css.borderTopColor !== css.backgroundColor
                    && parseFloat(css.paddingLeft) > 0 && rect.left >= 0 && rect.right <= innerWidth;
            }));
            check(presentation, `plain-child-${width}`, await rows('choices').first().evaluate(el => {
                const css = getComputedStyle(el);
                return !el.querySelector(':scope > fieldset.cv-formset-row-card') && parseFloat(css.borderTopWidth) === 0 && parseFloat(css.paddingLeft) === 0;
            }));
            const field = input(rows('choices').first(), 'label');
            await field.focus();
            await page.keyboard.press('Tab');
            check(presentation, `keyboard-child-controls-${width}`, await rows('choices').first().evaluate(el => el.contains(document.activeElement) && document.activeElement.matches('button')));
            check(presentation, `field-row-identity-${width}`, await field.evaluate(el =>
                el.name.startsWith(el.closest('.cv-formset-row').getAttribute('cv-data-formset-form-prefix') + '-')));
            await capture(`questionnaire-${width}`);
            await visit('labelled');
            await checkQuestionnaire(presentation, `labelled-suppression-${width}`);
            check(presentation, `explicit-label-associated-${width}`, await input(rows('choices').first(), 'label').evaluate(el =>
                Array.from(el.labels || []).some(label => label.closest('.cv-formset-row') === el.closest('.cv-formset-row')
                    && label.textContent.includes('Label'))));
            for (const kind of ['compact', 'classic-compact', 'compact-classic']) {
                await visit(kind);
                const shape = await shapes();
                check(presentation, `${kind}-${width}`, shape.length > 0 && shape.every(r => {
                    const compact = kind === 'compact' || (kind === 'classic-compact' ? r.key === 'choices' : r.key === 'questions');
                    return r.compact === compact && r.cards === (!compact && r.key === 'questions' ? 1 : 0);
                }));
                await plainRow(presentation, `${kind}-child-styles-${width}`, rows('choices').first());
                await (kind === "classic-compact" ? framedRow : borderlessCompactRow)(presentation, `${kind}-parent-styles-${width}`, rows('questions').first());
                const count = await rows('choices').count();
                await ownButton(rows('choices').first(), 'add').click();
                await page.waitForFunction(n => [...document.querySelectorAll('.cv-formset-row')].filter(el =>
                    JSON.parse(el.getAttribute('cv-data-formset-form')).key === 'questions-choices').length === n + 1, count);
                const added = rows('questions').first().locator('.cv-formset-row').nth(1);
                const addedLabel = `Added ${kind} ${width}`;
                await input(added, 'label').fill(addedLabel);
                await plainRow(presentation, `${kind}-inserted-child-${width}`, added);
                const original = await input(rows('choices').first(), 'label').inputValue();
                await input(rows('choices').first(), 'label').fill('');
                await submit();
                await plainRow(presentation, `${kind}-invalid-child-${width}`, rows('choices').first());
                check(presentation, `${kind}-required-error-${width}`, await input(rows('choices').first(), 'label').getAttribute('aria-invalid'), 'true');
                await input(rows('choices').first(), 'label').fill(original);
                await submit();
                check(presentation, `${kind}-save-redirect-${width}`, new URL(page.url()).pathname !== ready.urls[kind]);
                await visit(kind);
                check(presentation, `${kind}-added-saved-${width}`, await rows('choices').locator('input[name$="-label"]').evaluateAll(
                    (els, expected) => els.some(el => el.value === expected), addedLabel));
                await plainRow(presentation, `${kind}-reopened-child-${width}`, rows('choices').first());
                await capture(`${kind}-${width}`);
            }
            for (const kind of ['plain-parent', 'plain-classic-parent', 'plain-compact-parent']) {
                await visit(kind);
                await plainRow(presentation, `${kind}-parent-${width}`, rows('questions').first());
                await (kind === "plain-compact-parent" ? framedRow : borderlessCompactRow)(presentation, `${kind}-child-${width}`, rows('choices').first());
                const count = await rows('choices').count();
                await ownButton(rows('choices').first(), 'add').click();
                await page.waitForFunction(n => [...document.querySelectorAll('.cv-formset-row')].filter(el =>
                    JSON.parse(el.getAttribute('cv-data-formset-form')).key === 'questions-choices').length === n + 1, count);
                const added = rows('questions').first().locator('.cv-formset-row').nth(1);
                await input(added, 'label').fill('Mixed inserted answer');
                await (kind === "plain-compact-parent" ? framedRow : borderlessCompactRow)(presentation, `${kind}-inserted-child-${width}`, added);
                await input(rows('choices').first(), 'label').fill('');
                await submit();
                await plainRow(presentation, `${kind}-invalid-parent-${width}`, rows('questions').first());
                await (kind === "plain-compact-parent" ? framedRow : borderlessCompactRow)(presentation, `${kind}-invalid-child-${width}`, rows('choices').first());
                check(presentation, `${kind}-invalid-error-${width}`, await input(rows('choices').first(), 'label').getAttribute('aria-invalid'), 'true');
                await capture(`${kind}-${width}`);
            }
        }
        const borders = scenario('compact-border-precedence');
        for (const width of [1280, 390]) {
            await page.setViewportSize({width, height: 900});
            const observed = {};
            for (const kind of ['border-parent', 'border-child', 'border-false', 'border-empty', 'border-lazy-empty']) {
                await visit(kind);
                const suppressed = !['border-parent', 'border-child'].includes(kind);
                const inspect = async state => {
                    const parent = await compactRow(borders, `${kind}-${state}-parent-${width}`, rows('questions').first(),
                        suppressed ? 'plain' : kind === 'border-parent' ? 'bordered' : 'borderless');
                    const child = await compactRow(borders, `${kind}-${state}-child-${width}`, rows('choices').first(),
                        suppressed ? 'plain' : kind === 'border-child' ? 'bordered' : 'borderless');
                    check(borders, `${kind}-${state}-section-${width}`, await rows('choices').first().evaluate(el => {
                        const section = el.closest('.cv-formset-fieldset'), css = getComputedStyle(section);
                        return section.querySelector(':scope > legend').textContent.trim() === 'Choices'
                            && ['Top', 'Right', 'Bottom', 'Left'].every(side => parseFloat(css[`border${side}Width`]) > 0);
                    }));
                    return {parent, child};
                };
                observed[kind] = await inspect('initial');
                const count = await rows('choices').count();
                await ownButton(rows('choices').first(), 'add').click();
                await page.waitForFunction(n => [...document.querySelectorAll('.cv-formset-row')].filter(el =>
                    JSON.parse(el.getAttribute('cv-data-formset-form')).key === 'questions-choices').length === n + 1, count);
                const added = rows('questions').first().locator('.cv-formset-row').nth(1);
                await input(added, 'label').fill(`Border ${kind} ${width}`);
                await compactRow(borders, `${kind}-inserted-${width}`, added,
                    suppressed ? 'plain' : kind === 'border-child' ? 'bordered' : 'borderless');
                const original = await input(rows('choices').first(), 'label').inputValue();
                await input(rows('choices').first(), 'label').fill('');
                await submit();
                await inspect('invalid');
                check(borders, `${kind}-error-${width}`, await input(rows('choices').first(), 'label').getAttribute('aria-invalid'), 'true');
                await input(rows('choices').first(), 'label').fill(original);
                await inspect('corrected');
                await submit();
                check(borders, `${kind}-saved-${width}`, new URL(page.url()).pathname !== ready.urls[kind]);
                await visit(kind);
                await inspect('reopened');
                await capture(`${kind}-${width}`);
            }
            for (const level of ['parent', 'child']) for (const property of ['padding', 'margins', 'radius', 'background']) {
                check(borders, `border-only-${level}-${property}-${width}`, observed['border-parent'][level][property],
                    observed['border-child'][level][property]);
            }
        }
        const service = scenario('conditional-and-compact');
        for (const width of [1280, 390]) {
            await page.setViewportSize({width, height: 900});
            for (const kind of ['ordinary', 'service-compact']) {
                await visit(kind);
                check(service, `${kind}-note-${width}`, await page.locator('body').evaluate(el => {
                    const visible = el.cloneNode(true);
                    visible.querySelectorAll('pre, code, script, style').forEach(node => node.remove());
                    return visible.textContent.includes('Compact rows are borderless by default (row_border=False).');
                }), kind !== 'ordinary');
                const shape = await shapes();
                check(service, `${kind}-frames-${width}`, shape.length > 0 && shape.every(r => kind === 'ordinary' ? r.cards === 1 && r.legend === 'Service request' : r.cards === 0 && r.compact));
                const first = page.locator('.cv-formset-row').first();
                await (kind === "ordinary" ? framedRow : borderlessCompactRow)(service, `${kind}-default-frame-styles-${width}`, first);
                const address = first.locator('input[name$="-visit_address"]');
                const saved = await address.inputValue();
                const selector = first.locator('select[name$="-service"]');
                const original = await selector.inputValue();
                await selector.selectOption({label: 'Document review'});
                check(service, `${kind}-inactive-disabled-${width}`, await address.isDisabled());
                check(service, `${kind}-inactive-visibility-${width}`, await address.isVisible(), kind !== 'ordinary');
                await selector.selectOption(original);
                check(service, `${kind}-away-back-${width}`, await address.inputValue(), saved);
                const rowStyle = kind === 'ordinary' ? framedRow : borderlessCompactRow;
                const originalAddress = await address.inputValue();
                await address.fill('');
                await submit();
                await rowStyle(service, `${kind}-invalid-${width}`, page.locator('.cv-formset-row').first());
                check(service, `${kind}-error-${width}`, await page.locator('input[name$="-visit_address"]').first().getAttribute('aria-invalid'), 'true');
                await page.locator('input[name$="-visit_address"]').first().fill(originalAddress);
                await rowStyle(service, `${kind}-corrected-${width}`, page.locator('.cv-formset-row').first());
                await submit();
                check(service, `${kind}-saved-${width}`, new URL(page.url()).pathname !== ready.urls[kind]);
                await visit(kind);
                await rowStyle(service, `${kind}-reopened-${width}`, page.locator('.cv-formset-row').first());
                await capture(`${kind}-${width}`);
            }
        }
        assert.deepEqual(record.pageErrors, []);
        assert.deepEqual(record.failedRequests, []);
        assert(record.screenshots.length > 0);
        for (const capture of record.screenshots) assert.equal(digest(fs.readFileSync(capture.path)), capture.sha256);
        assert.deepEqual(fingerprints(), record.sourceHashes, 'Source changed during run');
        assert.deepEqual(record.scenarios.map(s => s.id), ['checklist-lifecycle', 'conference-leaf-lifecycle', 'assets', 'nested-lifecycle', 'presentation', 'compact-border-precedence', 'conditional-and-compact']);
        assert(record.scenarios.every(s => s.assertions.length > 0));
    } catch (error) {failure = error; record.failure = String(error); console.error(hostLog.slice(-3000));}
    finally {
        try {if (browser) await browser.close();}
        finally {
            try {
                if (child && child.exitCode === null && child.signalCode === null) await new Promise(resolve => {
                    const timer = setTimeout(() => child.kill('SIGKILL'), 5000);
                    child.once('exit', () => {clearTimeout(timer); resolve();}); child.kill('SIGTERM');
                });
            } finally {fs.rmSync(temporary, {recursive: true, force: true});}
        }
        record.cleanup = {reaped: !child || child.exitCode !== null || child.signalCode !== null, temporaryRemoved: !fs.existsSync(temporary)};
        record.completed = new Date().toISOString();
        record.passed = !failure && record.cleanup.reaped && record.cleanup.temporaryRemoved;
        fs.mkdirSync(path.dirname(output), {recursive: true});
        fs.writeFileSync(output, JSON.stringify(record, null, 2) + '\n');
    }
    if (failure) throw failure;
    assert(record.passed);
    console.log(`ROW_CARDS_OK ${record.scenarios.reduce((n, s) => n + s.assertions.length, 0)} assertions; ${output}`);
}
module.exports = {waitForReady, validateCompactStyle};
if (require.main === module) run().catch(error => {console.error(error); process.exitCode = 1;});
