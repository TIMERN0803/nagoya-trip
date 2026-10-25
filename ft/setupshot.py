import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-test"
db={f"{B}/checks/su-{k}@star":{"done":True} for k in ["home","me","sync","sos"]}
DB=json.dumps(db)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(10,25,13,30),tz="Asia/Taipei",ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        if not await pg.query_selector('.g-home'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
        await pg.wait_for_timeout(1800)
        await pg.evaluate('(()=>{const e=document.querySelector(".setup-entry");scrollTo(0,e.getBoundingClientRect().top+scrollY-420)})()');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/setup_1.png')
        await pg.click('[data-setup-open]');await pg.wait_for_timeout(500)
        await pg.screenshot(path='/home/claude/build/setup_2.png')
        await pg.evaluate('document.querySelector(".su-sheet").scrollTop=9999');await pg.wait_for_timeout(200)
        await pg.screenshot(path='/home/claude/build/setup_3.png')
        print(pg.errs);await b.close()
asyncio.run(main())
