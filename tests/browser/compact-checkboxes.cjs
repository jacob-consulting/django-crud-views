// Authenticated stock-checkbox contract. Existing dependencies only; disposable host/storage.
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const net = require('node:net');
const assert = require('node:assert/strict');
const test = require('node:test');
const crypto = require('node:crypto');
const os = require('node:os');
const root = path.resolve(__dirname, '../..');
process.chdir(root);
const args = process.argv.slice(2);
const option = (name, fallback) => args.includes(name) ? args[args.indexOf(name) + 1] : fallback;
const output = option('--output', '/tmp/compact-checkboxes.json');
const variant = option('--variant', 'current');
const phase = '.planning/phases/06.26-issue-351';
const canonicalCaptureRoot = `${phase}/browser-captures`;
const canonicalRefresh = path.resolve(output) === path.resolve(`${phase}/06.26-browser-${variant}.json`);
assert(canonicalRefresh || !['current','floor'].some(v=>path.resolve(output)===path.resolve(`${phase}/06.26-browser-${v}.json`)),
    'The variant must match the canonical report destination.');
const captureRoot = canonicalRefresh ? canonicalCaptureRoot : `${output}.captures`;
let stagedCaptureRoot;
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const filesIn = dir => fs.readdirSync(dir,{withFileTypes:true}).flatMap(e =>
    e.isDirectory() ? (e.name==='__pycache__' ? [] : filesIn(`${dir}/${e.name}`)) : [`${dir}/${e.name}`]);
const sourceFiles = ['tests/browser/compact-checkboxes.cjs','tests/browser/conditional_formsets_server.py',
    'tests/test1/conftest.py','tests/test1/app/models.py','node_modules/jquery/dist/jquery.js',
    ...filesIn('src/crud_views/lib/formsets'),...filesIn('src/crud_views/templates/crud_views/formsets'),
    ...filesIn('tests/browser/templates/conditional_formsets'),
    'src/crud_views/static/crud_views/css/formset.css',
    ...['formset','toggle','adapters','modal'].map(n=>`src/crud_views/static/crud_views/js/${n}.js`)];
const hashes = () => Object.fromEntries(sourceFiles.sort().map(f=>[f,digest(f)]));
const captureNames = v => ['390-initial','390-invalid','390-added','1280-initial','1280-invalid','1280-added',
    '767-nested','768-nested'].map(n=>`${canonicalCaptureRoot}/${v}-${n}.png`);
if(args.includes('--check-evidence')) {
    for(const v of ['current','floor']) {
        const data=JSON.parse(fs.readFileSync(`${phase}/06.26-browser-${v}.json`));
        assert(data.completed && data.passed && data.variant===v && data.mode==='full');
        assert(data.assertions.length>100 && data.assertions.every(a=>a.passed));
        assert.deepEqual(data.widths.map(w=>w.width),[390,767,768,1280]);
        assert.equal(data.compositions.length,12);
        assert(data.requests.some(r=>r.actor==='denied_actor' && r.status===403 && r.rowHtml===false));
        assert(data.requests.some(r=>r.actor==='authorized_actor' && r.status===400 && r.rowHtml===false));
        assert.deepEqual(data.sourceHashes,hashes(),'stale executed source');
        for(const name of ['python','django','django-crispy-forms','crispy-bootstrap5','playwright','chromium']) assert(data.runtime[name]);
        assert.deepEqual(data.captures.map(c=>c.path).sort(),captureNames(v).sort());
        for(const c of data.captures) {
            assert.equal(digest(c.path),c.sha256,c.path);
            assert(c.trackable);
        }
        assert(data.hosts.length===2 && data.hosts.every(h=>h.cleanup.exit.code===0 && h.cleanup.reaped && h.cleanup.temporaryRemoved));
        assert.equal(data.humanReview,'pending');
        assert(data.pageErrors.length===0 && data.failedAssets.length===0);
    }
    console.log('Current and floor checkbox evidence complete; source and sixteen capture hashes verified.');
    process.exit(0);
}
assert(['current', 'floor'].includes(variant));
assert(!(canonicalRefresh && args.includes('--tracer')), 'Canonical evidence requires a full run; use a temporary output for --tracer.');
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
    environment:{python,playwright,chromium}, sourceHashes:hashes(), mode:args.includes('--tracer')?'tracer':'full',
    runtime:{node:process.version}, hosts:[], widths:[], assertions:[], assets:[], pageErrors:[], failedAssets:[],
    requests:[], captures:[], compositions:[], persisted:[],
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
    check(`persist:${expected}`,state.checkbox_records.length===2 && state.checkbox_records[0].id===c.record &&
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
async function full(context,cases) {
    const c=cases.find(c=>c.id==='compact-checkbox');assert(c);
    for(const width of [390,767,768,1280]) {
        const page=await observedPage(context,width);
        await load(page,c.url);
        const {row,prefix}=await control(page,c);
        check('retained-required-checkbox',await row.locator(`input[name="${prefix}-accepted"]`).count()===1);
        check('retained-disabled-checkbox',await row.locator(`input[name="${prefix}-flag"]`).isDisabled());
        const profile=await inspect(page,c,width);
        await isolation(page,width);
        await keyboard(page,prefix);
        await keyboard(page,(await control(page,{...c,record:c.otherRecord})).prefix);
        if([390,1280].includes(width)) {
            await capture(page,`${width}-initial`);
            await profileLifecycle(page,context,c,width);
        } else {
            await field(page,prefix,'accepted').uncheck();
            await nativePost(page,c.url,422);
            await errorOwned(page,prefix);
            await inspect(page,c,width);
        }
        await page.close();
        for(const composition of ['compact-compact','compact-classic','classic-compact']) {
            const nested=await observedPage(context,width);
            const url=`${c.publisherUrl}?composition=${composition}`;
            await load(nested,url);
            const measurement=await inspect(nested,c,width);
            await isolation(nested,width);
            record.compositions.push({width,composition,measurement});
            if(composition==='compact-compact' && [767,768].includes(width)) await capture(nested,`${width}-nested`);
            if(width===1280) await nestedLifecycle(nested,context,c,url,composition);
            await nested.close();
        }
        record.widths.push({width,profile});
    }
    await authorization(context,c,cases.find(item=>item.id==='tracer' && item.theme==='stock').profile);
}

async function observedPage(context,width) {
    const page=await context.newPage();page.setDefaultTimeout(12000);
    await page.setViewportSize({width,height:900});
    page.on('pageerror',e=>record.pageErrors.push(e.message));
    page.on('requestfailed',r=>{if(['stylesheet','script','font','image'].includes(r.resourceType()))
        record.failedAssets.push({url:r.url(),error:r.failure()});});
    page.on('response',r=>{if(['stylesheet','script','font'].includes(r.request().resourceType())) {
        record.assets.push({url:r.url(),status:r.status()});
        if(!r.ok()) record.failedAssets.push({url:r.url(),status:r.status()});
    }});
    return page;
}
const field = (page,prefix,name) => page.locator(`#editor input[name="${prefix}-${name}"]`);
const content = (page,prefix) => page.locator(`#editor .cv-formset-content[cv-data-formset-prefix="${prefix}"]`);
const ownedRows = node => node.locator(':scope > .cv-formset-row');
const ownControl = (row,kind) => row.locator(`:scope > .cv-formset-form .cv-form-ctrl-${kind}`);
async function capture(page,name) {
    if(canonicalRefresh && !stagedCaptureRoot) stagedCaptureRoot=fs.mkdtempSync(path.join(os.tmpdir(),`cv-checkboxes-${variant}-`));
    const destination=stagedCaptureRoot || captureRoot;
    fs.mkdirSync(destination,{recursive:true});
    const file=`${captureRoot}/${variant}-${name}.png`;
    const screenshot=`${destination}/${variant}-${name}.png`;
    await page.screenshot({path:screenshot,fullPage:true});
    const trackable=canonicalRefresh ? cp.spawnSync('git',['check-ignore','-q',file]).status===1 : null;
    record.captures.push({path:file,sha256:digest(screenshot),trackable});
    check(`capture:${name}`,fs.existsSync(screenshot) && (!canonicalRefresh || trackable),file);
}
function finishOutput() {
    try {
        const successful=record.completed && record.passed && !record.error;
        let report=output;
        if(canonicalRefresh) {
            if(successful) {
                assert.deepEqual(record.captures.map(c=>c.path).sort(),captureNames(variant).sort());
                fs.mkdirSync(canonicalCaptureRoot,{recursive:true});
                for(const capture of record.captures) fs.copyFileSync(path.join(stagedCaptureRoot,path.basename(capture.path)),capture.path);
            } else {
                report=path.join(os.tmpdir(),`compact-checkboxes-${variant}-failed.json`);
                console.error(`Canonical evidence preserved; failed run report: ${report}`);
            }
        }
        fs.mkdirSync(path.dirname(report),{recursive:true});
        fs.writeFileSync(report,JSON.stringify(record,null,2)+'\n');
    } finally {
        if(stagedCaptureRoot) fs.rmSync(stagedCaptureRoot,{recursive:true,force:true});
    }
}
async function inspect(page,c,width) {
    const measurement=await page.locator('#editor').evaluate((editor,{width,fields,nestedFields})=>{
        const errors=[], controls=[], metadata=[];
        const composition=new URL(location.href).searchParams.get('composition')||'compact-compact';
        const ids=[...editor.querySelectorAll('[id]')].map(e=>e.id);
        const names=[...editor.querySelectorAll('input,select,textarea')].map(e=>e.name).filter(Boolean);
        if(new Set(ids).size!==ids.length || new Set(names).size!==names.length) errors.push('duplicate identity');
        for(const set of editor.querySelectorAll('fieldset[cv-data-formset-key]')) {
            const key=set.getAttribute('cv-data-formset-key').split('-').at(-1),body=set.querySelector(':scope > .cv-formset-content');
            const data=JSON.parse(body.getAttribute('cv-data-formset'));
            if(fields && key==='records' || nestedFields[key]) {
                const expected=key==='records'?fields:nestedFields[key];
                if(JSON.stringify(data.fields)!==JSON.stringify(expected)) errors.push(`metadata:${data.prefix}`);
                metadata.push({key,prefix:data.prefix,fields:data.fields});
            }
            const compact=set.classList.contains('cv-formset-compact');
            const expectedCompact=key==='books'?!composition.startsWith('classic-'):
                ['notes','memos'].includes(key)?!composition.endsWith('-classic'):key==='classic_books'?false:null;
            if(expectedCompact!==null && compact!==expectedCompact) errors.push(`composition:${key}`);
            const heading=body.querySelector(':scope > .cv-formset-compact-headings');
            if(compact && (!heading || (getComputedStyle(heading).display!=='none')!==(width>=768))) errors.push(`heading:${key}`);
            for(const row of body.querySelectorAll(':scope > .cv-formset-row')) {
                const prefix=row.getAttribute('cv-data-formset-form-prefix');
                const targets=key==='records'?['active','flag','accepted']:['books','classic_books','notes','memos'].includes(key)?['acknowledged']:[];
                for(const name of targets) {
                    const matches=[...row.querySelectorAll(`input[name="${prefix}-${name}"]`)];
                    const input=matches[0],labels=input?[...row.querySelectorAll(`label[for="${input.id}"]`)]:[];
                    if(matches.length!==1 || labels.length!==1 || input.closest('fieldset[cv-data-formset-key]')!==set) {
                        errors.push(`ownership:${prefix}-${name}`);continue;
                    }
                    const label=labels[0],s=getComputedStyle(label),r=label.getBoundingClientRect(),ir=input.getBoundingClientRect();
                    const cell=input.closest('.cv-formset-compact-fields > div');
                    const inner=input.closest('.form-check');
                    const text=label.textContent.trim();
                    if(!text || input.type!=='checkbox' || s.display==='none' || s.visibility==='hidden') errors.push(`label:${input.name}`);
                    if(compact && width>=768) {
                        if(s.clip!=='rect(0px, 0px, 0px, 0px)' || r.width!==1 || s.position!=='absolute') errors.push(`clip:${input.name}`);
                        if(!heading.textContent.includes(text.replace('*','').trim())) errors.push(`heading text:${input.name}`);
                    } else if(r.width<=1 || r.height<=1 || s.clip!=='auto') errors.push(`visible:${input.name}`);
                    if(compact && width<768 && (r.left<ir.right || Math.abs(r.top-ir.top)>10)) errors.push(`beside:${input.name}`);
                    if(compact && (inner.scrollWidth>inner.clientWidth+1 || ir.width<10 || ir.height<10)) errors.push(`geometry:${input.name}`);
                    if(compact && getComputedStyle(inner).marginBottom!=='0px') errors.push(`inner-margin:${input.name}`);
                    for(const helper of cell?.querySelectorAll('.form-text,.invalid-feedback')||[]) {
                        const rect=helper.getBoundingClientRect();
                        if(rect.width<=0 || rect.height<=0 || helper.scrollWidth>helper.clientWidth+1) errors.push(`feedback:${input.name}`);
                        if(helper.querySelector('em')) errors.push('ordinary help not escaped');
                    }
                    if(name==='accepted' && (!label.querySelector('.asteriskField') || !heading.querySelector('.asteriskField'))) errors.push(`required:${input.name}`);
                    controls.push({name:input.name,id:input.id,compact,checked:input.checked,disabled:input.disabled,text,
                        clip:s.clip,position:s.position,label:{x:r.x,y:r.y,width:r.width,height:r.height},
                        input:{x:ir.x,y:ir.y,width:ir.width,height:ir.height},innerMargin:getComputedStyle(inner).marginBottom});
                }
                if(key==='scores') for(const label of row.querySelectorAll(':scope > .cv-formset-form .cv-formset-compact-label')) {
                    const s=getComputedStyle(label);
                    if((s.position==='absolute')!==(width>=768)) errors.push('numeric score label contract');
                }
            }
        }
        if(document.documentElement.scrollWidth>innerWidth) errors.push('document overflow');
        return {errors,controls,metadata};
    },{width,fields:c.fields,nestedFields:c.nestedFields});
    check(`${width}:owned-rendering`,measurement.errors.length===0,measurement);
    // Playwright computes the actual accessible name from the native label association.
    for(const target of measurement.controls) {
        const input=page.locator(`#editor input[name="${target.name}"]`);
        check(`accessible:${target.name}`,await input.getAttribute('id')===target.id &&
            (await input.ariaSnapshot()).includes('checkbox "'+target.text.replace(/\s+/g,' ')));
    }
    return measurement;
}
async function isolation(page,width) {
    const result=await page.evaluate(()=>{
        const all=[...document.querySelectorAll('#editor input[type=checkbox]')];
        const classic=all.filter(el=>!el.closest('.cv-formset-compact-fields'));
        const compact=all.filter(el=>el.closest('.cv-formset-compact-fields'));
        const snapshot=inputs=>inputs.map(input=>{
            const label=document.querySelector(`label[for="${input.id}"]`),s=getComputedStyle(label);
            return {name:input.name,position:s.position,clip:s.clip,margin:s.margin,overflow:s.overflow,
                whiteSpace:s.whiteSpace,fontWeight:s.fontWeight,overflowWrap:s.overflowWrap,
                checkMargin:getComputedStyle(input.closest('.form-check')).marginBottom};
        });
        const before=snapshot(classic),positive=snapshot(compact),restores=[];
        try {
            const sheet=[...document.styleSheets].find(s=>s.href?.endsWith('/css/formset.css'));
            const visit=rules=>{for(const rule of rules) {
                if(rule.cssRules) visit(rule.cssRules);
                if(rule.selectorText?.includes('.form-check')) {
                    const original=rule.selectorText;
                    restores.push(()=>{rule.selectorText=original;});
                    rule.selectorText=original.split(',').filter(s=>!s.includes('.form-check')).join(',') || ':not(*)';
                }
            }};
            visit(sheet.cssRules);
            return {before,after:snapshot(classic),positive,disabled:snapshot(compact),changedRules:restores.length};
        } finally {restores.reverse().forEach(restore=>restore());}
    });
    check(`${width}:classic-rule-isolation`,result.before.length>0 && result.changedRules>=3 &&
        JSON.stringify(result.before)===JSON.stringify(result.after) && result.before.every(s=>s.clip==='auto'),result);
    if(width>=768) check('isolation-positive-control',result.positive.some((s,i)=>s.clip!==result.disabled[i].clip),result);
}
async function keyboard(page,prefix) {
    const input=field(page,prefix,'active'),accepted=field(page,prefix,'accepted'),disabled=field(page,prefix,'flag');
    await input.focus();
    const initial=await input.isChecked();
    await page.keyboard.press('Space');
    check('space-toggle',await input.isChecked()!==initial);
    const focus=await input.evaluate(el=>{const s=getComputedStyle(el);return {active:document.activeElement===el,shadow:s.boxShadow,outline:s.outlineStyle};});
    check('visible-focus',focus.active && (focus.shadow!=='none'||focus.outline!=='none'),focus);
    await page.keyboard.press('Tab');
    check('tab-skips-disabled',await accepted.evaluate(el=>document.activeElement===el));
    await page.keyboard.press('Shift+Tab');
    check('shift-tab-skips-disabled',await input.evaluate(el=>document.activeElement===el));
    const before=await disabled.isChecked();
    await disabled.evaluate(el=>{el.focus();el.click();});
    check('disabled-cannot-activate',await disabled.isChecked()===before &&
        await disabled.evaluate(el=>document.activeElement!==el));
}
async function nativePost(page,url,status) {
    const responsePromise=page.waitForResponse(r=>r.request().method()==='POST' && r.url()===base+url);
    await Promise.all([page.waitForNavigation({waitUntil:'load'}),page.locator('#editor').evaluate(form=>HTMLFormElement.prototype.submit.call(form))]);
    const response=await responsePromise;
    record.requests.push({kind:'native-post',url,status:response.status()});
    check(`post:${status}`,response.status()===status,{actual:response.status(),body:(await response.text()).slice(0,300)});
    if(status===200) {
        check('json-success',(await response.json()).saved===true);
        await load(page,url);
    }
}
async function errorOwned(page,prefix) {
    const error=await field(page,prefix,'accepted').evaluate(el=>{
        const owner=el.closest('.mb-3');
        const feedback=owner.querySelector('.invalid-feedback');
        return {name:el.name,text:feedback?.textContent,visible:!!feedback?.getClientRects().length,
            width:feedback?.clientWidth,scrollWidth:feedback?.scrollWidth};
    });
    check('field-owned-required-error',error.visible && error.text.includes('Bitte bestätigen') && error.scrollWidth<=error.width+1,error);
}
async function addRow(page,node) {
    const responsePromise=page.waitForResponse(r=>r.url().includes('template=') && r.request().method()==='GET');
    await ownControl(ownedRows(node),'add').last().click();
    const response=await responsePromise,body=await response.json();
    record.requests.push({kind:'authorized-fragment',url:response.url(),status:response.status(),rows:body.rows});
    check('authorized-fragment',response.status()===200 && body.rows.length===1 && body.html.includes(body.rows[0]),body.rows);
    const row=page.locator(`#editor .cv-formset-row[cv-data-formset-form-prefix="${body.rows[0]}"]`);
    await row.waitFor();
    return {row,prefix:body.rows[0]};
}
async function markUnmark(page,row,prefix) {
    await ownControl(row,'delete').click();
    check('delete-owned-row',await field(page,prefix,'DELETE').inputValue()==='1');
    await ownControl(row,'delete').click();
    check('unmark-owned-row',await field(page,prefix,'DELETE').inputValue()!=='1');
}
async function profileLifecycle(page,context,c,width) {
    const first=(await control(page,c)).prefix;
    const second=(await control(page,{...c,record:c.otherRecord})).prefix;
    const before=(await (await context.request.get(`${base}/state/`)).json()).checkbox_records;
    await field(page,first,'active').check();await field(page,second,'active').uncheck();
    await field(page,first,'accepted').uncheck();
    await nativePost(page,c.url,422);
    await errorOwned(page,first);
    check('invalid-optional-state',await field(page,first,'active').isChecked() && !await field(page,second,'active').isChecked());
    check('disabled-both-states',await field(page,first,'flag').isChecked() && !await field(page,second,'flag').isChecked());
    await inspect(page,c,width);
    await capture(page,`${width}-invalid`);
    await field(page,first,'accepted').check();
    const added=await addRow(page,content(page,`records-${c.profile}-0`));
    await field(page,added.prefix,'active').check();
    await markUnmark(page,added.row,added.prefix);
    await nativePost(page,c.url,422);
    await errorOwned(page,added.prefix);
    check('added-invalid-state',await field(page,added.prefix,'active').isChecked() && !await field(page,added.prefix,'accepted').isChecked());
    await field(page,added.prefix,'accepted').check();
    await inspect(page,c,width);
    await field(page,added.prefix,'active').focus();
    await capture(page,`${width}-added`);
    await nativePost(page,c.url,200);
    const state=await (await context.request.get(`${base}/state/`)).json();
    const stored=state.checkbox_records;
    const post=state.received.at(-1).post;
    check('persisted-disabled-and-optional',stored.find(r=>r.id===c.record).active===true &&
        stored.find(r=>r.id===c.record).flag===true && stored.find(r=>r.id===c.otherRecord).active===false &&
        stored.find(r=>r.id===c.otherRecord).flag===false,stored);
    check('one-edited-extra-only',stored.length===before.length+1 && stored.filter(r=>!before.some(b=>b.id===r.id)).every(r=>r.active),stored);
    check('native-disabled-omission',!Object.keys(post).some(n=>n.endsWith('-flag')) &&
        Object.hasOwn(post,`${first}-active`) && !Object.hasOwn(post,`${second}-active`) && Object.hasOwn(post,`${added.prefix}-accepted`),post);
    record.persisted.push({width,records:stored,post});
}
async function nestedLifecycle(page,context,c,url,composition) {
    const books=content(page,`books-${c.publisher}-0`);
    const first=ownedRows(books).filter({has:page.locator('input[value="Checkbox book 0"]')});
    check('seeded-parent-identity',await first.count()===1);
    const prefix=await first.getAttribute('cv-data-formset-form-prefix');
    await field(page,prefix,'acknowledged').check();
    const memos=first.locator('fieldset[cv-data-formset-key="books-memos"] > .cv-formset-content');
    const retained=ownedRows(memos);
    const firstMemo=await retained.nth(0).getAttribute('cv-data-formset-form-prefix');
    const secondMemo=await retained.nth(1).getAttribute('cv-data-formset-form-prefix');
    await field(page,firstMemo,'acknowledged').check();await field(page,secondMemo,'acknowledged').uncheck();
    const identities=await Promise.all([firstMemo,secondMemo].map(async p=>({prefix:p,id:await field(page,p,'id').inputValue(),checked:await field(page,p,'acknowledged').isChecked()})));
    await ownControl(retained.nth(1),'up').click();
    check('order-moves-owned-row',await retained.first().getAttribute('cv-data-formset-form-prefix')===secondMemo);
    for(const item of identities) check('order-keeps-checkbox-identity',await field(page,item.prefix,'id').inputValue()===item.id &&
        await field(page,item.prefix,'acknowledged').isChecked()===item.checked,item);
    const added=await addRow(page,books);
    await field(page,added.prefix,'title').fill(`Added ${composition}`);
    await field(page,added.prefix,'acknowledged').uncheck();
    const notes=added.row.locator('fieldset[cv-data-formset-key="books-notes"] > .cv-formset-content');
    const child=await addRow(page,notes);
    await field(page,child.prefix,'note').fill(`Child ${composition}`);
    await field(page,child.prefix,'acknowledged').check();
    await markUnmark(page,child.row,child.prefix);
    check('nested-full-prefix',child.prefix.startsWith(`books-notes-${c.publisher}-0-`) &&
        await child.row.evaluate((el,parent)=>el.closest('fieldset[cv-data-formset-key]').closest('.cv-formset-row').getAttribute('cv-data-formset-form-prefix')===parent,added.prefix));
    await inspect(page,c,1280);
    await nativePost(page,url,200);
    const state=await (await context.request.get(`${base}/state/`)).json(),post=state.received.at(-1).post;
    for(const item of identities) check('posted-checkbox-hidden-id-pair',post[`${item.prefix}-id`][0]===item.id &&
        Object.hasOwn(post,`${item.prefix}-acknowledged`)===item.checked,item);
    check('optional-nested-checked-and-unchecked',Object.hasOwn(post,`${child.prefix}-acknowledged`) &&
        !Object.hasOwn(post,`${added.prefix}-acknowledged`));
    const saved=state.books.find(b=>b.publisher_id===c.publisher && b.title===`Added ${composition}`);
    check('nested-saved-parentage',!!saved && state.notes.some(n=>n.book_id===saved.id && n.note===`Child ${composition}`));
    check('persisted-memo-order',state.memos.find(m=>String(m.id)===identities[1].id).order<state.memos.find(m=>String(m.id)===identities[0].id).order);
    record.persisted.push({composition,identities,post,book:saved});
}
async function authorization(context,c,foreignProfile) {
    const page=await observedPage(context,1280);await load(page,c.url);
    const params=await content(page,`records-${c.profile}-0`).evaluate(el=>{
        const data=JSON.parse(el.getAttribute('cv-data-formset'));
        const pk=data.prefix_key.match(new RegExp(`^(?:(.*)-)?(None|${data.pk})-(\\d+)$`))[2];
        return {template:data.hierarchy.join('|'),pk,num:document.querySelector(`input[name="${data.prefix}-TOTAL_FORMS"]`).value,
            formset_parent_prefix_key:data.parent_prefix_key};
    });
    const denied=await context.browser().newContext();
    try {
        await denied.request.get(`${base}/signin/?denied=1`);
        for(const [actor,client,payload,status] of [
            ['denied_actor',denied,{...params},403],['authorized_actor',context,{...params,pk:String(foreignProfile)},400]]) {
            const response=await client.request.get(base+c.url,{params:payload}),body=await response.text();
            check(`${actor}:fragment-${status}`,response.status()===status && !body.includes('cv-formset-row') && !body.includes('"rows"'),{status:response.status()});
            record.requests.push({kind:'rejected-fragment',actor,status:response.status(),rowHtml:false,params:payload});
        }
    } finally {await denied.close();await page.close();}
}
test('stock checkbox renders and persists through native POST',async()=>{
    let browser;
    try {
        for(const file of [python,playwright,chromium]) assert(fs.existsSync(file),file);
        browser=await require(playwright).chromium.launch({headless:true,executablePath:chromium,args:['--no-sandbox']});
        record.runtime={...record.runtime,...JSON.parse(cp.execFileSync(python,['-c',
            'import sys,json,importlib.metadata as m; print(json.dumps({"python":sys.version, **{n:m.version(n) for n in ["django","django-crispy-forms","crispy-bootstrap5"]}}))'],{encoding:'utf8'})),
            playwright:require(`${playwright}/package.json`).version,chromium:browser.version()};
        await startHost(browser,false,async()=>{});
        await startHost(browser,true,args.includes('--tracer') ? tracer : full);
        check('no-page-errors',record.pageErrors.length===0,record.pageErrors);
        check('no-failed-assets',record.failedAssets.length===0,record.failedAssets);
        check('unchanged-executed-source',JSON.stringify(record.sourceHashes)===JSON.stringify(hashes()));
        record.completed=true;record.passed=true;
    } catch(error) {record.error=error.stack;throw error;}
    finally {
        try {
            if(browser) await browser.close();
        } catch(error) {
            record.completed=false;record.passed=false;record.error=error.stack;
            throw error;
        } finally {finishOutput();}
    }
});
