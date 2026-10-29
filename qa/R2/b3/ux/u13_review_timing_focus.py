# C9 旅程回顧入口何時出現（首頁）＋記一筆面板 Tab/Esc 抽查
from uxlib import *
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, t in [("11/23 21:00", jst(11,23,21)), ("11/24 08:00", jst(11,24,8)), ("11/24 12:00", jst(11,24,12)), ("11/24 15:00", jst(11,24,15)), ("11/24 18:00", jst(11,24,18)), ("11/24 21:00", jst(11,24,21)), ("11/24 23:59", jst(11,24,23,59)), ("11/25 00:01", jst(11,25,0,1))]:
            ctx = await S.mkctx(b); pg = await S.opn(ctx, t, init=seed(META), wait=900)
            await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(600)
            has = await pg.query_selector('[data-story-open]') is not None
            print(f"{name}: 首頁有回顧入口={has}")
            await ctx.close()
        ctx = await S.mkctx(b); pg = await S.opn(ctx, jst(11,19,20), init=seed(META), wait=900)
        await tab(pg, "acct"); await S.expopen(pg)
        seq = []
        for i in range(25):
            await pg.keyboard.press("Tab"); seq.append(await pg.evaluate('(()=>{const a=document.activeElement;return a.closest(".exp-sheet")?"in":"OUT:"+(a.tagName+"."+(a.className||"")).slice(0,30)})()'))
        rec("鍵盤", "記一筆面板 Tab 25 次都在面板內", all(s == "in" for s in seq), [s for s in seq if s != "in"][:3])
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(450)
        rec("鍵盤", "空面板 Esc 直接關閉，焦點回到「記一筆」按鈕", await pg.query_selector('.exp-sheet:not(.leaving)') is None and await pg.evaluate('document.activeElement.matches("[data-exp-new]")'), await pg.evaluate('document.activeElement.outerHTML.slice(0,60)'))
        await ctx.close(); await b.close()
    summary()
asyncio.run(main())
