// Focused, authenticated observation of one application-owned marked Select. No installs.
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const net = require('node:net');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
process.chdir(root);
const phase = '.planning/phases/06.25-issue-349';
const output = `${phase}/06.25-browser-results.json`;
const python = process.env.CV_FOCUS_PYTHON || `${root}/.venv/bin/python`;
const playwright = process.env.CV_FOCUS_PLAYWRIGHT || '/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
const chromium = process.env.CV_FOCUS_CHROMIUM || '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
const port = Number(process.env.CV_CONDITIONAL_PORT || '8144');
assert(Number.isInteger(port) && port >= 1024 && port <= 65535 && port !== 8143);
const base = `http://127.0.0.1:${port}`;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const filesIn = dir => fs.readdirSync(dir, {withFileTypes:true}).flatMap(e =>
    e.isDirectory() ? filesIn(`${dir}/${e.name}`) : [`${dir}/${e.name}`]);
const sourceFiles = [
    'tests/browser/conditional_formsets_server.py', 'tests/browser/compact-widget-compatibility.cjs',
    'tests/browser/conditional-formsets.cjs', `${phase}/browser-captures/.gitignore`,
    'docs/reference/formsets.md', 'tests/test1/test_formsets_compact_docs.py', 'package-lock.json',
    ...filesIn('src/crud_views/lib/formsets'), ...filesIn('src/crud_views/templates/crud_views/formsets'),
    ...filesIn('tests/browser/templates/conditional_formsets'),
    'src/crud_views/static/crud_views/css/formset.css',
    ...['formset', 'conditional', 'toggle', 'modal', 'adapters'].map(n => `src/crud_views/static/crud_views/js/${n}.js`),
].filter(f => !f.includes('__pycache__') && fs.existsSync(f));
const hashes = () => Object.fromEntries(sourceFiles.sort().map(f => [f,digest(f)]));
const legacyIds = ['compact-lifecycle', 'compact-presentation', 'tracer', 'fragment-raw-balance',
    'inline-file-clear-unchanged', 'native-reset-user-default', 'native-reset-user-cancelled',
    'disabled-same-value-ownership', 'conditional-focus', 'lifecycle', 'tampered-post', 'late-init',
    'gap-capability', 'gap-ambiguity'].sort();
const record = {date:new Date().toISOString(), command:[process.execPath, ...process.argv.slice(1)],
    environment:{CV_FOCUS_PYTHON:python,CV_FOCUS_PLAYWRIGHT:playwright,CV_FOCUS_CHROMIUM:chromium},
    revision:cp.execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
    sourceHashes:hashes(), runtime:{node:process.version,nodePath:process.execPath}, hosts:[],
    widths:[], captures:[], assertions:[], pageErrors:[], humanReview:'pending', completed:false, passed:false};
function check(id, value, detail) {
    record.assertions.push({id,passed:Boolean(value),detail});
    assert(value, `${id}: ${JSON.stringify(detail)}`);
}
async function load(page, url) {
    const response = await page.goto(base + url);
    check(`protected-editor:${url}`, response.status() === 200 && page.url() === base + url,
        {status:response.status(),url:page.url()});
    await page.waitForFunction(() => typeof window.cv?.initFormsets === 'function');
}
async function startHost(browser, enabled, work) {
    await new Promise((resolve,reject) => {const probe=net.createServer();probe.once('error',reject);
        probe.listen(port,'127.0.0.1',()=>probe.close(resolve));});
    const env = {...process.env, PYTHONPATH:`${root}/src:${root}`, PYTHONUNBUFFERED:'1', CV_CONDITIONAL_PORT:String(port)};
    delete env.CV_COMPACT_WIDGET_FIXTURE;
    if (enabled) env.CV_COMPACT_WIDGET_FIXTURE='1';
    const host = {enabled, authentication:null, cleanup:{}};record.hosts.push(host);
    const child=cp.spawn(python,['tests/browser/conditional_formsets_server.py'],{cwd:root,env,stdio:['ignore','pipe','pipe']});
    let log='', context, spawnError;
    child.stdout.on('data',b=>{log+=b;});child.stderr.on('data',b=>{log+=b;});
    child.on('error',e=>{spawnError=e;});
    const exited=new Promise(resolve=>child.once('exit',(code,signal)=>resolve({code,signal})));
    try {
        let ready=false;
        for(let i=0;i<150;i++) {
            if(spawnError) throw spawnError;
            assert(child.exitCode===null && child.signalCode===null,log);
            try {ready=(await fetch(`${base}/cases/`,{signal:AbortSignal.timeout(500)})).ok;} catch {}
            if(ready) break;
            await delay(100);
        }
        assert(ready,`readiness timeout: ${log}`);
        host.temporary=log.split('\n').map(l=>{try{return JSON.parse(l);}catch{return null;}}).find(x=>x?.temporary)?.temporary;
        assert(host.temporary && fs.existsSync(host.temporary));
        context=await browser.newContext();
        check(`fresh-context:${enabled}`,(await context.cookies()).length===0);
        const signin=await context.request.get(`${base}/signin/`);
        host.authentication={status:signin.status(),...await signin.json()};
        check(`signin:${enabled}`,signin.status()===200 && host.authentication.authenticated===true);
        const cases=await (await context.request.get(`${base}/cases/`)).json();
        host.caseIds=[...new Set(cases.map(c=>c.id))].sort();
        check(`case-ids:${enabled}`,JSON.stringify(host.caseIds)===JSON.stringify([...legacyIds,...(enabled?['compact-widget']:[])].sort()),host.caseIds);
        // Every legacy id comes from the old runner's REQUIRED map; do not import its executable main.
        const oldSource=fs.readFileSync('tests/browser/conditional-formsets.cjs','utf8');
        check(`legacy-required-map:${enabled}`,legacyIds.every(id=>oldSource.includes(`'${id}':`)));
        const page=await context.newPage();
        const legacy=cases.find(c=>c.id==='compact-presentation');
        await load(page,legacy.url);
        const stock=await page.locator('fieldset[cv-data-formset-key="scores"] select[name$="-taster"]').first()
            .evaluate(el=>({choices:[...el.options].filter(o=>o.value).map(o=>o.textContent),marked:!!el.querySelector('[data-beans]')}));
        check(`legacy-stock:${enabled}`,stock.choices.length>0 && !stock.marked,stock);
        await page.close();
        await work(context,cases);
    } finally {
        if(context) await context.close();
        if(child.exitCode===null && child.signalCode===null) child.kill('SIGTERM');
        const exit=await Promise.race([exited,delay(5000).then(()=>null)]);
        if(!exit) {child.kill('SIGKILL');await exited;}
        host.cleanup={exit,reaped:child.exitCode!==null || child.signalCode!==null,
            temporaryRemoved:!!host.temporary && !fs.existsSync(host.temporary)};
        check(`cleanup:${enabled}`,!!exit && exit.code===0 && host.cleanup.reaped && host.cleanup.temporaryRemoved,host.cleanup);
    }
}
async function measure(page,c,prefix) {
    return page.evaluate(({c,prefix})=>{
        const set=document.querySelector('fieldset[cv-data-formset-key="scores"]');
        const row=[...set.querySelectorAll('.cv-formset-row')].find(r=>r.getAttribute('cv-data-formset-form-prefix')===prefix);
        const el=row.querySelector('select[name$="-taster"]');
        const labels=[...document.querySelectorAll('label')].filter(l=>l.htmlFor===el.id);
        const label=labels[0], style=label && getComputedStyle(label), desktop=innerWidth>=768;
        const option=[...el.options].find(o=>o.value===String(c.taster));
        const heading=set.querySelector(':scope > .cv-formset-content > .cv-formset-compact-headings');
        const help=row.querySelector('.form-text');
        const visible=e=>!!e && e.getClientRects().length>0 && getComputedStyle(e).display!=='none';
        const errors=[...row.querySelectorAll('.invalid-feedback')].filter(e=>e.id.includes(el.id));
        return {prefix,id:el.id,name:el.name,value:el.value,option:option && {value:option.value,label:option.textContent,beans:option.dataset.beans},
            identity:el.id===`id_${el.name}` && el.name===`${prefix}-taster` && document.querySelectorAll(`[id="${el.id}"]`).length===1 && document.querySelectorAll(`[name="${el.name}"]`).length===1,
            label:labels.length===1 && !!label.textContent.trim() && style.display!=='none' && style.visibility!=='hidden' && !label.hasAttribute('aria-hidden') &&
                (desktop?style.position==='absolute'&&style.width==='1px':style.position==='static'&&label.getBoundingClientRect().height>1),
            heading:set.querySelectorAll('.cv-formset-compact-headings').length===1 && heading.textContent.includes(label.textContent.replace('*','').trim()) && (visible(heading)===desktop),
            help:visible(help) && help.scrollWidth<=help.clientWidth+1,
            overflow:document.documentElement.scrollWidth<=document.documentElement.clientWidth,
            disabledOverall:row.querySelector('[name$="-overall"]').disabled,
            optionalSweetness:!row.querySelector('[name$="-sweetness"]').required,
            errors:errors.map(e=>({id:e.id,text:e.textContent.trim(),visible:visible(e)})),
            deleteValue:row.querySelector('[name$="-DELETE"]')?.value};
    },{c,prefix});
}
async function observe(page,c,width,state,prefix) {
    const m=await measure(page,c,prefix);
    check(`${width}:${state}:metadata`,m.option?.beans==='1' && m.option.value===String(c.taster) && m.option.label===c.taster_label,m);
    check(`${width}:${state}:layout`,m.identity&&m.label&&m.heading&&m.help&&m.overflow&&m.disabledOverall&&m.optionalSweetness,m);
    return m;
}
async function capture(page,width,state) {
    const file=`${phase}/browser-captures/${width}-${state}.png`;
    assert.equal(cp.spawnSync('git',['check-ignore','--no-index','--quiet',file]).status,1,'Named capture must be trackable');
    await page.screenshot({path:file,fullPage:true});
    record.captures.push({path:file,width,state,sha256:digest(file),trackable:true});
}
async function marked(context,cases) {
    const c=cases.find(c=>c.id==='compact-widget');assert(c);
    record.widgetClass=c.widget_class;record.pageURL=base+c.url;
    for(const width of [390,1280]) {
        const page=await context.newPage();page.setDefaultTimeout(12000);
        page.on('pageerror',e=>record.pageErrors.push(e.message));
        await page.setViewportSize({width,height:900});await load(page,c.url);
        const set=page.locator('fieldset[cv-data-formset-key="scores"]');
        const first=set.locator('select[name$="-taster"]').first();
        const prefix=await first.evaluate(el=>el.closest('.cv-formset-row').getAttribute('cv-data-formset-form-prefix'));
        const result={width,initial:await observe(page,c,width,'initial',prefix)};record.widths.push(result);
        await first.focus();await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');
        check(`${width}:keyboard-focus`,await first.evaluate(el=>document.activeElement===el));
        await capture(page,width,'initial');
        await first.selectOption('');
        const invalidResponse=page.waitForResponse(r=>r.request().method()==='POST' && r.url()===base+c.url);
        await Promise.all([
            page.waitForNavigation({waitUntil:'load'}),
            page.locator('#editor').evaluate(form=>HTMLFormElement.prototype.submit.call(form)),
        ]);
        const invalid=await invalidResponse;
        check(`${width}:invalid-status`,invalid.status()===422,{status:invalid.status(),url:invalid.url()});
        result.invalid=await observe(page,c,width,'invalid',prefix);
        check(`${width}:owned-error`,result.invalid.value===''&&result.invalid.errors.some(e=>e.visible&&e.text.length>0),result.invalid.errors);
        await capture(page,width,'invalid');
        const fragmentResponse=page.waitForResponse(r=>r.url().includes('template=') && r.request().method()==='GET');
        await set.locator(':scope > .cv-formset-content > .cv-formset-row > .cv-formset-form .cv-form-ctrl-add').last().click();
        const fragment=await fragmentResponse;assert.equal(fragment.status(),200);
        const body=await fragment.json();const added=body.rows[0];
        await page.waitForFunction(prefix=>!!document.querySelector(`[cv-data-formset-form-prefix="${prefix}"]`),added);
        result.fragment={status:fragment.status(),url:fragment.url(),prefix:added};
        result.added=await observe(page,c,width,'added',added);assert.notEqual(added,prefix);
        await capture(page,width,'added');
        const row=set.locator(`.cv-formset-row[cv-data-formset-form-prefix="${added}"]`);
        const remove=row.locator(':scope > .cv-formset-form .cv-form-ctrl-delete');
        await remove.click();result.deleted=await observe(page,c,width,'deleted',added);
        check(`${width}:delete`,result.deleted.deleteValue==='1');
        await remove.click();result.unmarked=await observe(page,c,width,'unmarked',added);
        check(`${width}:unmark`,result.unmarked.deleteValue!=='1');
        await page.close();
    }
}
async function main() {
    let browser;
    try {
        for(const file of [python,playwright,chromium]) assert(fs.existsSync(file),file);
        Object.assign(record.runtime,JSON.parse(cp.execFileSync(python,['-c',
            'import sys,json,django,crispy_forms;print(json.dumps({"python":sys.version,"django":django.get_version(),"crispy":crispy_forms.__version__}))'],{encoding:'utf8'})),
            {pythonPath:fs.realpathSync(python),playwright:require(`${playwright}/package.json`).version,chromiumPath:fs.realpathSync(chromium)});
        browser=await require(playwright).chromium.launch({headless:true,executablePath:chromium,args:['--no-sandbox']});
        record.runtime.chromium=browser.version();
        await startHost(browser,false,async()=>{});
        await startHost(browser,true,marked);
        check('no-page-errors',record.pageErrors.length===0,record.pageErrors);
        check('all-widths-and-captures',record.widths.length===2 && record.captures.length===6);
        check('unchanged-measured-source',JSON.stringify(record.sourceHashes)===JSON.stringify(hashes()));
        record.completed=true;record.passed=true;
    } catch(error) {record.error=error.stack;throw error;}
    finally {
        if(browser) await browser.close();
        fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
    }
    console.log(`PASS: ${record.assertions.length} assertions; six trackable captures; human review pending`);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
