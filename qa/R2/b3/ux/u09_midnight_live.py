# 極端時間：App 開著跨午夜（dayCheck 30 秒檢查 → location.reload）。含「正在記一筆／寫心情時跨午夜」會不會丟輸入
from uxlib import *
async def cross(b, name, t_open, tz, ff="01:10"):
    ctx = await S.mkctx(b, tz=tz)
    pg = await S.opn(ctx, t_open, init=seed(META), wait=1000)
    await pg.evaluate('window.__mark=1')
    before = await pg.evaluate('todayIdx')
    await pg.clock.fast_forward(ff); await pg.wait_for_timeout(1800)
    after = await pg.evaluate('({today:todayIdx,mark:window.__mark===1,tab,view,dayIdx})')
    print(f"{name:34s} 開啟 today={before} → 跨午夜後 {after} errs={len(pg.errs)}")
    await ctx.close(); return before, after, pg.errs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        exp = {"11/16→17": (jst(11,16,23,59,), -1, 0), "11/17→18": (jst(11,17,23,59), 0, 1), "11/23→24": (jst(11,23,23,59), 6, 7), "11/24→25": (jst(11,24,23,59), 7, -1)}
        for tz in ("Asia/Tokyo", "Asia/Taipei"):
            for k, (t, a, z) in exp.items():
                # 在 23:59:00 開，快轉 70 秒
                bf, af, errs = await cross(b, f"{k} 手機{tz[-5:]}", t, tz, ff="01:10")
                rec("跨午夜", f"{k} 手機時區 {tz[-5:]}：App 開著跨午夜後自動換到新的一天（today={z}）", bf == a and af["today"] == z and not af["mark"] and not errs, {"before": bf, "after": af, "errs": errs[:1]})
        # 記一筆填寫中跨午夜
        for label, kind in [("記一筆（金額打好，焦點在金額欄）", "amt_focus"), ("記一筆（金額打好，已點類別按鈕，焦點在按鈕）", "amt_btn"), ("記一筆（面板開著還沒打字）", "empty"), ("心情（選了分數、打了字，焦點在文字框）", "mood_focus"), ("心情（選了分數、打了字，焦點在按鈕外）", "mood_blur"), ("清單新增一項（打字中，已移開焦點）", "item_blur")]:
            ctx = await S.mkctx(b)
            pg = await S.opn(ctx, jst(11, 19, 23, 59), init=seed(META), wait=1000)
            await pg.evaluate('window.__mark=1')
            if kind.startswith("amt") or kind == "empty":
                await tab(pg, "acct"); await S.expopen(pg)
                if kind != "empty":
                    await pg.fill('#f-amt', '1500'); await pg.fill('#f-note', '半夜的拉麵')
                    if kind == "amt_btn": await pg.click('.exp-sheet [data-pick] .pick >> nth=1') if await pg.query_selector('.exp-sheet [data-pick] .pick') else await pg.click('.exp-sheet .pick >> nth=1')
            elif kind.startswith("mood"):
                await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(500)
                await pg.click('#mood .fbtn[data-score="4"]'); await pg.fill('#mood-note', '半夜寫的心情')
                if kind == "mood_blur": await pg.evaluate('document.activeElement.blur()')
            else:
                await tab(pg, "list"); await pg.click('[data-list-tab="buy"]'); await pg.click('[data-item-new="buy"]'); await pg.fill('.chk-form input[name=title]', '半夜的清單項目'); await pg.evaluate('document.activeElement.blur()')
            fa = await pg.evaluate('document.activeElement.tagName')
            await pg.clock.fast_forward("01:40"); await pg.wait_for_timeout(2000)
            kept = await pg.evaluate('window.__mark===1')
            print(f"{label}：焦點={fa} 跨午夜後頁面{'沒有' if kept else '已'}重新載入")
            rec("跨午夜", f"{label}：跨午夜不丟輸入", kept, {"焦點": fa, "reloaded": not kept})
            await ctx.close()
        await b.close()
    summary()
asyncio.run(main())
