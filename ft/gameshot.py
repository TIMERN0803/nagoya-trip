import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
EXP=json.dumps({"trips/neko-test/expenses/a":{"amt":3000,"cat":"food","who":"zhang","split":"both","day":"11/18","note":"","ts":1},"trips/neko-test/expenses/b":{"amt":1200,"cat":"move","who":"star","split":"both","day":"11/18","note":"","ts":2}})
async def shot(b,t,tz,name,scroll=False,init=""):
    ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id=tz)
    await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
    pg=await ft.newpage(b,t,tz=tz,ctx=ctx,init=init)
    if not await pg.query_selector('.g-home'):await pg.click('[data-home]');await pg.wait_for_timeout(500)
    await pg.evaluate('scrollTo(0,0)');await pg.wait_for_timeout(300)
    await pg.screenshot(path=f'/home/claude/build/{name}_1.png')
    await pg.evaluate('scrollTo(0,760)');await pg.wait_for_timeout(300)
    await pg.screenshot(path=f'/home/claude/build/{name}_2.png')
    await pg.evaluate('scrollTo(0,document.body.scrollHeight)');await pg.wait_for_timeout(300)
    await pg.screenshot(path=f'/home/claude/build/{name}_3.png')
    print(name,pg.errs);await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        await shot(b,ft.twt(10,24,22,50),"Asia/Taipei","gpre")
        await shot(b,ft.jst(11,21,10,20),"Asia/Tokyo","gtrip",init=f'localStorage.setItem("mockdb",{json.dumps(EXP)});')
        await b.close()
if __name__=="__main__":asyncio.run(main())
