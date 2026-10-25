import asyncio,json,time,re,statistics,inspect
from pathlib import Path
import fulltest as ft
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parents[3]/'outputs'/'journey';OUT.mkdir(parents=True,exist_ok=True)
R=[];D={}
def rec(n,c,d=None):R.append({'name':n,'pass':bool(c),'details':d});print(json.dumps(R[-1],ensure_ascii=False),flush=True)
async def shot(g,name):
 await g.wait_for_timeout(500)
 await g.screenshot(path=str(OUT/name))
async def home(g):
 await g.click('[data-tab="plan"]')
 if not await g.locator('.g-home').count():await g.click('[data-home]')
 await g.evaluate('scrollTo(0,0)');await g.wait_for_timeout(150)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch()
  g=await ft.newpage(b,ft.twt(10,25,18),me=None,code=None);await shot(g,'01-first-open.png');D['onboarding']=await g.locator('body').inner_text()
  await ft.close(g)
  g=await ft.newpage(b,ft.jst(11,18,8));await home(g);await shot(g,'02-morning-home.png');await g.click('[data-tab="wx"]');await shot(g,'03-weather.png')
  await g.click('[data-tab="plan"]');await g.click('.tile[data-day="1"]');await shot(g,'04-daily-route.png');D['route_links']=await g.locator('a[href*="google"]').evaluate_all('(a)=>a.map(x=>({text:x.innerText,href:x.href}))')
  await g.click('[data-tab="acct"]');await g.fill('#f-amt','5000');await g.click('[data-tf-toggle]');await g.fill('#f-note','demo免稅現金');await shot(g,'05-checkout.png');await g.click('#f-save');await g.wait_for_timeout(120);await g.click('.wchip');await shot(g,'06-wallet.png');await g.locator('.ws .sm-x').click()
  await g.evaluate('openSos()');await g.click('[data-sos-tab="emg"]');D['tel_links']=await g.locator('a[href^="tel:"]').evaluate_all('(a)=>a.map(x=>({text:x.innerText,href:x.href}))');await g.click('[data-sos-show="hotel"]');await shot(g,'07-driver-address.png')
  await ft.close(g)
  g=await ft.newpage(b,ft.jst(11,17,22,30));await home(g);await shot(g,'08-evening-home.png');await g.click('[data-tab="list"]');await g.click('[data-pack-open]');await shot(g,'09-packing.png');await ft.close(g)
  g=await ft.newpage(b,ft.jst(11,24,7,30));await g.click('[data-tab="acct"]');btn=g.locator('[data-tf-open]');
  if await btn.count():await btn.click()
  await shot(g,'10-last-day.png');await ft.close(g)
  g=await ft.newpage(b,ft.jst(11,26,12));await home(g);await g.click('[data-story-open]');await shot(g,'11-review.png');await ft.close(g)
  # Two pages share the mock db; identity is explicitly held equal (mock limitation).
  a=await ft.newpage(b,ft.jst(11,18,20));c=await ft.newpage(b,ft.jst(11,18,20),ctx=a.ctx)
  await a.click('[data-tab="acct"]');await c.click('[data-tab="acct"]');await a.fill('#f-amt','100');await c.fill('#f-amt','200');await asyncio.gather(a.click('#f-save'),c.click('#f-save'));await a.wait_for_timeout(150)
  amounts=await a.evaluate('Object.entries(JSON.parse(localStorage.mockdb)).filter(([k])=>k.includes("/expenses/")).map(([k,v])=>v.amt)');rec('two_page_concurrent_add',sorted(amounts)==[100,200],amounts)
  await a.fill('#f-amt','333');await a.evaluate('window.__writeDelay=300;for(let i=0;i<10;i++)document.getElementById("f-save").click()');await a.wait_for_timeout(700)
  amounts=await a.evaluate('Object.entries(JSON.parse(localStorage.mockdb)).filter(([k])=>k.includes("/expenses/")).map(([k,v])=>v.amt)');rec('ten_clicks_single_expense',amounts.count(333)==1,amounts)
  await a.click('[data-tab="list"]');await c.click('[data-tab="list"]');id=await a.locator('.chk input[type=checkbox]').first.get_attribute('id');await a.locator('#'+id).check();await c.wait_for_timeout(150);rec('two_page_check_sync',await c.locator('#'+id).is_checked())
  await a.ctx.close()
  # Cold navigation under CDP Slow 3G. Only localhost+mock SDK; fonts/APIs intentionally blocked.
  ctx=await b.new_context();g=await ctx.new_page();cdp=await ctx.new_cdp_session(g);await cdp.send('Network.enable');await cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':400,'downloadThroughput':50000,'uploadThroughput':50000,'connectionType':'cellular3g'})
  t=time.perf_counter();await g.goto('http://localhost:8766/');await g.wait_for_selector('nav.tabs');D['slow3g']={'latency_ms':400,'bytes_per_sec':50000,'navigation_to_tabs_ms':round((time.perf_counter()-t)*1000,2),'caveat':'localhost; mock SDK; external fonts and APIs blocked; not a production network benchmark'};await ctx.close()
  # Dimension and DOM contrast candidates on actual rendered controls.
  g=await ft.newpage(b,ft.twt(10,25,18));await g.click('[data-tab="acct"]');D['a11y_controls']=await g.locator('button,input,select,textarea').evaluate_all('''a=>a.filter(e=>{let r=e.getBoundingClientRect();return r.width&&r.height}).map(e=>({tag:e.tagName,id:e.id,text:e.getAttribute('aria-label')||e.innerText,labelled:!!(e.getAttribute('aria-label')||e.labels?.length||e.innerText),width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))''')
  samples=await g.locator('body *').evaluate_all('''a=>a.filter(e=>e.children.length===0&&e.textContent.trim()&&e.getBoundingClientRect().width).map(e=>{let cs=getComputedStyle(e),p=e,bg='';while(p){let v=getComputedStyle(p).backgroundColor;if(v!=='rgba(0, 0, 0, 0)'&&v!=='transparent'){bg=v;break}p=p.parentElement}return {text:e.textContent.trim().slice(0,40),fg:cs.color,bg,size:cs.fontSize,weight:cs.fontWeight,cls:e.className}}).filter(x=>x.fg.startsWith('rgb')&&x.bg.startsWith('rgb')).slice(0,200)''')
  def rgb(s):return [float(x)/255 for x in re.findall(r'[\d.]+',s)[:3]]
  def lum(s):return sum(w*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v,w in zip(rgb(s),[.2126,.7152,.0722]))
  for x in samples:
   l1,l2=sorted([lum(x['fg']),lum(x['bg'])]);x['ratio']=round((l2+.05)/(l1+.05),2)
  D['contrast_candidates']=[x for x in samples if x['ratio']<4.5]
  await g.evaluate('document.body.style.zoom="2"');await shot(g,'12-css-zoom-200.png');D['css_zoom_200']=await g.evaluate('({innerWidth,scrollWidth:document.documentElement.scrollWidth})');await ft.close(g)
  # Final proof for mood deletion, with both UI states recorded.
  a=await ft.newpage(b,ft.jst(11,18,21));await a.click('#mood .fbtn[data-score="5"]');await a.fill('#mood-form textarea','刪除同步測試');await a.click('#mood-form .primary');await a.wait_for_timeout(100);c=await ft.newpage(b,ft.jst(11,18,21),ctx=a.ctx)
  await c.evaluate('''async()=>{let F=await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js');let key=Object.keys(JSON.parse(localStorage.mockdb)).find(k=>k.includes('/moods/'));await F.deleteDoc(F.doc({},key))}''');await a.wait_for_timeout(150);await shot(a,'13-deleted-mood-still-visible.png');rec('mood_delete_stale_reproduced','刪除同步測試' in await a.locator('#mood').inner_text());await a.ctx.close();await b.close()
 (OUT/'results.json').write_text(json.dumps({'results':R,'data':D},ensure_ascii=False,indent=2),encoding='utf8')
asyncio.run(main())
