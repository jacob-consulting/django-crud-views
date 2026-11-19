async (page) => {
  const base = "http://127.0.0.1:9000";
  const output = "/home/alex/projects/alex/django-crud-views/.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/";
  const result = {browser: page.context().browser().version(), urls: [], measurements: [], keyboard: [], assertions: [], failures: []};
  const check = (value, name) => { (value ? result.assertions : result.failures).push(name); };
  const nav = () => page.locator(".cv-navbar nav");
  const links = () => nav().locator("a");
  const requests = [];
  const failed = [];
  const contexts = [];
  const onRequest = request => requests.push({url: request.url(), type: request.resourceType()});
  const onFailed = request => failed.push({url: request.url(), error: request.failure()});
  page.on("request", onRequest);
  page.on("requestfailed", onFailed);
  async function follow(link) {
    const href = await link.evaluate(a => a.href);
    await page.evaluate(() => { window.__navbarOldDocument = true; });
    await link.click();
    await page.waitForURL(href);
    check(page.url() === href, "exact href: " + href);
    check(await page.evaluate(() => !window.__navbarOldDocument), "full document: " + href);
    result.urls.push(href);
  }
  async function login(user) {
    const context = await page.context().browser().newContext();
    contexts.push(context);
    page = await context.newPage();
    page.on("request", onRequest);
    page.on("requestfailed", onFailed);
    await page.setViewportSize({width:1280,height:1000});
    for (const key of ["Shift","Control","Alt","Meta"]) await page.keyboard.up(key);
    await page.context().clearCookies();
    await page.goto(base + "/login/");
    await page.locator('[name="username"]').fill(user);
    await page.locator('[name="password"]').fill(user);
    await page.locator('input[name="login"]').click();
    await page.waitForURL(base + "/");
    await page.goto(base + "/object-navbar/");
    await follow(page.getByRole("link", {name: "Explore object navigation"}).first());
  }
  async function bar(expected, active) {
    check(JSON.stringify((await links().allTextContents()).map(x => x.trim())) === JSON.stringify(expected), "ordered visible links: " + expected.join(", "));
    check(await nav().getAttribute("aria-label") === "Sections for Acme Coffee", "accessible landmark name");
    check((await nav().locator('[aria-current="true"]').innerText()).trim() === active, "current section: " + active);
    check(await nav().locator('[role="tab"], [role="tablist"], [aria-selected], [data-bs-toggle]').count() === 0, "ordinary links without tabs");
    check((await page.locator(".cv-navbar-identity").innerText()).trim() === "Acme Coffee", "stable plain owner caption");
  }
  async function measure(width, stress, method) {
    await page.setViewportSize({width, height: 1000});
    const measured = await page.evaluate(() => {
      const root = document.documentElement;
      const wrapper = document.querySelector(".cv-navbar");
      const nav = wrapper.querySelector("nav");
      const identity = wrapper.querySelector(".cv-navbar-identity");
      const box = el => { const r = el.getBoundingClientRect(); return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}; };
      const textRects = el => { const range = document.createRange(); range.selectNodeContents(el); return [...range.getClientRects()].map(r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom})); };
      const details = el => { const s=getComputedStyle(el); return {box:box(el), parent:box(el.parentElement), text:el.textContent.trim(), textRects:textRects(el), scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,scrollHeight:el.scrollHeight,clientHeight:el.clientHeight, overflow:s.overflow,textOverflow:s.textOverflow,whiteSpace:s.whiteSpace,display:s.display,visibility:s.visibility,color:s.color,background:s.backgroundColor,fontSize:s.fontSize}; };
      return {viewport:innerWidth,scrollWidth:root.scrollWidth,clientWidth:root.clientWidth,identity:details(identity),nav:box(nav),links:[...nav.querySelectorAll("a")].map(details),header:box(document.querySelector(".card h1"))};
    });
    check(measured.scrollWidth <= measured.clientWidth + 1, `${width}/${stress}: no page horizontal overflow (${measured.scrollWidth}/${measured.clientWidth})`);
    for (const item of [measured.identity,...measured.links]) {
      check(item.box.left >= item.parent.left - 1 && item.box.right <= item.parent.right + 1, `${width}/${stress}: element inside parent`);
      check(item.scrollWidth <= item.clientWidth + 1 && item.scrollHeight <= item.clientHeight + 1, `${width}/${stress}: text not clipped`);
      check(item.textOverflow !== "ellipsis" && item.display !== "none" && item.visibility === "visible", `${width}/${stress}: visible complete text`);
      check(item.textRects.every(r=>r.left >= item.box.left-1 && r.right <= item.box.right+1), `${width}/${stress}: text rects within box`);
    }
    measured.rows = new Set(measured.links.map(x => Math.round(x.box.top))).size;
    if (width === 320) check(measured.rows >= 2, "320px links wrap into rows");
    if (!stress) check(measured.identity.box.bottom <= measured.nav.top && measured.nav.bottom <= measured.header.top, "layout B above original header");
    result.measurements.push({width,stress,method,...measured});
  }
  try {
    await page.setViewportSize({width:1280,height:1000});
    await login("alice");
    const expected = ["Details","Notes","Orders","Addresses"];
    await bar(expected,"Details");
    const ownerHrefs = await links().evaluateAll(items=>items.map(a=>a.href));
    result.ownerHrefs = ownerHrefs;
    await measure(320,false,"Customer page at 320 CSS px; retain any shared-layout failure");
    await page.setViewportSize({width:1280,height:1000});
    await follow(nav().getByRole("link",{name:"Notes",exact:true}));
    await bar(expected,"Notes");
    await follow(nav().getByRole("link",{name:"Orders",exact:true}));
    await bar(expected,"Orders");
    await follow(page.locator("table a[href*=navbar_item]").first());
    await follow(page.locator("table a").filter({hasText:"707"}).first());
    await bar(expected,"Orders");
    check(JSON.stringify(await links().evaluateAll(items=>items.map(a=>a.href))) === JSON.stringify(ownerHrefs), "Item uses identical Customer/Tenant section hrefs");
    await measure(1280,false,"1280 CSS px at 100% browser zoom");
    await page.screenshot({path:output+"06.40-desktop.png",fullPage:true});
    await measure(320,false,"320 CSS px at 100% browser zoom");
    await measure(640,false,"200% reflow equivalent: 1280 physical CSS-px baseline / 2 = 640 CSS px; deviceScaleFactor unchanged");
    await links().first().focus();
    for(let i=0;i<4;i++) {
      if(i) await page.keyboard.press("Tab");
      const focus = await page.evaluate(()=>({text:document.activeElement.textContent.trim(),outline:getComputedStyle(document.activeElement).outline,shadow:getComputedStyle(document.activeElement).boxShadow,visible:document.activeElement.matches(":focus-visible")}));
      check(focus.text===expected[i], "Tab reaches " + expected[i]);
      result.keyboard.push(focus);
    }
    for(let i=2;i>=0;i--) { await page.keyboard.press("Shift+Tab"); check(await page.evaluate(()=>document.activeElement.textContent.trim())===expected[i], "Shift+Tab reaches " + expected[i]); }
    check(await page.locator('.cv-navbar-identity a, .cv-navbar-identity [tabindex], .cv-navbar i[tabindex]').count()===0,"caption/icons add no focus stops");
    const colors=await links().evaluateAll(elements=>elements.map(el=>({text:el.textContent.trim(),color:getComputedStyle(el).color,background:getComputedStyle(el).backgroundColor})));
    const luminance=color=>{const rgb=color.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];};
    result.contrast=colors.map(c=>{const bg=c.background==="rgba(0, 0, 0, 0)"?"rgb(255, 255, 255)":c.background;const a=luminance(c.color),b=luminance(bg);return {...c,backgroundUsed:bg,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};});
    check(result.contrast.every(c=>c.ratio>=4.5),"actual Bootstrap link text contrast >=4.5:1");
    const stress={caption:"Long customer identity " + "X".repeat(90) + " with several descriptive words for complete wrapping",label:"Long multiword section label describing customer delivery instructions and historical order activity",token:"Y".repeat(90)};
    result.stress=stress;
    const applyStress = () => page.evaluate(stress=>{
      const caption=document.querySelector(".cv-navbar-identity");
      for(const child of [...caption.childNodes]) if(child.nodeType===Node.TEXT_NODE) child.remove();
      caption.append(document.createTextNode(stress.caption));
      const nav=document.querySelector(".cv-navbar nav"); nav.setAttribute("aria-label","Sections for "+stress.caption);
      const links=nav.querySelectorAll("a");
      for(const [index,text] of [[1,stress.label],[2,stress.token]]) {for(const child of [...links[index].childNodes]) if(child.nodeType===Node.TEXT_NODE) child.remove();links[index].append(document.createTextNode(text));}
    },stress);
    await applyStress();
    for(const width of [1280,320,640]) await measure(width,true,width===640?"200% equivalent CSS reflow (1280/2), not deviceScaleFactor":"100% browser zoom");
    await page.setViewportSize({width:320,height:1000});
    await links().first().focus(); await page.keyboard.press("Tab");
    const focus=await links().nth(1).evaluate(el=>({visible:el.matches(":focus-visible"),outline:getComputedStyle(el).outline,shadow:getComputedStyle(el).boxShadow}));
    check(focus.visible && (focus.shadow!=="none" || !focus.outline.startsWith("0px")),"visible keyboard focus on narrow wrapped link");
    result.narrowFocus=focus;
    await page.screenshot({path:output+"06.40-narrow-focus.png",fullPage:true});
    await links().nth(2).focus();
    const activeHref=await links().nth(2).evaluate(a=>a.href);
    await page.evaluate(()=>{window.__navbarOldDocument=true;});
    await page.keyboard.press("Enter");
    await page.waitForURL(activeHref);
    check(page.url()===activeHref && await page.evaluate(()=>!window.__navbarOldDocument),"Enter activates clickable current section with full document");
    await follow(nav().getByRole("link",{name:"Details",exact:true}));
    for(const width of [1280,320,640]) await measure(width,false,"Customer normal; 640 CSS px is 200% equivalent of 1280 baseline");
    await applyStress();
    for(const width of [1280,320,640]) await measure(width,true,"Customer stress; 640 CSS px is 200% equivalent of 1280 baseline");
    await login("charlie");
    await bar(["Details","Notes","Orders"],"Details");
    await follow(nav().getByRole("link",{name:"Orders",exact:true}));
    await bar(["Details","Notes","Orders"],"Orders");
    check(!requests.some(r=>["fetch","xhr"].includes(r.type)),"no fetch/XHR navbar navigation");
    check(failed.length===0,"all requested assets loaded");
    result.requests=requests; result.failedRequests=failed; result.status=result.failures.length?"failed":"passed";
    return result;
  } catch (error) {
    result.status="error"; result.error=String(error); result.currentUrl=page.url(); return result;
  } finally {
    page.off("request",onRequest); page.off("requestfailed",onFailed);
    for (const context of contexts) await context.close();
  }
}
