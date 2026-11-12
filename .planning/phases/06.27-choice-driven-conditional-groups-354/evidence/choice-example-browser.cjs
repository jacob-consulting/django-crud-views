// Actual Bootstrap example, installed runtimes only. Captures live beside --output.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const net = require('node:net');
const root = cp.execFileSync('git', ['rev-parse', '--show-toplevel'], {encoding:'utf8'}).trim();
const REQUIRED = ['navigation', 'create', 'unsaved-return', 'shared-retained', 'wholesale-cleared',
    'consumer-clears-business', 'automatic-null-not-default', 'explicit-unset', 'saved-detail',
    'reopened-values', 'invalid-zero-write', 'native-reset', 'docs-link', 'keyboard-focus'];
const CELLS = ['select:390', 'select:1280', 'radio:390', 'radio:1280'];
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
function hashes() {
    const paths = cp.execFileSync('git', ['ls-files', 'examples/bootstrap5/conditional',
        'src/crud_views/lib/conditional', 'src/crud_views/templates/crud_views/conditional'], {cwd:root,encoding:'utf8'})
        .trim().split('\n');
    paths.push('examples/bootstrap5/project/settings.py', 'examples/bootstrap5/project/features.py',
        'examples/bootstrap5/project/tests.py', 'examples/bootstrap5/project/templates/project/snippet_panels.html',
        'examples/bootstrap5/project/templates/project/base.html', 'docs/reference/conditional.md',
        'docs/reference/javascript.md', 'src/crud_views/checks.py', 'src/crud_views/static/crud_views/js/toggle.js',
        'src/crud_views/static/crud_views/js/modal.js', 'package-lock.json', path.relative(root,__filename));
    return Object.fromEntries(paths.sort().map(file=>[file,hash(path.join(root,file))]));
}
function validateEvidence(record) {
    assert.equal(record.passed, true);
    assert.deepEqual(record.sourceHashes, hashes(), 'Stale or missing source hashes');
    assert.deepEqual(record.pageErrors, []);
    assert.deepEqual(record.failedAssets, []);
    assert.deepEqual(record.cleanup, {browserClosed:true, serverReaped:true, temporaryRemoved:true, developerDbUnchanged:true});
    assert.deepEqual(record.cases.map(c=>`${c.widget}:${c.width}`).sort(), [...CELLS].sort());
    for (const cell of record.cases) {
        assert.equal(cell.skipped, false);
        assert.deepEqual(cell.assertions.map(a=>a.id).sort(), [...REQUIRED].sort());
        for (const assertion of cell.assertions) {
            assert.equal(assertion.passed, true, assertion.id);
            assert.equal(assertion.skipped, false);
            assert.equal(assertion.widget, cell.widget);
            assert.equal(assertion.width, cell.width);
            assert(Object.hasOwn(assertion,'observed') && Object.hasOwn(assertion,'expected'));
            assert.deepEqual(assertion.observed, assertion.expected, assertion.id);
        }
    }
    assert.deepEqual(record.captures.map(c=>`${c.widget}:${c.width}`).sort(), ['radio:1280','select:1280']);
    for (const capture of record.captures) assert.equal(hash(path.resolve(root,capture.path)), capture.sha256);
    assert(fs.readFileSync(path.join(root,'site/reference/conditional/index.html'),'utf8').includes('id="choice-driven-groups"'));
    assert(record.runtime.django.startsWith('5.2.'));
    assert.equal(record.runtime.crud_views, path.join(root,'src/crud_views/__init__.py'));
}
function checkEvidence(file) {
    const record = JSON.parse(fs.readFileSync(file));
    validateEvidence(record);
    const mutations = [r=>r.cases.pop(), r=>r.cases[0].assertions.pop(), r=>r.cases.push(r.cases[0]),
        r=>r.cases[0].assertions[0].passed=false, r=>r.cases[0].skipped=true,
        r=>r.cases[0].assertions[0].skipped=true, r=>r.sourceHashes[Object.keys(r.sourceHashes)[0]]='stale',
        r=>delete r.cleanup, r=>r.captures[0].sha256='stale', r=>r.pageErrors.push('error'),
        r=>r.cases[0].assertions[0].observed='invented', r=>r.cases[0].width=768];
    for (const mutate of mutations) {
        const copy = structuredClone(record); mutate(copy);
        assert.throws(()=>validateEvidence(copy), 'Corruption accepted');
    }
    console.log(`CHOICE_EXAMPLE_EVIDENCE_OK ${record.cases.length} cells, ${mutations.length} corruption checks`);
}
const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));
async function main(output) {
    const python = process.env.CV_FOCUS_PYTHON || path.join(root,'.nox/tests-3-12-django-5-2/bin/python');
    const playwright = process.env.CV_FOCUS_PLAYWRIGHT || path.join(os.homedir(),'.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
    const chromium = process.env.CV_FOCUS_CHROMIUM || path.join(os.homedir(),'.cache/ms-playwright/chromium-1228/chrome-linux64/chrome');
    for (const installed of [python,playwright,chromium]) assert(fs.existsSync(installed),`Missing installed runtime ${installed}`);
    const temporary = fs.mkdtempSync(path.join(os.tmpdir(),'cv-choice-example-'));
    const env = {...process.env, PYTHONPATH:[temporary,path.join(root,'src'),path.join(root,'examples/bootstrap5')].join(path.delimiter),
        DJANGO_SETTINGS_MODULE:'choice_example_settings', PYTHONUNBUFFERED:'1'};
    const database = path.join(temporary,'db.sqlite3');
    const settings = `from project.settings import *\nDATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ${JSON.stringify(database)}}}\nMEDIA_ROOT = ${JSON.stringify(path.join(temporary,'media'))}\nALLOWED_HOSTS = ["127.0.0.1", "localhost"]\n`;
    fs.writeFileSync(path.join(temporary,'choice_example_settings.py'), settings);
    const developerDb = path.join(root,'examples/bootstrap5/db.sqlite3');
    const before = fs.existsSync(developerDb) ? hash(developerDb) : null;
    const record = {passed:false, started:new Date().toISOString(), humanReview:'pending', sourceHashes:hashes(),
        command:[process.execPath,__filename,...process.argv.slice(2)], commands:[], cases:[], captures:[],
        pageErrors:[], failedAssets:[], cleanup:{}, temporaryRoot:temporary, settings,
        revision:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim()};
    const run = args => {
        record.commands.push([python,...args]);
        return cp.execFileSync(python,args,{cwd:root,env,encoding:'utf8'});
    };
    const query = code => JSON.parse(run(['-c',`import django,json; django.setup(); ${code}`]).trim());
    const stored = name => query(`from conditional.models import Customer; print(json.dumps(list(Customer.objects.filter(name=${JSON.stringify(name)}).values())))`);
    let browser, server, exit, failure;
    try {
        record.runtime = {node:process.version, pythonPath:python, playwrightPath:playwright, chromiumPath:chromium,
            playwright:require(path.join(playwright,'package.json')).version,
            ...query('import sys,crud_views,importlib.metadata as m; print(json.dumps({"python":sys.version.split()[0],"django":django.get_version(),"crispy":m.version("django-crispy-forms"),"crispy_bootstrap5":m.version("crispy-bootstrap5"),"crud_views":crud_views.__file__}))')};
        assert(record.runtime.django.startsWith('5.2.'));
        assert.equal(record.runtime.crud_views,path.join(root,'src/crud_views/__init__.py'));
        run(['examples/bootstrap5/manage.py','migrate','--noinput']);
        run(['examples/bootstrap5/manage.py','seed']);
        const port = await new Promise((resolve,reject)=>{
            const probe=net.createServer(); probe.once('error',reject);
            probe.listen(0,'127.0.0.1',()=>{const p=probe.address().port; probe.close(()=>resolve(p));});
        });
        const base=`http://127.0.0.1:${port}`;
        record.base=base;
        const serverArgs=['examples/bootstrap5/manage.py','runserver',`127.0.0.1:${port}`,'--noreload'];
        record.commands.push([python,...serverArgs]);
        server=cp.spawn(python,serverArgs,{cwd:root,env,stdio:['ignore','pipe','pipe']});
        let serverLog=''; server.stdout.on('data',d=>serverLog+=d); server.stderr.on('data',d=>serverLog+=d);
        exit=new Promise(resolve=>server.once('exit',resolve));
        let ready=false;
        for(let i=0;i<150;i++) {try {ready=(await fetch(base+'/login/')).ok;} catch {} if(ready)break; await delay(100);}
        assert(ready,serverLog);
        browser=await require(playwright).chromium.launch({headless:true,executablePath:chromium,args:['--no-sandbox']});
        record.runtime.chromium=browser.version();
        for(const widget of ['select','radio']) for(const width of [390,1280]) {
            const cell={widget,width,skipped:false,assertions:[]}; record.cases.push(cell);
            const check=(id,observed,expected)=>{
                cell.assertions.push({id,widget,width,passed:true,skipped:false,observed,expected});
                assert.deepEqual(observed,expected,`${widget}:${width}:${id}`);
            };
            const context=await browser.newContext({viewport:{width,height:900},ignoreHTTPSErrors:true});
            const page=await context.newPage();
            page.on('pageerror',e=>record.pageErrors.push(String(e)));
            page.on('response',r=>{if(r.status()>=400 && /\.(css|js)(\?|$)/.test(r.url())) record.failedAssets.push({url:r.url(),status:r.status()});});
            await page.goto(base+'/login/');
            await page.locator('[name=username]').fill('alice'); await page.locator('[name=password]').fill('alice');
            await Promise.all([page.waitForURL(base+'/'),page.getByRole('button',{name:'Log In',exact:true}).click()]);
            await page.goto(base+'/conditional/registration/');
            await page.getByRole('link',{name:'Choice-driven customers',exact:true}).click();
            check('navigation',new URL(page.url()).pathname,'/conditional/customer/');
            const createPath=widget==='select'?'create/':'create-radio/';
            // Use the actual menu link, even when Bootstrap collapses it at this viewport.
            const createLink=page.locator(`.card-header a[href*="/customer/${createPath}"]`);
            assert.equal(await createLink.count(),1);
            await page.goto(new URL(await createLink.getAttribute('href'),base).href);
            const name=`Browser ${widget} ${width}`;
            const form=()=>page.locator('form.cv-form');
            const input=field=>form().locator(`[name="${field}"]`);
            const choose=async value=>{
                if(widget==='select') await input('kind').selectOption(value);
                else await form().locator(`[name=kind][value="${value}"]`).check();
            };
            const selected=()=>widget==='select'?input('kind').inputValue():form().locator('[name=kind]:checked').inputValue();
            const submit=async valid=>{
                const response=page.waitForResponse(r=>r.request().method()==='POST' && r.url().includes('/customer/'));
                await form().locator('button[type=submit]').filter({hasText:'Save'}).click();
                const result=await response;
                if(valid) {assert.equal(result.status(),302); await page.waitForURL(base+'/conditional/customer/');}
                else {assert.equal(result.status(),200); await page.locator('.invalid-feedback').first().waitFor();}
            };
            await input('name').fill(name);
            await choose('wholesale');
            // Server-required rules deliberately stay authoritative (including with native validation bypassed).
            await form().evaluate(el=>el.noValidate=true);
            await submit(false);
            assert.deepEqual(stored(name),[]);
            assert.equal(await selected(),'wholesale');
            await input('company').fill('Shared Company'); await input('price_tier').selectOption('B');
            await input('payment_terms').selectOption('net60'); await input('wholesale_terms').selectOption('0');
            await choose('consumer'); await choose('wholesale');
            check('unsaved-return',[await input('company').inputValue(),await input('wholesale_terms').inputValue()],['Shared Company','0']);
            await submit(true);
            let row=stored(name)[0];
            check('create',{kind:row.kind,name:row.name,company:row.company,wholesale_terms:row.wholesale_terms},
                {kind:'wholesale',name,company:'Shared Company',wholesale_terms:0});
            const update=base+`/conditional/customer/${row.id}/${widget==='select'?'update':'update-radio'}/`;
            await page.goto(update);
            // The form's named Reset control shadows form.reset; call the native method directly.
            await choose('consumer'); await form().evaluate(el=>HTMLFormElement.prototype.reset.call(el));
            await page.waitForFunction(()=>document.querySelector('[name=company]').disabled===false);
            check('native-reset',[await selected(),await input('company').inputValue()],['wholesale','Shared Company']);
            const control=widget==='select'?input('kind'):form().locator('[name=kind]:checked');
            await control.focus(); await page.keyboard.press('ArrowDown');
            if(widget==='select') await page.keyboard.press('Enter');
            assert.equal(await selected(),'distributor');
            check('keyboard-focus',await page.evaluate(()=>document.activeElement.name),'kind');
            check('shared-retained',[await input('company').inputValue(),await input('price_tier').inputValue(),await input('payment_terms').inputValue()],
                ['Shared Company','B','net60']);
            await input('distribution_region').fill('North'); await submit(true);
            row=stored(name)[0];
            check('wholesale-cleared',{kind:row.kind,company:row.company,wholesale_terms:row.wholesale_terms,region:row.distribution_region},
                {kind:'distributor',company:'Shared Company',wholesale_terms:null,region:'North'});
            await page.goto(update);
            const docsURL='https://django-crud-views.readthedocs.io/en/stable/reference/conditional/#choice-driven-groups';
            check('docs-link',{links:await page.locator(`a[href="${docsURL}"]`).count(),
                anchor:fs.readFileSync(path.join(root,'site/reference/conditional/index.html'),'utf8').includes('id="choice-driven-groups"'),
                explanation:(await page.locator('body').innerText()).includes('Wholesale and Distributor keep their shared business details')},
                {links:1,anchor:true,explanation:true});
            if(width===1280) {
                const staged=path.join(temporary,`choice-${widget}.png`);
                await page.screenshot({path:staged,fullPage:true});
                const destination=path.join(path.dirname(output),`choice-${widget}.png`);
                record.captures.push({widget,width,path:path.relative(root,destination),sha256:hash(staged)});
            }
            // Send a real invalid controller through the real editor with CSRF/session intact.
            const snapshot=stored(name);
            if(widget==='select') await input('kind').evaluate(el=>{el.add(new Option('Forged','forged')); el.value='forged';});
            else await form().locator('[name=kind]:checked').evaluate(el=>el.value='forged');
            await form().evaluate(el=>el.noValidate=true); await submit(false);
            check('invalid-zero-write',stored(name),snapshot);
            await page.goto(update); await choose('consumer'); await input('consumer_note').fill('Outside business');
            await submit(true); row=stored(name)[0];
            check('consumer-clears-business',{name:row.name,kind:row.kind,company:row.company,region:row.distribution_region,wholesale:row.wholesale_terms},
                {name,kind:'consumer',company:null,region:'',wholesale:null});
            check('automatic-null-not-default',row.price_tier,null);
            check('explicit-unset',row.payment_terms,'unset');
            await page.goto(base+`/conditional/customer/${row.id}/detail/`);
            const detail=await page.locator('body').innerText();
            check('saved-detail',{name:detail.includes(name),null:detail.includes('None'),unset:detail.includes('unset'),note:detail.includes('Outside business')},
                {name:true,null:true,unset:true,note:true});
            await page.goto(update);
            check('reopened-values',{kind:await selected(),name:await input('name').inputValue(),company:await input('company').inputValue(),
                price:await input('price_tier').inputValue(),payment:await input('payment_terms').inputValue(),region:await input('distribution_region').inputValue()},
                {kind:'consumer',name,company:'',price:'',payment:'unset',region:''});
            await context.close();
        }
        assert.deepEqual(record.pageErrors,[]); assert.deepEqual(record.failedAssets,[]);
        assert.deepEqual(record.sourceHashes,hashes(),'Sources changed during run');
        fs.mkdirSync(path.dirname(output),{recursive:true});
        for(const capture of record.captures) fs.copyFileSync(path.join(temporary,`choice-${capture.widget}.png`),path.resolve(root,capture.path));
    } catch(error) { failure=error; }
    finally {
        try {if(browser) await browser.close(); record.cleanup.browserClosed=true;} catch(error) {failure ||= error;}
        try {
            if(server) {
                if(server.exitCode===null && server.signalCode===null) server.kill('SIGTERM');
                let timer;
                try {await Promise.race([exit,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Server cleanup timeout')),5000);})]);}
                finally {clearTimeout(timer);}
            }
            record.cleanup.serverReaped=true;
        } catch(error) {failure ||= error; if(server) server.kill('SIGKILL');}
        try {fs.rmSync(temporary,{recursive:true,force:true}); record.cleanup.temporaryRemoved=!fs.existsSync(temporary);}
        catch(error) {failure ||= error;}
        record.cleanup.developerDbUnchanged=before===(fs.existsSync(developerDb)?hash(developerDb):null);
    }
    if(failure) throw failure;
    record.passed=true; record.completed=new Date().toISOString();
    validateEvidence(record);
    fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
    checkEvidence(output);
}
if(require.main===module) {
    const args=process.argv.slice(2), index=args.indexOf('--output');
    assert(index>=0 && args[index+1] && !args[index+1].startsWith('--'),'Pass --output FILE');
    const output=path.resolve(args[index+1]);
    (args.includes('--check-evidence') ? Promise.resolve().then(()=>checkEvidence(output)) : main(output))
        .catch(error=>{console.error(error);process.exitCode=1;});
}
module.exports={validateEvidence,checkEvidence,hashes,REQUIRED,CELLS};
