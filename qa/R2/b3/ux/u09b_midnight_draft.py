# 跨午夜重載後，記一筆草稿是否還在（amt_btn 情境）；重跑 3 次
from uxlib import *
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for r in range(3):
            ctx = await S.mkctx(b)
            pg = await S.opn(ctx, jst(11, 19, 23, 59), init=seed(META), wait=1000)
            await tab(pg, "acct"); await S.expopen(pg)
            await pg.fill('#f-amt', '1500'); await pg.fill('#f-note', '半夜的拉麵')
            await pg.click('.exp-sheet .pick >> nth=1')
            await pg.clock.fast_forward("01:40"); await pg.wait_for_timeout(2200)
            st = await pg.evaluate('({amt:document.getElementById("f-amt")?.value||"",draft:draft.amt,sheet:!!document.querySelector(".exp-sheet"),today:todayIdx,tab})')
            print(f"[{r}] 重載後:", st)
            await ctx.close()
        await b.close()
asyncio.run(main())
