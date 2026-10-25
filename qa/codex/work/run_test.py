import json,os,runpy,sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'work'/'run-tools'/'ft'))
from playwright.async_api import Browser,BrowserType
original_context=Browser.new_context
original_launch=BrowserType.launch
audit={'external_blocked':{},'firestore_blocked':0,'contexts':0}
async def launch(self,*args,**kwargs):
    if self.name=='chromium':kwargs['executable_path']=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    return await original_launch(self,*args,**kwargs)
async def context(self,*args,**kwargs):
    kwargs['service_workers']='allow' if os.environ.get('SAFE_SW')=='1' else 'block'
    ctx=await original_context(self,*args,**kwargs)
    audit['contexts']+=1
    if os.environ.get('FORCE_DOWNLOAD')=='1':await ctx.add_init_script('Object.defineProperty(navigator,"canShare",{value:()=>false,configurable:true})')
    async def guard(route):
        u=urlparse(route.request.url)
        if u.hostname in ('localhost','127.0.0.1') or u.scheme in ('data','blob','about'):return await route.continue_()
        if '/firebasejs/' in u.path and u.path.endswith(('firebase-app.js','firebase-firestore.js')):
            name='fs.js' if u.path.endswith('firebase-firestore.js') else 'app.js'
            return await route.fulfill(body=(ROOT/'test-tools'/'ft'/name).read_text(encoding='utf-8'),content_type='text/javascript',headers={'access-control-allow-origin':'*'})
        audit['external_blocked'][u.hostname]=audit['external_blocked'].get(u.hostname,0)+1
        if u.hostname and ('firestore' in u.hostname or 'firebaseio' in u.hostname):audit['firestore_blocked']+=1
        return await route.abort()
    await ctx.route('**/*',guard)
    await ctx.route('**/firestore.googleapis.com/**',lambda r:r.abort())
    return ctx
Browser.new_context=context
BrowserType.launch=launch
target=Path(sys.argv[1]).resolve()
os.chdir(target.parent)
sys.path.insert(0,str(target.parent))
try:runpy.run_path(str(target),run_name='__main__')
finally:
    out=ROOT/'outputs'/'baseline';out.mkdir(parents=True,exist_ok=True)
    (out/(target.stem+'.safety.json')).write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
