from common import *
from panels2 import FULL
W=int(sys.argv[1]) if len(sys.argv)>1 else 390; H={375:812,390:844,430:932}[W]
from sweep_ui import M
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await mkctx(b,tz="Asia/Taipei"); pg=await opn(ctx,ft.twt(11,24,23,59),init=seed(FULL),wait=1100); await pg.set_viewport_size({"width":W,"height":H})
        await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(600)
        await pg.click('[data-story-open]'); await pg.wait_for_timeout(900)
        for i in range(14):
            await pg.screenshot(path=OUT+f'story_{W}_{i:02d}.png')
            m=await pg.evaluate("("+M+")()")
            cls=await pg.evaluate('document.querySelector(".st-page")?.className')
            print(i,cls,"| low",m['low'][:3],"| small",m['small'][:2],"| trunc",m['trunc'][:2],"| hscroll",m['hscroll'][:2],flush=True)
            if not await pg.query_selector('.story'): break
            await pg.mouse.click(W-40,H//2); await pg.wait_for_timeout(2600)
        await ctx.close(); await b.close()
asyncio.run(main())
