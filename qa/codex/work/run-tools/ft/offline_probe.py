import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parents[3]/'outputs'/'offline';OUT.mkdir(parents=True,exist_ok=True)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch();ctx=await b.new_context();g=await ctx.new_page();await g.add_init_script('localStorage.setItem("ngy:tour","1")')
  await g.goto('http://localhost:8767/manifest.webmanifest');await g.evaluate('caches.open("ngy-v-old").then(c=>c.put("/old",new Response("old")))');await g.goto('http://localhost:8767/');await g.evaluate('navigator.serviceWorker.ready');await g.reload();await g.wait_for_timeout(300)
  await g.wait_for_timeout(400)
  info={'controller':await g.evaluate('!!navigator.serviceWorker.controller'),'caches':await g.evaluate('caches.keys()')}
  await ctx.set_offline(True);await g.reload();await g.wait_for_timeout(200);info['offline_body']=await g.locator('body').inner_text();info['app_opens']='名古屋' in info['offline_body']
  await g.click('.tile[data-day="1"]');info['map_cached']=await g.locator('.inmap img').evaluate('(e)=>e.complete&&e.naturalWidth>0');await g.screenshot(path=str(OUT/'offline-map.png'))
  await ctx.close();ctx=await b.new_context();await ctx.set_offline(True);g=await ctx.new_page()
  try:await g.goto('http://localhost:8767/');info['first_ever_offline']='loaded'
  except Exception:info['first_ever_offline']='cannot load without initial cache (expected browser constraint)'
  (OUT/'results.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(info,ensure_ascii=False),flush=True);await b.close()
asyncio.run(main())
