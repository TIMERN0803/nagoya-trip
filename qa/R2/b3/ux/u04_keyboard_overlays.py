# CODE-07 行為驗證：旅程回顧（11/25 起）與新手導覽用鍵盤：Tab 會不會跑到背後、Esc、關閉後焦點
from uxlib import *
DESC = '''(()=>{const a=document.activeElement;if(!a||a===document.body)return"body";const d=a.closest(".story,.coach,.sheet-modal,.sos-show");
 return (a.tagName+(a.id?"#"+a.id:"")+(a.className&&typeof a.className==="string"?"."+a.className.split(" ")[0]:"")+(a.dataset&&Object.keys(a.dataset).length?"["+Object.keys(a.dataset)[0]+"]":""))+(d?" (在層內)":" (在背後)")})()'''
async def tabs(pg, n=14, label=""):
    seq = []
    for i in range(n):
        await pg.keyboard.press("Tab"); await pg.wait_for_timeout(60); seq.append(await pg.evaluate(DESC))
    return seq
async def story(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 25, 10), init=seed(META), wait=1200)
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(500)
    btn = '[data-story-open]'
    print("回顧入口存在:", await pg.query_selector(btn) is not None)
    await pg.focus(btn); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(900)
    print("開啟後焦點:", await pg.evaluate(DESC))
    seq = await tabs(pg, 14)
    print("Tab x14:", seq)
    leaked = [s for s in seq if "背後" in s or s == "body"]
    rec("CODE-07 回顧", "Tab 14 次焦點都留在回顧層內", not leaked, leaked[:3])
    await pg.screenshot(path=SHOTS + 'u04_story_tab.png')
    # Esc 在焦點跑出去後
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(600)
    still = await pg.query_selector('.story:not(.leaving)') is not None
    print("焦點在背後時按 Esc，回顧還在:", still)
    rec("CODE-07 回顧", "焦點在背後時 Esc 仍能關閉", not still, {"還在": still, "焦點": await pg.evaluate(DESC)})
    if still:
        # 把焦點拉回層內再 Esc
        await pg.evaluate('document.querySelector(".story .st-x").focus()'); await pg.keyboard.press("Escape"); await pg.wait_for_timeout(600)
    print("關閉後焦點:", await pg.evaluate(DESC), "| 期待回到入口:", await pg.evaluate('document.activeElement&&document.activeElement.matches("[data-story-open]")'))
    rec("CODE-07 回顧", "關閉後焦點回到「我們的名古屋回顧」入口", await pg.evaluate('document.activeElement&&document.activeElement.matches("[data-story-open]")'), await pg.evaluate(DESC))
    # 層內 Esc（焦點在層內）
    await pg.focus(btn); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(900)
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(600)
    rec("CODE-07 回顧", "焦點在層內時 Esc 可關", await pg.query_selector('.story:not(.leaving)') is None)
    # 方向鍵換頁
    await pg.focus(btn); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(900)
    await pg.keyboard.press("ArrowRight"); await pg.wait_for_timeout(300)
    print("→ 後頁碼:", await pg.evaluate('document.querySelector(".st-page.on")?.dataset.pg'))
    rec("CODE-07 回顧", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
async def tour(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 18, 10), init=seed(META) + 'localStorage.removeItem("ngy:tour");', wait=2200)
    print("導覽已開:", await pg.query_selector('.coach:not(.leaving)') is not None, "焦點:", await pg.evaluate(DESC))
    seq = await tabs(pg, 8)
    print("Tab x8:", seq)
    leaked = [s for s in seq if "背後" in s or s == "body"]
    rec("CODE-07 導覽", "Tab 8 次焦點都留在導覽層內", not leaked, leaked[:3])
    # 焦點在背後時 Esc
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(700)
    still = await pg.query_selector('.coach:not(.leaving)') is not None
    rec("CODE-07 導覽", "焦點在背後時 Esc 仍能關閉", not still, {"還在": still, "焦點": await pg.evaluate(DESC)})
    if still:
        await pg.evaluate('document.querySelector("[data-coach-next]").focus()'); await pg.keyboard.press("Escape"); await pg.wait_for_timeout(700)
    print("關閉後焦點:", await pg.evaluate(DESC), "| ngy:tour =", await pg.evaluate('localStorage.getItem("ngy:tour")'))
    # 從設定面板的「重看教學」打開 → 關閉後焦點
    rec("CODE-07 導覽", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        await story(b); await tour(b)
        await b.close()
    summary()
asyncio.run(main())
