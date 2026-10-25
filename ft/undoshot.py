import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
EXP=json.dumps({"trips/neko-test/expenses/a":{"amt":3000,"cat":"food","who":"zhang","split":"both","day":"11/18","note":"燒肉","ts":1,"pay":"cash"},"trips/neko-test/expenses/b":{"amt":1200,"cat":"move","who":"star","split":"both","day":"11/18","note":"名鐵","ts":2,"pay":"card"}})
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Tokyo")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.jst(11,18,20,0),ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(EXP)});')
        await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(500)
        ed=await pg.query_selector('[data-group-id=buy] [data-item-edit]');id=await ed.get_attribute('data-item-edit')
        await ed.click();await pg.wait_for_timeout(300);await pg.click(f'[data-item-del="{id}"]');await pg.wait_for_timeout(500)
        await pg.evaluate('document.querySelector("[data-group-id=buy]").scrollIntoView({block:"start"});scrollBy(0,-90)');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/undo_list.png')
        await pg.click('nav.tabs button[data-tab="acct"]');await pg.wait_for_timeout(500)
        await pg.click('.ex[data-edit] >> nth=0');await pg.wait_for_timeout(300)
        await (await pg.query_selector('[data-del]')).click();await pg.wait_for_timeout(500)
        await pg.evaluate('document.getElementById("acct-list").scrollIntoView({block:"start"});scrollBy(0,-120)');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/undo_acct.png')
        print(pg.errs);await b.close()
asyncio.run(main())
