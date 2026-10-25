import asyncio,json,traceback,inspect,time,struct
from pathlib import Path
import fulltest as ft
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parents[3]/'outputs'/'followup';OUT.mkdir(parents=True,exist_ok=True)
R=[]
def rec(n,c,d=None):R.append({'name':n,'pass':bool(c),'details':d});print(json.dumps(R[-1],ensure_ascii=False),flush=True)
async def home(g):
 await g.click('[data-tab="plan"]')
 if not await g.locator('.g-home').count():await g.click('[data-home]')
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch()
  g=await ft.newpage(b,ft.jst(11,26,12));await home(g);await g.click('[data-story-open]');await g.wait_for_timeout(200)
  # Actual button with browser-native PNG export; retain the error text if it fails.
  for _ in range(8):
   if await g.locator('.st-tap.next').get_attribute('hidden') is not None:break
   await g.evaluate('document.querySelector(".st-tap.next").click()');await g.wait_for_timeout(200)
  await g.evaluate('Object.defineProperty(navigator,"canShare",{value:()=>false,configurable:true})')
  try:
   t=time.perf_counter()
   async with g.expect_download(timeout=8000) as event:await g.click('[data-story-save]')
   d=await event.value;await d.save_as(str(OUT/'review-empty.png'));raw=(OUT/'review-empty.png').read_bytes();rec('review_native_download',raw[:8]==b'\x89PNG\r\n\x1a\n',{'seconds':round(time.perf_counter()-t,2),'bytes':len(raw),'size':struct.unpack('>II',raw[16:24])})
  except Exception as e:
   rec('review_native_download',False,{'message':await g.locator('.st-msg').inner_text(),'error':str(e)[:300],'page_errors':g.errs})
   probe=await g.evaluate('''async()=>{try {await rvSvgImg('<use href="#cats-hi" xlink:href="#cats-hi"/>','0 0 132 80',270,164);return 'ok'}catch(e){return {type:e?.type,message:e?.message,target:e?.target?.src?.slice(0,100)}}}''');rec('review_svg_probe',probe=='ok',probe)
  await g.screenshot(path=str(OUT/'review-save-state.png'))
  await ft.close(g)
  # Voice list initially empty then asynchronously populated (iOS-style).
  stub='''(()=>{window.said=[];window.cancels=0;window.voices=[];window.listeners=[];const ss={getVoices:()=>voices,speak:u=>said.push({text:u.text,lang:u.lang,rate:u.rate,voice:u.voice?.name||null}),cancel:()=>window.cancels++,addEventListener:(n,f)=>listeners.push(f),removeEventListener:()=>{}};Object.defineProperty(window,'speechSynthesis',{value:ss,configurable:true});window.SpeechSynthesisUtterance=function(t){this.text=t}})();'''
  g=await ft.newpage(b,ft.twt(10,25,18));await g.add_init_script(stub);await g.reload();await g.wait_for_timeout(200);await home(g);await g.evaluate('openSos()');await g.click('.sos-ph button >> nth=0');await g.click('[data-say]');rec('voice_empty_fallback_requests_japanese',await g.evaluate('said.length===1&&said[0].lang==="ja-JP"&&said[0].rate===0.85'))
  await g.evaluate('voices=[{lang:"ja-JP",name:"Kyoko"}];listeners.forEach(f=>f());speechSynthesis.onvoiceschanged?.()');await g.click('[data-say]');rec('voice_async_japanese_available',await g.evaluate('said.length===2&&said[1].voice==="Kyoko"'),await g.evaluate('said'))
  await g.evaluate('for(let i=0;i<10;i++)document.querySelector("[data-say]").click()');rec('voice_rapid_no_queue',await g.evaluate('cancels>=said.length-1'),await g.evaluate('({cancels,utterances:said.length})'))
  old=await g.evaluate('cancels');await g.click('.sos-show .sm-x');rec('voice_close_cancels',await g.evaluate('cancels')>old)
  await ft.close(g)
  # Cash zero/negative and payer change with per-person wallet balances.
  data={'trips/neko-test/wallet/zhang':{'cashIn':100},'trips/neko-test/wallet/star':{'cashIn':200}}
  g=await ft.newpage(b,ft.jst(11,18,20),init='localStorage.setItem("mockdb",'+json.dumps(json.dumps(data))+');');await g.click('[data-tab="acct"]');await g.fill('#f-amt','100');await g.click('#f-save');await g.wait_for_timeout(100);rec('wallet_exact_zero','¥0' in await g.locator('.wchip').inner_text(),await g.locator('.wchip').inner_text())
  await g.fill('#f-amt','1');await g.click('#f-save');await g.wait_for_timeout(100);rec('wallet_negative_warning',await g.locator('.wchip.low').count()==1 and '-1' in await g.locator('.wchip').inner_text(),await g.locator('.wchip').inner_text())
  await g.locator('.ex[data-edit]').last.click();await g.click('[data-pick="who"] [data-v="star"]');await g.click('#f-save');await g.wait_for_timeout(100);await g.click('.wchip');text=await g.locator('.ws').inner_text();rec('payer_edit_updates_both_wallets','¥99' in text and '¥100' in text,text);await ft.close(g)
  await b.close()
 (OUT/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2),encoding='utf8')
asyncio.run(main())
