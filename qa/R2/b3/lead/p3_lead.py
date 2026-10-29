# R2 批 3 lead 重現：用和 qa-ux 不同的觀察點驗 UX-01～04
# UX-01／02：直接看 B 的 outbox（送出前的寫入內容）有沒有 merge 旗標、帶不帶舊值
# UX-03：改走 visibilitychange（App 放背景過午夜再切回來），不靠 setInterval
# UX-04：Shift+Tab 從第一個元素往回、以及關閉後 activeElement
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ux'))  # 也可放回 /home/claude/qa-r2/work/lead 執行
from uxlib import *

OB = 'JSON.parse(localStorage.getItem(window.__ns_key||"ngy:outbox")||"{}")'

async def ux01(b):
    ctx = await newctx(b); T = jst(11, 21, 20)
    db = {**META, f"{B}/expenses/e1": {"amt": 6000, "cat": "shop", "who": "star", "split": "both", "pay": "card", "day": "11/21", "note": "藥妝", "ts": 1, "tf": True}}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "acct")
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await A.click('.ex[data-edit="e1"]'); await A.wait_for_timeout(700); await A.fill('#f-amt', '7500'); await A.click('#f-save'); await A.wait_for_timeout(800)
    aob_before = (await exps(A))["e1"]["amt"]
    await Bp.click('[data-carry="e1"]'); await Bp.wait_for_timeout(300)
    ob = await Bp.evaluate('outbox["expenses/e1"]||null')
    rec("UX-01", "B 按隨身後 outbox 是 merge（m 旗標）且不帶 amt", bool(ob) and ob.get("m") == 1 and "amt" not in (ob.get("d") or {}), ob)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    e = (await exps(A))["e1"]
    rec("UX-01", f"A 改的 7500 在 B 上線後保留（A 存後雲端={aob_before}）", e.get("amt") == 7500, e)
    await ctx.close()

async def ux02(b):
    ctx = await newctx(b); T = jst(11, 18, 10)
    db = {**META, f"{B}/items/t1": {"group": "prep", "title": "換日圓", "note": "原備註", "due": "", "order": 1}}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "list")
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await A.click('[data-item-edit="t1"]'); await A.wait_for_timeout(300); await A.fill('.chk-form input[name=title]', 'A 改的標題'); await A.click('.chk-form .primary'); await A.wait_for_timeout(700)
    await Bp.click('[data-item-edit="t1"]'); await Bp.wait_for_timeout(300); await Bp.fill('.chk-form input[name=note]', 'B 改的備註'); await Bp.click('.chk-form .primary'); await Bp.wait_for_timeout(400)
    ob = await Bp.evaluate('outbox["items/t1"]||null')
    rec("UX-02", "B 改備註的 outbox 是 merge 且不帶 title", bool(ob) and ob.get("m") == 1 and "title" not in (ob.get("d") or {}), ob)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    it = (await items_cloud(A))["t1"]
    rec("UX-02", "上線後 A 的標題與 B 的備註都在", it.get("title") == "A 改的標題" and it.get("note") == "B 改的備註", it)
    await ctx.close()

async def ux03(b):
    for label, focus in [("焦點在按鈕", "btn"), ("焦點在金額欄（對照）", "amt")]:
        ctx = await newctx(b)
        pg = await S.opn(ctx, jst(11, 19, 23, 58), init=seed(META), wait=1000)
        await tab(pg, "acct"); await S.expopen(pg)
        await pg.fill('#f-amt', '1500'); await pg.fill('#f-note', '半夜的拉麵')
        if focus == "btn": await pg.evaluate('document.activeElement.blur()')
        else: await pg.focus('#f-amt')
        await pg.evaluate('window.__mark=1')
        # 模擬 App 放到背景、過午夜後切回來：只觸發 visibilitychange，不等 30 秒計時器
        await pg.clock.set_system_time(await pg.evaluate('Date.now()') + 5 * 60 * 1000)
        await pg.evaluate('document.dispatchEvent(new Event("visibilitychange"))'); await pg.wait_for_timeout(2000)
        st = await pg.evaluate('({reloaded:!window.__mark,busy:typeof busyEditing==="function"?busyEditing():null,amt:document.getElementById("f-amt")?.value||""})')
        rec("UX-03", f"{label}：切回 App 時有未存草稿不重新載入", not st["reloaded"], st)
        await ctx.close()

DESC = 'document.activeElement===document.body?"body":(document.activeElement.closest(".story,.coach")?"in":"out:"+document.activeElement.className)'
async def ux04(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 25, 10), init=seed(META), wait=1200)
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(500)
    await pg.focus('[data-story-open]'); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(900)
    seq = []
    for i in range(4): await pg.keyboard.press("Shift+Tab"); await pg.wait_for_timeout(60); seq.append(await pg.evaluate(DESC))
    rec("UX-04", "回顧：Shift+Tab 4 次焦點不離開回顧層", all(s == "in" for s in seq), seq)
    await pg.evaluate('document.querySelector(".story .st-x")?.click()'); await pg.wait_for_timeout(700)
    rec("UX-04", "回顧：按 × 關閉後焦點回到入口", await pg.evaluate('!!document.activeElement&&document.activeElement.matches("[data-story-open]")'), await pg.evaluate(DESC))
    await ctx.close()
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 18, 10), init=seed(META) + 'localStorage.removeItem("ngy:tour");', wait=2200)
    seq = []
    for i in range(4): await pg.keyboard.press("Shift+Tab"); await pg.wait_for_timeout(60); seq.append(await pg.evaluate(DESC))
    rec("UX-04", "導覽：Shift+Tab 4 次焦點不離開導覽層", all(s == "in" for s in seq), seq)
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in (ux01, ux02, ux03, ux04):
            try: await f(b)
            except Exception as ex: rec(f.__name__, "腳本執行", False, repr(ex)[:300])
        await b.close()
    summary()
asyncio.run(main())
