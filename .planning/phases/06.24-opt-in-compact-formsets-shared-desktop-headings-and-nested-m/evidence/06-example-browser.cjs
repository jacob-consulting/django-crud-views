// Replay from repository root: node .planning/phases/06.24-*/evidence/06-example-browser.cjs
// Uses installed runtimes only; the disposable settings/database/server are removed in finally.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const net = require('node:net');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = cp.execFileSync('git', ['rev-parse', '--show-toplevel'], {encoding:'utf8'}).trim();
const phase = path.dirname(__dirname);
const captureDir = path.join(phase, 'browser-captures/compact-example');
const python = path.join(root, '.venv/bin/python');
const playwrightPath = process.env.CV_FOCUS_PLAYWRIGHT || '/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
const chromiumPath = process.env.CV_FOCUS_CHROMIUM || '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const record = {started:new Date().toISOString(), command:[process.execPath, __filename],
    revision:cp.execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
    humanReview:'pending', assertions:[], captures:[], fragments:[], assets:[], pageErrors:[], cleanup:{}, passed:false};
const check = (name, condition, measurements={}) => {
    record.assertions.push({name, passed:!!condition, measurements}); assert(condition,name);
};
let temporary, server, browser, serverExit;
async function main() {
    try {
        for (const file of [python, playwrightPath, chromiumPath]) assert(fs.existsSync(file), `Missing installed runtime ${file}`);
        record.runtime = {node:process.version, nodePath:process.execPath, pythonPath:python, playwrightPath, chromiumPath,
            playwright:require(path.join(playwrightPath,'package.json')).version,
            ...JSON.parse(cp.execFileSync(python,['-c','import sys,json,django; print(json.dumps({"python":sys.version,"django":django.get_version()}))'],{encoding:'utf8'}))};
        const sources = ['examples/bootstrap5/formsets/views.py','examples/bootstrap5/formsets/tests.py',
            'examples/bootstrap5/project/features.py','examples/bootstrap5/project/tests.py','docs/reference/formsets.md',
            'src/crud_views/lib/formsets/inline_formset.py','src/crud_views/lib/formsets/compact.py',
            'src/crud_views/static/crud_views/css/formset.css','src/crud_views/static/crud_views/js/formset.js',
            'src/crud_views/templates/crud_views/formsets/formset.html', 'examples/bootstrap5/project/templates/project/base.html'];
        record.sourceHashes = Object.fromEntries(sources.map(file=>[file,digest(path.join(root,file))]));
        record.sourceHashes[path.relative(root,__filename)] = digest(__filename);
        temporary = fs.mkdtempSync(path.join(os.tmpdir(),'cv-compact-example-'));
        const settings = 'from project.settings import *\nDATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ' + JSON.stringify(path.join(temporary,'demo.sqlite3')) + '}}\nALLOWED_HOSTS = ["127.0.0.1", "localhost"]\n';
        fs.writeFileSync(path.join(temporary,'compact_example_settings.py'),settings);
        const env = {...process.env, PYTHONPATH:`${root}/src:${root}/examples/bootstrap5:${temporary}`,
            DJANGO_SETTINGS_MODULE:'compact_example_settings', PYTHONUNBUFFERED:'1'};
        record.setup = {settings, PYTHONPATH:env.PYTHONPATH, DJANGO_SETTINGS_MODULE:env.DJANGO_SETTINGS_MODULE, commands:[]};
        for (const args of [['migrate','--noinput'],['seed']]) {
            const command = [python, 'examples/bootstrap5/manage.py', ...args];
            const result = cp.spawnSync(command[0],command.slice(1),{cwd:root,env,encoding:'utf8'});
            record.setup.commands.push({command,exitCode:result.status,output:result.stdout+result.stderr});
            assert.equal(result.status,0);
        }
        const port = await new Promise((resolve,reject)=>{const probe=net.createServer();probe.once('error',reject);probe.listen(0,'127.0.0.1',()=>{const p=probe.address().port;probe.close(()=>resolve(p));});});
        const base = `http://127.0.0.1:${port}`;
        record.base=base;
        record.setup.serverCommand=[python,'examples/bootstrap5/manage.py','runserver',`127.0.0.1:${port}`,'--noreload'];
        server=cp.spawn(python,record.setup.serverCommand.slice(1),{cwd:root,env,stdio:['ignore','pipe','pipe']});
        record.serverLog='';server.stdout.on('data',d=>record.serverLog+=d);server.stderr.on('data',d=>record.serverLog+=d);
        serverExit=new Promise(resolve=>server.once('exit',(code,signal)=>resolve({code,signal})));
        let ready=false;
        for(let i=0;i<100;i++){try{ready=(await fetch(`${base}/login/`)).ok;}catch{}if(ready)break;await delay(100);}
        assert(ready,'server ready');
        browser=await require(playwrightPath).chromium.launch({headless:true,executablePath:chromiumPath,args:['--no-sandbox']});
        record.runtime.chromium=browser.version();
        const page=await browser.newPage({viewport:{width:1280,height:900},ignoreHTTPSErrors:true});
        const contextAction=async name=>{
            await page.locator('.card-header').getByRole('button',{name:'More actions',exact:true}).click();
            const link=page.locator('.card-header').getByRole('link',{name,exact:true});
            check(name+' menu label is visible',await link.isVisible());
            await link.click();
        };
        page.on('pageerror',error=>record.pageErrors.push(String(error)));
        page.on('response',response=>{if(/bootstrap|formset\.(css|js)/.test(response.url())) record.assets.push({url:response.url(),status:response.status()});});
        await page.goto(`${base}/login/`);
        await page.locator('[name=username]').fill('alice');await page.locator('[name=password]').fill('alice');
        await Promise.all([page.waitForURL(base+'/'),page.getByRole('button',{name:'Log In',exact:true}).click()]);
        await page.locator('.card').filter({hasText:'Compare classic and compact inline formsets'}).getByRole('link',{name:'Open',exact:true}).click();
        await contextAction('Create compact');
        await page.waitForLoadState('networkidle');
        check('home catalog reaches compact create',new URL(page.url()).pathname.endsWith('/create-compact/'),{url:page.url()});
        const form=()=>page.locator('form.cv-form');
        await form().locator('[name=title]').fill('Browser compact example');
        await form().locator('input[name$="-text"]').fill('First browser question');
        await form().locator('input[name$="-label"]').fill('First browser choice');
        await Promise.all([page.waitForURL(base+'/formsets/questionnaire/'),form().locator('button[type=submit]').first().click()]);
        const tableRow=page.locator('table tbody tr').filter({hasText:'Browser compact example'});
        await tableRow.getByRole('link',{name:'Edit compact',exact:true}).click();
        await page.waitForLoadState('networkidle');
        const compactURL=page.url();record.compactURL=compactURL;
        check('create redirect and persisted nested values',await form().locator('input[name$="-label"]').first().inputValue()==='First browser choice');
        const rootRows=()=>form().locator('fieldset[cv-data-formset-key="questions"] > .cv-formset-content > .cv-formset-row');
        const add = async (button, name) => {
            const before=await form().locator('.cv-formset-row').count();
            const responsePromise=page.waitForResponse(r=>r.url().includes('template=')&&r.request().method()==='GET');
            await button.click();const response=await responsePromise;const data=await response.json();
            record.fragments.push({name,url:response.url(),status:response.status(),rows:data.rows});
            check(name+' successful HTTP fragment',response.status()===200&&data.html.includes('cv-formset-row-compact'));
            await page.waitForFunction(n=>document.querySelectorAll('form.cv-form .cv-formset-row').length>n,before);
        };
        await add(rootRows().last().locator(':scope > .cv-formset-form .cv-form-ctrl-add').first(),'new question');
        const newQuestion=rootRows().last();
        await newQuestion.locator('input[name$="-text"]').fill('Added browser question');
        await newQuestion.locator('input[name$="-label"]').first().fill('Initial added-question choice');
        await add(newQuestion.locator('.cv-form-ctrl-add').last(),'choice under nonfirst question');
        await rootRows().last().locator('input[name$="-label"]').last().fill('AJAX nested choice');
        const identities=await form().evaluate(el=>({ids:[...el.querySelectorAll('[id]')].map(n=>n.id),prefixes:[...el.querySelectorAll('.cv-formset-row')].map(n=>n.getAttribute('cv-data-formset-form-prefix'))}));
        check('unique IDs and prefixes after actual additions',new Set(identities.ids).size===identities.ids.length&&new Set(identities.prefixes).size===identities.prefixes.length,identities);
        const owned=await rootRows().last().evaluate(el=>({text:el.querySelector('input[name$="-text"]').value,choices:[...el.querySelectorAll('input[name$="-label"]')].map(n=>n.value),compact:el.classList.contains('cv-formset-row-compact')}));
        check('added child remains inside owning compact question',owned.compact&&owned.text==='Added browser question'&&owned.choices.includes('AJAX nested choice'),owned);
        const firstRow=rootRows().first();const deletion=firstRow.locator(':scope > .cv-formset-form input[name$="-DELETE"]');
        await firstRow.locator(':scope > .cv-formset-form .cv-form-ctrl-delete').click();
        check('delete marks containing question',await deletion.inputValue()==='1');
        await firstRow.locator(':scope > .cv-formset-form .cv-form-ctrl-delete').click();
        check('unmark retains containing question',await deletion.inputValue()==='');
        await rootRows().last().locator(':scope > .cv-formset-form .cv-form-ctrl-up').click();
        check('order moves containing question',await rootRows().nth(1).locator('input[name$="-text"]').inputValue()==='Added browser question');
        await rootRows().nth(1).locator(':scope > .cv-formset-form .cv-form-ctrl-down').click();
        check('order can restore question position',await rootRows().last().locator('input[name$="-text"]').inputValue()==='Added browser question');
        await Promise.all([page.waitForURL(base+'/formsets/questionnaire/'),form().locator('button[type=submit]').first().click()]);
        await page.locator('table tbody tr').filter({hasText:'Browser compact example'}).getByRole('link',{name:'Edit compact',exact:true}).click();
        await page.waitForLoadState('networkidle');
        const savedRow=rootRows().filter({has:page.locator('input[value="Added browser question"]')});
        check('saved AJAX question owns both choices',await savedRow.locator('input[value="AJAX nested choice"]').count()===1&&await savedRow.locator('input[value="Initial added-question choice"]').count()===1);
        fs.mkdirSync(captureDir,{recursive:true});
        const capture=async(name,width,compact,invalid=false)=>{
            await page.setViewportSize({width,height:900});await delay(120);
            const m=await form().evaluate(el=>{
                const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right};};
                return {form:rect(el),scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,
                    bootstrapRowDisplay:getComputedStyle(el.querySelector('.row')).display,
                    viewport:{width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth},
                    outsideViewport:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().width>1&&e.getBoundingClientRect().right>document.documentElement.clientWidth+1).slice(0,12).map(e=>({tag:e.tagName,classes:e.className,box:rect(e),text:e.textContent.trim().slice(0,150)})),
                    formsets:[...el.querySelectorAll('.cv-formset-content')].map(e=>({prefix:e.getAttribute('cv-data-formset-prefix'),width:e.clientWidth,scrollWidth:e.scrollWidth,box:rect(e)})),
                    fields:[...el.querySelectorAll('.cv-formset-compact-fields input:not([type=hidden])')].map(input=>{const label=el.querySelector(`label[for="${input.id}"]`);return {id:input.id,input:rect(input),column:rect(input.closest('[class*="col-md-"]')),grid:rect(input.closest('.cv-formset-compact-fields')),label:label&&rect(label),labelPosition:label&&getComputedStyle(label).position,clip:label&&getComputedStyle(label).clip};}),
                    headings:[...el.querySelectorAll('.cv-formset-compact-headings')].map(h=>({display:getComputedStyle(h).display,insideRow:!!h.closest('.cv-formset-row'),owner:h.closest('[cv-data-formset-key]').getAttribute('cv-data-formset-key')})),
                    children:[...el.querySelectorAll('.cv-formset-compact-child')].map(e=>({box:rect(e),parent:rect(e.closest('.cv-formset-row')),display:getComputedStyle(e).display})),
                    errors:[...el.querySelectorAll('.invalid-feedback')].map(e=>({text:e.textContent,display:getComputedStyle(e).display,owner:!!e.closest('.cv-formset-row-compact')})),
                    compactRows:el.querySelectorAll('.cv-formset-row-compact').length};
            });
            check(`${name}-${width} no horizontal page overflow`,m.viewport.scrollWidth===m.viewport.width,m.viewport);
            if(compact)check(`${name}-${width} no horizontal formset overflow`,m.formsets.every(f=>f.scrollWidth<=f.width+1&&f.box.x>=0&&f.box.right<=m.viewport.width+1),m);
            if(compact){
                check(`${name}-${width} associated labels`,m.fields.length>0&&m.fields.every(f=>f.label));
                check(`${name}-${width} responsive headings`,m.headings.length>0&&m.headings.every(h=>h.display===(width<768?'none':'flex')));
                // Child headings live inside their parent row, but outside their OWN row collection.
                const independent=await form().evaluate(el=>[...el.querySelectorAll('.cv-formset-compact-headings')].every(h=>h.closest('.cv-formset-row')?.getAttribute('cv-data-formset-prefix')!==h.closest('.cv-formset-content').getAttribute('cv-data-formset-prefix')));
                check(`${name}-${width} expanded owned choices`,m.children.length>0&&m.children.every(c=>c.display!=='none'&&c.box.width>0&&c.box.x>=c.parent.x&&c.box.right<=c.parent.right+1));
                check(`${name}-${width} headings outside own rows`,independent);
                if(width<768)check(`${name}-${width} full-width labelled fields`,m.fields.every(f=>f.label.width>1&&f.label.height>1&&f.labelPosition!=='absolute'&&Math.abs(f.column.width-f.grid.width)<2));
                else check(`${name}-${width} desktop label association retained`,m.fields.every(f=>f.label.width<=1&&f.label.height<=1));
                if(invalid)check(`${name}-${width} visible field-local error`,m.errors.some(e=>e.owner&&e.display!=='none'&&e.text.includes('at most 100')));
                await form().locator('input[name$="-text"]').first().focus();
                const focused=[];
                for(let i=0;i<5;i++){
                    focused.push(await page.evaluate(()=>({name:document.activeElement.name,classes:document.activeElement.className,outline:getComputedStyle(document.activeElement).outline,shadow:getComputedStyle(document.activeElement).boxShadow})));
                    await page.keyboard.press('Tab');
                }
                check(`${name}-${width} keyboard reaches input and row controls`,focused[0].name.endsWith('-text')&&['up','down','add','delete'].every(kind=>focused.some(f=>f.classes.includes('cv-form-ctrl-'+kind))),{focused});
            }else check(`${name}-${width} classic comparison has no compact rows`,m.compactRows===0);
            const file=path.join(captureDir,`${name}-${width}.png`);await form().screenshot({path:file});
            record.captures.push({path:path.relative(root,file),sha256:digest(file),width,url:page.url(),measurements:m});
        };
        for(const width of [1280,390])await capture('compact-saved',width,true);
        await contextAction('Edit classic');await page.waitForLoadState('networkidle');
        record.classicURL=page.url();
        check('visible classic action edits same records',await form().locator('input[value="AJAX nested choice"]').count()===1);
        for(const width of [1280,390])await capture('classic-saved',width,false);
        await contextAction('Edit compact');await page.waitForLoadState('networkidle');
        const invalidInput=form().locator('input[value="AJAX nested choice"]');const invalidName=await invalidInput.getAttribute('name');
        await invalidInput.evaluate(el=>{el.removeAttribute('maxlength');el.value='x'.repeat(101);});
        await form().evaluate(el=>el.noValidate=true);
        await Promise.all([page.waitForNavigation(),form().locator('button[type=submit]').first().click()]);
        check('server invalid POST redisplays submitted nested value',new URL(page.url()).pathname===new URL(compactURL).pathname&&await form().locator(`[name="${invalidName}"]`).inputValue()==='x'.repeat(101));
        for(const width of [1280,390])await capture('compact-invalid',width,true,true);
        await form().locator(`[name="${invalidName}"]`).fill('Corrected AJAX choice');
        await Promise.all([page.waitForURL(base+'/formsets/questionnaire/'),form().locator('button[type=submit]').first().click()]);
        await page.locator('table tbody tr').filter({hasText:'Browser compact example'}).getByRole('link',{name:'Edit classic',exact:true}).click();
        check('corrected save visible in classic editor',await form().locator('input[value="Corrected AJAX choice"]').count()===1);
        const db=JSON.parse(cp.execFileSync(python,['-c','import django,json;django.setup();from formsets.models import Questionnaire;q=Questionnaire.objects.get(title="Browser compact example");print(json.dumps({"id":q.pk,"questions":[{"id":x.pk,"text":x.text,"questionnaire":x.questionnaire_id,"choices":[{"label":c.label,"question":c.question_id} for c in x.choices.all()]} for x in q.questions.all()]}))'],{cwd:root,env,encoding:'utf8'}));
        check('database confirms nested persistence and ownership',db.questions.length===2&&db.questions.every(q=>q.questionnaire===db.id&&q.choices.every(c=>c.question===q.id))&&db.questions.find(q=>q.text==='Added browser question').choices.some(c=>c.label==='Corrected AJAX choice'),db);
        const assets=await page.evaluate(()=>({scripts:[...document.scripts].map(s=>s.src),styles:[...document.styleSheets].map(s=>s.href),jquery:typeof window.jQuery,bootstrap:typeof window.bootstrap}));
        check('actual Bootstrap and formset assets loaded',record.assets.some(a=>a.status===200&&a.url.includes('bootstrap.min.css'))&&record.assets.some(a=>a.status===200&&a.url.includes('/formset.css'))&&record.assets.some(a=>a.status===200&&a.url.includes('/formset.js'))&&assets.jquery==='function'&&assets.bootstrap==='object',assets);
        check('no browser page errors',record.pageErrors.length===0,record.pageErrors);
        record.passed=true;
    }catch(error){record.error=error.stack;process.exitCode=1;console.error(error);}
    finally{
        if(browser)await browser.close();
        if(server){server.kill('SIGTERM');record.cleanup.server=await serverExit;record.cleanup.reaped=true;}
        if(temporary){fs.rmSync(temporary,{recursive:true,force:true});record.cleanup.temporaryRemoved=!fs.existsSync(temporary);}
        record.completed=new Date().toISOString();
        fs.writeFileSync(path.join(__dirname,'06-example-browser.json'),JSON.stringify(record,null,2)+'\n');
        console.log(JSON.stringify({passed:record.passed,assertions:record.assertions.length,captures:record.captures.length,cleanup:record.cleanup}));
    }
}
main();
