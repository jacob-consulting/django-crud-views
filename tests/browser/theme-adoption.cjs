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
async function main() {
    const config=await configuration();
    const {port,opts,executable,root}=config;
    const work=fs.mkdtempSync(path.join(os.tmpdir(),'dcv-theme-'));
    const report={status:'running',scope:opts.case,cases:[],runtime:config.runtime,commands:[],cleanup:{},consoleErrors:[],pageErrors:[],coverageLimits:['Chromium automated checks only; no human visual or assistive-technology acceptance.']};
    let child,exit,browser,log='';
    try {
        const prepare=cp.spawnSync(executable,[path.join(root,'tests/browser/theme_adoption_server.py'),'--prepare',work,...(opts['delivered-source'] ? ['--delivered-source',config.source] : [])],{cwd:root,encoding:'utf8',shell:false,maxBuffer:20*1024*1024});
        assert.equal(prepare.status,0,prepare.stderr);
        const prepared=JSON.parse(prepare.stdout); Object.assign(report,prepared);
        const env={...process.env,...prepared.env,CV_THEME_PORT:String(port),PYTHONUNBUFFERED:'1'};
        child=cp.spawn(executable,[path.join(prepared.core,'tests/browser/theme_adoption_server.py'),'--serve'],{cwd:prepared.companion,env,shell:false,stdio:['ignore','pipe','pipe']});
        child.stdout.on('data',v=>log+=v); child.stderr.on('data',v=>log+=v);
        exit=new Promise((resolve,reject)=>{child.once('exit',(code,signal)=>resolve({code,signal}));child.once('error',reject);});
        await bounded((async()=>{while(!log.includes('"ready"')) {assert(child.exitCode===null,log);await delay(50);}})(),20000,'Server readiness timed out');
        const playwright=process.env.CV_FOCUS_PLAYWRIGHT ?? cached(path.join(os.homedir(),'.npm/_npx'),'node_modules/playwright');
        const chromium=process.env.CV_FOCUS_CHROMIUM ?? cached(path.join(os.homedir(),'.cache/ms-playwright'),'chrome-linux64/chrome');
        assert(playwright && chromium,'Missing cached browser assets');
        browser=await require(playwright).chromium.launch({executablePath:chromium,headless:true});
        report.browser={playwright,chromium,version:browser.version()};
        const context=await browser.newContext(); const page=await context.newPage(); page.setDefaultTimeout(6000);
        page.on('pageerror',e=>report.pageErrors.push(e.message));
        page.on('console',m=>{if(m.type()==='error')report.consoleErrors.push(m.text());});
        const base=`http://127.0.0.1:${port}`;
        assert.equal((await context.request.get(base+'/signin/')).status(),200);
        await ownedForm(page,base,report);
        assert.deepEqual(report.pageErrors,[]); assert.deepEqual(report.consoleErrors,[]);
        report.status='partial'; report.pending=['csrf-post','label-floor','action-groups','alert-dismiss','modal-replace','conditional-formset','cancel-navigation'];
    } catch(error) {report.status='failed';report.error=error.stack;process.exitCode=1;}
    finally {
        try {if(browser) await bounded(browser.close(),5000,'Browser cleanup timeout'); report.cleanup.browserClosed=true;}
        catch(error) {report.cleanup.browserError=error.message;report.status='failed';process.exitCode=1;}
        if(child && child.exitCode===null && child.signalCode===null)child.kill('SIGTERM');
        if(exit) {try {report.cleanup.serverExit=await bounded(exit,5000,'Server cleanup timeout');} catch {child.kill('SIGKILL');report.cleanup.serverExit=await exit;}}
        report.serverLog=log; fs.rmSync(work,{recursive:true,force:true});report.cleanup.temporaryRemoved=!fs.existsSync(work);
        atomicJSON(path.resolve(opts.output),report);
        console.log(JSON.stringify({status:report.status,cases:report.cases.length,error:report.error}));
    }
}
module.exports={resolveCompanionPython,resolveSource,portValue,available,configuration,atomicJSON};
if(require.main===module) main().catch(error=>{console.error(error.stack);process.exitCode=1;});
