import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(10,25,13,30),tz="Asia/Taipei",ctx=ctx,init='localStorage.removeItem("ngy:tour");')
        await pg.clock.run_for(1000);await pg.wait_for_timeout(500)
        for i in range(5):
            await pg.screenshot(path=f'/home/claude/build/tour_{i+1}.png')
            await pg.click('[data-tour-next]');await pg.clock.run_for(600);await pg.wait_for_timeout(600)
        await pg.screenshot(path='/home/claude/build/tour_6.png')
        print(pg.errs);await b.close()
asyncio.run(main())
