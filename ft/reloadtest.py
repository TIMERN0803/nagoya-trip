# reloadtest：自動重新整理不吃掉沒存的內容（QA R2 修正階段 F4：UX-03、CX-03、CX-04）
# 三個入口都走 safeReload()：跨日（dayCheck）、起飛倒數歸零、網路恢復後程式庫重新載入（reloadSoon）。
# 有沒存的內容就先等；存檔、取消、關面板後會馬上再檢查一次。「有沒存的內容」看內容，不看模式旗標。
# 一律假資料庫；測試代碼 qa-r2-test。
import sys
from phonelib import *

async def cross_midnight(pg, minutes=5):
    """App 放背景、過午夜後切回來：只觸發 visibilitychange，不等 30 秒計時器"""
    await pg.clock.set_system_time(await pg.evaluate('Date.now()') + minutes * 60 * 1000)
    await pg.evaluate('document.dispatchEvent(new Event("visibilitychange"))'); await pg.wait_for_timeout(1500)

async def day_exp(b):
    for label, focus in [("焦點在按鈕", "btn"), ("焦點在金額欄", "amt")]:
        ctx = await newctx(b)
        pg = await S.opn(ctx, jst(11, 19, 23, 58), init=seed(META), wait=1000)
        await tab(pg, "acct"); await S.expopen(pg)
        await pg.fill('#f-amt', '1500'); await pg.fill('#f-note', '半夜的拉麵')
        if focus == "btn": await pg.evaluate('document.activeElement.blur()')
        else: await pg.focus('#f-amt')
        await pg.evaluate('window.__mark=1')
        await cross_midnight(pg)
        st = await pg.evaluate('({reloaded:!window.__mark,amt:document.getElementById("f-amt")?.value||"",note:document.getElementById("f-note")?.value||""})')
        rec("F4 跨日", f"記一筆有草稿（{label}）：過 0 點不重新整理，內容還在", not st["reloaded"] and st["amt"] == "1500" and st["note"] == "半夜的拉麵", st)
        if focus == "btn":
            # 存檔後（草稿清掉）會馬上補做重新整理
            await pg.click('#f-save'); await pg.wait_for_timeout(2500)
            ok = not await pg.evaluate('window.__mark')
            cl = [v for k, v in (await cloud(pg)).items() if "/expenses/" in k and v.get("note") == "半夜的拉麵"]
            rec("F4 跨日", "存檔後補做重新整理，帳已記下且日期是開始填的那天（11/19）", ok and len(cl) == 1 and cl[0].get("day") == "11/19", {"reloaded": ok, "cloud": cl})
        await ctx.close()
    # 放棄草稿也會補做
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 23, 58), init=seed(META), wait=1000)
    await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '900'); await pg.evaluate('document.activeElement.blur()'); await pg.evaluate('window.__mark=1')
    await cross_midnight(pg)
    held = await pg.evaluate('!!window.__mark')
    await pg.click('.exp-sheet:not(.leaving) [data-exp-x]'); await pg.wait_for_timeout(500)
    if await pg.is_visible('.exp-sheet:not(.leaving) .exp-confirm'): await pg.click('[data-exp-discard]')
    await pg.wait_for_timeout(2500)
    rec("F4 跨日", "放棄草稿、關掉面板後補做重新整理", held and not await pg.evaluate('window.__mark'), {"held": held})
    await ctx.close()

async def day_control(b):
    # 沒有草稿：跨日照常重新整理
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 23, 58), init=seed(META), wait=1000)
    await tab(pg, "acct"); await pg.evaluate('window.__mark=1'); await cross_midnight(pg)
    rec("F4 對照", "沒有草稿：過 0 點照常重新整理", not await pg.evaluate('window.__mark'), None)
    await ctx.close()
    # 只點了表情、沒寫字：不算草稿，不擋換日
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 23, 58), init=seed(META), wait=1000)
    await pg.evaluate('tab="plan";view="day";dayIdx=2;render(true)'); await pg.wait_for_timeout(400)
    await pg.evaluate('moodDraft={d:"11/19",score:3,note:""}'); await pg.evaluate('window.__mark=1'); await cross_midnight(pg)
    rec("F4 對照", "心情只點了表情、沒寫備註：不擋換日", not await pg.evaluate('window.__mark'), None)
    await ctx.close()
    # 打開編輯但什麼都沒改：不擋換日
    ctx = await newctx(b)
    db = {**META, f"{B}/items/t1": {"group": "prep", "title": "換日圓", "note": "原備註", "due": "", "order": 1}}
    pg = await S.opn(ctx, jst(11, 19, 23, 58), init=seed(db), wait=1200)
    await tab(pg, "list"); await pg.click('[data-item-edit="t1"]'); await pg.wait_for_timeout(400); await pg.evaluate('document.activeElement.blur()')
    await pg.evaluate('window.__mark=1'); await cross_midnight(pg)
    rec("F4 對照", "清單打開編輯但沒改任何東西：不擋換日（看內容不看模式）", not await pg.evaluate('window.__mark'), None)
    await ctx.close()
    # 清單編輯改了標題：擋住
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 23, 58), init=seed(db), wait=1200)
    await tab(pg, "list"); await pg.click('[data-item-edit="t1"]'); await pg.wait_for_timeout(400); await pg.fill('.chk-form input[name=title]', '改一半'); await pg.evaluate('document.activeElement.blur()')
    await pg.evaluate('window.__mark=1'); await cross_midnight(pg)
    rec("F4 跨日", "清單編輯改到一半：不重新整理", bool(await pg.evaluate('window.__mark')), None)
    await ctx.close()

async def countdown(b):
    for label, to, expect_hold in [("跨過 0 點、到起飛時間（11/17 日本 08:06）", jst(11, 17, 8, 6), True)]:
        ctx = await newctx(b)
        pg = await S.opn(ctx, jst(11, 16, 23, 58), init=seed(META), wait=1200)
        await pg.evaluate('tab="plan";view="home";render(true)'); await pg.wait_for_timeout(300)
        has_cd = await pg.evaluate('!!document.getElementById("cd-s")')
        await pg.click('[data-sos]'); await pg.wait_for_timeout(700)
        await pg.click('[data-sos-tab="emg"]'); await pg.wait_for_timeout(300); await pg.click('[data-sos-edit]'); await pg.wait_for_timeout(300)
        await pg.fill('[data-sos-f="insTel"]', '0800-123-456')
        await pg.evaluate('document.activeElement.blur()')   # 焦點離開輸入框：只靠內容判斷
        await pg.evaluate('window.__mark=1')
        await pg.clock.set_system_time(to); await pg.wait_for_timeout(3000)
        st = await pg.evaluate('({reloaded:!window.__mark,ins:document.querySelector("[data-sos-f=insTel]")?.value||""})')
        rec("F4 倒數歸零", f"{label}：首頁有倒數 {has_cd}，旅平險草稿保留不重載", not st["reloaded"] and st["ins"] == "0800-123-456", st)
        await pg.click('[data-sos-cancel]'); await pg.wait_for_timeout(2500)
        rec("F4 倒數歸零", "取消編輯後補做重新整理", not await pg.evaluate('window.__mark'), None)
        await ctx.close()

async def lib_back(b):
    for label, prep in [("第一次設定錢包（walletEdit 是 null）", None), ("已設定錢包、按「補錢」", "add")]:
        lib = {"mode": "abort"}
        ctx = await S.mkctx(b, fs=FSO, lib=lib)
        db = {**META} if not prep else {**META, f"{B}/wallet/zhang": {"cashIn": 20000, "ts": 1}}
        pg = await S.opn(ctx, jst(11, 19, 20), init=seed(db) + ('localStorage.setItem("ngy:wallet",%s);' % json.dumps(json.dumps({"zhang": {"cashIn": 20000, "ts": 1}})) if prep else ''), wait=1500)
        await tab(pg, "acct"); await pg.click('[data-wallet-open]'); await pg.wait_for_timeout(700)
        if prep: await pg.click('[data-wallet-edit][data-mode="add"]'); await pg.wait_for_timeout(300)
        await pg.fill('.w-form input[name=amt]', '30000'); await pg.evaluate('document.activeElement.blur()'); await pg.evaluate('window.__mark=1')
        lib["mode"] = "mock"; await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(3000)
        st = await pg.evaluate('({reloaded:!window.__mark,amt:document.querySelector(".w-form input[name=amt]")?.value??null})')
        rec("F4 恢復連線", f"{label}：程式庫恢復時不重新整理、金額還在", not st["reloaded"] and st["amt"] == "30000", st)
        await pg.click('.ws .sm-x, .sheet-modal .sm-x'); await pg.wait_for_timeout(2500)
        rec("F4 恢復連線", f"{label}：關掉錢包後補做重新整理", not await pg.evaluate('window.__mark'), None)
        await ctx.close()
    # 沒有草稿：程式庫恢復後照常重新整理
    lib = {"mode": "abort"}
    ctx = await S.mkctx(b, fs=FSO, lib=lib)
    pg = await S.opn(ctx, jst(11, 19, 20), init=seed(META), wait=1500)
    await pg.evaluate('window.__mark=1'); lib["mode"] = "mock"; await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(3500)
    rec("F4 對照", "沒有草稿：程式庫恢復後照常重新整理一次", not await pg.evaluate('window.__mark'), None)
    await ctx.close()

ALL = [day_exp, day_control, countdown, lib_back]
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
