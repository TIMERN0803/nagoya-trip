# R2 批 5 lead：核對 Codex「修法風險」的兩個前提（不改網站，只量）
# 1. UX-04：回顧非當頁是 opacity:0（不是 hidden），共用 modal 的可聚焦篩選（getClientRects）會把它們算進去
# 2. UX-03：today／todayIdx 是載入時的 const；換日延後期間「今天」標示與記帳預設日期停在舊日
import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b3', 'ux'))
from uxlib import *
FOC = 'a[href],button:not([disabled]),input:not([disabled]),select,textarea,[tabindex]:not([tabindex="-1"])'
async def story(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 25, 10), init=seed(META), wait=1200)
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(500)
    await pg.click('[data-story-open]'); await pg.wait_for_timeout(900)
    st = await pg.evaluate('''(()=>{const s=document.querySelector(".story");const all=[...s.querySelectorAll(%s)].filter(e=>e.getClientRects().length);
      const off=all.filter(e=>{const p=e.closest(".st-page");return p&&!p.classList.contains("on")});
      return {pages:s.querySelectorAll(".st-page").length,focusable:all.length,onHiddenPages:off.length,example:off.slice(0,3).map(e=>e.className||e.tagName),inert:[...s.querySelectorAll(".st-page")].some(p=>p.inert)}})()''' % json.dumps(FOC))
    rec("風險-UX04", "回顧非當頁的按鈕不會被可聚焦篩選收到", st["onHiddenPages"] == 0, st)
    await ctx.close()
async def today(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 18, 23, 58), init=seed(META), wait=1200)
    await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '900'); await pg.focus('#f-amt')
    await pg.evaluate('window.__mark=1')
    await pg.clock.set_system_time(jst(11, 19, 0, 5)); await pg.wait_for_timeout(500); await pg.evaluate('dayCheck()')
    st = await pg.evaluate('({reloaded:!window.__mark,todayIdx,draftDay:draft.day,fday:document.getElementById("f-day")?.value})')
    rec("風險-UX03", "延後換日時（焦點在金額欄）記帳預設日期跟著變 11/19", st["draftDay"] == "11/19" or st["fday"] == "11/19", st)
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in (story, today):
            try: await f(b)
            except Exception as ex: rec(f.__name__, "腳本執行", False, repr(ex)[:300])
        await b.close()
    summary()
asyncio.run(main())
