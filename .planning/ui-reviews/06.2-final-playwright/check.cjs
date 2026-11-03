const {chromium}=require('/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('fs'), assert=require('assert/strict');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:'/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',args:['--no-sandbox']});
const cases=JSON.parse(fs.readFileSync('/tmp/dcv-playwright-062/cases.json'));
const results=[], errors=[]; const base='http://127.0.0.1:8139';
for (const c of cases){
const ctx=await browser.newContext({viewport:{width:1280,height:900},ignoreHTTPSErrors:true});
const page=await ctx.newPage(); page.on('pageerror',e=>errors.push(`${c.user}: ${e.message}`));
await page.goto(base+'/signin/'+c.user+'/');
async function verify(root,label){
 const text=await root.innerText();
 assert.equal((text.match(/Deletion is blocked by protected relationships/g)||[]).length,1,label+' single notice');
 assert(!text.includes('SECRET-CONTRACT'),label+' hidden labels');
 assert.equal(await root.locator('form.cv-form').count(),0,label+' form omitted');
 assert.equal(await root.locator('input[name=confirm]').count(),0,label+' confirm omitted');
 if(c.mode==='visible') assert(text.includes('VISIBLE-CONTRACT'),label+' permitted label');
 else assert(text.includes('Other objects still reference this one; remove or reassign them before deleting it.'),label+' complete generic notice');
 const state=await (await ctx.request.get(base+'/state/'+c.pk+'/')).json(); assert(state.exists&&state.contracts>=1,label+' storage preserved');
 results.push({scenario:label,...state});
}
if(c.mode!=='stale'){
 const response=await page.goto(base+c.url); assert.equal(response.status(),200);
 await verify(page.locator('main'),c.user+' full');
 await page.screenshot({path:`/tmp/dcv-playwright-062/${c.user}-full.png`,fullPage:true});
}
await page.goto(base+'/harness/?target='+encodeURIComponent(c.url));
await page.waitForFunction(()=>typeof bootstrap==='object'&&typeof cv.cvModalOpen==='function');
await page.locator('#launch').click();
const modal=page.locator('#cv-modal'); await modal.waitFor({state:'visible'});
if(c.mode==='stale'){
 await modal.locator('input[name=confirm]').check();
 const protection=await ctx.request.post(base+'/protect/'+c.pk+'/'); assert.equal(protection.status(),200);
 const origin=page.url();
 const post=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(c.url));
 await modal.locator('button[type=submit], input[type=submit]').click();
 const response=await post; assert.equal(response.status(),422); assert.equal(response.headers()['x-cv-redirect'],undefined);
 await modal.locator('form.cv-form').waitFor({state:'detached'});
 assert.equal(page.url(),origin); assert(await modal.isVisible());
}
await verify(modal,c.user+' modal'+(c.mode==='stale'?' 422 recovery':''));
await page.screenshot({path:`/tmp/dcv-playwright-062/${c.user}-modal.png`});
await page.setViewportSize({width:390,height:844});
await page.screenshot({path:`/tmp/dcv-playwright-062/${c.user}-mobile.png`});
assert(await modal.locator('[data-cv-modal-dismiss]').first().isVisible());
await modal.locator('[data-cv-modal-dismiss]').first().click();
await modal.waitFor({state:'hidden'});
results.push({scenario:c.user+' modal closed after mobile resize',passed:true});
await ctx.close();
}
assert.deepEqual(errors,[]);
fs.writeFileSync('/tmp/dcv-playwright-062/results.json',JSON.stringify({browser:browser.version(),results,pageErrors:errors},null,2));
console.log(JSON.stringify({browser:browser.version(),checks:results.length,results,pageErrors:errors},null,2));
await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
