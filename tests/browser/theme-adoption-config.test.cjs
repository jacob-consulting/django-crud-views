const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const entry = path.join(__dirname, 'theme-adoption.cjs');
const cp = require('node:child_process');
const os = require('node:os');
const net = require('node:net');

test('shared recorded interpreter resolver exists without starting the CLI', () => {
    const harness = fs.existsSync(entry) ? require(entry) : {};
    assert.equal(typeof harness.resolveCompanionPython, 'function');
});

test('asset capture reads each actual URL once and retains body errors without an unhandled rejection',async()=>{
    const {observeAsset}=require(entry);const report={assets:[],assetErrors:[]},jobs=[],seen=new Set();
    let reads=0;
    const response={url:()=> 'https://fixture.invalid/asset',status:()=>200,body:async()=>{reads++;return Buffer.from('actual bytes');}};
    observeAsset(response,report,jobs,seen);
    observeAsset({...response,body:async()=>{throw Error('duplicate navigation lost body');}},report,jobs,seen);
    observeAsset({...response,url:()=> 'https://fixture.invalid/failed',body:async()=>{throw Error('first response unavailable');}},report,jobs,seen);
    await Promise.all(jobs);
    assert.equal(reads,1);assert.equal(report.assets.length,1);
    assert.deepEqual(report.assetErrors,[{url:'https://fixture.invalid/failed',error:'first response unavailable'}]);
});

test('real Tabler create uses the native check icon from its registered form floor',()=>{
    const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'theme-native-check-'));
    try {
        const output=path.join(temporary,'report.json');const env={...process.env,CV_THEME_PORT:'8158'};
        delete env.CV_THEME_PYTHON;delete env.CV_FOCUS_PYTHON;
        const result=cp.spawnSync(process.execPath,[entry,'--case','owned-form','--output',output],{env,encoding:'utf8',timeout:40000,shell:false});
        assert.equal(result.status,0,result.stdout+result.stderr);
        const report=JSON.parse(fs.readFileSync(output));
        const ownership=report.cases[0].assertions.find(a=>a.id==='native-controls-formdata-submitter').observed;
        assert.deepEqual(ownership.submitSVG,['M5 12l5 5l10 -10']);
        assert.equal(report.cleanup.temporaryRemoved,true);
        assert.equal(report.cleanup.serverExit.code,0);
    } finally {fs.rmSync(temporary,{recursive:true,force:true});}
});

test('fresh process resolves the recorded executable with both overrides absent', () => {
    const env={...process.env}; delete env.CV_THEME_PYTHON; delete env.CV_FOCUS_PYTHON;
    const result=cp.spawnSync(process.execPath,['-e',`console.log(JSON.stringify(require(${JSON.stringify(entry)}).resolveCompanionPython()))`],{cwd:os.tmpdir(),env,encoding:'utf8',shell:false});
    assert.equal(result.status,0,result.stderr);
    const selected=JSON.parse(result.stdout);
    assert.equal(selected.executable,JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/06-companion-baseline.json'))).companion_python);
    assert.match(selected.runtime.versions.Django,/^6\.1\./);
});
for(const port of ['','bad','8143','8144','1023','65536','8145.1']) test(`actual CLI rejects invalid port ${JSON.stringify(port)} first`,()=>{
    const result=cp.spawnSync(process.execPath,[entry],{env:{...process.env,CV_THEME_PORT:port,CV_THEME_PYTHON:'/missing'},encoding:'utf8',timeout:4000,shell:false});
    assert.equal(result.status,1);
    assert.match(result.stderr,/CV_THEME_PORT.*1024\.\.65535.*8143.*8144/);
});
for(const key of ['CV_THEME_PYTHON','CV_FOCUS_PYTHON']) for(const value of ['', 'relative', '/wrong/python']) test(`${key} rejects ${JSON.stringify(value)}`,()=>{
    assert.throws(()=>require(entry).resolveCompanionPython({env:{[key]:value}}),/absolute path|conflicting/);
});
test('presentation collision preserves the existing listener',async()=>{
    const server=net.createServer(socket=>socket.end('still alive'));
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(8145,'127.0.0.1',resolve);});
    try {
        const result=cp.spawnSync(process.execPath,[entry],{env:{...process.env,CV_THEME_PORT:'8145',CV_THEME_PYTHON:'/missing'},encoding:'utf8',timeout:4000,shell:false});
        assert.equal(result.status,1);assert.match(result.stderr,/EADDRINUSE/);
        const data=await new Promise(resolve=>{let value='';const socket=net.connect(8145,'127.0.0.1');socket.on('data',chunk=>value+=chunk);socket.on('end',()=>resolve(value));});
        assert.equal(data,'still alive');
    } finally {await new Promise(resolve=>server.close(resolve));}
});
test('recorded root and runtime resolve from an isolated script location with spaces, independently of cwd and siblings',()=>{
    const temp=fs.mkdtempSync(path.join(os.tmpdir(),'theme config '));
    const root=path.join(temp,'core copy');const source=path.join(temp,'recorded companion');
    const phase='.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync';
    try {
        fs.mkdirSync(path.join(root,'tests/browser'),{recursive:true});fs.copyFileSync(entry,path.join(root,'tests/browser/theme-adoption.cjs'));
        fs.mkdirSync(source);cp.execFileSync('git',['init','-q',source]);
        cp.execFileSync('git',['-C',source,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-qm','fixture']);
        cp.execFileSync('git',['-C',source,'remote','add','origin','https://example.invalid/fixture.git']);
        const baseline=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../..',phase,'06-companion-baseline.json')));
        const venv=path.join(temp,'venv with spaces');fs.symlinkSync(baseline.runtime.prefix,venv,'dir');
        baseline.companion_python=path.join(venv,'bin/python');
        const identity=JSON.parse(cp.execFileSync(baseline.companion_python,['-c','import json,sys;print(json.dumps({"prefix":sys.prefix}))'],{encoding:'utf8'}));
        baseline.runtime.prefix=identity.prefix;
        baseline.companion_root=source;baseline.origin='https://example.invalid/fixture.git';baseline.revision=cp.execFileSync('git',['-C',source,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
        fs.mkdirSync(path.join(root,phase),{recursive:true});fs.writeFileSync(path.join(root,phase,'06-companion-baseline.json'),JSON.stringify(baseline));
        const isolated=path.join(root,'tests/browser/theme-adoption.cjs');const env={...process.env,CV_THEME_PORT:'8159'};delete env.CV_THEME_PYTHON;delete env.CV_FOCUS_PYTHON;
        for(const sibling of [false,true]) {
            if(sibling)fs.mkdirSync(path.join(temp,'tabler-test'));
            const result=cp.spawnSync(process.execPath,['-e',`require(${JSON.stringify(isolated)}).configuration(['--case','label-floor','--delivered-source','recorded']).then(c=>console.log(JSON.stringify(c))).catch(e=>{console.error(e);process.exitCode=1})`],{cwd:os.tmpdir(),env,encoding:'utf8',shell:false});
            assert.equal(result.status,0,result.stderr);const config=JSON.parse(result.stdout);
            assert.equal(config.executable,baseline.companion_python);assert.equal(config.source,source);assert.equal(config.runtime.prefix,identity.prefix);
        }
        const harness=require(isolated);
        assert.throws(()=>harness.resolveSource('relative'),/absolute/);
        assert.throws(()=>harness.resolveSource(path.join(temp,'tabler-test')),/does not match/);
        assert.throws(()=>harness.resolveSource('recorded',{env:{CV_PACK_SOURCE:root}}),/conflicting/);
        for(const mutation of [b=>delete b.companion_python,b=>b.companion_python='',b=>b.runtime.prefix='/wrong',b=>b.runtime.python=[3,12,0]]) {
            const changed=structuredClone(baseline);mutation(changed);fs.writeFileSync(path.join(root,phase,'06-companion-baseline.json'),JSON.stringify(changed));
            assert.throws(()=>harness.resolveCompanionPython({env:{}}));
        }
    } finally {fs.rmSync(temp,{recursive:true,force:true});}
});

test('partial delivery form writer preserves every other slot and cannot certify completion',()=>{
    const dir=fs.mkdtempSync(path.join(os.tmpdir(),'theme-delivery-slot-'));
    try {
        const output=path.join(dir,'bundle.json');const prior={schema:1,status:'provisional',delivered_probe:{receipt:'existing'},committed_probe:{receipt:'historical'}};
        fs.writeFileSync(output,JSON.stringify(prior));
        const harness=require(entry);const report={status:'partial',bindings:{source:'bound'},commands:[harness.commandRecord(['node','probe'],dir,0,'observed output','')],assertions:[{id:'actual',passed:true}],run_id:'fresh'};
        const result=harness.mergeFormProbe(output,report);
        assert.deepEqual(result.delivered_probe,prior.delivered_probe);assert.deepEqual(result.committed_probe,prior.committed_probe);
        assert.equal(result.form_probe.scope,'partial');assert.equal(result.form_probe.complete,false);assert.equal(result.status,'provisional');
        result.status='complete';fs.writeFileSync(output,JSON.stringify(result));
        assert.throws(()=>harness.mergeFormProbe(output,report),/cannot overwrite completed/);
    } finally {fs.rmSync(dir,{recursive:true,force:true});}
});

test('browser startup failure cleans up its owned server and temporary copies',()=>{
    const dir=fs.mkdtempSync(path.join(os.tmpdir(),'theme-cleanup-'));
    try {
        const output=path.join(dir,'failure.json');const env={...process.env,CV_THEME_PORT:'8158',CV_FOCUS_PLAYWRIGHT:'/missing/playwright'};
        delete env.CV_THEME_PYTHON;delete env.CV_FOCUS_PYTHON;
        const result=cp.spawnSync(process.execPath,[entry,'--case','owned-form','--output',output],{env,encoding:'utf8',timeout:40000,shell:false});
        assert.equal(result.status,1);const report=JSON.parse(fs.readFileSync(output));
        assert.equal(report.status,'failed');assert.equal(report.cleanup.serverExit.code,0);assert.equal(report.cleanup.temporaryRemoved,true);
    } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
