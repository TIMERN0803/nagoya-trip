import asyncio,json
from pathlib import Path
import fulltest as ft
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parents[3]/'outputs'/'journey'
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch();data={'trips/neko-test/expenses/tax':{'amt':6600,'cat':'shop','who':'zhang','split':'both','pay':'cash','day':'11/21','note':'測試藥妝店','tf':True,'ts':1}}
  g=await ft.newpage(b,ft.jst(11,24,7,30),init='localStorage.setItem("mockdb",'+json.dumps(json.dumps(data))+');');await g.click('[data-tab="acct"]');await g.locator('#tf-list').scroll_into_view_if_needed();await g.wait_for_timeout(500);await g.screenshot(path=str(OUT/'10-last-day.png'));print('TAX',await g.locator('#tf-list').inner_text(),flush=True);await ft.close(g)
  g=await ft.newpage(b,ft.jst(11,18,21));await g.click('#mood .fbtn[data-score="5"]');await g.fill('#mood-form textarea','deletion-reload-check');await g.click('#mood-form .primary');await g.wait_for_timeout(100);c=await ft.newpage(b,ft.jst(11,18,21),ctx=g.ctx)
  await c.evaluate('''async()=>{const F=await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js');let k=Object.keys(JSON.parse(localStorage.mockdb)).find(k=>k.includes('/moods/'));await F.deleteDoc(F.doc({},k))}''');await g.wait_for_timeout(100);await g.reload();await g.wait_for_timeout(200)
  v={'daily_stale_after_reload':'deletion-reload-check' in await g.locator('#mood').inner_text(),'remote_mood_count':await g.evaluate('Object.keys(JSON.parse(localStorage.mockdb)).filter(k=>k.includes("/moods/")).length')};print(json.dumps(v),flush=True);(OUT/'deletion-reload.json').write_text(json.dumps(v),encoding='utf8');await g.ctx.close();await b.close()
asyncio.run(main())
