// Focused presentation acceptance; owns its loopback host, SQLite database and browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, '.planning/phases/06.30-queryset-driven-conditional-fields-360/evidence/10-row-cards.json');
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const python = process.env.CV_QUERYSET_PYTHON || path.join(root, '.venv/bin/python');
const playwright = process.env.CV_QUERYSET_PLAYWRIGHT || '/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
const chromium = process.env.CV_QUERYSET_CHROMIUM || '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
// Reuse real example views, settings and seeds. The two mixed routes change only their declarations.
const host = String.raw`
import importlib, json, os, platform, sys
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
from formsets.seed import seed as seed_formsets
from queryset_conditional.seed import seed as seed_services
from formsets.models import Questionnaire
from queryset_conditional.models import RequestBatch
from formsets.views import cv_formsets, cv_compact_formsets, QuestionnaireUpdateView
import crud_views
assert Path(crud_views.__file__).resolve() == root / 'src/crud_views/__init__.py'
call_command('migrate', verbosity=0, interactive=False)
User = get_user_model()
User.objects.create_superuser(username='browser', password='browser-only-password', email='')
for name in ('alice', 'bob'): User.objects.create_user(username=name)
seed_formsets()
seed_services()
mixed = cv_formsets.model_copy(deep=True)
mixed['questions'].children['choices'] = cv_compact_formsets['questions'].children['choices'].model_copy(deep=True)
reverse_mixed = cv_compact_formsets.model_copy(deep=True)
reverse_mixed['questions'].children['choices'] = cv_formsets['questions'].children['choices'].model_copy(deep=True)
labelled = cv_formsets.model_copy(deep=True)
labelled['questions'].children['choices'].form_show_labels = True
urlpatterns = [
    path('favicon.ico', lambda request: HttpResponse(status=204)),
    path('__mixed/classic-compact/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=mixed)),
    path('__mixed/compact-classic/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=reverse_mixed)),
    path('__mixed/labelled/<int:pk>/', QuestionnaireUpdateView.as_view(cv_formsets=labelled)),
    path('', include('project.urls')),
]
pk = Questionnaire.objects.get(title='Customer Survey').pk
batch = RequestBatch.objects.get(title='Weekly service requests').pk
urls = {
    'questionnaire': reverse('questionnaire-update', kwargs={'pk': pk}),
    'compact': reverse('questionnaire-compact_update', kwargs={'pk': pk}),
    'classic-compact': f'/__mixed/classic-compact/{pk}/',
    'compact-classic': f'/__mixed/compact-classic/{pk}/',
    'labelled': f'/__mixed/labelled/{pk}/',
    'ordinary': reverse('service_batch-update', kwargs={'pk': batch}),
    'service-compact': reverse('service_batch_compact-update', kwargs={'pk': batch}),
}
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
        || f === 'tests/browser/formset-row-cards.cjs').sort().map(f => [f, digest(fs.readFileSync(path.join(root, f)))]));
}

async function run() {
    for (const file of [python, playwright, chromium]) assert(fs.existsSync(file), `Missing prerequisite ${file}`);
    const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-row-cards-'));
    // Captures survive resource cleanup for review, outside the repository's tracked source.
    const captures = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-row-card-captures-'));
    const record = {scope: 'G-06.30-1 only', started: new Date().toISOString(), command: process.argv,
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
        const ready = await new Promise((resolve, reject) => {
            let stdout = '';
            const timer = setTimeout(() => reject(Error(`Host startup timeout: ${hostLog}`)), 60000);
            child.once('error', error => {clearTimeout(timer); reject(error);});
            child.once('exit', code => {clearTimeout(timer); reject(Error(`Host exited ${code}: ${hostLog}`));});
            child.stdout.on('data', data => {
                stdout += data;
                for (const line of stdout.split('\n')) if (line.startsWith('{"port":')) {
                    clearTimeout(timer); resolve(JSON.parse(line)); return;
                }
            });
        });
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
        const rows = kind => page.locator(`.cv-formset-row[cv-data-formset-form*='"key": "${kind === 'choices' ? 'questions-choices' : kind}"']`);
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
                await capture(`${kind}-${width}`);
            }
        }
        const service = scenario('conditional-and-compact');
        for (const width of [1280, 390]) {
            await page.setViewportSize({width, height: 900});
            for (const kind of ['ordinary', 'service-compact']) {
                await visit(kind);
                const shape = await shapes();
                check(service, `${kind}-frames-${width}`, shape.length > 0 && shape.every(r => kind === 'ordinary' ? r.cards === 1 && r.legend === 'Service request' : r.cards === 0 && r.compact));
                const first = page.locator('.cv-formset-row').first();
                const address = first.locator('input[name$="-visit_address"]');
                const saved = await address.inputValue();
                const selector = first.locator('select[name$="-service"]');
                const original = await selector.inputValue();
                await selector.selectOption({label: 'Document review'});
                check(service, `${kind}-inactive-disabled-${width}`, await address.isDisabled());
                check(service, `${kind}-inactive-visibility-${width}`, await address.isVisible(), kind !== 'ordinary');
                await selector.selectOption(original);
                check(service, `${kind}-away-back-${width}`, await address.inputValue(), saved);
                await capture(`${kind}-${width}`);
            }
        }
        assert.deepEqual(record.pageErrors, []);
        assert.deepEqual(record.failedRequests, []);
        assert.deepEqual(fingerprints(), record.sourceHashes, 'Source changed during run');
        assert.deepEqual(record.scenarios.map(s => s.id), ['assets', 'nested-lifecycle', 'presentation', 'conditional-and-compact']);
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
run().catch(error => {console.error(error); process.exitCode = 1;});
