// Bounded real-page acceptance runner. Self-tests never start Django or Chromium.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const REQUIRED = {upstream: ['standalone', 'ordinary', 'compact', 'lifecycle', 'mutation', 'navigation'],
    downstream:['orders','retained-products','mutation','printing']};
const widths = ids => [1280,390].flatMap(width=>ids.map(id=>`${id}-${width}`));
const inlineAssertions = [...widths(['inactive-disabled','layout','sibling-value','sibling-enabled','parent-unaffected','row-away-back']),
    'authorized-insert-initialized','save-status','insert-persisted','inactive-persisted-clear','reopen-clear'];
const ASSERTIONS = {
    upstream: {
        standalone:[...widths(['shared-keeps','ordinary-hidden','away-back','blank-disables','label']),
            'accessible-required-error','keyboard-active-field','active-required-status','active-required-error','active-required-zero-write',
            'forged-zero-write','forged-native-error','invalid-write-count','forged-write-count','no-js-tampered-save','fresh-get-cleared','db-cleared'],
        ordinary:inlineAssertions,
        compact:[...inlineAssertions,...widths(['geometry','own-focus-fallback','other-focus-preserved'])],
        lifecycle:['cancelled-reset','native-reset','reset-disabled','independent-disabled','exact-prefix-modal-lifecycle','lifecycle-no-write'],
        mutation:['changed-category-safe-redisplay','diagnostic-visible','sibling-error-visible','atomic-parent','atomic-rows-empty-extra',
            'restored-categories','mutation-write-count','unchanged-save','unchanged-db-cleared'],
        navigation:[...['standalone','ordinary','compact'].flatMap(v=>['relevant-source','docs-links','navigation'].map(a=>`${v}-${a}`)),
            'navigation-db-unchanged'],
    },
    downstream:{
        orders:[...widths(['compact-visible-disabled','compact-geometry','focus-fallback','row-isolation','preserved-coffee','label']),
            'native-reset','independent-disabled','invalid-active-status','invalid-active-error','invalid-active-zero-lines','invalid-active-zero-parent',
            'forged-retired-rejected','forged-zero-write','invalid-write-count','forged-write-count','accessible-invalid-row','row-insertion','inactive-submit','persisted-clearing',
            'fresh-get-cleared','inserted-optional-coffee','create-optional','create-persisted'],
        'retained-products':['retained-product','subscription-no-fields','subscription-away-back','retained-save','retired-coffee-retained','subscription-persisted-clear'],
        mutation:['changed-queryset-safe-rejection','changed-queryset-error','atomic-rows','atomic-parent','mutation-write-count','restored-product-types','unchanged-submit','unchanged-db-clearing'],
        printing:['print-page','print-handler','print-no-write'],
    },
};
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
    assert.equal(record.runtime.source,path.join(sources.upstream,'src/crud_views/__init__.py'));
    assert.equal(record.runtime.settings,target==='upstream'?'project.settings':'config.settings');
    for(const key of ['python','django','pythonPath','node','nodePath','playwright','playwrightPath','chromium','chromiumPath','packageLockHash'])
        assert(record.runtime[key],`Missing runtime ${key}`);
    assert.equal(record.servedToggle.actualHash,record.servedToggle.expectedHash,'Served static mismatch');
    assert(record.pages.length>0 && record.pages.every(p=>p.status===200&&p.htmlBytes>0&&p.sha256),'Missing served HTML');
    assert.equal(record.captures.length,target==='upstream'?7:3,'Missing capture');
    assert.deepEqual(record.pageErrors,[]);
    assert.deepEqual(record.failedRequests,[]);
    assert.deepEqual(record.scenarios.map(s => s.id).sort(), [...REQUIRED[target]].sort());
    for (const scenario of record.scenarios) {
        assert(scenario.assertions.length > 0, `Empty ${scenario.id}`);
        assert.deepEqual(scenario.assertions.map(a=>a.id).sort(),[...ASSERTIONS[target][scenario.id]].sort(),`Missing/duplicate dimensions ${scenario.id}`);
        assert.equal(scenario.dbConfirmed, true, `Missing database proof ${scenario.id}`);
        for (const assertion of scenario.assertions) {
            assert.equal(assertion.passed, true, assertion.id);
            assert(Object.hasOwn(assertion,'actual') && Object.hasOwn(assertion,'expected'));
            assert.deepEqual(assertion.actual,assertion.expected,`False observation ${assertion.id}`);
        }
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
        runtime:{source:path.join(sources.upstream,'src/crud_views/__init__.py'),settings:target==='upstream'?'project.settings':'config.settings',
            ...Object.fromEntries(['python','django','pythonPath','node','nodePath','playwright','playwrightPath','chromium','chromiumPath','packageLockHash'].map(k=>[k,'offline-fixture']))},
        servedToggle:{actualHash:'offline-fixture',expectedHash:'offline-fixture'},
        pages:[{status:200,htmlBytes:100,sha256:'offline-fixture'}],captures:Array(target==='upstream'?7:3).fill({sha256:'offline-fixture'}),
        pageErrors:[],failedRequests:[],
        scenarios: REQUIRED[target].map(id => ({id, assertions: ASSERTIONS[target][id].map(id=>({id,passed:true,actual:true,expected:true})), dbConfirmed: true})),
        cleanup: {reaped: true, temporaryRemoved: true}};
    test('accept complete target', () => validateEvidence(valid, target, sources, valid.sourceHashes));
    if(target==='downstream') {
        for(const id of ['retained-product','print-handler','row-insertion','persisted-clearing']) test(`missing ${id}`,()=>{
            const r=structuredClone(valid);r.scenarios.forEach(s=>s.assertions=s.assertions.filter(a=>a.id!==id));
            assert.throws(()=>validateEvidence(r,target,sources,valid.sourceHashes));
        });
        test('reject substituted upstream',()=>{const r=structuredClone(valid);r.target='upstream';assert.throws(()=>validateEvidence(r,target,sources,valid.sourceHashes));});
        test('reject wrong downstream source',()=>{const r=structuredClone(valid);r.sources.downstream='/wrong';assert.throws(()=>validateEvidence(r,target,sources,valid.sourceHashes));});
    }
    for (const [name, corrupt] of [
        ['zero scenarios', r => r.scenarios = []],
        ['missing scenario', r => r.scenarios.pop()],
        ['missing dimension', r => r.scenarios[0].assertions.pop()],
        ['duplicate dimension', r => r.scenarios[0].assertions.push(r.scenarios[0].assertions[0])],
        ['false assertion', r => r.scenarios[0].assertions[0].passed = false],
        ['false observation labelled passed', r => r.scenarios[0].assertions[0].actual = false],
        ['false database proof', r => r.scenarios[0].dbConfirmed = false],
        ['missing HTML',r=>r.pages=[]],
        ['missing capture',r=>r.captures.pop()],
        ['stale served script',r=>r.servedToggle.actualHash='stale'],
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
        sourceHashes: fingerprint(sources), docsHashes: fingerprint(sources, true), scenarios: [], captures: [], pages: [],
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
        record.isolation={bind:'127.0.0.1',port:ready.port,temporary:resources.dir,
            database:path.join(resources.dir,'db.sqlite3'),media:path.join(resources.dir,'media')};
        resources.browser = await require(playwright).chromium.launch({headless:true, executablePath:chromium, args:['--no-sandbox']});
        record.runtime.chromium = resources.browser.version();
        const context = await resources.browser.newContext({viewport:{width:1280,height:900}});
        const page = await context.newPage();
        page.on('pageerror', error => record.pageErrors.push(String(error)));
        page.on('requestfailed', request => record.failedRequests.push({url:request.url(), error:request.failure().errorText}));
        page.on('response', response=>{if(response.status()>=400 && ['script','stylesheet','font','image'].includes(response.request().resourceType()))
            record.failedRequests.push({url:response.url(),status:response.status()});});
        page.setDefaultTimeout(10000);
        await page.goto(`${base}${ready.login}`);
        await page.locator('[name="username"]').fill('browser');
        await page.locator('[name="password"]').fill('browser-only-password');
        await Promise.all([page.waitForURL(url => url.pathname!==ready.login,{waitUntil:'domcontentloaded'}),
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
        const visit = async url => { const response = await page.goto(`${base}${url}`); assert.equal(response.status(),200, `GET ${url}`);
            const html=await page.content();assert(html.includes('<form'));record.pages.push({url:page.url(),status:response.status(),htmlBytes:Buffer.byteLength(html),sha256:digest(html)}); };
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
    check(s,'invalid-write-count',(await state()).writes,before.writes);
    response=await post({service:'99999999',visit_address:'forged'});
    check(s,'forged-zero-write',(await state()).requests,before.requests);
    check(s,'forged-native-error',response.html.includes('Select a valid choice'));
    check(s,'forged-write-count',(await state()).writes,before.writes);
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
        check(s,'mutation-write-count',after.writes,snapshot.writes);
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
async function downstream(e) {
    const {page,state,initial,visit,scenario,check,capture,post}=e;
    const coffee=String(initial.products.coffee), equipment=String(initial.products.equipment),
        retired=String(initial.products.retired), subscription=String(initial.products.subscription);
    let s=scenario('orders'); await visit(initial.urls.order);
    let names=await fields(page,'-product'), first=names[0], second=names[1];
    const grind=first.replace(/product$/,'grind'), bag=first.replace(/product$/,'bag_size'),
        other=second.replace(/product$/,'grind');
    for(const width of [1280,390]) {
        await page.setViewportSize({width,height:900});
        await set(page,grind,'filter');await set(page,bag,'250g');
        const geometry=await info(page,grind);
        await page.evaluate(name=>Array.from(document.querySelectorAll('[name]')).find(n=>n.name===name).focus(),grind);
        await set(page,first,equipment);
        const disabled=await info(page,grind);
        check(s,`compact-visible-disabled-${width}`,{visible:disabled.visible,disabled:disabled.disabled},{visible:true,disabled:true});
        check(s,`compact-geometry-${width}`,{x:disabled.x,y:disabled.y,width:disabled.width,height:disabled.height},
            {x:geometry.x,y:geometry.y,width:geometry.width,height:geometry.height});
        check(s,`focus-fallback-${width}`,(await info(page,first)).focused);
        check(s,`row-isolation-${width}`,(await info(page,other)).disabled);
        await set(page,first,coffee);
        check(s,`preserved-coffee-${width}`,[await value(page,grind),await value(page,bag)],['filter','250g']);
        check(s,`label-${width}`,(await info(page,grind)).label);
        await capture(`orders-${width}`);
    }
    await page.evaluate(name=>{const f=Array.from(document.querySelectorAll('[name]')).find(n=>n.name===name).form;HTMLFormElement.prototype.reset.call(f);},first);
    await page.waitForTimeout(30);check(s,'native-reset',await value(page,grind),'espresso');
    await page.evaluate(name=>Array.from(document.querySelectorAll('[name]')).find(n=>n.name===name).disabled=true,bag);
    await set(page,first,equipment);await set(page,first,coffee);
    check(s,'independent-disabled',(await info(page,bag)).disabled);
    // Reload releases fixture-only ownership before normal persistence.
    await visit(initial.urls.order);
    const before=await state();
    let response=await post({[grind]:'invalid-active',notes:'Must not save'});
    check(s,'invalid-active-status',response.status,200);
    check(s,'invalid-active-error',response.html.includes('Select a valid choice'));
    check(s,'invalid-active-zero-lines',(await state()).lines,before.lines);
    check(s,'invalid-active-zero-parent',(await state()).orders,before.orders);
    check(s,'invalid-write-count',(await state()).writes,before.writes);
    response=await post({[first]:retired});
    check(s,'forged-retired-rejected',response.html.includes('Select a valid choice'));
    check(s,'forged-zero-write',(await state()).lines,before.lines);
    check(s,'forged-write-count',(await state()).writes,before.writes);
    const quantity=first.replace(/product$/,'quantity');await set(page,quantity,'0');
    await Promise.all([page.waitForNavigation(),page.evaluate(name=>HTMLFormElement.prototype.submit.call(Array.from(document.querySelectorAll('[name]')).find(n=>n.name===name).form),first)]);
    check(s,'accessible-invalid-row',await page.evaluate(name=>{
        const f=Array.from(document.querySelectorAll('[name]')).find(n=>n.name===name);
        return f.getAttribute('aria-invalid')==='true' && !!f.labels.length && (f.getAttribute('aria-describedby')||'').split(' ').some(id=>document.getElementById(id)?.textContent.includes('greater'));
    },quantity));
    await capture('orders-error-390'); await visit(initial.urls.order);
    const count=(await fields(page,'-product')).length;
    await page.locator('button.cv-form-ctrl-add').last().click();
    await page.waitForFunction(count=>document.querySelectorAll('select[name$="-product"]').length>count,count);
    names=await fields(page,'-product');const added=names.at(-1);
    await set(page,added,coffee);await set(page,added.replace(/product$/,'quantity'),'2');
    check(s,'row-insertion',(await info(page,added.replace(/product$/,'grind'))).disabled,false);
    await set(page,first,equipment);
    response=await post({[grind]:'forged', [bag]:'forged'});
    check(s,'inactive-submit',response.status,302);
    await visit(initial.urls.order);
    const lines=(await state()).lines.filter(l=>l.order_id===initial.fixtures.order);
    check(s,'persisted-clearing',[lines[0].grind,lines[0].bag_size],['','']);
    check(s,'fresh-get-cleared',await value(page,grind),'');
    check(s,'inserted-optional-coffee',lines.some(l=>l.product_id===initial.products.coffee&&l.quantity===2&&l.grind===''&&l.bag_size===''));
    // Actual create route, normal CSRF HTTP with no conditional JavaScript in the submission path.
    await visit(initial.urls.create);names=await fields(page,'-product');
    response=await post({[names[0]]:coffee,[names[0].replace(/product$/,'quantity')]:'1'});
    check(s,'create-optional',response.status,302);
    check(s,'create-persisted',(await state()).orders.length,before.orders.length+1);s.dbConfirmed=true;
    s=scenario('retained-products');await visit(initial.urls.retained);
    names=await fields(page,'-product');const retiredName=names[0],subName=names[1],subGrind=subName.replace(/product$/,'grind');
    check(s,'retained-product',[await value(page,retiredName),await value(page,subName)],[retired,subscription]);
    await set(page,subName,coffee);await set(page,subGrind,'espresso');await set(page,subName,subscription);
    check(s,'subscription-no-fields',(await info(page,subGrind)).disabled);
    await set(page,subName,coffee);check(s,'subscription-away-back',await value(page,subGrind),'espresso');
    await set(page,subName,subscription);
    response=await post({[subGrind]:'forged', [subName.replace(/product$/,'bag_size')]:'forged'});
    check(s,'retained-save',response.status,302);await visit(initial.urls.retained);
    const retained=(await state()).lines.filter(l=>l.order_id===initial.fixtures.retained);
    check(s,'retired-coffee-retained',retained[0].product_id,initial.products.retired);
    check(s,'subscription-persisted-clear',[retained[1].grind,retained[1].bag_size],['','']);s.dbConfirmed=true;
    s=scenario('mutation');await visit(initial.urls.mutation);names=await fields(page,'-product');
    const snapshot=await state(), original=snapshot.types.find(p=>p.pk===initial.products.coffee);
    try {
        await state({operation:'active',pk:initial.products.coffee,active:false});
        response=await post({[names[1]]:coffee,notes:'Invalid sibling'});
        check(s,'changed-queryset-safe-rejection',response.status,200);
        check(s,'changed-queryset-error',response.html.includes('Select a valid choice'));
        check(s,'atomic-rows',(await state()).lines,snapshot.lines);
        check(s,'atomic-parent',(await state()).orders,snapshot.orders);
        check(s,'mutation-write-count',(await state()).writes,snapshot.writes);
    } finally {
        await state({operation:'active',pk:initial.products.coffee,active:original.is_active});
        check(s,'restored-product-types',(await state()).types,snapshot.types);
    }
    await state({operation:'stale'});await visit(initial.urls.unchanged);
    response=await post({});check(s,'unchanged-submit',response.status,302);
    check(s,'unchanged-db-clearing',(await state()).lines.filter(l=>l.order_id===initial.fixtures.unchanged).every(l=>l.grind===''&&l.bag_size===''));s.dbConfirmed=true;
    s=scenario('printing');const beforePrint=await state();
    const printResponse=await page.goto(`${e.base}${initial.urls.print}`);check(s,'print-page',printResponse.status(),200);
    await page.evaluate(()=>{window.__printCalls=0;window.print=()=>window.__printCalls++;});
    await page.locator('[data-print]').click();check(s,'print-handler',await page.evaluate(()=>window.__printCalls),1);
    check(s,'print-no-write',(await state()).lines,beforePrint.lines);s.dbConfirmed=true;
}
module.exports = {parseArgs, validateEvidence, fingerprint, REQUIRED, ASSERTIONS};
if (require.main === module) (async()=>{const args=parseArgs(process.argv.slice(2)); await (args['self-test'] ? selfTest(args.target) : run(args));})().catch(error=>{console.error(error);process.exitCode=1;});
