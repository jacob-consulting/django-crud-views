// Authenticated stock-checkbox tracer. Existing dependencies only; disposable host/storage.
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const net = require('node:net');
const assert = require('node:assert/strict');
const test = require('node:test');
const root = path.resolve(__dirname, '../..');
process.chdir(root);
const args = process.argv.slice(2);
const option = (name, fallback) => args.includes(name) ? args[args.indexOf(name) + 1] : fallback;
const output = option('--output', '/tmp/compact-checkboxes.json');
const variant = option('--variant', 'current');
assert(['current', 'floor'].includes(variant));
const python = process.env.CV_FOCUS_PYTHON || `${root}/.venv/bin/python`;
const playwright = process.env.CV_FOCUS_PLAYWRIGHT || `${process.env.HOME}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`;
const chromium = process.env.CV_FOCUS_CHROMIUM || `${process.env.HOME}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const port = Number(process.env.CV_CONDITIONAL_PORT || '8144');
assert(Number.isInteger(port) && port >= 1024 && port <= 65535 && port !== 8143);
const base = `http://127.0.0.1:${port}`;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const legacyIds = ['compact-lifecycle', 'compact-presentation', 'tracer', 'fragment-raw-balance',
    'inline-file-clear-unchanged', 'native-reset-user-default', 'native-reset-user-cancelled',
    'disabled-same-value-ownership', 'conditional-focus', 'lifecycle', 'tampered-post', 'late-init',
    'gap-capability', 'gap-ambiguity'].sort();
const record = {date:new Date().toISOString(), command:[process.execPath,...process.argv.slice(1)], variant,
    revision:cp.execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
    environment:{python,playwright,chromium}, hosts:[], widths:[], assertions:[], assets:[], pageErrors:[],
    humanReview:'pending', completed:false, passed:false};
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
    delete env.CV_COMPACT_CHECKBOX_FIXTURE;
    if (enabled) env.CV_COMPACT_CHECKBOX_FIXTURE='1';
    const host={enabled,cleanup:{}};record.hosts.push(host);
    const child=cp.spawn(python,['tests/browser/conditional_formsets_server.py'],{cwd:root,env,stdio:['ignore','pipe','pipe']});
    let log='',context,spawnError;
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
        const signin=await context.request.get(`${base}/signin/`);
        host.authentication={status:signin.status(),...await signin.json()};
        check(`signin:${enabled}`,signin.status()===200 && host.authentication.authenticated===true);
        const cases=await (await context.request.get(`${base}/cases/`)).json();
        host.caseIds=[...new Set(cases.map(c=>c.id))].sort();
        check(`case-ids:${enabled}`,JSON.stringify(host.caseIds)===JSON.stringify([...legacyIds,...(enabled?['compact-checkbox']:[])].sort()),host.caseIds);
        const legacy=cases.find(c=>c.id==='tracer' && c.theme==='stock');
        const page=await context.newPage();
        await load(page,legacy.filesUrl);
        check(`legacy-isolation:${enabled}`,await page.locator('#other').count()===1);
        check(`legacy-records:${enabled}`,await page.locator('#editor input[type=file]').count()>0);
        await page.close();
        await work(context,cases);
    } finally {
        if(context) await context.close();
        if(child.exitCode===null && child.signalCode===null) child.kill('SIGTERM');
        const exit=await Promise.race([exited,delay(5000).then(()=>null)]);
        if(!exit) {child.kill('SIGKILL');await exited;}
        host.cleanup={exit,reaped:child.exitCode!==null || child.signalCode!==null,
            temporaryRemoved:!!host.temporary && !fs.existsSync(host.temporary)};
        if(record.assertions.some(a=>!a.passed)) host.log=log;
        check(`cleanup:${enabled}`,!!exit && exit.code===0 && host.cleanup.reaped && host.cleanup.temporaryRemoved,host.cleanup);
    }
}
async function control(page,c) {
    const set=page.locator('#editor fieldset[cv-data-formset-key="records"]');
    assert.equal(await set.count(),1);
    const row=set.locator('.cv-formset-row').filter({has:page.locator(`input[name$="-id"][value="${c.record}"]`)});
    assert.equal(await row.count(),1);
    const prefix=await row.getAttribute('cv-data-formset-form-prefix');
    const input=row.locator(`input[name="${prefix}-active"]`);
    assert.equal(await input.count(),1);
    const id=await input.getAttribute('id');
    const label=row.locator(`label[for="${id}"]`);
    assert.equal(await label.count(),1);
    return {set,row,input,label,prefix};
}
async function observe(page,c,width) {
    check(`${width}:one-editor`,await page.locator('#editor').count()===1 && await page.locator('#other').count()===0);
    const {set,input,label}=await control(page,c);
    const metadata=JSON.parse(await set.locator(':scope > .cv-formset-content').getAttribute('cv-data-formset'));
    check(`${width}:field-metadata`,JSON.stringify(metadata.fields)===JSON.stringify(c.fields),metadata);
    const geometry=await label.evaluate(el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();
        const input=el.previousElementSibling,ir=input.getBoundingClientRect();
        return {position:s.position,width:s.width,height:r.height,clip:s.clip,display:s.display,
            visible:s.visibility,beside:r.left>=ir.right,aligned:Math.abs(r.top-ir.top)<10,text:el.textContent.trim()};});
    const heading=set.locator(':scope > .cv-formset-content > .cv-formset-compact-headings');
    check(`${width}:label`,geometry.display!=='none' && geometry.visible!=='hidden' &&
        (width>=768 ? geometry.position==='absolute' && geometry.width==='1px' && geometry.clip==='rect(0px, 0px, 0px, 0px)' :
            geometry.position==='static' && geometry.height>1 && geometry.beside && geometry.aligned),geometry);
    check(`${width}:heading`,await heading.isVisible()===(width>=768) && (await heading.textContent()).includes(geometry.text));
    const ids=await page.locator('input[id]').evaluateAll(els=>els.map(el=>el.id));
    check(`${width}:unique-input-ids`,new Set(ids).size===ids.length,ids);
    const classic=page.locator('#editor input[name="with_contact"]');
    check(`${width}:classic-checkbox`,await classic.count()===1 && await classic.getAttribute('type')==='checkbox' &&
        await classic.evaluate(el=>!el.closest('.cv-formset-compact-fields')));
    check(`${width}:native-widget`,await input.getAttribute('type')==='checkbox');
    check(`${width}:overflow`,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    return geometry;
}
async function submit(page,c,context,expected) {
    const responsePromise=page.waitForResponse(r=>r.request().method()==='POST' && r.url()===base+c.url);
    await Promise.all([page.waitForNavigation({waitUntil:'load'}),
        page.locator('#editor').evaluate(form=>HTMLFormElement.prototype.submit.call(form))]);
    const response=await responsePromise;
    check(`save:${expected}`,response.status()===200 && (await response.json()).saved===true,{status:response.status()});
    const state=await (await context.request.get(`${base}/state/`)).json();
    check(`persist:${expected}`,state.checkbox_records.length===1 && state.checkbox_records[0].id===c.record &&
        state.checkbox_records[0].active===expected,state.checkbox_records);
    const name=`records-${c.profile}-0-0-active`;
    check(`native-payload:${expected}`,Object.hasOwn(state.received.at(-1).post,name)===expected,state.received.at(-1).post);
    await load(page,c.url);
    check(`redisplay:${expected}`,await (await control(page,c)).input.isChecked()===expected);
}
async function tracer(context,cases) {
    const c=cases.find(c=>c.id==='compact-checkbox');assert(c);
    for(const width of [390,1280]) {
        const page=await context.newPage();page.setDefaultTimeout(12000);
        page.on('pageerror',e=>record.pageErrors.push(e.message));
        const assets=[];
        page.on('response',r=>{if(r.url().includes('/static/') || r.url().includes('/bootstrap@'))
            assets.push({url:r.url(),status:r.status()});});
        await page.setViewportSize({width,height:900});await load(page,c.url);
        record.widths.push({width,initial:await observe(page,c,width)});
        check(`${width}:assets`,assets.some(a=>a.url.includes('bootstrap.min.css')) &&
            assets.some(a=>a.url.includes('/css/formset.css')) && assets.every(a=>a.status===200),assets);
        record.assets.push(...assets);
        let input=(await control(page,c)).input;
        await input.focus();await page.keyboard.press('Space');
        check(`${width}:keyboard`,await input.isChecked() && await input.evaluate(el=>document.activeElement===el));
        await submit(page,c,context,true);
        input=(await control(page,c)).input;
        await input.focus();await page.keyboard.press('Space');
        check(`${width}:unchecked`,!await input.isChecked());
        await submit(page,c,context,false);
        await page.close();
    }
}
test('stock checkbox renders and persists through native POST',async()=>{
    let browser;
    try {
        for(const file of [python,playwright,chromium]) assert(fs.existsSync(file),file);
        browser=await require(playwright).chromium.launch({headless:true,executablePath:chromium,args:['--no-sandbox']});
        await startHost(browser,false,async()=>{});
        await startHost(browser,true,tracer);
        check('no-page-errors',record.pageErrors.length===0,record.pageErrors);
        record.completed=true;record.passed=true;
    } catch(error) {record.error=error.stack;throw error;}
    finally {
        if(browser) await browser.close();
        fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
    }
});
