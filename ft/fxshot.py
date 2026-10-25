import asyncio,json
import fulltest as ft
import fxtest as fx
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Tokyo")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        await ctx.route("**/open.er-api.com/**",lambda r:r.fulfill(body=json.dumps(fx.ER),content_type="application/json",headers={"access-control-allow-origin":"*"}))
        pg=await ft.newpage(b,ft.jst(11,20,20,0),ctx=ctx,init='localStorage.setItem("mockdb",JSON.stringify({"trips/neko-test/expenses/a":{"amt":3000,"cat":"food","who":"zhang","split":"both","pay":"cash","day":"11/20","note":"挽き肉のトリコ","ts":1}}));')
        await pg.clock.run_for(3000);await pg.wait_for_timeout(600)
        await pg.click('nav.tabs button[data-tab="acct"]');await pg.wait_for_timeout(400)
        box=await (await pg.query_selector('#acct-sum')).bounding_box()
        await pg.screenshot(path='/home/claude/build/fx_1.png',clip={'x':0,'y':box['y']-8,'width':390,'height':box['height']+16})
        await pg.fill('#f-rate','0.21');await pg.press('#f-rate','Tab');await pg.wait_for_timeout(400)
        box=await (await pg.query_selector('#acct-sum')).bounding_box()
        await pg.screenshot(path='/home/claude/build/fx_2.png',clip={'x':0,'y':box['y']-8,'width':390,'height':box['height']+16})
        print(pg.errs);await b.close()
asyncio.run(main())
