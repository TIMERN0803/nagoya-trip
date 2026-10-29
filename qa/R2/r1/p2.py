import asyncio,sys
sys.path.insert(0,'/home/claude/qa/scripts')
import qa_common as q
from playwright.async_api import async_playwright
CASES={"求助":('openSos()','.sheet-modal .sm-x'),"錢包":('openWallet()','.sheet-modal .sm-x'),"行事曆":('openCalSheet()','.sheet-modal .sm-x'),
"出發前設定":('openSetup()','.sheet-modal .sm-x'),"地圖檢視器":('openViewer("ghibli-map.jpg","x")','.viewer:not(.out) .vclose'),
"給司機看":('sosShow("hotel")','.sos-show .sm-x'),"回顧故事":('openStory()','.story .st-x')}
LEFT='document.querySelectorAll(".sheet-modal,.viewer,.sos-show,.story").length'
async def gc(pg):
    c=await pg.context.new_cdp_session(pg); await c.send("HeapProfiler.collectGarbage"); await c.detach()
async def run(b,name,op,x,mode):
    ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,10,12,0) if name!="回顧故事" else q.jst(11,26,12,0)); await q.home(pg)
    await pg.wait_for_timeout(400); await gc(pg); m0=await q.metrics(pg)
    if mode=="burst":
        for i in range(30): await pg.evaluate(f'{op};document.querySelector({x!r}).click()')
        await pg.wait_for_timeout(500); left500=await pg.evaluate(LEFT); await pg.wait_for_timeout(2000)
    else:
        for i in range(30):
            await pg.evaluate(op); await pg.wait_for_timeout(350); await pg.evaluate(f'document.querySelector({x!r})?.click()'); await pg.wait_for_timeout(450)
        left500=None; await pg.wait_for_timeout(500)
    left=await pg.evaluate(LEFT); await gc(pg); m1=await q.metrics(pg)
    print(f"{mode:6} {name:6} listeners {m0['listeners']}→{m1['listeners']} (+{m1['listeners']-m0['listeners']}) nodes {m0['nodes']}→{m1['nodes']} left@500ms={left500} left_end={left}",flush=True)
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for mode in ("burst","paced"):
            for n,(op,x) in CASES.items(): await run(b,n,op,x,mode)
        await b.close()
asyncio.run(main())
