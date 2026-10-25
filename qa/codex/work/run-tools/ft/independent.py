import asyncio,json,time,traceback,datetime as dt
from pathlib import Path
import fulltest as ft
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parents[3]/'outputs'/'independent';OUT.mkdir(parents=True,exist_ok=True)
RESULT=[];DATA={}
def rec(name,ok,details=None):
 r={'name':name,'pass':bool(ok),'details':details};RESULT.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
async def home(g):
 await g.click('[data-tab="plan"]')
 if not await g.locator('.g-home').count():await g.click('[data-home]')
 await g.wait_for_timeout(80)
async def db(g):return await g.evaluate('JSON.parse(localStorage.getItem("mockdb")||"{}")')
async def money(b):
 g=await ft.newpage(b,ft.jst(11,18,20));await g.click('[data-tab="acct"]')
 for raw,expected in [('0','0'),('-100',''),('1.5',''),('999999999',''),('99,999,999','99999999'),('1e3','')]:
  await g.fill('#f-amt',raw);v=await g.input_value('#f-amt');rec('amount_input_'+raw,v==expected,{'entered':raw,'actual':v,'expected':expected or 'reject or explain invalid amount'})
 # Confirm data saved by actual UI, rather than relying on only the field.
 await g.fill('#f-amt','1.5');await g.fill('#f-note','decimal-boundary');await g.click('#f-save');await g.wait_for_timeout(150)
 saved=[v for k,v in (await db(g)).items() if '/expenses/' in k and v.get('note')=='decimal-boundary'];rec('decimal_saved_without_reinterpretation',not saved, saved)
 await g.screenshot(path=str(OUT/'amount-decimal-saved.png'),full_page=True)
 for raw in ['0','   ','']:
  n=len([k for k in await db(g) if '/expenses/' in k]);await g.fill('#f-amt',raw);await g.click('#f-save');await g.wait_for_timeout(50);n2=len([k for k in await db(g) if '/expenses/' in k]);rec('reject_empty_zero_'+repr(raw),n==n2,await g.locator('#f-msg').inner_text())
 for amt in ['4999','5000','99999999']:
  await g.fill('#f-amt',amt);vis=await g.locator('#f-tf-row').is_visible();rec('tax_threshold_'+amt,vis==(int(amt)>=5000),vis)
  await g.fill('#f-note','boundary-'+amt);await g.click('#f-save');await g.wait_for_timeout(100)
  rows=[v for k,v in (await db(g)).items() if '/expenses/' in k and v.get('note')=='boundary-'+amt];rec('integer_exact_'+amt,len(rows)==1 and rows[0]['amt']==int(amt),rows)
 await ft.close(g)
async def xss(b):
 g=await ft.newpage(b,ft.jst(11,18,20));await g.click('[data-tab="list"]')
 payload='<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>😀日本語'+('長'*510)
 await g.click('[data-item-new="buy"]');await g.fill('.chk-form input[name=title]',payload);await g.click('.chk-form .primary');await g.wait_for_timeout(150)
 rec('list_xss_not_executed',await g.evaluate('!window.__xss'))
 saved=[v for k,v in (await db(g)).items() if '/items/' in k and '<img' in v.get('title','')];rec('long_unicode_roundtrip',len(saved)==1 and payload.startswith(saved[0]['title']),{'length':len(payload),'saved':len(saved)})
 rec('long_text_no_horizontal_overflow',await g.evaluate('document.documentElement.scrollWidth<=innerWidth'),await g.evaluate('({width:innerWidth,scrollWidth:document.documentElement.scrollWidth})'))
 await g.screenshot(path=str(OUT/'long-list.png'),full_page=True)
 await g.click('[data-tab="acct"]');await g.fill('#f-amt','100');await g.fill('#f-note',payload);await g.click('#f-save');await g.wait_for_timeout(120);rec('expense_xss_not_executed',await g.evaluate('!window.__xss'))
 await ft.close(g)
async def mood_sync(b):
 a=await ft.newpage(b,ft.jst(11,18,21));await a.click('#mood .fbtn[data-score="5"]');await a.fill('#mood-form textarea','remote-delete-probe');await a.click('#mood-form .primary');await a.wait_for_timeout(150)
 c=await ft.newpage(b,ft.jst(11,18,21,1),ctx=a.ctx);await c.wait_for_timeout(150)
 key=next(k for k in await db(c) if '/moods/' in k)
 # Simulate a different device deleting the document via the same mock Firestore API.
 await c.evaluate('''async key=>{const F=await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js');await F.deleteDoc(F.doc({},key))}''',key)
 await a.wait_for_timeout(250);await home(a)
 text=await a.locator('body').inner_text();rec('remote_mood_delete_clears_home','remote-delete-probe' not in text,{'mock_document_exists':key in await db(a),'stale_note_visible':'remote-delete-probe' in text})
 await a.screenshot(path=str(OUT/'remote-mood-deletion.png'),full_page=True)
 await a.click('.tile[data-day="1"]');t=await a.locator('#mood').inner_text();rec('remote_mood_delete_clears_daily','remote-delete-probe' not in t,t)
 await a.reload();await a.wait_for_timeout(300)
 if await a.locator('[data-home]').count():await a.click('[data-home]')
 rec('remote_mood_delete_reload_clears_cache','remote-delete-probe' not in await a.locator('body').inner_text())
 await a.ctx.close()
async def modal_keyboard(b):
 g=await ft.newpage(b,ft.twt(10,25,18),tz='Asia/Taipei')
 for fn in ['openSos','openWallet','openCalSheet','openSetup']:
  await g.evaluate(fn+'()');await g.wait_for_timeout(100)
  role=await g.locator('.sheet-modal').get_attribute('role');modal=await g.locator('.sheet-modal').get_attribute('aria-modal')
  inside=await g.evaluate('!!document.activeElement?.closest(".sheet-modal")')
  rec(fn+'_focus_enters_dialog',inside,{'role':role,'aria-modal':modal})
  await g.keyboard.press('Escape');rec(fn+'_escape_closes',await g.locator('.sheet-modal').count()==0)
  if await g.locator('.sheet-modal').count():await g.locator('.sheet-modal .sm-x').click(force=True)
 await ft.close(g)
async def timeline(b):
 cases=[(ft.twt(10,25,18),'Asia/Taipei',None),(ft.twt(11,16,23,59),'Asia/Taipei',None),(ft.twt(11,17,0,1),'Asia/Taipei',None),(ft.twt(11,17,6),'Asia/Taipei',None),(ft.jst(11,17,12),'Asia/Tokyo',0),(ft.jst(11,17,18),'Asia/Tokyo',0),(ft.jst(11,18,13),'Asia/Tokyo',1),(ft.jst(11,17,21),'Asia/Tokyo',0),(ft.jst(11,17,22,30),'Asia/Tokyo',0),(ft.jst(11,21,21,30),'Asia/Tokyo',4),(ft.jst(11,21,22,10),'Asia/Tokyo',4),(ft.jst(11,24,7,30),'Asia/Tokyo',7),(ft.jst(11,24,15),'Asia/Tokyo',7),(ft.jst(11,25,12),'Asia/Tokyo',None),(ft.jst(12,15,12),'Asia/Tokyo',None),(ft.jst(11,19,0,1),'Asia/Taipei',2)]
 records=[]
 for t,tz,idx in cases:
  g=await ft.newpage(b,t,tz=tz);initial=await g.locator('body').inner_text();await home(g)
  v=await g.evaluate('''()=>({hero:document.querySelector('.hero')?.innerText,today:[...document.querySelectorAll('.tile.today')].map(x=>x.dataset.day),fab:document.querySelector('.fab')?.hidden?null:document.querySelector('.fab')?.innerText,reminders:[...document.querySelectorAll('.due-alert,.chip.coral')].map(x=>x.innerText)})''')
  rec('timeline_'+t.isoformat()+'_'+tz,not g.errs and (idx is None or v['today']==[str(idx)]),v)
  if t.month==11 and t.day==24:rec('last_day_no_home_fab_'+str(t.hour),'回家' not in (v['fab'] or ''),v['fab'])
  if t.month==11 and t.day==17 and t.hour==22:rec('late_evening_home_fab','回家' in (v['fab'] or ''),v['fab'])
  records.append({'time':t.isoformat(),'tz':tz,'initial':initial[:250],**v});await ft.close(g)
 DATA['timeline']=records
 for start,advance,expected in [(ft.jst(11,18,23,59),'00:02:00','11/19'),(ft.jst(11,24,23,59),'00:02:00','回顧'),(ft.twt(11,16,23,59),'00:02:00',None)]:
  g=await ft.newpage(b,start);await g.clock.fast_forward(advance);await g.wait_for_timeout(800);await g.evaluate('document.dispatchEvent(new Event("visibilitychange"))');await g.wait_for_timeout(150);await home(g)
  v=await g.locator('body').inner_text();rec('midnight_'+start.isoformat(),not g.errs and (expected is None or expected in v),v[:250]);await ft.close(g)
async def layout(b):
 allsizes=[]
 for w,h in [(320,568),(375,667),(390,844),(430,932),(844,390),(568,320)]:
  g=await ft.newpage(b,ft.twt(10,25,18));await g.set_viewport_size({'width':w,'height':h})
  for tab in ['plan','acct','list','wx','move']:
   btn=g.locator('[data-tab="'+tab+'"]');
   if not await btn.count():continue
   await btn.click();await g.wait_for_timeout(40)
   d=await g.evaluate('''()=>({w:innerWidth,sw:document.documentElement.scrollWidth,small:[...document.querySelectorAll('button,a,input[type=checkbox],[role=button]')].filter(e=>{let r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.top<innerHeight&&r.bottom>0&&(r.width<44||r.height<44)}).map(e=>({tag:e.tagName,text:(e.getAttribute('aria-label')||e.innerText||e.id).slice(0,45),width:Math.round(e.getBoundingClientRect().width),height:Math.round(e.getBoundingClientRect().height)}))})''')
   rec(f'layout_{w}x{h}_{tab}',d['sw']<=w+1,d);allsizes.append({'size':[w,h],'tab':tab,**d})
  await home(g);await g.emulate_media(reduced_motion='reduce')
  rec(f'reduced_motion_{w}',await g.evaluate('document.getAnimations().filter(a=>a.playState==="running").length')==0)
  await g.evaluate('openSos()');await g.wait_for_timeout(100)
  rec(f'sos_within_{w}x{h}',await g.locator('.sm-card').evaluate('(e)=>{let r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight+1}'))
  if w in (320,844):await g.screenshot(path=str(OUT/f'sos-{w}x{h}.png'),full_page=True)
  await ft.close(g)
 DATA['layout']=allsizes
async def stress(b):
 measurements=[]
 for n in [50,300,1000]:
  mock={f'trips/neko-test/expenses/e{i}':{'amt':100,'cat':'food','who':'zhang','split':'both','pay':'cash','day':'2026-11-18','note':f'stress-{i}','ts':i+1} for i in range(n)}
  mock['trips/neko-test/settings/meta']={'itemsSeeded':True,'itemsRestore':2}
  if n==1000:
   for group in ['prep','pack','buy']:
    for i in range(200):mock[f'trips/neko-test/items/{group}{i}']={'group':group,'title':f'{group}-{i}','note':'','cat':'etc','order':i,'due':''}
  g=await ft.newpage(b,ft.jst(11,18,20),init='localStorage.setItem("mockdb",'+json.dumps(json.dumps(mock))+');');g.set_default_timeout(12000)
  session=await g.ctx.new_cdp_session(g);await session.send('Performance.enable')
  samples=[]
  for i in range(3):
   await g.evaluate('document.querySelector("[data-tab=plan]").click()')
   ms=await g.evaluate('''async()=>{let t=performance.now();document.querySelector('[data-tab=acct]').click();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return performance.now()-t}''');samples.append(round(ms,2))
  count=await g.locator('.ex[data-edit]').count();s=await g.locator('#acct-sum').inner_text();rec(f'stress_count_{n}',count==n,{'count':count,'sum':s[:100]})
  rec(f'stress_sum_{n}',f'{n*100:,}' in s,s[:120])
  metrics=(await session.send('Performance.getMetrics'))['metrics'];m={x['name']:x['value'] for x in metrics}
  record={'expenses':n,'account_render_ms':samples,'heap_mb':round(m.get('JSHeapUsedSize',0)/1048576,2),'dom_nodes':m.get('Nodes')}
  if n==1000:
   await g.click('[data-tab="list"]');rec('stress_200_prep_200_buy',await g.locator('.chk-row').count()>=400,await g.locator('.chk-row').count())
   await g.click('[data-pack-open]');rec('stress_200_pack',await g.locator('.chk-row').count()==200,await g.locator('.chk-row').count())
   await g.click('[data-pack-close]')
   await session.send('HeapProfiler.collectGarbage');before={x['name']:x['value'] for x in (await session.send('Performance.getMetrics'))['metrics']}
   elapsed=await g.evaluate('''async()=>{let t=performance.now();for(let i=0;i<100;i++){document.querySelector('[data-tab='+(['plan','acct','list'][i%3])+']').click();await new Promise(r=>requestAnimationFrame(r))}return performance.now()-t}''')
   await session.send('HeapProfiler.collectGarbage');after={x['name']:x['value'] for x in (await session.send('Performance.getMetrics'))['metrics']}
   record['switch100']={'ms':round(elapsed,2),'heap_before_mb':round(before['JSHeapUsedSize']/1048576,2),'heap_after_mb':round(after['JSHeapUsedSize']/1048576,2),'listeners_before':before.get('JSEventListeners'),'listeners_after':after.get('JSEventListeners')}
   await session.send('Emulation.setCPUThrottlingRate',{'rate':4});slow=await g.evaluate('''async()=>{let t=performance.now();document.querySelector('[data-tab=acct]').click();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return performance.now()-t}''');record['cpu4_account_ms']=round(slow,2);await session.send('Emulation.setCPUThrottlingRate',{'rate':1})
   await g.clock.fast_forward('12:00:00');rec('stress_12hours_no_js_errors',not g.errs,g.errs[:5])
  measurements.append(record);await ft.close(g)
 DATA['stress']=measurements
async def failure(b):
 for mode in ['500','timeout']:
  ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id='Asia/Tokyo')
  if mode=='500':await ctx.route('**/firebasejs/**',lambda r:r.fulfill(status=500,body='blocked'))
  else:await ctx.route('**/firebasejs/**',lambda r:r.abort('timedout'))
  g=await ft.newpage(b,ft.jst(11,18,20),ctx=ctx);await g.click('[data-tab="acct"]');await g.fill('#f-amt','400');await g.click('#f-save');await g.wait_for_timeout(100)
  t=await g.locator('body').inner_text();local=await g.evaluate('localStorage.getItem("ngy:exp")');rec('firebase_'+mode+'_local_write',local and '400' in local,{'local':local,'text':t[:160]})
  await ctx.close()
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch();DATA['browser']=b.version
  for fn in [money,xss,mood_sync,modal_keyboard,timeline,layout,stress,failure]:
   try:await fn(b)
   except Exception as e:rec(fn.__name__+'_execution',False,traceback.format_exc());DATA.setdefault('execution_errors',[]).append(fn.__name__)
   (OUT/'results.json').write_text(json.dumps({'results':RESULT,'data':DATA},ensure_ascii=False,indent=2),encoding='utf-8')
  await b.close()
 print('TOTAL',len(RESULT),'FAIL',sum(not r['pass'] for r in RESULT),flush=True)
if __name__=='__main__':asyncio.run(main())
