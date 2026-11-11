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

async function ownedChild(t) {
    const child = cp.spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)']);
    t.after(() => {if(child.exitCode===null && child.signalCode===null) child.kill('SIGKILL');});
    await once(child,'spawn');
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
