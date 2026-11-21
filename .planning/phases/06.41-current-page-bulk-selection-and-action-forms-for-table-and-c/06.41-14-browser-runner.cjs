const {chromium} = require('/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {execFileSync} = require('node:child_process');
const out = '.planning/phases/06.41-current-page-bulk-selection-and-action-forms-for-table-and-c/06.41-14-browser.json';
const snapshot = () => execFileSync('python3',['-c', "import sqlite3,json; c=sqlite3.connect('/tmp/cv-0641-14-browser/db.sqlite3'); print(json.dumps(c.execute('select * from bulk_selection_document order by id').fetchall()))"],{encoding:'utf8'});
(async()=>{
const browser=await chromium.launch({executablePath:'/home/alex/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome',headless:true});
const results=[]; const before=snapshot();
try {
 for(const javaScriptEnabled of [false,true]) {
 const ctx=await browser.newContext({javaScriptEnabled,locale:'en-GB'});
 const p=await ctx.newPage();
 await p.goto('http://127.0.0.1:8842/bulk-selection/document/');
 await p.locator('[name=username]').fill('alice');
 await p.locator('[name=password]').fill('alice');
 await p.locator('[name=login]').click();
 await p.waitForURL('**/bulk-selection/document/');
 for(const source of ['list','card']){
 const origin=source==='list'?'http://127.0.0.1:8842/bulk-selection/document/?page=2&sort=title':'http://127.0.0.1:8842/bulk-selection/document/card/?page=2&order=title&dir=asc';
 const eligible=source==='list'?13:10, blocked=source==='list'?17:9;
 const cases=[['archive',[eligible,blocked],false],['archive',[blocked],false],['assign_owner',[eligible],false],['assign_owner',[eligible],true]];
 if(source==='list')cases.push(['bulk_delete',[eligible],false]);
 for(const [action,ids,invalid] of cases){
 await p.goto(origin);
 for(const id of ids)await p.getByRole('checkbox',{name:'Select Document '+String(id).padStart(2,'0'),exact:true}).check();
 await p.locator('[data-cv-bulk-action="'+action+'"]').click();
 await p.waitForLoadState('load');
 if(invalid){await p.getByRole('button',{name:'Assign',exact:true}).click(); await p.waitForLoadState('load'); assert.ok((await p.locator('body').innerText()).includes('This field is required.'));}
 const cancel=p.getByRole('link',{name:'Cancel',exact:true});
 assert.equal(await cancel.count(),1);
 const href=await cancel.getAttribute('href'); assert.ok(href);
 const requests=[]; const listener=r=>requests.push(r.method()); p.on('request',listener);
 await cancel.click(); await p.waitForLoadState('load'); p.off('request',listener);
 assert.ok(!requests.includes('POST'));
 const actual=new URL(p.url()), expected=new URL(origin);
 assert.equal(actual.pathname,expected.pathname);
 for(const [k,v] of expected.searchParams)assert.equal(actual.searchParams.get(k),v);
 assert.equal(snapshot(),before);
 results.push({javaScriptEnabled,source,action,ids,invalid,status:'passed',url:p.url(),noPost:true,recordsUnchanged:true});
 }
 }
 await ctx.close();
 }
 fs.writeFileSync(out,JSON.stringify({browser:browser.version(),results,recordSnapshot:JSON.parse(before)},null,2)+'\n');
 console.log(JSON.stringify({passed:results.length,browser:browser.version()}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
