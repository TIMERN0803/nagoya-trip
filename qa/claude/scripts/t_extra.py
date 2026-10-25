import asyncio, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for amt in [123456,1234567,12345678]:
            db={f"{B}/expenses/e1":{"amt":amt,"cat":"shop","who":"zhang","split":"both","pay":"card","day":"11/19","note":"電器行很長的店名測試","ts":1}}
            ctx=await q.mkctx(b,vw=320,vh=568); pg=await q.page(ctx,q.jst(11,19,12,0),init=q.seed(db)); await q.tab(pg,"acct")
            sw=await pg.evaluate('document.documentElement.scrollWidth')
            q.rec("320px 記帳",f"單筆 ¥{amt:,}（總額 {len(f'{amt:,}')+1} 字）不撐破",sw<=320,sw)
            if amt==1234567: await pg.screenshot(path=q.SHOTS+"acct_1234567_320.png",full_page=True)
            await ctx.close()
        # 11/17 21:00 晚餐進行中，nowcard 說「都走完了」
        ctx=await q.mkctx(b,dsf=2); pg=await q.page(ctx,q.jst(11,17,21,0))
        await pg.screenshot(path=q.SHOTS+"time_1117_2100_nowcard.png")
        await ctx.close()
        ctx=await q.mkctx(b,dsf=2); pg=await q.page(ctx,q.jst(11,17,17,30)); await q.home(pg)
        await pg.screenshot(path=q.SHOTS+"time_1117_1730_fab.png")
        await ctx.close()
        q.dump("extra"); await b.close()
asyncio.run(main())
