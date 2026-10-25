import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-test"
db={f"{B}/expenses/a":{"amt":13200,"cat":"shop","who":"zhang","split":"self","pay":"card","day":"11/21","note":"大國藥妝 榮店","ts":1,"tf":True,"carry":True},
    f"{B}/expenses/b":{"amt":8640,"cat":"shop","who":"star","split":"self","pay":"card","day":"11/22","note":"Mont bell 名古屋","ts":2,"tf":True},
    f"{B}/expenses/c":{"amt":2800,"cat":"food","who":"zhang","split":"both","pay":"cash","day":"11/22","note":"鰻魚飯","ts":3}}
DB=json.dumps(db)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Tokyo")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.jst(11,24,6,0),ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        await pg.wait_for_timeout(600)
        await pg.evaluate('(()=>{const e=[...document.querySelectorAll("ol.tl li.item")].find(l=>l.innerText.includes("先辦退稅，再託運"));scrollTo(0,e.getBoundingClientRect().top+scrollY-330)})()');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/tf_4.png')
        await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(500)
        await pg.evaluate('(()=>{const g=document.querySelector("[data-group-id=buy]");scrollTo(0,g.getBoundingClientRect().top+scrollY-80)})()');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/tf_1.png')
        await pg.click('nav.tabs button[data-tab="acct"]');await pg.wait_for_timeout(500)
        await pg.fill('#f-amt','5500');await pg.click('[data-tf-toggle]');await pg.fill('#f-note','松坂屋')
        await pg.evaluate('(()=>{const g=document.getElementById("acct-form");scrollTo(0,g.getBoundingClientRect().top+scrollY+120)})()');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/tf_2.png')
        await pg.evaluate('(()=>{const g=document.getElementById("tf-list");scrollTo(0,g.getBoundingClientRect().top+scrollY-80)})()');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/tf_3.png')
        print(pg.errs);await b.close()
asyncio.run(main())
