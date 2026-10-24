import asyncio,sys
import fulltest as ft
from playwright.async_api import async_playwright
R=[]
def ok(n,c,x=""):R.append((n,bool(c)));print(("PASS " if c else "FAIL ")+n+(" "+str(x) if not c else ""))
async def st(pg):return await pg.evaluate('({k:document.querySelector(".fab").dataset.k,p:document.querySelector(".fab").classList.contains("pulse"),c:getComputedStyle(document.querySelector(".fab"),"::before").borderTopColor})')
async def home(pg):
    if not await pg.query_selector('.g-home'):
        await pg.click('[data-tab="plan"]');await pg.wait_for_timeout(300)
        if not await pg.query_selector('.g-home'):await pg.click('[data-home]')
    await pg.wait_for_timeout(300)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id="Asia/Tokyo")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/fonts.googleapis.com/**",lambda r:r.abort())
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.jst(11,19,9,0),ctx=ctx)
        await home(pg);a=await st(pg);ok("first open pulses",a["p"],a)
        ok("ring light brown",a["c"]=="rgb(140, 109, 85)",a["c"])
        await pg.clock.fast_forward(11000);await pg.wait_for_timeout(200)
        ok("stops after 10s",not (await st(pg))["p"])
        await pg.reload();await pg.wait_for_timeout(900);await home(pg)
        ok("same item on reopen: no pulse",not (await st(pg))["p"])
        k0=(await st(pg))["k"];ch=False
        for _ in range(16):
            await pg.clock.fast_forward("15:00");await pg.wait_for_timeout(150)
            s=await st(pg)
            if s["k"]!=k0:ch=True;break
        ok("item changed",ch,k0)
        ok("change pulses",s["p"],s)
        ok("no errors",not pg.errs,pg.errs)
        await b.close()
    f=[n for n,c in R if not c];print(f"{len(R)-len(f)}/{len(R)} passed",f);sys.exit(1 if f else 0)
asyncio.run(main())
