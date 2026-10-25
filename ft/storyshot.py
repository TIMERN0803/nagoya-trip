import asyncio,json
import fulltest as ft
import reviewshot as rs
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(11,25,20,0),tz="Asia/Taipei",ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(rs.DB)});')
        if not await pg.query_selector('.g-home'):await pg.click('[data-home]')
        await pg.wait_for_timeout(700)
        await pg.evaluate('(()=>{const e=document.getElementById("review");scrollTo(0,e.getBoundingClientRect().top+scrollY-500)})()');await pg.wait_for_timeout(200)
        await pg.screenshot(path='/home/claude/build/st_0.png')
        await pg.click('[data-story-open]');await pg.wait_for_timeout(300)
        n=await pg.evaluate('document.querySelectorAll(".st-page").length')
        for i in range(n):
            await pg.clock.run_for(1600);await pg.wait_for_timeout(1500)
            await pg.screenshot(path=f'/home/claude/build/st_{i+1}.png')
            if i<n-1:await pg.click('.st-tap.next')
        print(n,pg.errs);await b.close()
if __name__=="__main__":asyncio.run(main())
