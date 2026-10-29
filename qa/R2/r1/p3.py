import asyncio,sys
sys.path.insert(0,'/home/claude/qa/scripts')
import qa_common as q
from playwright.async_api import async_playwright
CASES={"行事曆":('openCalSheet()','.sheet-modal .sm-x'),"地圖檢視器":('openViewer("ghibli-map.jpg","x")','.viewer:not(.out) .vclose'),"給司機看":('sosShow("hotel")','.sos-show .sm-x')}
LEFT='[...document.querySelectorAll(".sheet-modal,.viewer,.sos-show")].map(e=>e.className+"|"+getComputedStyle(e).pointerEvents+"|"+getComputedStyle(e).visibility+"|"+getComputedStyle(e).opacity)'
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for gap in (0,16,50,120):
      for n,(op,x) in CASES.items():
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,10,12,0)); await q.home(pg); await pg.wait_for_timeout(300)
        for i in range(5):
            await pg.evaluate(op)
            if gap: await pg.wait_for_timeout(gap)
            await pg.evaluate(f'document.querySelector({x!r})?.click()')
            await pg.wait_for_timeout(gap or 0)
        await pg.wait_for_timeout(1500); left=await pg.evaluate(LEFT)
        # 殘留時，頁面還點得到嗎：點底部「記帳」分頁
        hit=await pg.evaluate('(()=>{const t=document.querySelector("[data-tab=acct]").getBoundingClientRect();const e=document.elementFromPoint(t.x+t.width/2,t.y+t.height/2);return e?.closest("[data-tab]")?"tab":(e?.className||e?.tagName)})()')
        print(f"gap={gap:3}ms {n:6} left={len(left)} {left[:1]} tap-target={hit}",flush=True)
        await ctx.close()
    await b.close()
asyncio.run(main())
