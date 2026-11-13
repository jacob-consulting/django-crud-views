// Bounded real-page acceptance runner. Self-tests never start Django or Chromium.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const REQUIRED = {upstream: ['standalone', 'ordinary', 'compact', 'lifecycle', 'mutation', 'navigation'],
    downstream:['orders','retained-products','mutation','printing']};
function parseArgs(args) {
    const result = {};
    for (let i = 0; i < args.length; i++) {
        const flag = args[i];
        assert(['--target', '--output', '--self-test'].includes(flag), `Unknown argument ${flag}`);
        const key = flag.slice(2);
        assert(!Object.hasOwn(result, key), `Repeated ${flag}`);
        if (flag === '--self-test') result[key] = true;
        else { assert(args[i + 1] && !args[i + 1].startsWith('--'), `Missing ${flag}`); result[key] = args[++i]; }
    }
    assert(Object.hasOwn(REQUIRED, result.target), 'Unknown or missing target');
    assert(!(result['self-test'] && result.output), '--self-test cannot write acceptance evidence');
    assert(result['self-test'] || result.output, 'Acceptance requires --output');
    return result;
}
function validateEvidence(record, target, sources, hashes) {
    assert.equal(record.target, target);
    assert.deepEqual(record.sources, sources);
    assert.deepEqual(record.sourceHashes, hashes);
    assert.deepEqual(record.scenarios.map(s => s.id).sort(), [...REQUIRED[target]].sort());
    for (const scenario of record.scenarios) {
        assert(scenario.assertions.length > 0, `Empty ${scenario.id}`);
        assert.equal(scenario.dbConfirmed, true, `Missing database proof ${scenario.id}`);
        for (const assertion of scenario.assertions) assert.equal(assertion.passed, true, assertion.id);
    }
    assert.equal(record.cleanup.reaped, true);
    assert.equal(record.cleanup.temporaryRemoved, true);
}
async function cleanup(resources) {
    try { if (resources.browser) await resources.browser.close(); }
    finally {
        try {
            const child = resources.child;
            if (child && child.exitCode === null && child.signalCode === null) {
                await new Promise((resolve, reject) => {
                    const timer = setTimeout(() => { child.kill('SIGKILL'); reject(new Error('Host cleanup timed out')); }, 5000);
                    child.once('exit', () => { clearTimeout(timer); resolve(); });
                    child.kill('SIGTERM');
                });
            }
        } finally { if (resources.dir) fs.rmSync(resources.dir, {recursive: true, force: true}); }
    }
    return {reaped: !resources.child || resources.child.exitCode !== null || resources.child.signalCode !== null,
        temporaryRemoved: !fs.existsSync(resources.dir)};
}
const digest = data => crypto.createHash('sha256').update(data).digest('hex');
function fingerprint(sources, docs = false) {
    const entries = [];
    for (const [label, root] of Object.entries(sources)) {
        if (!root) continue;
        const files = cp.execFileSync('git', ['ls-files', '-co', '--exclude-standard', '-z'], {cwd: root}).toString().split('\0');
        for (const file of new Set(files)) {
            if (!file || !fs.existsSync(path.join(root, file))) continue;
            const include = docs ? file.startsWith('docs/') && file !== 'docs/crud_views_upstream_findings_roastery.md'
                : /^(src\/|tests\/|examples\/|example\/|package(-lock)?\.json$|pyproject\.toml$|uv\.lock$|noxfile\.py$|pytest\.ini$|vitest.*|mkdocs\.yml$)/.test(file);
            if (include && fs.statSync(path.join(root, file)).isFile()) entries.push([`${label}/${file}`, digest(fs.readFileSync(path.join(root, file)))]);
        }
    }
    return Object.fromEntries(entries.sort(([a], [b]) => a.localeCompare(b)));
}
async function selfTest(target) {
    const started = Date.now();
    let count = 0;
    const test = (name, callback) => { callback(); count++; console.log(`ok ${name}`); };
    test('parse target', () => assert.equal(parseArgs(['--self-test', '--target', target]).target, target));
    for (const args of [['--target', 'other'], ['--unknown'], ['--self-test', '--output', 'x'], ['--target']]) {
        test(`reject ${args.join(' ')}`, () => assert.throws(() => parseArgs(args)));
    }
    const sources = {upstream: '/expected/upstream', downstream: target === 'downstream' ? '/expected/downstream' : null};
    const valid = {target, sources, sourceHashes: {'upstream/src/example.py': 'abc'},
        scenarios: REQUIRED[target].map(id => ({id, assertions: [{id: 'observed', passed: true}], dbConfirmed: true})),
        cleanup: {reaped: true, temporaryRemoved: true}};
    if(target==='downstream') valid.scenarios[0].assertions.push(...['retained-product','print-handler','row-insertion','persisted-clearing'].map(id=>({id,passed:true})));
    test('accept complete target', () => validateEvidence(valid, target, sources, valid.sourceHashes));
    if(target==='downstream') {
        for(const id of ['retained-product','print-handler','row-insertion','persisted-clearing']) test(`missing ${id}`,()=>{
            const r=structuredClone(valid);r.scenarios[0].assertions=r.scenarios[0].assertions.filter(a=>a.id!==id);
            assert.throws(()=>validateEvidence(r,target,sources,valid.sourceHashes));
        });
        test('reject substituted upstream',()=>{const r=structuredClone(valid);r.target='upstream';assert.throws(()=>validateEvidence(r,target,sources,valid.sourceHashes));});
        test('reject wrong downstream source',()=>{const r=structuredClone(valid);r.sources.downstream='/wrong';assert.throws(()=>validateEvidence(r,target,sources,valid.sourceHashes));});
    }
    for (const [name, corrupt] of [
        ['zero scenarios', r => r.scenarios = []],
        ['missing scenario', r => r.scenarios.pop()],
        ['false assertion', r => r.scenarios[0].assertions[0].passed = false],
        ['false database proof', r => r.scenarios[0].dbConfirmed = false],
        ['wrong source', r => r.sources.upstream = '/wrong'],
        ['stale fingerprint', r => r.sourceHashes = {}],
        ['failed cleanup', r => r.cleanup.reaped = false],
    ]) test(name, () => { const r = structuredClone(valid); corrupt(r); assert.throws(() => validateEvidence(r, target, sources, valid.sourceHashes)); });
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-queryset-self-'));
    const child = cp.spawn(process.execPath, ['-e', 'setInterval(() => {}, 1000)']);
    const resources = {dir, child};
    await assert.rejects(async () => {
        try { throw new Error('injected scenario failure'); }
        finally { await cleanup(resources); }
    }, /injected scenario failure/);
    test('exception cleanup reaps child and removes directory', () => {
        assert(child.exitCode !== null || child.signalCode !== null);
        assert(!fs.existsSync(dir));
    });
    assert(count > 0);
    console.log(`SELF_TEST_OK ${target}: ${count} named assertions in ${Date.now() - started}ms`);
}
async function run(options) {
    const root = fs.realpathSync(process.env.CV_QUERYSET_UPSTREAM || path.resolve(__dirname, '../..'));
    const sources = {upstream: root, downstream: options.target === 'downstream'
        ? fs.realpathSync(process.env.CV_QUERYSET_DOWNSTREAM || '/home/alex/projects/alex/tabler-test') : null};
    const python = process.env.CV_QUERYSET_PYTHON || path.join(sources.downstream || root, '.venv/bin/python');
    const playwright = process.env.CV_QUERYSET_PLAYWRIGHT || '/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
    const chromium = process.env.CV_QUERYSET_CHROMIUM || '/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome';
    for (const file of [python, playwright, chromium]) assert(fs.existsSync(file), `Missing existing executable ${file}`);
    const output = path.resolve(options.output);
    const captures = path.join(path.dirname(output), `08-${options.target}-captures`);
    fs.mkdirSync(captures, {recursive: true});
    const resources = {dir: fs.mkdtempSync(path.join(os.tmpdir(), 'cv-queryset-'))};
    const secret = crypto.randomBytes(24).toString('hex');
    const record = {target: options.target, sources, started: new Date().toISOString(), command: process.argv,
        sourceHashes: fingerprint(sources), docsHashes: fingerprint(sources, true), scenarios: [], captures: [],
        provenance: Object.fromEntries(Object.entries(sources).filter(([,r])=>r).map(([k,r])=>[k, {
            head: cp.execFileSync('git',['rev-parse','HEAD'],{cwd:r}).toString().trim(),
            status: cp.execFileSync('git',['status','--short'],{cwd:r}).toString()}])),
        runtime: {node: process.version, nodePath: process.execPath, pythonPath: python, playwrightPath: playwright,
            playwright: require(path.join(playwright, 'package.json')).version, chromiumPath: chromium,
            packageLockHash: digest(fs.readFileSync(path.join(root, 'package-lock.json')))}, pageErrors: [], failedRequests: []};
    let hostOutput = '';
    try {
        resources.child = cp.spawn(python, [path.join(root, 'tests/browser', options.target === 'upstream'
            ? 'queryset_conditional_server.py' : 'queryset_downstream_server.py')], {cwd: root, env: {...process.env,
            PYTHONDONTWRITEBYTECODE:'1', PYTHONPATH:[path.join(root,'src'), sources.downstream ? path.join(sources.downstream,'src') : '',
                path.join(sources.downstream || root, sources.downstream ? 'example' : 'examples/bootstrap5')].filter(Boolean).join(':'),
            CV_QUERYSET_UPSTREAM:root, CV_QUERYSET_DOWNSTREAM:sources.downstream || '', CV_QUERYSET_TEMP:resources.dir, CV_QUERYSET_SECRET:secret}});
        resources.child.stderr.on('data', chunk => { hostOutput += chunk; });
        const ready = await new Promise((resolve, reject) => {
            let stdout = '';
            const timer = setTimeout(() => reject(new Error(`Host startup timed out: ${hostOutput}`)), 60000);
            resources.child.once('exit', code => { clearTimeout(timer); reject(new Error(`Host exited ${code}: ${hostOutput}`)); });
            resources.child.stdout.on('data', chunk => {
                stdout += chunk;
                for (const line of stdout.split('\n')) if (line.startsWith('{"port":')) {
                    clearTimeout(timer); resolve(JSON.parse(line)); return;
                }
            });
        });
        const base = `http://127.0.0.1:${ready.port}`;
        resources.browser = await require(playwright).chromium.launch({headless:true, executablePath:chromium, args:['--no-sandbox']});
        record.runtime.chromium = resources.browser.version();
        const context = await resources.browser.newContext({viewport:{width:1280,height:900}});
        const page = await context.newPage();
        page.on('pageerror', error => record.pageErrors.push(String(error)));
        page.on('requestfailed', request => record.failedRequests.push({url:request.url(), error:request.failure().errorText}));
        page.setDefaultTimeout(10000);
        await page.goto(`${base}/login/`);
        await page.locator('[name="username"]').fill('browser');
        await page.locator('[name="password"]').fill('browser-only-password');
        await Promise.all([page.waitForURL(url => !url.pathname.includes('login'),{waitUntil:'domcontentloaded'}),
            page.locator('form').filter({has:page.locator('[name="username"]')}).locator('button[type="submit"],input[type="submit"]').click()]);
        const state = async mutation => {
            const cookies = await context.cookies(base);
            const response = await context.request[mutation ? 'post' : 'get'](`${base}/__fixture__/state/`, {
                headers:{'X-Fixture-Key':secret, 'X-CSRFToken':cookies.find(c=>c.name==='csrftoken').value}, ...(mutation ? {data:mutation} : {})});
            assert.equal(response.status(),200, await response.text()); return response.json();
        };
        const initial = await state();
        assert.equal(initial.runtime.source, path.join(root,'src/crud_views/__init__.py'));
        assert.equal(initial.runtime.settings, options.target === 'upstream' ? 'project.settings' : 'config.settings');
        Object.assign(record.runtime, initial.runtime);
        const visit = async url => { const response = await page.goto(`${base}${url}`); assert.equal(response.status(),200, `GET ${url}`); assert((await page.content()).includes('<form')); };
        await visit(initial.urls.standalone || initial.urls.order);
        const toggleURL = await page.locator('script[src*="/toggle.js"]').getAttribute('src');
        const toggle = await context.request.get(new URL(toggleURL, base).href);
        assert.equal(toggle.status(),200);
        const actual = await toggle.body(), expected = fs.readFileSync(path.join(root,'src/crud_views/static/crud_views/js/toggle.js'));
        assert.deepEqual(actual, expected, 'Actually loaded toggle.js differs from asserted source');
        record.servedToggle = {url:new URL(toggleURL,base).href, expectedHash:digest(expected), actualHash:digest(actual)};
        const scenario = id => { const s={id,assertions:[],dbConfirmed:false}; record.scenarios.push(s); console.log(`SCENARIO ${id}`); return s; };
        const check = (s,id,actual,expected=true) => { assert.deepEqual(actual,expected,`${s.id}: ${id}`); s.assertions.push({id,passed:true,actual,expected}); };
        const capture = async name => { const file=path.join(captures,`${name}.png`); await page.screenshot({path:file,fullPage:true}); record.captures.push({path:path.relative(root,file),sha256:digest(fs.readFileSync(file))}); };
        const post = async overrides => {
            const payload = await page.locator('form').filter({has:page.locator('[cv-data-toggle-group]')}).first().evaluate(form => Object.fromEntries(new FormData(form)));
            const response = await context.request.post(page.url(),{form:{...payload,...overrides},maxRedirects:0});
            return {status:response.status(),html:await response.text(), location:response.headers().location};
        };
        const env={page,context,base,state,initial,visit,scenario,check,capture,post,record};
        if(options.target==='upstream') await upstream(env); else await downstream(env);
        assert.deepEqual(record.pageErrors,[], 'Browser uncaught errors');
        assert.deepEqual(record.failedRequests,[], 'Required page assets failed');
    } catch(error) { console.error(`Host tail: ${hostOutput.slice(-5000)}`); throw error; }
    finally { record.cleanup = await cleanup(resources); }
    assert.deepEqual(fingerprint(sources),record.sourceHashes,'Sources changed during browser run');
    validateEvidence(record,options.target,sources,record.sourceHashes);
    record.completed=new Date().toISOString();
    fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
    console.log(`BROWSER_OK ${record.target}: ${record.scenarios.length} scenarios, ${record.scenarios.reduce((n,s)=>n+s.assertions.length,0)} assertions; ${output}`);
}
async function fields(page, suffix) { return page.locator(`select[name$="${suffix}"]`).evaluateAll(nodes=>nodes.map(n=>n.name)); }
async function value(page,name) { return page.evaluate(name=>Array.from(document.querySelectorAll('[name]')).find(e=>e.name===name).value,name); }
async function set(page,name,val) {
    await page.evaluate(({name,val})=>{const e=Array.from(document.querySelectorAll('[name]')).find(e=>e.name===name);e.value=String(val);e.dispatchEvent(new Event('change',{bubbles:true}));},{name,val});
}
async function info(page,name) {
    return page.evaluate(name=>{
        const e=Array.from(document.querySelectorAll('[name]')).find(e=>e.name===name), group=e.closest('[cv-data-toggle-group]');
        const cell=group || e.parentElement, rect=cell.getBoundingClientRect();
        return {value:e.value,disabled:e.disabled,visible:!!cell.getClientRects().length,display:getComputedStyle(cell).display,
            x:rect.x,y:rect.y,width:rect.width,height:rect.height,label:!!e.labels?.length,focused:document.activeElement===e};
    },name);
}
async function upstream(e) {
    const {page,state,initial,visit,scenario,check,capture,post}=e;
    const services=initial.services, on=String(services['Boiler inspection']), shared=String(services['Appliance installation']),
        off=String(services['Document review']);
    let s=scenario('standalone');
    await visit(initial.urls.standalone);
    for(const width of [1280,390]) {
        await page.setViewportSize({width,height:900});
        await set(page,'visit_address','Unsaved address');
        await set(page,'service',shared);
        check(s,`shared-keeps-${width}`,(await info(page,'visit_address')).value,'Unsaved address');
        await set(page,'service',off);
        check(s,`ordinary-hidden-${width}`,(await info(page,'visit_address')).visible,false);
        await set(page,'service',on);
        check(s,`away-back-${width}`,await value(page,'visit_address'),'Unsaved address');
        await set(page,'service','');
        check(s,`blank-disables-${width}`,(await info(page,'visit_address')).disabled);
        await set(page,'service',on);
        check(s,`label-${width}`,(await info(page,'visit_address')).label);
        await capture(`standalone-${width}`);
    }
    const before=await state();
    await set(page,'visit_address','');
    await Promise.all([page.waitForNavigation(),page.evaluate(()=>HTMLFormElement.prototype.submit.call(document.querySelector('[name="service"]').form))]);
    const errors=await page.locator('[name="visit_address"]').evaluate(field=>({invalid:field.getAttribute('aria-invalid'),
        described:(field.getAttribute('aria-describedby')||'').split(' ').some(id=>document.getElementById(id)?.textContent.includes('required')),
        labelled:!!field.labels.length}));
    check(s,'accessible-required-error',errors,{invalid:'true',described:true,labelled:true});
    await page.locator('[name="service"]').focus();await page.keyboard.press('Tab');
    check(s,'keyboard-active-field',(await info(page,'visit_address')).focused);
    await capture('standalone-error-390');
    let response=await post({service:on,visit_address:''});
    check(s,'active-required-status',response.status,200);
    check(s,'active-required-error',response.html.includes('This field is required'));
    check(s,'active-required-zero-write',(await state()).requests,before.requests);
    response=await post({service:'99999999',visit_address:'forged'});
    check(s,'forged-zero-write',(await state()).requests,before.requests);
    check(s,'forged-native-error',response.html.includes('Select a valid choice'));
    response=await post({service:off,visit_address:'forged inactive',meeting_url:'invalid URL'});
    check(s,'no-js-tampered-save',response.status,302);
    await visit(initial.urls.standalone);
    check(s,'fresh-get-cleared',await value(page,'visit_address'),'');
    check(s,'db-cleared',(await state()).requests.find(r=>r.batch_id===null).visit_address,''); s.dbConfirmed=true;
    for(const variant of ['ordinary','compact']) {
        s=scenario(variant); await visit(initial.urls[variant]);
        let names=await fields(page,'-service'), first=names[0], second=names[1];
        const address=first.replace(/service$/,'visit_address'), remote=second.replace(/service$/,'meeting_url');
        for(const width of [1280,390]) {
            await page.setViewportSize({width,height:900});
            await set(page,address,'Preserved row address');
            const other=await info(page,remote), parent=await value(page,'title'), geometry=await info(page,address);
            if(variant==='compact') await page.evaluate(name=>Array.from(document.querySelectorAll('[name]')).find(n=>n.name===name).focus(),address);
            await set(page,first,off);
            const disabled=await info(page,address);
            check(s,`inactive-disabled-${width}`,disabled.disabled);
            check(s,`layout-${width}`,disabled.visible,variant==='compact');
            if(variant==='compact') {
                check(s,`geometry-${width}`,{x:disabled.x,y:disabled.y,width:disabled.width,height:disabled.height},
                    {x:geometry.x,y:geometry.y,width:geometry.width,height:geometry.height});
                check(s,`own-focus-fallback-${width}`,(await info(page,first)).focused);
                await set(page,first,on);
                await page.evaluate(name=>Array.from(document.querySelectorAll('[name]')).find(n=>n.name===name).focus(),remote);
                await set(page,first,off);
                check(s,`other-focus-preserved-${width}`,(await info(page,remote)).focused);
            }
            check(s,`sibling-value-${width}`,(await info(page,remote)).value,other.value);
            check(s,`sibling-enabled-${width}`,(await info(page,remote)).disabled,false);
            check(s,`parent-unaffected-${width}`,await value(page,'title'),parent);
            await set(page,first,on);
            check(s,`row-away-back-${width}`,await value(page,address),'Preserved row address');
            await capture(`${variant}-${width}`);
        }
        const count=names.length;
        await page.locator('button.cv-form-ctrl-add').last().click();
        await page.waitForFunction(count=>document.querySelectorAll('select[name$="-service"]').length>count,count);
        names=await fields(page,'-service');
        const added=names.at(-1), addedAddress=added.replace(/service$/,'visit_address');
        await set(page,added,on); await set(page,addedAddress,'Inserted address');
        check(s,'authorized-insert-initialized',(await info(page,addedAddress)).disabled,false);
        await set(page,first,off);
        response=await post({}); check(s,'save-status',response.status,302);
        await visit(initial.urls[variant]);
        const rows=(await state()).requests.filter(r=>r.batch_id===initial.fixtures[variant]);
        check(s,'insert-persisted',rows.some(r=>r.visit_address==='Inserted address'));
        check(s,'inactive-persisted-clear',rows[0].visit_address,'');
        check(s,'reopen-clear',await value(page,address),''); s.dbConfirmed=true;
    }
    s=scenario('lifecycle'); await visit(initial.urls.create);
    await set(page,'service',on); await set(page,'visit_address','Reset sample');
    await page.evaluate(()=>{const f=document.querySelector('[name="service"]').form;f.addEventListener('reset',ev=>ev.preventDefault(),{once:true});HTMLFormElement.prototype.reset.call(f);});
    await page.waitForTimeout(30);
    check(s,'cancelled-reset',await value(page,'service'),on);
    await page.evaluate(()=>HTMLFormElement.prototype.reset.call(document.querySelector('[name="service"]').form)); await page.waitForTimeout(30);
    check(s,'native-reset',await value(page,'service'),'');
    check(s,'reset-disabled',(await info(page,'visit_address')).disabled);
    await set(page,'service',on);
    await page.evaluate(()=>document.querySelector('[name="visit_address"]').disabled=true);
    await set(page,'service',off); await set(page,'service',on);
    check(s,'independent-disabled',(await info(page,'visit_address')).disabled);
    // Actual server-rendered forms, with unusual names in a bounded fixture subtree.
    // This tests the documented modal event interface, not unsupported parent-formset modal views.
    const lifecycle=await page.evaluate(({on,off})=>{
        const original=document.querySelector('[name="service"]').form;
        const host=document.createElement('div'); document.body.append(host);
        const clone=original.cloneNode(true); host.append(clone);
        const prefix='fixture[<]."-0-';
        clone.querySelectorAll('[name]').forEach(n=>{n.name=prefix+n.name;if(n.id)n.id=prefix+n.id;});
        clone.querySelectorAll('[cv-data-toggle-field]').forEach(n=>n.setAttribute('cv-data-toggle-field',prefix+n.getAttribute('cv-data-toggle-field')));
        const select=Array.from(clone.elements).find(n=>n.name===prefix+'service');
        const field=Array.from(clone.elements).find(n=>n.name===prefix+'visit_address'); field.disabled=false;
        select.value=on;host.dispatchEvent(new Event('cv:modal:loaded',{bubbles:true}));
        const initialized=!field.disabled;
        select.value=off;select.dispatchEvent(new Event('change',{bubbles:true})); const inactive=field.disabled;
        host.dispatchEvent(new Event('cv:modal:unload',{bubbles:true}));
        select.value=on;select.dispatchEvent(new Event('change',{bubbles:true}));const released=!field.disabled;
        host.dispatchEvent(new Event('cv:modal:loaded',{bubbles:true}));
        select.value=off;select.dispatchEvent(new Event('change',{bubbles:true}));const reloaded=field.disabled;
        const isolated=original.elements.service.value===on;
        host.dispatchEvent(new Event('cv:modal:unload',{bubbles:true}));host.remove();
        return {initialized,inactive,released,reloaded,isolated};
    },{on,off});
    check(s,'exact-prefix-modal-lifecycle',lifecycle,{initialized:true,inactive:true,released:true,reloaded:true,isolated:true});
    check(s,'lifecycle-no-write',(await state()).categories,initial.categories);s.dbConfirmed=true;
    s=scenario('mutation');await visit(initial.urls.mutation);
    const snapshot=await state(), category=snapshot.categories.find(c=>c.code==='on_site');
    const names=await fields(page,'-service');
    try {
        await state({operation:'category',pk:category.id,code:'unmatched-browser'});
        response=await post({[names[1].replace(/service$/,'meeting_url')]:'invalid sibling',title:'Must not persist'});
        check(s,'changed-category-safe-redisplay',response.status,200);
        check(s,'diagnostic-visible',response.html.includes('unmatched-browser'));
        check(s,'sibling-error-visible',response.html.includes('Enter a valid URL'));
        const after=await state();check(s,'atomic-parent',after.batches,snapshot.batches);check(s,'atomic-rows-empty-extra',after.requests,snapshot.requests);
    } finally {
        await state({operation:'category',pk:category.id,code:category.code});
        check(s,'restored-categories',(await state()).categories,snapshot.categories);
    }
    await state({operation:'stale'});await visit(initial.urls.unchanged);
    response=await post({});check(s,'unchanged-save',response.status,302);
    const unchanged=(await state()).requests.filter(r=>r.batch_id===initial.fixtures.unchanged);
    check(s,'unchanged-db-cleared',unchanged.every(r=>r.visit_address==='' && r.meeting_url===''));s.dbConfirmed=true;
    s=scenario('navigation');
    for(const variant of ['standalone','ordinary','compact']) {
        await visit(initial.urls[variant]);
        const panels=await page.locator('[id^="snippet-queryset_conditional-"]').evaluateAll(ns=>ns.map(n=>n.id));
        check(s,`${variant}-relevant-source`,panels.sort(),['models.py','conditions.py',variant==='standalone'?'standalone.py':'inlines.py'].map(n=>'snippet-queryset_conditional-'+n.replace('.','-')).sort());
        const links=await page.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
        check(s,`${variant}-docs-links`,links.some(l=>l.includes('reference/conditional')&&l.includes('queryset')));
        check(s,`${variant}-navigation`,['service-request','service-batch','service-batch-compact'].every(p=>links.some(l=>l.includes(`/queryset-conditional/${p}/`))));
    }
    check(s,'navigation-db-unchanged',(await state()).categories,initial.categories);s.dbConfirmed=true;
}
module.exports = {parseArgs, validateEvidence, fingerprint, REQUIRED};
if (require.main === module) (async()=>{const args=parseArgs(process.argv.slice(2)); await (args['self-test'] ? selfTest(args.target) : run(args));})().catch(error=>{console.error(error);process.exitCode=1;});
