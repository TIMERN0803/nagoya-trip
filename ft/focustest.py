# focustest：旅程回顧與新手導覽走共用的 modal()（QA R2 修正階段 F6：UX-04、CODE-07）
# Tab／Shift+Tab 不會跑到背後、Esc 可以關、關閉後焦點回到入口；回顧非當頁的控制 inert、不會被 Tab 到；
# 從設定開導覽時設定層正常退出；自動第一次開的導覽關閉後焦點在底部「行程」分頁。一律假資料庫。
import sys
from phonelib import *

IN = 'document.activeElement&&document.activeElement.closest(".story,.coach")?"in":"out:"+(document.activeElement&&(document.activeElement.className||document.activeElement.tagName))'
def ok_in(seq): return all(s == "in" for s in seq)

async def story(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 25, 10), init=seed(META), wait=1200)
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(500)
    await pg.focus('[data-story-open]'); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(900)
    n = await pg.evaluate('document.querySelectorAll(".story .st-page").length')
    seq = []
    for _ in range(5): await pg.keyboard.press("Shift+Tab"); await pg.wait_for_timeout(60); seq.append(await pg.evaluate(IN))
    rec("F6 回顧", "Shift+Tab 5 次焦點都在回顧層", ok_in(seq), seq)
    seq = []
    for _ in range(6): await pg.keyboard.press("Tab"); await pg.wait_for_timeout(60); seq.append(await pg.evaluate(IN))
    rec("F6 回顧", "Tab 6 次焦點都在回顧層", ok_in(seq), seq)
    inert = await pg.evaluate('[...document.querySelectorAll(".story .st-page")].map((s,i)=>s.inert)')
    rec("F6 回顧", f"只有當頁（第 1 頁）不是 inert（共 {n} 頁）", inert[0] is False and all(inert[1:]), inert)
    # 翻到最後一頁，Tab 一圈：焦點不會落在看不到的頁面上
    for _ in range(n): await pg.keyboard.press("ArrowRight"); await pg.wait_for_timeout(80)
    seq = []
    for _ in range(8):
        await pg.keyboard.press("Tab"); await pg.wait_for_timeout(60)
        seq.append(await pg.evaluate('(()=>{const a=document.activeElement;return a&&a.closest(".story")?(a.closest("[inert]")?"INERT":(a.getClientRects().length?"ok":"HIDDEN")):"OUT"})()'))
    rec("F6 回顧", "最後一頁 Tab 8 次：都落在看得到的控制上（沒有 inert、隱藏、離開回顧層）", all(x == "ok" for x in seq), seq)
    # 「再看一次」回第一頁：焦點不掉到 body
    await pg.evaluate('document.querySelector("[data-story-again]")?.focus()'); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(400)
    st = await pg.evaluate('({cur:[...document.querySelectorAll(".story .st-page")].findIndex(s=>!s.inert),focus:document.activeElement&&document.activeElement.closest(".story")?(document.activeElement.className||document.activeElement.tagName):"OUT"})')
    rec("F6 回顧", "按「再看一次」回第 1 頁，焦點移到這頁看得到的控制", st["cur"] == 0 and st["focus"] != "OUT" and st["focus"] != "BODY", st)
    await pg.screenshot(path=SHOTS + 'f6_story_focus.png')
    # Esc 關閉、焦點回入口
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(700)
    st = await pg.evaluate('({gone:!document.querySelector(".story"),stack:modals.length,onEntry:!!document.activeElement&&document.activeElement.matches("[data-story-open]")})')
    rec("F6 回顧", "Esc 關閉，焦點回到入口，modal 堆疊清空", st["gone"] and st["stack"] == 0 and st["onEntry"], st)
    # × 關閉
    await pg.focus('[data-story-open]'); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(800)
    await pg.evaluate('document.querySelector(".story .st-x").click()'); await pg.wait_for_timeout(700)
    rec("F6 回顧", "按 × 關閉後焦點回到入口", await pg.evaluate('!!document.activeElement&&document.activeElement.matches("[data-story-open]")'), None)
    # 左右鍵與點擊仍可換頁
    await pg.focus('[data-story-open]'); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(800)
    await pg.keyboard.press("ArrowRight"); await pg.wait_for_timeout(200); c1 = await pg.evaluate('[...document.querySelectorAll(".story .st-page")].findIndex(s=>!s.inert)')
    await pg.click('.st-tap.next'); await pg.wait_for_timeout(200); c2 = await pg.evaluate('[...document.querySelectorAll(".story .st-page")].findIndex(s=>!s.inert)')
    await pg.keyboard.press("ArrowLeft"); await pg.wait_for_timeout(200); c3 = await pg.evaluate('[...document.querySelectorAll(".story .st-page")].findIndex(s=>!s.inert)')
    rec("F6 回顧", "方向鍵與點右邊仍可換頁", (c1, c2, c3) == (1, 2, 1), (c1, c2, c3))
    await ctx.close()

async def tour(b):
    # 自動第一次開（沒有入口按鈕）
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 18, 10), init=seed(META) + 'localStorage.removeItem("ngy:tour");', wait=2200)
    seq = []
    for _ in range(5): await pg.keyboard.press("Shift+Tab"); await pg.wait_for_timeout(60); seq.append(await pg.evaluate(IN))
    rec("F6 導覽", "Shift+Tab 5 次焦點都在導覽層", ok_in(seq), seq)
    seq = []
    for _ in range(5): await pg.keyboard.press("Tab"); await pg.wait_for_timeout(60); seq.append(await pg.evaluate(IN))
    rec("F6 導覽", "Tab 5 次焦點都在導覽層", ok_in(seq), seq)
    hole0 = await pg.evaluate('(()=>{const h=document.querySelector(".coach-hole").getBoundingClientRect();return[Math.round(h.left),Math.round(h.top),Math.round(h.width),Math.round(h.height)]})()')
    rec("F6 導覽", "鏤空框有定位（寬高 > 0）", hole0[2] > 0 and hole0[3] > 0, hole0)
    await pg.screenshot(path=SHOTS + 'f6_tour_step1.png')
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(700)
    st = await pg.evaluate('({gone:!document.querySelector(".coach"),stack:modals.length,flag:localStorage.getItem("ngy:tour"),focus:document.activeElement&&document.activeElement.dataset.tab||document.activeElement.tagName})')
    rec("F6 導覽", "Esc 關閉、記為看過、焦點在底部「行程」分頁", st["gone"] and st["stack"] == 0 and st["flag"] == "1" and st["focus"] == "plan", st)
    await ctx.close()
    # 從設定開：設定層正常退出，堆疊不留殭屍
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 10, 10), init=seed(META), wait=1500)
    await pg.evaluate('tab="plan";view="home";render(true)'); await pg.wait_for_timeout(400)
    await pg.click('[data-setup-open]'); await pg.wait_for_timeout(800)
    await pg.click('[data-tour-open]'); await pg.wait_for_timeout(900)
    st = await pg.evaluate('({tour:!!document.querySelector(".coach"),setup:!!document.querySelector(".su-sheet")&&!document.querySelector(".su-sheet").closest(".leaving"),stack:modals.filter(m=>m.v&&m.v.isConnected).length})')
    rec("F6 導覽", "從設定開導覽：設定層關閉、只剩導覽一層", st["tour"] and not st["setup"] and st["stack"] == 1, st)
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(800)
    st = await pg.evaluate('({gone:!document.querySelector(".coach"),stack:modals.length,onEntry:!!document.activeElement&&document.activeElement.matches("[data-setup-open],[data-tour-open]")})')
    rec("F6 導覽", "Esc 關導覽：堆疊清空、焦點回到設定入口", st["gone"] and st["stack"] == 0 and st["onEntry"], st)
    # 最後一步「開始設定」：先關導覽、再開設定
    await pg.evaluate('openTour()'); await pg.wait_for_timeout(600)
    for _ in range(12):
        t = (await pg.inner_text('[data-coach-next]')).strip()
        if t == "開始設定": break
        await pg.click('[data-coach-next]'); await pg.wait_for_timeout(500)
    await pg.click('[data-coach-next]'); await pg.wait_for_timeout(900)
    st = await pg.evaluate('({coach:!!document.querySelector(".coach")&&!document.querySelector(".coach").closest(".leaving"),setup:!!document.querySelector(".su-sheet")&&!document.querySelector(".su-sheet").closest(".leaving"),stack:modals.filter(m=>m.v&&m.v.isConnected).length})')
    rec("F6 導覽", "最後一步「開始設定」：導覽關掉、設定打開、堆疊一層", not st["coach"] and st["setup"] and st["stack"] == 1, st)
    rec("F6 導覽", "沒有頁面錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

ALL = [story, tour]
async def main():
    names = sys.argv[1:]
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in ALL:
            if names and f.__name__ not in names: continue
            try: await f(b)
            except Exception as ex: rec(f.__name__, "腳本執行", False, repr(ex)[:300])
        await b.close()
    summary()
asyncio.run(main())
