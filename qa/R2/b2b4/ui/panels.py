from common import *
from sweep_ui import DB,M
W=int(sys.argv[1]) if len(sys.argv)>1 else 390
H={375:812,390:844,430:932}[W]
async def metr(pg): return await pg.evaluate("("+M+")()")
async def shot(pg,name,wait=700):
    await pg.wait_for_timeout(wait); await pg.screenshot(path=OUT+f'pn_{W}_{name}.png')
    m=await metr(pg); print(name,"| sw",m['sw'],"| low",m['low'][:4],"| small",m['small'][:2],"| trunc",m['trunc'][:2],"| hscroll",m['hscroll'][:2],flush=True)
async def close_top(pg):
    for sel in ['.sm-x','[data-exp-x]','[data-close]','.sv-x','.rv-x','.x']:
        e=await pg.query_selector(sel)
        if e and await e.is_visible():
            try: await e.click(); break
            except Exception: pass
    await pg.wait_for_timeout(500)
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
async def run(b,label,t,tz,steps):
    ctx=await mkctx(b,tz=tz); pg=await opn(ctx,t,init=seed(DB),wait=1100); await pg.set_viewport_size({"width":W,"height":H})
    for name,js,sel in steps:
        try:
            await pg.evaluate(js); await pg.wait_for_timeout(600)
            if sel:
                await pg.click(sel); 
            await shot(pg,f"{label}_{name}")
        except Exception as e: print("ERR",label,name,str(e)[:150])
        await close_top(pg)
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        await run(b,"j1913",ft.jst(11,19,13),"Asia/Tokyo",[
          ("acct_list",'tab="acct";render()',None),
          ("exp_new",'tab="acct";render()','[data-exp-new]'),
          ("wallet",'tab="plan";view="home";render()','[data-wallet-open]'),
          ("sos",'tab="plan";view="home";render()','[data-sos]'),
          ("sync",'tab="plan";view="home";render()','[data-sync-info]'),
          ("list_prep",'tab="list";listTab="prep";listSub=null;render()',None),
          ("list_buy",'tab="list";listTab="buy";listSub=null;render()',None),
          ("pack",'tab="list";listSub="pack";render()',None),
          ("wx",'tab="wx";render()',None),
          ("move",'tab="move";render()',None),
          ("day_mood",'tab="plan";view="day";dayIdx=2;render();document.querySelector("#mood")?.scrollIntoView({block:"center"})',None),
          ("cal",'tab="plan";view="home";render()','[data-cal]'),
        ])
        await run(b,"tw1030",ft.twt(10,30,20),"Asia/Taipei",[
          ("setup",'tab="plan";view="home";render()','[data-setup-open]'),
          ("list_prep",'tab="list";listTab="prep";listSub=null;render()',None),
          ("list_empty_pack",'tab="list";listSub="pack";render()',None),
          ("acct_empty",'tab="acct";render()',None),
        ])
        await run(b,"tw1125",ft.twt(11,25,10),"Asia/Taipei",[
          ("story",'tab="plan";view="home";render()','[data-story-open]'),
        ])
        await b.close()
if __name__=='__main__': asyncio.run(main())
