import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-test"
DB=json.dumps({f"{B}/expenses/a":{"amt":13200,"cat":"shop","who":"zhang","split":"self","pay":"card","day":"11/21","note":"大國藥妝 榮店","ts":1,"tf":True,"carry":True},
 f"{B}/expenses/b":{"amt":8640,"cat":"shop","who":"star","split":"self","pay":"card","day":"11/22","note":"Mont bell 名古屋","ts":2,"tf":True}})
O='/home/claude/build/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Tokyo")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.jst(11,21,20,0),ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(500)
        await pg.click('[data-list-tab="buy"]');await pg.wait_for_timeout(400)
        await pg.screenshot(path=O+'tr_1_buy.png')
        await pg.click('nav.tabs button[data-tab="acct"]');await pg.wait_for_timeout(600)
        await pg.evaluate('(()=>{const g=document.getElementById("tf-list");scrollTo(0,g.getBoundingClientRect().top+scrollY-80)})()');await pg.wait_for_timeout(300)
        await pg.screenshot(path=O+'tr_2_acct.png')
        await pg.click('#tf-list [data-tr-open]');await pg.wait_for_timeout(800)
        await pg.screenshot(path=O+'tr_3_sheet_top.png')
        for i,y in enumerate([620,1240,1860]):
            await pg.evaluate(f'document.querySelector(".tr-sheet").scrollTop={y}');await pg.wait_for_timeout(250)
            await pg.screenshot(path=O+f'tr_{4+i}_sheet.png')
        d=await ft.newpage(b,ft.jst(11,24,7,0),ctx=ctx)
        await d.wait_for_timeout(500)
        await d.evaluate('(()=>{const e=[...document.querySelectorAll("ol.tl li.item")].find(l=>l.innerText.includes("先辦退稅，再託運"));scrollTo(0,e.getBoundingClientRect().top+scrollY-330)})()');await d.wait_for_timeout(300)
        await d.screenshot(path=O+'tr_7_day8.png')
        await d.click('ol.tl [data-tr-open]');await d.wait_for_timeout(800)
        await d.screenshot(path=O+'tr_8_sheet_fly.png')
        await d.click('.tr-sheet [data-tr-ph=fly] details.tr-d summary');await d.wait_for_timeout(300)
        await d.screenshot(path=O+'tr_9_fly_detail.png')
        print(pg.errs,d.errs);await b.close()
asyncio.run(main())
