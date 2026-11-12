// Execute the runner's real cleanup and request code; replace only external browser/Git I/O.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
const vm = require('node:vm');
const {once} = require('node:events');
const test = require('node:test');
const source = fs.readFileSync(path.join(__dirname, '06.26-checklist-browser.cjs'), 'utf8');

function runner(t, {retain = true, publicationFailure = false} = {}) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'checklist-regression-'));
    t.after(() => fs.rmSync(root, {recursive:true, force:true}));
    const phase = path.join(root, '.planning/phases/06.26-issue-351');
    const output = retain ? path.join(phase, '06.26-EXAMPLE-BROWSER.json') : path.join(root, 'ordinary.json');
    const captures = retain ? path.join(phase, 'browser-captures/checklist') : output + '.captures';
    fs.mkdirSync(captures, {recursive:true});
    fs.writeFileSync(output, 'retained report');
    fs.writeFileSync(path.join(captures, 'old.png'), 'retained capture');
    const fakeFs = {...fs,
        readFileSync: file => fs.existsSync(file) ? fs.readFileSync(file) : Buffer.from('source fixture'),
        mkdirSync: (file, options) => {
            if(publicationFailure && file === captures) throw new Error('injected destination EACCES');
            return fs.mkdirSync(file, options);
        },
    };
    const processState = {argv:['node','runner','--output',output,...(retain ? ['--retain'] : [])],
        env:process.env, version:process.version};
    const sandbox = {Buffer, URL, URLSearchParams, Response, Request, setTimeout, clearTimeout,
        console:{log(){},error(){}}, process:processState,
        require: name => name === 'node:fs' ? fakeFs : name === 'node:os' ? {...os,tmpdir:()=>root} :
            name === 'node:child_process' ? {...cp,execFileSync:()=>root} : require(name)};
    const start = source.indexOf('    finally {') + '    finally {'.length;
    const end = source.lastIndexOf('\n    }\n})();');
    const api = vm.runInNewContext(source.slice(0, source.indexOf('(async()=>{')) +
        '\nasync function finish() {' + source.slice(start,end) + '\n}\n' +
        '({finish, save, record, scratch, staged, setResources(s,b,fd,error) {' +
        'server=s; browser=b; logFd=fd; failed=error; if(error) record.error=String(error.stack);}})', sandbox);
    fs.writeFileSync(path.join(api.staged,'new.png'),'new capture');
    api.record.captures.push({path:path.relative(root,path.join(captures,'new.png'))});
    return {api, root, output, captures, processState,
        diagnostic:()=>JSON.parse(fs.readFileSync(path.join(root,'checklist-example-failed.json'),'utf8'))};
}

async function ownedChild(t, ignoreTerm = false) {
    const child = cp.spawn(process.execPath, ['-e',
        (ignoreTerm ? 'process.on("SIGTERM",()=>{}); process.send("ready");' : '') + 'setInterval(()=>{},1000)'],
        ignoreTerm ? {stdio:['ignore','ignore','ignore','ipc']} : {});
    t.after(() => {if(child.exitCode===null && child.signalCode===null) child.kill('SIGKILL');});
    await once(child,'spawn');
    if(ignoreTerm) await once(child,'message');
    return child;
}

test('browser close rejection still reaps child, closes log, removes scratch and preserves primary failure', async t => {
    const run = runner(t);
    const child = await ownedChild(t);
    const fd = fs.openSync(path.join(run.api.scratch,'server.log'),'w');
    run.api.setResources(child,{close:async()=>{throw new Error('injected browser close');}},fd,new Error('primary browser failure'));
    await run.api.finish();
    assert(child.exitCode!==null || child.signalCode!==null, 'owned child was left alive');
    assert.throws(()=>fs.fstatSync(fd),/EBADF/);
    assert(!fs.existsSync(run.api.scratch));
    assert.equal(fs.readFileSync(run.output,'utf8'),'retained report');
    assert.equal(fs.readFileSync(path.join(run.captures,'old.png'),'utf8'),'retained capture');
    assert(!fs.existsSync(path.join(run.captures,'new.png')));
    const report = run.diagnostic();
    assert.match(report.error,/primary browser failure/);
    assert(report.cleanupErrors.some(e=>e.includes('injected browser close')));
    assert.equal(run.processState.exitCode,1);
});

test('capture destination failure removes scratch and writes failed diagnostic without publishing success', async t => {
    const run = runner(t,{publicationFailure:true});
    await run.api.finish();
    assert(!fs.existsSync(run.api.scratch));
    assert.equal(fs.readFileSync(run.output,'utf8'),'retained report');
    assert.equal(fs.readFileSync(path.join(run.captures,'old.png'),'utf8'),'retained capture');
    assert(run.diagnostic().cleanupErrors.some(e=>e.includes('injected destination EACCES')));
    assert.equal(run.processState.exitCode,1);
});

test('ordinary success publishes captures beside its report and removes temporary storage', async t => {
    const run = runner(t,{retain:false});
    await run.api.finish();
    assert.equal(fs.readFileSync(path.join(run.captures,'new.png'),'utf8'),'new capture');
    const report = JSON.parse(fs.readFileSync(run.output,'utf8'));
    assert.equal(report.cleanup.temporaryRemoved,true);
    assert(!fs.existsSync(path.join(run.root,'.planning/phases/06.26-issue-351/browser-captures/checklist')));
});

test('a child whose SIGTERM exit preceded cleanup does not block reporting or temporary removal', async t => {
    const run = runner(t);
    const child = await ownedChild(t);
    const exit = once(child,'exit');
    child.kill('SIGTERM');
    await exit;
    assert.equal(child.exitCode,null);
    assert.equal(child.signalCode,'SIGTERM');
    run.api.setResources(child);
    let timer;
    try {
        await Promise.race([run.api.finish(),new Promise((_,reject)=>{
            timer=setTimeout(()=>reject(new Error('cleanup waited for an exit event that already fired')),250);
        })]);
    } finally { clearTimeout(timer); }
    assert(!fs.existsSync(run.api.scratch));
    const report = JSON.parse(fs.readFileSync(run.output,'utf8'));
    assert.equal(report.cleanup.serverReaped,true);
    assert.equal(report.serverExit.signal,'SIGTERM');
});

test('an owned child ignoring SIGTERM is killed within a bounded cleanup wait', {timeout:6000}, async t => {
    const run = runner(t);
    const child = await ownedChild(t,true);
    run.api.setResources(child);
    await run.api.finish();
    assert.equal(child.signalCode,'SIGKILL');
    assert(!fs.existsSync(run.api.scratch));
    assert.equal(JSON.parse(fs.readFileSync(run.output,'utf8')).cleanup.serverReaped,true);
});

async function saveFixture(api, {urlencoded = false, wrongDone = false} = {}) {
    const fields = new FormData();
    for(const [name,value] of [
        ['csrfmiddlewaretoken','token'],['title','Release'],['items-TOTAL_FORMS','2'],['items-INITIAL_FORMS','0'],
        ['items-0-id',''],['items-0-label','Review'],['items-0-done','on'],['items-1-id',''],['items-1-label','Publish'],
    ]) fields.append(name,value);
    if(wrongDone) {fields.delete('items-0-done'); fields.append('items-1-done','on');}
    const request = new Request('http://localhost/formsets/checklist/create/',
        {method:'POST',body:urlencoded ? new URLSearchParams(fields) : fields});
    const body = Buffer.from(await request.arrayBuffer());
    const post = {url:()=>request.url, postData:()=>body.toString(),postDataBuffer:()=>body,
        headers:()=>Object.fromEntries(request.headers)};
    const page = {waitForRequest:async()=>post,waitForURL:async()=>{},locator:()=>({
        filter:()=>({click:async()=>{}}),
        evaluateAll:async()=>[{name:'items-0-done',checked:true,disabled:false},{name:'items-1-done',checked:false,disabled:false}],
    })};
    await api.save(page);
}

for(const urlencoded of [false,true]) test(`${urlencoded?'URL-encoded':'multipart'} save records actual keys and native checkbox omission`, async t => {
    const {api} = runner(t);
    await saveFixture(api,{urlencoded});
    assert.deepEqual(Array.from(api.record.requests[0].fields),[
        'csrfmiddlewaretoken','title','items-TOTAL_FORMS','items-INITIAL_FORMS','items-0-id','items-0-label',
        'items-0-done','items-1-id','items-1-label',
    ]);
    assert(!api.record.requests[0].fields.includes('items-1-done'));
});

test('save rejects a request that swaps the checked and omitted Done fields', async t => {
    const {api} = runner(t);
    await assert.rejects(saveFixture(api,{wrongDone:true}),/checkbox submission/);
});
