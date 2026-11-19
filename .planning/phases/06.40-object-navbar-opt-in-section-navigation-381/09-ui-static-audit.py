"""Fresh static UI evidence using existing tools and an exclusively owned server."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request

root = Path.cwd()
phase = Path(__file__).resolve().parent
shots = root / '.planning/ui-reviews/06.40-plan09-fresh'
shots.mkdir(parents=True, exist_ok=True)
directory = Path(tempfile.mkdtemp(prefix='cv09-ui-'))
server = None
report = {'product_revision': '6e8434394b73fe160210c22dab248d4cf3714b7d', 'interaction_capture': 'off'}
try:
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    report['port'] = port
    (directory / 'audit_settings.py').write_text('from project.settings import *\nDATABASES["default"]["NAME"] = ' + repr(str(directory / 'db.sqlite3')) + '\n')
    env = {**os.environ, 'PYTHONPATH': f'{root}/src:{directory}', 'PYTHONDONTWRITEBYTECODE': '1'}
    command = [str(root / '.nox/examples-3-12-django-5-2/bin/python'), 'manage.py']
    cwd = root / 'examples/bootstrap5'
    for args in [['migrate', '--noinput'], ['shell', '-c', 'from navbar_demo.seed import seed; seed()']]:
        subprocess.run(command + args + ['--settings=audit_settings'], cwd=cwd, env=env, check=True, stdout=subprocess.DEVNULL)
    with (directory / 'server.log').open('w') as log:
        server = subprocess.Popen(command + ['runserver', f'127.0.0.1:{port}', '--noreload', '--settings=audit_settings'], cwd=cwd, env=env, stdout=log, stderr=log)
        for _ in range(100):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{port}/login/', timeout=1).close()
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('readiness failed')
        js = r'''
const {chromium} = require('/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({executablePath:'/home/alex/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome',headless:true,args:['--no-sandbox']});
 try {
 const context=await browser.newContext(); const page=await context.newPage();
 const base=process.argv[2], out=process.argv[3];
 await page.goto(base+'/login/');
 await page.locator('[name="username"]').fill('alice'); await page.locator('[name="password"]').fill('alice');
 await page.locator('input[name="login"]').click(); await page.waitForURL(base+'/');
 await page.goto(base+'/object-navbar/');
 const landing=await page.locator('.card-body p').evaluateAll(es=>es.map(e=>({text:e.textContent,fontSize:getComputedStyle(e).fontSize})));
 const target=await page.getByRole('link',{name:'Explore ViewSet Navigation'}).first().getAttribute('href');
 await page.goto(base+target);
 const measurements=[];
 for(const width of [1440,375,768,1280,320,640]) {
 await page.setViewportSize({width,height:1000}); await page.screenshot({path:out+'/'+width+'.png',fullPage:true});
 measurements.push(await page.evaluate(()=>{ const n=document.querySelector('.cv-navbar'), id=n.querySelector('.cv-navbar-identity'); const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}}; const detail=e=>({text:e.textContent.trim(),box:rect(e),fontSize:getComputedStyle(e).fontSize,fontWeight:getComputedStyle(e).fontWeight,color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor}); return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,identity:detail(id),nav:rect(n.querySelector('nav')),name:n.querySelector('nav').getAttribute('aria-label'),links:[...n.querySelectorAll('a')].map(detail),current:n.querySelectorAll('[aria-current="true"]').length,header:rect(document.querySelector('.card h1'))}; }));
 }
 console.log(JSON.stringify({browser:browser.version(),landing,measurements,screenshots:'captured (6/6)',interaction_captures:'off; login used only to reach authenticated static page'}));
 } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        (directory / 'capture.cjs').write_text(js)
        run = subprocess.run(['node', str(directory / 'capture.cjs'), f'http://127.0.0.1:{port}', str(shots)], capture_output=True, text=True, timeout=100)
        report['capture_exit'] = run.returncode
        if run.returncode:
            report['error'] = run.stderr
        else:
            report.update(json.loads(run.stdout))
finally:
    if server is not None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=10)
        report['server_exit'] = server.returncode
    shutil.rmtree(directory)
    report['settings_and_database_removed'] = not directory.exists()
    with socket.socket() as probe:
        report['port_released'] = probe.connect_ex(('127.0.0.1', port)) != 0
    (phase / '09-ui-static-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
