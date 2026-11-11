/* Actual example lifecycle. Ordinary runs isolate all captures beside --output. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const net = require('node:net');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

const root = cp.execFileSync('git', ['rev-parse', '--show-toplevel'], {encoding:'utf8'}).trim();
const args = process.argv.slice(2);
const output = path.resolve(args[args.indexOf('--output') + 1] || '/tmp/checklist-example.json');
assert(args.includes('--output'), 'Pass an explicit --output file');
const retain = args.includes('--retain');
const phase = path.join(root, '.planning/phases/06.26-issue-351');
const canonical = path.join(phase, '06.26-EXAMPLE-BROWSER.json');
assert(!retain || output === canonical, '--retain requires the example-specific canonical report');
assert(retain || !output.startsWith(phase + path.sep), 'Ordinary output must stay outside retained phase evidence');
const captures = retain ? path.join(phase, 'browser-captures/checklist') : output + '.captures';
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-checklist-'));
const staged = path.join(scratch, 'captures');
fs.mkdirSync(staged);
const python = process.env.CV_FOCUS_PYTHON || path.join(root, '.venv/bin/python');
const playwright = process.env.CV_FOCUS_PLAYWRIGHT || `${os.homedir()}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`;
const chromium = process.env.CV_FOCUS_CHROMIUM || `${os.homedir()}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const env = {...process.env, PYTHONPATH:[scratch,path.join(root,'src'),path.join(root,'examples/bootstrap5')].join(path.delimiter),
    DJANGO_SETTINGS_MODULE:'checklist_settings'};
fs.writeFileSync(path.join(scratch, 'checklist_settings.py'),
    `from project.settings import *\nDATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ${JSON.stringify(path.join(scratch,'db.sqlite3'))}}}\n`);
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const sourceFiles = [
    'examples/bootstrap5/formsets/models.py','examples/bootstrap5/formsets/views.py',
    'examples/bootstrap5/formsets/urls.py','examples/bootstrap5/formsets/seed.py',
    'examples/bootstrap5/formsets/tests.py','examples/bootstrap5/formsets/migrations/0003_checklist_checklistitem.py',
    'examples/bootstrap5/project/features.py','examples/bootstrap5/project/tests.py',
    'examples/bootstrap5/project/settings.py','docs/reference/formsets.md',
    'src/crud_views/lib/formsets/compact.py','src/crud_views/lib/formsets/render_tree.py',
    'src/crud_views/static/crud_views/css/formset.css','src/crud_views/static/crud_views/js/formset.js',
    'src/crud_views/templates/crud_views/formsets/formset.html',
    '.planning/phases/06.26-issue-351/06.26-checklist-browser.cjs',
];
const record = {revision:cp.execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
    started:new Date().toISOString(), humanReview:'pending', temporaryRoot:scratch,
    sourceHashes:Object.fromEntries(sourceFiles.map(f=>[f,hash(path.join(root,f))])),
    commands:[], checks:[], requests:[], captures:[], pageErrors:[], failedAssets:[]};
const developerDb = path.join(root,'examples/bootstrap5/db.sqlite3');
record.developerDbBefore = fs.existsSync(developerDb) ? hash(developerDb) : null;
const check = (name, condition, detail) => { record.checks.push({name,passed:!!condition,detail}); assert(condition,name); };
function manage(...cmd) {
    record.commands.push([python,'examples/bootstrap5/manage.py',...cmd]);
    return cp.execFileSync(python,['examples/bootstrap5/manage.py',...cmd],{cwd:root,env,encoding:'utf8'});
}
function stored(title) {
    return JSON.parse(manage('shell','-c',`import json; from formsets.models import Checklist; c=Checklist.objects.get(title=${JSON.stringify(title)}); print(json.dumps(list(c.items.values_list("label","done"))))`).trim().split('\n').at(-1));
}
const rows = page => page.locator('.cv-formset-row-compact');
const label = row => row.locator('input[name$="-label"]');
const done = row => row.locator('input[name$="-done"]');
const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));
async function save(page) {
    const request = page.waitForRequest(r=>r.method()==='POST' && r.url().includes('/checklist/'));
    await page.locator('button[type=submit]').filter({hasText:'Save'}).click();
    const post = await request;
    record.requests.push({kind:'save',url:post.url(),fields:[...new URLSearchParams(post.postData()).keys()]});
    await page.waitForURL('**/formsets/checklist/');
}
async function capture(page,name) {
    await page.screenshot({path:path.join(staged,name),fullPage:true});
    record.captures.push({path:path.relative(root,path.join(captures,name)),sha256:hash(path.join(staged,name))});
}
async function inspect(page,width) {
    const geometry = await page.evaluate(()=>{
        const form = document.querySelector('input[name="title"]').form;
        const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
        const names=[...form.querySelectorAll('[name]')].map(e=>e.name);
        const inputs=[...form.querySelectorAll('input[name$="-done"],input[name$="-label"]')];
        return {forms:document.querySelectorAll('form').length, nestedForms:form.querySelectorAll('form').length,
            editorForms:[...document.forms].filter(f=>f.querySelector('input[name="title"]')).length,
            uniqueIds:new Set(ids).size===ids.length,
            uniqueNames:new Set(names).size===names.length,
            associations:inputs.every(e=>form.querySelectorAll(`label[for="${e.id}"]`).length===1),
            labels:[...form.querySelectorAll('.form-check-label')].map(e=>({width:e.getBoundingClientRect().width,
                clip:getComputedStyle(e).clipPath,position:getComputedStyle(e).position})),
            headings:[...form.querySelectorAll('.cv-formset-compact-headings')].map(e=>getComputedStyle(e).display),
            overflow:[...form.querySelectorAll('.cv-formset-compact-fields')].some(e=>e.scrollWidth>e.clientWidth+1),
            css:[...document.styleSheets].map(e=>e.href).filter(Boolean),
            js:[...document.scripts].map(e=>e.src).filter(Boolean)};
    });
    check(`${width}:single editor form and unique identities`,geometry.editorForms===1 && geometry.nestedForms===0 && geometry.uniqueIds && geometry.uniqueNames,geometry);
    check(`${width}:associated labels and no compact overflow`,geometry.associations && !geometry.overflow,geometry);
    check(`${width}:assets loaded`,geometry.css.some(s=>s.includes('formset.css')) && geometry.js.some(s=>s.includes('formset.js')),geometry);
    check(`${width}:responsive labels`,geometry.labels.length>0 && geometry.labels.every(l=>width<768 ? l.width>1 : l.width<=1),geometry.labels);
    check(`${width}:shared headings`,geometry.headings.length===1 && geometry.headings[0]===(width<768?'none':'flex'),geometry.headings);
}

let server, browser, logFd, failed;
(async()=>{
    try {
        manage('migrate','--noinput'); manage('seed');
        const probe=net.createServer();
        await new Promise(resolve=>probe.listen(0,'127.0.0.1',resolve));
        const port=probe.address().port;
        await new Promise(resolve=>probe.close(resolve));
        const base=`http://127.0.0.1:${port}`;
        record.base=base;
        logFd=fs.openSync(path.join(scratch,'server.log'),'w');
        record.commands.push([python,'examples/bootstrap5/manage.py','runserver',`127.0.0.1:${port}`,'--noreload']);
        server=cp.spawn(python,['examples/bootstrap5/manage.py','runserver',`127.0.0.1:${port}`,'--noreload'],{cwd:root,env,stdio:['ignore',logFd,logFd]});
        let ready=false;
        for(let i=0;i<100;i++) { try { ready=(await fetch(base+'/login/')).ok; } catch {} if(ready) break; await delay(150); }
        check('server ready',ready);
        browser=await require(playwright).chromium.launch({headless:true,executablePath:chromium,args:['--no-sandbox']});
        record.runtime={node:process.version,playwright:require(playwright+'/package.json').version,chromium:browser.version(),
            python:cp.execFileSync(python,['-c','import sys,importlib.metadata as m,json; print(json.dumps({"python":sys.version.split()[0],**{p:m.version(p) for p in ["Django","django-crispy-forms","crispy-bootstrap5"]}}))'],{encoding:'utf8'}).trim()};
        for(const width of [390,1280]) {
            const context=await browser.newContext({viewport:{width,height:900}});
            const page=await context.newPage();
            page.on('pageerror',e=>record.pageErrors.push(String(e)));
            page.on('response',r=>{if(r.status()>=400 && /\.(css|js)(\?|$)/.test(r.url())) record.failedAssets.push({url:r.url(),status:r.status()});});
            await page.goto(base+'/login/');
            await page.locator('[name=username]').fill(width===390?'alice':'bob');
            await page.locator('[name=password]').fill(width===390?'alice':'bob');
            await page.getByRole('button',{name:'Log In',exact:true}).click();
            await page.waitForLoadState('networkidle');
            await page.goto(base+'/formsets/questionnaire/');
            await page.getByRole('link',{name:'Checklist example',exact:true}).click();
            check(`${width}:landing link`,page.url()===base+'/formsets/checklist/');
            await page.locator('a[cv-key=create]').click();
            const title=`Browser checklist ${width}`;
            await page.locator('[name=title]').fill(title);
            await label(rows(page).first()).fill('Review release notes');
            await label(rows(page).first()).press('Tab');
            check(`${width}:Tab focuses native checkbox`,await done(rows(page).first()).evaluate(e=>document.activeElement===e));
            const focus=await done(rows(page).first()).evaluate(e=>({visible:e.matches(':focus-visible'),shadow:getComputedStyle(e).boxShadow,outline:getComputedStyle(e).outlineStyle}));
            check(`${width}:visible focus`,focus.visible && (focus.shadow!=='none'||focus.outline!=='none'),focus);
            await page.keyboard.press('Space');
            check(`${width}:Space checks native checkbox`,await done(rows(page).first()).isChecked());
            await inspect(page,width); await capture(page,`${width}-initial.png`);
            const responsePromise=page.waitForResponse(r=>r.url().includes('template=') && r.request().method()==='GET');
            await rows(page).last().locator('.cv-form-ctrl-add').click();
            const response=await responsePromise, fragment=await response.json();
            record.requests.push({kind:'fragment',url:response.url(),status:response.status(),rows:fragment.rows});
            check(`${width}:real authorized fragment`,response.status()===200 && fragment.rows.length===1);
            await label(rows(page).nth(1)).fill('Publish release');
            await inspect(page,width); await capture(page,`${width}-added.png`);
            await save(page);
            check(`${width}:mixed values persisted`,JSON.stringify(stored(title))===JSON.stringify([['Review release notes',true],['Publish release',false]]));
            await page.getByRole('link',{name:title,exact:true}).click();
            const updateUrl=page.url(); record.requests.push({kind:'edit',url:updateUrl});
            check(`${width}:reload checked and unchecked`,await done(rows(page).nth(0)).isChecked() && !await done(rows(page).nth(1)).isChecked());
            await done(rows(page).first()).uncheck(); await done(rows(page).nth(1)).check();
            await save(page);
            check(`${width}:omission persisted False`,JSON.stringify(stored(title))===JSON.stringify([['Review release notes',false],['Publish release',true]]));
            await page.goto(updateUrl);
            check(`${width}:reload omitted False`,!await done(rows(page).first()).isChecked() && await done(rows(page).nth(1)).isChecked());
            const row=rows(page).first();
            await row.locator('.cv-form-ctrl-delete').click();
            check(`${width}:mark delete`,await row.locator('input[name$="-DELETE"]').inputValue()==='1');
            await row.locator('.cv-form-ctrl-delete').click();
            check(`${width}:unmark delete`,await row.locator('input[name$="-DELETE"]').inputValue()!=='1');
            await row.locator('.cv-form-ctrl-delete').click(); await save(page);
            check(`${width}:deletion persisted`,JSON.stringify(stored(title))===JSON.stringify([['Publish release',true]]));
            await page.goto(updateUrl);
            await label(rows(page).first()).evaluate(e=>e.removeAttribute('maxlength'));
            await label(rows(page).first()).fill('x'.repeat(201));
            await page.locator('button[type=submit]').filter({hasText:'Save'}).click();
            await page.locator('.invalid-feedback').first().waitFor();
            check(`${width}:invalid checked state retained`,await done(rows(page).first()).isChecked());
            check(`${width}:server validation atomic`,JSON.stringify(stored(title))===JSON.stringify([['Publish release',true]]));
            await inspect(page,width); await capture(page,`${width}-invalid.png`);
            await label(rows(page).first()).fill('Publish corrected release'); await save(page);
            check(`${width}:corrected save`,JSON.stringify(stored(title))===JSON.stringify([['Publish corrected release',true]]));
            await page.goto(updateUrl);
            if(width===1280) for(const boundary of [767,768]) { await page.setViewportSize({width:boundary,height:900}); await inspect(page,boundary); await capture(page,`${boundary}-labels.png`); }
            await context.close();
        }
        check('no page errors',record.pageErrors.length===0,record.pageErrors);
        check('no failed assets',record.failedAssets.length===0,record.failedAssets);
    } catch(error) { failed=error; record.error=String(error.stack); console.error(error); }
    finally {
        const cleanupError = (stage,error) => {
            (record.cleanupErrors ??= []).push(`${stage}: ${error.stack || error}`);
            failed ??= error;
            record.error ??= String(error.stack || error);
            console.error(stage,error);
        };
        try { if(browser) await browser.close(); } catch(error) { cleanupError('browser close',error); }
        try {
            if(server && server.exitCode===null) { const exit=new Promise(resolve=>server.once('exit',(code,signal)=>resolve({code,signal}))); server.kill('SIGTERM'); record.serverExit=await exit; }
        } catch(error) { cleanupError('server termination',error); }
        try { if(logFd!==undefined) fs.closeSync(logFd); } catch(error) { cleanupError('log close',error); }
        try {
            record.developerDbAfter=fs.existsSync(developerDb)?hash(developerDb):null;
            check('developer database unchanged',record.developerDbBefore===record.developerDbAfter);
        } catch(error) { cleanupError('developer database check',error); }
        // Hold this small capture set in memory so cleanup finishes before retained publication.
        let images=[];
        try { if(!failed) images=fs.readdirSync(staged).map(file=>[file,fs.readFileSync(path.join(staged,file))]); }
        catch(error) { cleanupError('capture staging',error); }
        try { fs.rmSync(scratch,{recursive:true,force:true}); } catch(error) { cleanupError('temporary removal',error); }
        record.cleanup={serverReaped:!server||server.exitCode!==null||server.signalCode!==null,temporaryRemoved:!fs.existsSync(scratch)};
        record.finished=new Date().toISOString();
        try {
            if(!failed) {
                fs.mkdirSync(captures,{recursive:true});
                for(const [file,data] of images) fs.writeFileSync(path.join(captures,file),data);
            }
        } catch(error) { cleanupError('capture publication',error); }
        let destination=failed?path.join(os.tmpdir(),'checklist-example-failed.json'):output;
        record.passed=!failed;
        try {
            fs.mkdirSync(path.dirname(destination),{recursive:true});
            fs.writeFileSync(destination,JSON.stringify(record,null,2)+'\n');
        } catch(error) {
            cleanupError('report publication',error);
            record.passed=false;
            destination=path.join(os.tmpdir(),'checklist-example-failed.json');
            try { fs.writeFileSync(destination,JSON.stringify(record,null,2)+'\n'); }
            catch(diagnosticError) { cleanupError('diagnostic publication',diagnosticError); }
        }
        console.log(JSON.stringify({output:destination,checks:record.checks.length,captures:record.captures.length,cleanup:record.cleanup}));
        if(failed) process.exitCode=1;
    }
})();
