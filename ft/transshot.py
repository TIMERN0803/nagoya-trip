# 轉場截圖：換頁（首頁→某天）與彈窗關閉的中間影格，拼成一張給使用者看
import asyncio, sys
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/trans"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await S.mkctx(b); pg = await opn(ctx)
        await pg.set_viewport_size({"width": 390, "height": 760})
        await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(500)
        # 慢放 4 倍方便看清楚中間影格
        c = await ctx.new_cdp_session(pg); await c.send("Animation.enable"); await c.send("Animation.setPlaybackRate", {"playbackRate": 0.25})
        await pg.click('.g-home .grid .tile[data-day="2"]')
        for i, t in enumerate([0, 250, 500, 900]):
            if i: await pg.wait_for_timeout(t - [0, 250, 500, 900][i - 1])
            await pg.screenshot(path=f"{OUT}/page{i}.png")
        await pg.wait_for_timeout(400)
        await pg.click('.bar [data-sos]'); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f"{OUT}/sheet0.png")
        await pg.click('.sheet-modal .sm-x')
        for i, t in enumerate([200, 420, 600]):
            await pg.wait_for_timeout(t - ([0, 200, 420][i]))
            await pg.screenshot(path=f"{OUT}/sheet{i+1}.png")
        await b.close()
async def opn(ctx): return await S.opn(ctx, ft.jst(11, 10, 12), init=S.seed(S.META))
asyncio.run(main())
