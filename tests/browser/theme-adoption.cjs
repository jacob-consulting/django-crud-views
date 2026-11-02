// Import-pure configuration and owned-process real companion acceptance.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const net = require('node:net');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const ROOT = path.resolve(__dirname, '../..');
const PHASE = '.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync';
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
function absolute(value, name) {
    assert(typeof value === 'string' && value && path.isAbsolute(value), `${name} must be a nonempty absolute path`);
    return path.normalize(value);
}
function manifest(root = ROOT) {return JSON.parse(fs.readFileSync(path.join(root, PHASE, '06-companion-baseline.json'), 'utf8'));}
function resolveCompanionPython({root = ROOT, env = process.env, probe} = {}) {
    const recorded = manifest(root);
    const executable = absolute(recorded.companion_python, 'recorded companion_python');
    for (const key of ['CV_THEME_PYTHON', 'CV_FOCUS_PYTHON']) {
        if (key in env) assert.equal(absolute(env[key], key), executable, `conflicting ${key}`);
    }
    assert(fs.existsSync(executable), 'recorded companion Python is missing');
    const program = "import importlib.metadata,json,sys;print(json.dumps({'python':list(sys.version_info[:3]),'prefix':sys.prefix,'versions':{n:importlib.metadata.version(n) for n in ['Django','django-crispy-forms','crispy-bootstrap5','pytest','pytest-django','pytest-xdist','tblib']},'missing':[]}))";
    const runtime = probe ? probe(executable) : JSON.parse(cp.execFileSync(executable, ['-c', program], {encoding: 'utf8', shell: false}));
    assert(runtime.python?.[0] === 3 && runtime.python[1] >= 14 && /^6\.1\./.test(runtime.versions?.Django), 'incompatible companion Python/Django');
    assert.deepEqual(runtime, recorded.runtime, 'recorded runtime prefix/version identity changed');
    return {executable, runtime};
}
function resolveSource(operand, {root = ROOT, env = process.env} = {}) {
    const recorded = manifest(root);
    const expected = absolute(recorded.companion_root, 'recorded companion_root');
    const selected = operand === undefined || operand === 'recorded' ? expected : absolute(operand, 'delivered-source');
    assert.equal(selected, expected, 'delivered source does not match recorded root');
    for (const key of ['CV_THEME_SOURCE', 'CV_PACK_SOURCE']) if (key in env) assert.equal(absolute(env[key], key), expected, `conflicting ${key}`);
    assert(fs.statSync(selected).isDirectory(), 'recorded companion source missing');
    const git = args => cp.execFileSync('git', ['-C', selected, ...args], {encoding: 'utf8', shell: false}).trim();
    assert.equal(git(['rev-parse', '--show-toplevel']), fs.realpathSync(selected));
    assert.equal(git(['remote', 'get-url', 'origin']), recorded.origin, 'source origin mismatch');
    assert.equal(git(['rev-parse', `${recorded.revision}^{commit}`]), recorded.revision, 'source revision mismatch');
    return selected;
}
function portValue(env = process.env) {
    const value = env.CV_THEME_PORT ?? '8145';
    assert(/^[0-9]+$/.test(value) && +value >= 1024 && +value <= 65535 && ![8143,8144].includes(+value), 'CV_THEME_PORT must be decimal 1024..65535; reserved ports: 8143, 8144');
    return +value;
}
async function available(port) {
    await new Promise((resolve, reject) => {const server = net.createServer(); server.once('error', reject); server.listen(port, '127.0.0.1', () => server.close(resolve));});
}
function options(argv) {
    const result = {case: 'all', output: path.join(ROOT, PHASE, '07-browser-results.json')};
    for (let i=0;i<argv.length;i+=2) {
        assert(['--case','--output','--delivered-source'].includes(argv[i]) && argv[i+1] && !argv[i+1].startsWith('--'), 'Invalid CLI option');
        result[argv[i].slice(2)] = argv[i+1];
    }
    assert(['owned-form','label-floor','all'].includes(result.case), 'Use --case owned-form|label-floor|all');
    return result;
}
async function configuration(argv = process.argv.slice(2), env = process.env, root = ROOT) {
    const port = portValue(env); // Invalid/occupied ports are rejected before any runtime starts.
    await available(port);
    const opts = options(argv);
    const selected = resolveCompanionPython({root, env});
    const source = resolveSource(opts['delivered-source'], {root, env});
    return {port, opts, ...selected, source, root};
}
function cached(directory, suffix) {
    return fs.existsSync(directory) ? fs.readdirSync(directory).sort().reverse().map(name => path.join(directory, name, suffix)).find(p => fs.existsSync(p)) : null;
}
async function bounded(promise, ms, message) {
    let timer;
    try {return await Promise.race([promise,new Promise((_,reject) => {timer=setTimeout(() => reject(Error(message)),ms);})]);}
    finally {clearTimeout(timer);}
}
function check(record, id, condition, observed) {
    record.assertions.push({id, passed:!!condition, ...(observed === undefined ? {} : {observed})});
    assert(condition, `${record.id}: ${id}: ${JSON.stringify(observed)}`);
}
function atomicJSON(target, value) {
    fs.mkdirSync(path.dirname(target), {recursive:true});
    const temporary = `${target}.${process.pid}.tmp`;
    fs.writeFileSync(temporary, JSON.stringify(value,null,2)+'\n');
    fs.renameSync(temporary,target);
}
function canonical(value) {
    if(Array.isArray(value))return value.map(canonical);
    if(value && typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])]));
    return value;
}
function commandRecord(argv,cwd,exit_code,stdout,stderr) {
    const value={argv,cwd,exit_code,stdout,stderr};
    return {...value,log_sha256:sha(JSON.stringify(canonical(value)))};
}
function mergeFormProbe(output, report) {
    const bundle=fs.existsSync(output)?JSON.parse(fs.readFileSync(output,'utf8')):{schema:1};
    assert.notEqual(bundle.status,'complete','partial form probe cannot overwrite completed delivery');
    assert(report.bindings && report.commands?.length && report.assertions?.length,'Missing embedded probe evidence');
    bundle.form_probe={...report,status:report.status==='partial'?'passed':report.status,scope:'partial',complete:false};
    bundle.status=bundle.form_probe.status==='passed'?'provisional':'failed';
    atomicJSON(output,bundle);return bundle;
}
async function ownedForm(page, base, report) {
    const record = {id:'owned-form', passed:false, assertions:[]}; report.cases.push(record);
    const response = await page.goto(base+'/create/');
    check(record,'HTTP-200',response.status()===200);
    const raw = await (await page.request.get(base+'/observations/')).json();
    const owners=raw.last.forms.filter(f=>(f.attrs.class??'').split(' ').includes('cv-form'));
    const siblings=raw.last.forms.filter(f=>['aux-search','aux-action'].includes(f.attrs.id));
    check(record,'raw-no-nesting-one-owned-token',owners.length===1 && owners[0].tokens===1 && siblings.length===2 && siblings.every(f=>f.tokens===1) && raw.last.nested.length===0,raw.last);
    const ownership=await page.locator('form.cv-form').evaluate(form=>({
        method:form.method, encoding:form.enctype, action:form.action,
        submitSVG:[...form.querySelectorAll('[type=submit] svg path:not([stroke="none"])')].map(el=>el.getAttribute('d')),
        controls:[...form.querySelectorAll('input,button,select,textarea')].map(el=>({name:el.name,owned:el.form===form})),
        token:new FormData(form).getAll('csrfmiddlewaretoken').length,
        submitter:(()=>{const button=form.querySelector('[type=submit]');return new FormData(form,button).get(button.name)===button.value;})(),
    }));
    check(record,'native-controls-formdata-submitter',ownership.controls.length>3 && ownership.controls.every(c=>c.owned) && ownership.token===1 && ownership.submitter,ownership);
    check(record,'page-owned-attributes',ownership.method==='post' && ownership.encoding==='multipart/form-data');
    check(record,'real-frame-shadow',raw.last.templates.some(t=>t.name==='crud_views/snippets/form_frame.html' && t.origin.includes('/tabler-test/src/crud_views_tabler/')));
    record.passed=true;
}
async function control(locator) {
    return locator.evaluate(el=>({tag:el.tagName.toLowerCase(),type:el.getAttribute('type'),value:el.getAttribute('value'),
        href:el.getAttribute('href'),accessible_name:el.textContent.trim(),
        svg_paths:[...el.querySelectorAll('svg path:not([stroke="none"])')].map(p=>p.getAttribute('d')),
        visible_text:!!el.querySelector('span:not(.visually-hidden)'),hidden_text:!!el.querySelector('span.visually-hidden'),
        font_awesome:!!el.querySelector('i,[class*="fa-solid"],[class*="fa-regular"]'),
        attribute_present:el.hasAttribute('data-cv-cancel-url'),attribute_value:el.getAttribute('data-cv-cancel-url')}));
}
async function labelFloor(page,base,report) {
    const record={id:'label-floor',passed:false,assertions:[]};report.cases.push(record);report.actions=[];report.cancel_no_url=[];
    for(const mode of ['both','icon','label']) for(const [route,kinds] of [
        ['create',[['submit','check','form.cv-form [type=submit]'],['cancel','arrow-left','form.cv-form [type=button]']]],
        ['delete',[['delete','trash','form.cv-form [type=submit]']]],
        ['filter',[['filter-submit','filter','#filter-button'],['filter-reset','filter-x','#filter-button-reset']]],
    ]) {
        assert.equal((await page.goto(`${base}/${route}/?mode=${mode}&pinned=1`)).status(),200);
        for(const [kind,glyph,selector] of kinds) {
            const row={kind,mode,...await control(page.locator(selector)),source_sha256:report.source_sha256,passed:false};
            check(record,`${kind}-${mode}-native`,JSON.stringify(row.svg_paths)===JSON.stringify(mode==='label'?[]:report.native_icons[glyph]) && row.accessible_name && row.visible_text===(mode!=='icon') && row.hidden_text===(mode==='icon') && !row.font_awesome,row);
            if(kind==='filter-reset') {
                const input=page.locator('#filter-form input[name=name]');const initial=await input.inputValue();await input.fill('edited filter');
                await page.evaluate(()=>{sessionStorage.setItem('filterSubmits','0');sessionStorage.setItem('filterResets','0');
                    const form=document.querySelector('#filter-form');form.addEventListener('submit',()=>sessionStorage.setItem('filterSubmits','1'));
                    form.addEventListener('reset',()=>{sessionStorage.setItem('filterResets','1');setTimeout(()=>sessionStorage.setItem('filterNativeValue',form.elements.name.value),0);});});
                const navigation=page.waitForResponse(r=>r.request().isNavigationRequest() && r.url()===base+'/filter/?reset_filter=true');
                await page.locator(selector).click();const response=await navigation;await page.waitForLoadState('load');
                Object.assign(row,await page.evaluate(()=>({submit_events:+sessionStorage.getItem('filterSubmits'),reset_events:+sessionStorage.getItem('filterResets'),native_value:sessionStorage.getItem('filterNativeValue')})));
                row.reset_restored=row.reset_events===1 && row.native_value===initial && await input.inputValue()===initial;
                row.navigation={url:response.url(),status:response.status(),method:response.request().method()};
                check(record,`reset-${mode}`,row.type==='reset' && row.value && row.reset_restored && row.submit_events===0,row);
            }
            row.passed=true;report.actions.push(row);
        }
    }
    for(const [query,paths,hidden] of [['',report.native_icons.check,false],['?mode=label',[],false],['?mode=label&owner=icon',report.native_icons.check,true],['',report.native_icons.check,false]]) {
        await page.goto(base+'/create/'+query);const row=await control(page.locator('form.cv-form [type=submit]'));
        check(record,`floor-owner-restoration-${record.assertions.length}`,JSON.stringify(row.svg_paths)===JSON.stringify(paths) && row.hidden_text===hidden,row);
    }
    for(const destination of ['absent','none','empty']) for(const requested_tag of ['button','a']) for(const mode of ['both','icon','label']) for(const activation of ['click','Enter','Space']) {
        const url=`${base}/cancel/?destination=${destination}&tag=${requested_tag}&mode=${mode}`;
        await page.goto(url);await page.waitForFunction(()=>!!globalThis.cv?.adapters);
        const input=page.locator('form.cv-form input[name=first_name]');await input.fill('edited cancel input');
        const button=page.locator('form.cv-form [name=cancel]');
        const row={destination,requested_tag,mode,activation,...await control(button),source_sha256:report.source_sha256,
            input_before:await input.inputValue(),url_before:page.url(),navigation_intercepted:false,passed:false};
        check(record,`cancel-render-${destination}-${requested_tag}-${mode}-${activation}`,row.tag==='button' && row.type==='button' && row.href===null && row.accessible_name==='Cancel' && row.attribute_present===(destination==='empty') && row.attribute_value===(destination==='empty'?'':null) && JSON.stringify(row.svg_paths)===JSON.stringify(mode==='label'?[]:report.native_icons['arrow-left']),row);
        await page.evaluate(()=>{sessionStorage.setItem('cancel-submit','0');sessionStorage.setItem('cancel-reset','0');window.__cancelDocument=true;
            for(const event of ['submit','reset'])document.querySelector('form.cv-form').addEventListener(event,()=>sessionStorage.setItem('cancel-'+event,String(+sessionStorage.getItem('cancel-'+event)+1)));});
        let posts=0;const listener=request=>{if(request.method()==='POST')posts++;};page.on('request',listener);
        const navigation=destination==='empty' ? page.waitForResponse(r=>r.request().isNavigationRequest() && r.request().frame()===page.mainFrame() && r.url()===url) : null;
        if(activation==='click')await button.click();else await button.press(activation);
        if(navigation) {const response=await navigation;await page.waitForLoadState('load');await page.waitForFunction(()=>!window.__cancelDocument);
            Object.assign(row,{navigation:'same-url-get',document_replaced:true,document_method:response.request().method(),document_status:response.status()});
        } else {await delay(40);Object.assign(row,{navigation:'none',document_replaced:!await page.evaluate(()=>window.__cancelDocument===true)});}
        Object.assign(row,await page.evaluate(()=>({submit_events:+sessionStorage.getItem('cancel-submit'),reset_events:+sessionStorage.getItem('cancel-reset')})),{post_requests:posts,input_after:await input.inputValue(),url_after:page.url()});
        page.off('request',listener);
        check(record,`cancel-activation-${destination}-${requested_tag}-${mode}-${activation}`,row.submit_events===0 && row.reset_events===0 && posts===0 && row.url_before===row.url_after && (destination==='empty'?row.document_replaced && row.document_method==='GET' && row.document_status===200:!row.document_replaced && row.input_after===row.input_before),row);
        row.passed=true;report.cancel_no_url.push(row);
    }
    record.passed=true;
}
async function actionGroups(page,base,report) {
    const record={id:'action-groups',passed:false,assertions:[]};report.cases.push(record);
    for(const kind of ['create','filter'])for(const variant of ['default','custom','empty']) {
        await page.goto(`${base}/${kind}/?classes=${variant}&pinned=1`);
        const group=page.locator(kind==='create'?'form.cv-form .form-footer':'#filter-form .form-footer');
        const classes=(await group.getAttribute('class')).split(/\s+/);const expected=variant==='custom'?(kind==='create'?'ordinary-native':'filter-native'):variant==='default'?(kind==='create'?'gap-2':'gap-1'):null;
        check(record,`${kind}-${variant}`,classes.includes('form-footer') && (expected?classes.includes(expected):!classes.some(c=>/gap-|native/.test(c))) && !classes.includes(kind==='create'?'filter-native':'ordinary-native'),classes);
        if(kind==='filter')check(record,`filter-owner-hidden-${variant}`,await page.locator('#filter-form').getAttribute('method')==='get' && await page.locator('#filter-form input[name=sort]').count()===1);
        const observed=(await (await page.request.get(base+'/observations/')).json()).last;
        const names=kind==='filter'?['crud_views/tags/list_filter.html','crud_views/tags/list_filter.inner.html']:['crud_views/snippets/form_frame.html'];
        check(record,`${kind}-actual-shadow-origins-${variant}`,names.every(name=>observed.templates.some(t=>t.name===name && t.origin.startsWith(report.companion+'/src/crud_views_tabler/'))),observed.templates);
    }
    report.pack_probe=await (await page.request.get(base+'/pack-probe/')).json();
    check(record,'actual-pack-empty-bytes-and-escaped-class',report.pack_probe.before_empty===report.pack_probe.after_empty && report.pack_probe.escaped.includes('native&quot; &amp; &lt;class&gt;') && report.pack_probe.origin===report.companion+'/src/django_tabler/templates/crispy_tabler/layout/formactions.html',report.pack_probe);
    record.passed=true;
}
async function alerts(page,base,report) {
    const record={id:'alert-dismiss',passed:false,assertions:[]};report.cases.push(record);report.alert_branches=[];
    for(const native of [true,false])for(const variant of native?['default']:['default','custom','empty'])for(const activation of ['click','Enter','Space']) {
        await page.goto(`${base}/alerts/?native=${+native}&classes=${variant}`);await page.waitForFunction(()=>!!globalThis.tabler?.Alert);
        const frames=page.locator('[role=alert]');assert.equal(await frames.count(),2);
        const close=frames.first().locator('button');
        const hook=await close.evaluate(el=>({native:el.getAttribute('data-bs-dismiss'),crud:el.getAttribute('data-cv-alert-dismiss'),name:el.getAttribute('aria-label'),type:el.type}));
        check(record,`hooks-${native}-${variant}-${activation}`,hook.name==='Close' && hook.type==='button' && (native?hook.native==='alert' && hook.crud===null:hook.native===null && hook.crud===''),hook);
        if(native)check(record,'dependency-free-native',await page.evaluate(()=>typeof globalThis.cv==='undefined' && ![...document.scripts].some(s=>s.src.includes('/crud_views/'))));
        else {
            const classValue=await close.getAttribute('class');const frameClasses=(await frames.first().getAttribute('class')).split(/\s+/);
            check(record,`alert-classes-${variant}-${activation}`,classValue===(variant==='default'?'btn-close':variant==='custom'?'native-close':'') && (variant==='default'?frameClasses.includes('alert-dismissible'):!frameClasses.includes('alert-dismissible')) && frameClasses.includes('native-dismissible')===(variant==='custom'),{classValue,frameClasses});
            await page.evaluate(()=>{window.alertAdapterCalls=0;const close=cv.adapters.alert.close;cv.adapters.alert.close=function(...args){window.alertAdapterCalls++;return close.apply(this,args);};});
        }
        const observed=(await (await page.request.get(base+'/observations/')).json()).last;
        const name=native?'django_tabler/includes/messages.html':'crud_views/tags/alert.html';
        check(record,`actual-alert-origin-${native}-${variant}-${activation}`,observed.templates.some(t=>t.name===name && t.origin.startsWith(report.companion+'/src/')),observed.templates);
        if(activation==='click')await close.click();else await close.press(activation);
        await page.waitForFunction(()=>document.querySelectorAll('[role=alert]').length===1);
        const calls=native?null:await page.evaluate(()=>window.alertAdapterCalls);
        check(record,`dismiss-${native}-${variant}-${activation}`,(await frames.textContent()).trim().includes('Second notice') && (native || calls===1),{calls});
        report.alert_branches.push({native,variant,activation,hook,templates:observed.templates,adapter_calls:calls,passed:true});
    }
    record.passed=true;
}
async function ownedBranch(page,base,report,route,modal=false,status=200) {
    const observation=(await (await page.request.get(base+'/observations/')).json()).last;
    assert.equal(observation.route,`/${route}/`);assert.equal(observation.status,status);assert.equal(observation.modal,modal);
    const owners=observation.forms.filter(f=>(f.attrs.class??'').split(' ').includes('cv-form'));
    assert.equal(observation.nested.length,0);
    const omitted=route==='protected' || route==='workflow-none' && !modal;
    assert.equal(owners.length,omitted?0:1);if(!omitted)assert.equal(owners[0].tokens,1);
    if(route.startsWith('workflow')) {
        const names=observation.templates.map(t=>t.name);
        const expected=modal?['crud_views/view_custom_form.content.html']:['crud_views_workflow/view_workflow.content.html','crud_views_workflow/view_workflow.action.html'];
        for(const name of expected)assert(observation.templates.some(t=>t.name===name && t.origin.startsWith(report.core+'/src/')));
        if(modal)assert(!names.includes('crud_views_workflow/view_workflow.action.html'));
        assert.equal(observation.has_workflow_choices,route==='workflow');
        report.workflow_branches.push({...observation,passed:true});
    }
    return observation;
}
async function modalReplace(page,base,report) {
    const record={id:'modal-replace',passed:false,assertions:[]};report.cases.push(record);report.workflow_branches=[];
    for(const route of ['create','update','custom','delete','workflow','workflow-none','protected','parent-create','parent-update']) {
        assert.equal((await page.goto(`${base}/${route}/`)).status(),200);
        const observation=await ownedBranch(page,base,report,route);
        check(record,`full-${route}`,true,observation);
        if(route==='workflow-none')check(record,'full-no-choice-message',(await page.locator('body').textContent()).includes('There are no workflow steps available from the current state.'));
    }
    for(const route of ['custom','delete','workflow','workflow-none','protected']) {
        await page.goto(base+'/create/');await page.waitForFunction(()=>!!globalThis.tabler?.Modal && !!globalThis.cv?.cvModalOpen);
        const opener=page.locator('#launch');await opener.evaluate((el,route)=>el.setAttribute('href',`/${route}/`),route);
        await opener.focus();await page.keyboard.press('Enter');
        await page.locator('#cv-modal.show').waitFor();await page.waitForFunction(()=>!document.querySelector('#cv-modal').classList.contains('cv-loading'));
        check(record,`modal-get-${route}`,true,await ownedBranch(page,base,report,route,true));
        if(route!=='protected') {
            const response=page.waitForResponse(r=>r.url()===`${base}/${route}/` && r.request().method()==='POST');
            await page.locator('#cv-modal form').evaluate(form=>form.dataset.beforeReplacement='true');
            if(route==='workflow-none')await page.locator('#cv-modal form').evaluate(form=>{const field=document.createElement('input');field.name='transition';field.value='wf_activate';form.append(field);});
            await page.locator('#cv-modal form [type=submit]').click();
            assert.equal((await response).status(),422);await page.waitForFunction(()=>!document.querySelector('#cv-modal').classList.contains('cv-loading'));
            await page.waitForFunction(()=>document.querySelector('#cv-modal form') && !document.querySelector('#cv-modal form').hasAttribute('data-before-replacement'));
            check(record,`modal-422-${route}`,true,await ownedBranch(page,base,report,route,true,422));
            check(record,`modal-focus-${route}`,await page.evaluate(()=>document.querySelector('#cv-modal').contains(document.activeElement)));
        }
        await page.locator('#cv-modal [data-cv-modal-dismiss]').first().click();
        await page.waitForFunction(()=>!document.querySelector('#cv-modal').classList.contains('show') && document.activeElement.id==='launch');
        check(record,`return-focus-${route}`,true);
    }
    for(const route of ['create','update']) {
        const response=await page.request.get(`${base}/${route}/`,{headers:{'X-CV-Modal':'true'}});
        check(record,`unsupported-${route}-stays-full-page`,response.status()===200 && (await response.text()).includes('<!doctype html>'));
    }
    record.passed=true;
}
async function conditionalFormset(page,base,report) {
    const record={id:'conditional-formset',passed:false,assertions:[]};report.cases.push(record);
    for(const route of ['parent-create','parent-update']) {
        await page.goto(`${base}/${route}/`);const contact=page.locator('[name=contact]');await contact.fill('edited contact');
        await page.locator('[name=enabled]').uncheck();
        check(record,`${route}-conditional-off`,await contact.isDisabled() && !await contact.isVisible());
        await page.locator('[name=enabled]').check();
        check(record,`${route}-conditional-on`,!await contact.isDisabled() && await contact.isVisible());
        const total=page.locator('input[name^="books-"][name$="-TOTAL_FORMS"]').first();const before=+(await total.inputValue());
        const prefix=(await total.getAttribute('name')).slice(0,-'-TOTAL_FORMS'.length);
        await page.locator('.cv-form-ctrl-add[cv-data-formset-form-prefix^="books-"]').first().click();
        await page.waitForFunction(({prefix,before})=>+document.querySelector(`[name="${prefix}-TOTAL_FORMS"]`).value===before+1,{prefix,before});
        const title=page.locator(`[name="${prefix}-${before}-title"]`);await title.fill('Browser added book');
        check(record,`${route}-dynamic-native-ownership`,await title.evaluate(el=>el.form===document.querySelector('form.cv-form')));
        const data=await page.locator('form.cv-form').evaluate(form=>Object.fromEntries(new FormData(form)));
        check(record,`${route}-management-values`,+data[`${prefix}-TOTAL_FORMS`]===before+1 && data[`${prefix}-${before}-title`]==='Browser added book',data);
        const invalid=await page.request.post(`${base}/${route}/`,{form:{...data,name:''},maxRedirects:0});assert.equal(invalid.status(),200);
        check(record,`${route}-invalid-post-retains-management`,(await invalid.text()).includes('Browser added book'));
        check(record,`${route}-focus-visible`,await title.evaluate(el=>el===document.activeElement && !!el.getClientRects().length));
    }
    record.passed=true;
}
async function cancelNavigation(page,base,report) {
    const record={id:'cancel-navigation',passed:false,assertions:[]};report.cases.push(record);
    for(const activation of ['click','Enter','Space']) {
        await page.goto(base+'/create/');const cancel=page.locator('form.cv-form [data-cv-cancel-url]');const target=await cancel.getAttribute('data-cv-cancel-url');
        let posts=0;const listener=r=>{if(r.method()==='POST')posts++;};page.on('request',listener);
        await page.evaluate(()=>{sessionStorage.setItem('nav-submit','0');sessionStorage.setItem('nav-reset','0');for(const type of ['submit','reset'])document.querySelector('form.cv-form').addEventListener(type,()=>sessionStorage.setItem('nav-'+type,'1'));});
        const response=page.waitForResponse(r=>r.request().isNavigationRequest() && r.url()===base+target);
        if(activation==='click')await cancel.click();else await cancel.press(activation);
        assert.equal((await response).status(),200);await page.waitForLoadState('load');page.off('request',listener);
        check(record,`navigation-${activation}`,page.url()===base+target && posts===0 && await page.evaluate(()=>sessionStorage.getItem('nav-submit')==='0' && sessionStorage.getItem('nav-reset')==='0'));
    }
    record.passed=true;
}
async function csrfPost(page,base,report) {
    const record={id:'csrf-post',passed:false,assertions:[]};report.cases.push(record);
    await page.goto(base+'/create/');
    const sharedToken=await page.locator('form.cv-form [name=csrfmiddlewaretoken]').inputValue();
    for(const route of ['workflow-none','protected']) {
        const before=await (await page.request.get(base+'/snapshot/')).json();
        const response=await page.request.post(`${base}/${route}/`,{form:{csrfmiddlewaretoken:sharedToken,transition:'wf_activate',confirm:'on'},maxRedirects:0});
        check(record,`${route}-valid-token-still-refused`,response.status()===200);
        assert.deepEqual(await (await page.request.get(base+'/snapshot/')).json(),before);
        check(record,`${route}-omitted-after-post`,true,await ownedBranch(page,base,report,route));
    }
    for(const route of ['create','update','custom','workflow','delete']) {
        await page.goto(`${base}/${route}/`);const form=page.locator('form.cv-form');const token=await form.locator('[name=csrfmiddlewaretoken]').inputValue();
        const before=await (await page.request.get(base+'/snapshot/')).json();
        for(const bad of [null,'invalid']) {
            const response=await page.request.post(`${base}/${route}/`,{form:bad===null?{}:{csrfmiddlewaretoken:bad},maxRedirects:0});
            check(record,`${route}-csrf-${bad}`,response.status()===403);
        }
        assert.deepEqual(await (await page.request.get(base+'/snapshot/')).json(),before);
        const invalid=await page.request.post(`${base}/${route}/`,{form:{csrfmiddlewaretoken:token},maxRedirects:0});
        check(record,`${route}-invalid-post`,invalid.status()===200);
        check(record,`${route}-invalid-owner`,true,await ownedBranch(page,base,report,route));
        const data=route==='create'||route==='update'?{first_name:'Saved',last_name:'Browser'}:route==='custom'?{subject:'Ownership',body:'Native HTTP'}:route==='workflow'?{transition:'wf_activate',comment:''}:{confirm:'on'};
        const response=await page.request.post(`${base}/${route}/`,{form:{...data,csrfmiddlewaretoken:token,submit:'Save'},maxRedirects:0});
        check(record,`${route}-valid-post`,response.status()===302,{status:response.status(),location:response.headers().location});
    }
    await page.request.get(base+'/signin/?denied=1');
    const forbidden=await page.request.get(base+'/create/');check(record,'authorization-denied',forbidden.status()===403);
    await page.request.get(base+'/signin/');
    record.passed=true;
}
async function main() {
    const config=await configuration();
    const {port,opts,executable,root}=config;
    const work=fs.mkdtempSync(path.join(os.tmpdir(),'dcv-theme-'));
    const report={status:'running',scope:opts.case,cases:[],runtime:config.runtime,commands:[],cleanup:{},consoleErrors:[],pageErrors:[],coverageLimits:['Chromium automated checks only; no human visual or assistive-technology acceptance.']};
    let child,exit,browser,log='',serverOut='',serverErr='',serverArgv,serverCwd;
    try {
        const prepare=cp.spawnSync(executable,[path.join(root,'tests/browser/theme_adoption_server.py'),'--prepare',work,...(opts.case==='all'?['--full']:[]),...(opts['delivered-source'] ? ['--delivered-source',config.source] : [])],{cwd:root,encoding:'utf8',shell:false,maxBuffer:20*1024*1024});
        assert.equal(prepare.status,0,prepare.stderr);
        const prepared=JSON.parse(prepare.stdout); Object.assign(report,prepared);
        const env={...process.env,...prepared.env,CV_THEME_PORT:String(port),PYTHONUNBUFFERED:'1'};
        serverArgv=[executable,path.join(prepared.core,'tests/browser/theme_adoption_server.py'),'--serve'];serverCwd=prepared.companion;
        child=cp.spawn(executable,serverArgv.slice(1),{cwd:serverCwd,env,shell:false,stdio:['ignore','pipe','pipe']});
        child.stdout.on('data',v=>{log+=v;serverOut+=v;}); child.stderr.on('data',v=>{log+=v;serverErr+=v;});
        exit=new Promise((resolve,reject)=>{child.once('exit',(code,signal)=>resolve({code,signal}));child.once('error',reject);});
        await bounded((async()=>{while(!log.includes('"ready"')) {assert(child.exitCode===null,log);await delay(50);}})(),20000,'Server readiness timed out');
        const playwright=process.env.CV_FOCUS_PLAYWRIGHT ?? cached(path.join(os.homedir(),'.npm/_npx'),'node_modules/playwright');
        const chromium=process.env.CV_FOCUS_CHROMIUM ?? cached(path.join(os.homedir(),'.cache/ms-playwright'),'chrome-linux64/chrome');
        assert(playwright && chromium,'Missing cached browser assets');
        browser=await require(playwright).chromium.launch({executablePath:chromium,headless:true});
        report.browser={playwright,chromium,version:browser.version()};
        const context=await browser.newContext(); const page=await context.newPage(); page.setDefaultTimeout(6000);
        report.assets=[];const assetJobs=[];
        page.on('response',response=>{if(response.url().startsWith('https://cdn.jsdelivr.net/npm/@tabler/core@1.6.1/') || response.url()==='https://code.jquery.com/jquery-3.7.1.js')assetJobs.push((async()=>{
            const body=await response.body();const asset={url:response.url(),status:response.status(),sha256:sha(body),
                sri256:'sha256-'+crypto.createHash('sha256').update(body).digest('base64'),
                sri384:'sha384-'+crypto.createHash('sha384').update(body).digest('base64')};
            const previous=report.assets.find(a=>a.url===asset.url);if(previous)assert.equal(previous.sha256,asset.sha256,'Asset changed during run');else report.assets.push(asset);
        })());});
        page.on('pageerror',e=>report.pageErrors.push(e.message));
        page.on('console',m=>{if(m.type()==='error')report.consoleErrors.push(m.text());});
        const base=`http://127.0.0.1:${port}`;
        const login=await context.request.get(base+'/signin/');assert.equal(login.status(),200);
        const metadata=await login.json();assert.deepEqual(metadata.adoption,report.adoption);report.adoption=metadata.adoption;
        report.mode_support=metadata.mode_support;assert(report.mode_support.every(row=>row.supported===false && row.opt_in_checks.includes('viewset.E251')));
        await ownedForm(page,base,report);
        await page.waitForFunction(()=>!!globalThis.tabler?.Modal);
        await Promise.all(assetJobs);
        report.assetDeclarations=await page.locator('script[src^="https:"],link[href^="https:"]').evaluateAll(nodes=>nodes.map(el=>({url:el.src||el.href,integrity:el.integrity,crossorigin:el.crossOrigin})));
        for(const declared of report.assetDeclarations) {const asset=report.assets.find(a=>a.url===declared.url);assert(asset && [asset.sri256,asset.sri384].includes(declared.integrity),'Actual asset integrity mismatch');}
        for(const suffix of ['css/tabler.min.css','js/tabler-theme.min.js','js/tabler.min.js'])assert(report.assets.some(a=>a.url.endsWith(suffix)&&a.status===200&&a.sha256),`Missing real Tabler asset ${suffix}`);
        assert.equal(report.focused_result.outcome,'passed',report.focused_command.stderr);
        if(opts.case!=='owned-form') await labelFloor(page,base,report);
        if(opts.case==='all') {
            await actionGroups(page,base,report);
            await alerts(page,base,report);
            await modalReplace(page,base,report);
            await conditionalFormset(page,base,report);
            await cancelNavigation(page,base,report);
            await csrfPost(page,base,report);
            await Promise.all(assetJobs);
            assert(report.assets.some(a=>a.url==='https://code.jquery.com/jquery-3.7.1.js' && a.status===200),'Missing formset jQuery asset');
        }
        report.expectedHTTPConsoleErrors=report.consoleErrors.filter(message=>/^Failed to load resource: the server responded with a status of 422 \(Unprocessable Content\)$/.test(message));
        report.unexpectedConsoleErrors=report.consoleErrors.filter(message=>!report.expectedHTTPConsoleErrors.includes(message));
        assert.deepEqual(report.pageErrors,[]); assert.deepEqual(report.unexpectedConsoleErrors,[]);
        report.status=opts.case==='all'?'passed':'partial'; report.pending=['owned-form','csrf-post','label-floor','action-groups','alert-dismiss','modal-replace','conditional-formset','cancel-navigation'].filter(id=>!report.cases.some(c=>c.id===id&&c.passed));
    } catch(error) {report.status='failed';report.error=error.stack;process.exitCode=1;}
    finally {
        try {if(browser) await bounded(browser.close(),5000,'Browser cleanup timeout'); report.cleanup.browserClosed=true;}
        catch(error) {report.cleanup.browserError=error.message;report.status='failed';process.exitCode=1;}
        if(child && child.exitCode===null && child.signalCode===null)child.kill('SIGTERM');
        if(exit) {try {report.cleanup.serverExit=await bounded(exit,5000,'Server cleanup timeout');} catch {child.kill('SIGKILL');report.cleanup.serverExit=await exit;}}
        report.serverLog=log; fs.rmSync(work,{recursive:true,force:true});report.cleanup.temporaryRemoved=!fs.existsSync(work);
        if(report.preserved) {
            try {
                report.preserved_after=JSON.parse(cp.execFileSync(executable,[path.join(root,'tests/browser/theme_adoption_server.py'),'--preservation'],{cwd:root,encoding:'utf8',shell:false}));
                assert.deepEqual(report.preserved_after,report.preserved,'Original companion changed during isolated browser run');
                report.cleanup.originalUnchanged=true;
            } catch(error) {report.status='failed';report.cleanup.preservationError=error.message;process.exitCode=1;}
        }
        report.commands=[report.origin_command,report.focused_command, ...(serverArgv?[commandRecord(serverArgv,serverCwd,report.cleanup.serverExit?.code??1,serverOut,serverErr)]:[])].filter(Boolean);
        report.assertions=report.cases.flatMap(c=>c.assertions.map(a=>({...a,id:c.id+':'+a.id})));
        report.run_id=process.env.CV_THEME_PROBE_RUN_ID??null;
        if(opts['delivered-source'])mergeFormProbe(path.resolve(opts.output),report);else atomicJSON(path.resolve(opts.output),report);
        console.log(JSON.stringify({status:report.status,cases:report.cases.length,error:report.error}));
    }
}
module.exports={resolveCompanionPython,resolveSource,portValue,available,configuration,atomicJSON,mergeFormProbe,commandRecord};
if(require.main===module) main().catch(error=>{console.error(error.stack);process.exitCode=1;});
