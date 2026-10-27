# 換頁與彈窗轉場：往深一層整頁從右推入（舊頁往左退）、返回舊頁往右滑走、底部分頁切換不播、點記帳滑到輸入金額、換天左右翻頁、全部不淡入淡出；同步重畫不播；彈窗關閉有退場動畫且一定會移除；
# 退場中的面板點不到、不擋下一個面板；減少動態時直接移除；轉場只動 opacity／transform；滑入時沒有橫向捲軸
# 一律用假資料庫（synctest.mkctx 的攔截）
import asyncio
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
rec = ft.rec
B, META, seed, opn, tab = S.B, S.META, S.seed, S.opn, S.tab
cls = 'document.querySelector("#app .view").className'
props = '''(()=>{const a=document.querySelector("#app .view").getAnimations()[0];if(!a)return [];return [...new Set(a.effect.getKeyframes().flatMap(k=>Object.keys(k).filter(x=>!["offset","easing","composite","computedOffset"].includes(x))))]})()'''

async def pages(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('.g-home .grid .tile[data-day="2"]'); c = await pg.evaluate(cls)
    rec("換頁", "首頁點某一天：從右邊滑進（go-fwd）", "go-fwd" in c, c)
    rec("換頁", "轉場只動 transform（不淡入淡出）", await pg.evaluate(props) == ["transform"], await pg.evaluate(props))
    sw = await pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
    rec("換頁", "滑入過程中沒有橫向捲軸", sw)
    o = await pg.evaluate('(()=>{const L=document.querySelector(".vt-old");return L?{n:document.querySelectorAll(".vt-old").length,hid:L.getAttribute("aria-hidden"),inert:L.querySelector(".view").inert,pe:getComputedStyle(L).pointerEvents,anim:getComputedStyle(L.querySelector(".view")).animationName,inApp:!!document.querySelector("#app .vt-old")}:null})()')
    rec("換頁", "推入時舊頁暫留在下層往左退（不能點、對輔助技術隱藏、不在 #app 裡）", o and o["n"] == 1 and o["hid"] == "true" and o["inert"] and o["pe"] == "none" and o["anim"] == "vpushOut" and not o["inApp"], o)
    rec("換頁", "推入時新頁不透明、蓋住舊頁", await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).backgroundColor!=="rgba(0, 0, 0, 0)"'))
    await pg.wait_for_timeout(500)
    rec("換頁", "轉場結束舊頁移除、新頁恢復一般版面", await pg.evaluate('!document.querySelector(".vt-old")&&!document.querySelector(".view.vt-in")&&!document.querySelector(".shell.vt")'))
    await pg.click('[data-home]'); c = await pg.evaluate(cls)
    rec("換頁", "當天行程按返回：從左邊滑進（go-back）", "go-back" in c, c)
    rec("換頁", "返回時舊頁在上層往右滑走", await pg.evaluate('getComputedStyle(document.querySelector(".vt-old.go-back>.view")).animationName') == "vbackOut")
    await pg.wait_for_timeout(500)
    await pg.click('nav.tabs button[data-tab="wx"]'); c = await pg.evaluate(cls)
    rec("換頁", "切底部分頁：不播動畫、不留舊頁", await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).animationName') == "none" and not await pg.evaluate('!!document.querySelector(".vt-old")'), c)
    await pg.wait_for_timeout(400)
    await pg.click('nav.tabs button[data-tab="list"]'); await pg.wait_for_timeout(300)
    await pg.evaluate('listSub="pack";render()'); c = await pg.evaluate(cls)
    rec("換頁", "清單進行李頁：從右邊滑進", "go-fwd" in c, c)
    await pg.wait_for_timeout(500)
    await pg.evaluate('render(true)'); c = await pg.evaluate(cls)
    rec("換頁", "同步資料進來重畫（keep）：不播轉場", "go-" not in c and await pg.evaluate('document.querySelector("#app .view").style.animationName==="none"||document.querySelector("#app .view").style.animation.includes("none")'), c)
    await pg.evaluate('render()'); c = await pg.evaluate(cls)
    rec("換頁", "同一頁重畫：不播動畫", "go-" not in c and await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).animationName') == "none", c)
    # 從當天行程按底部「行程」回首頁：是切分頁，不播
    await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(500)
    await pg.click('nav.tabs button[data-tab="plan"]')
    rec("換頁", "當天行程按底部「行程」回首頁：直接換、不滑動", not await pg.evaluate('!!document.querySelector(".vt-old")') and await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).animationName') == "none")
    # 點「行程」後再點一天：照樣推入（切分頁的旗標不會殘留）
    await pg.click('nav.tabs button[data-tab="plan"]'); await pg.wait_for_timeout(200)
    await pg.click('.g-home .grid .tile[data-day="3"]')
    rec("換頁", "同一分頁再點一下後點某天：照樣推入", "go-fwd" in await pg.evaluate(cls))
    await pg.wait_for_timeout(500)
    # 連續快速換頁：最多只暫留一頁，結束後全部清掉
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(500)
    for i in range(4):
        await pg.evaluate(f'view="day";dayIdx={i};render();view="home";render()')
    n = await pg.evaluate('document.querySelectorAll(".vt-old").length')
    await pg.wait_for_timeout(600)
    rec("換頁", "連續快速換頁：畫面上最多兩頁、結束後清乾淨", n <= 1 and await pg.evaluate('!document.querySelector(".vt-old")&&document.querySelectorAll("#app .view").length===1'), n)
    # 推入中同步資料進來重畫：新頁仍不透明，舊頁照樣收掉
    await pg.evaluate('view="day";dayIdx=1;render();render(true)')
    rec("換頁", "推入中同步重畫：新頁仍蓋住舊頁", await pg.evaluate('!!document.querySelector("#app .view.vt-in")'))
    await pg.wait_for_timeout(600)
    rec("換頁", "之後舊頁和暫時樣式都移除", await pg.evaluate('!document.querySelector(".vt-old")&&!document.querySelector(".view.vt-in")'))
    # 轉場結束後 .view 沒有殘留位移（sticky、固定元素位置正常）
    await pg.wait_for_timeout(100)
    rec("換頁", "轉場結束後沒有殘留 transform", await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).transform') == "none")
    rec("換頁", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def sheets(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    for nm, op, x, sel in [("求助", 'openSos()', '.sheet-modal .sm-x', '.sheet-modal'), ("錢包", 'openWallet()', '.sheet-modal .sm-x', '.sheet-modal'),
                           ("地圖", 'openViewer("ghibli-map.jpg","x")', '.viewer .vclose', '.viewer'), ("給司機看", 'sosShow("hotel")', '.sos-show .sm-x', '.sos-show')]:
        await pg.evaluate(op); await pg.wait_for_timeout(300)
        await pg.click(x)
        st = await pg.evaluate(f'(()=>{{const v=document.querySelector("{sel}");return v?{{leaving:v.classList.contains("leaving"),role:v.getAttribute("role"),pe:getComputedStyle(v).pointerEvents,anim:getComputedStyle(v).animationName}}:null}})()')
        rec("彈窗關閉", f"{nm}：按關閉後往下滑走（背景遮罩漸淡、內容不淡出）", st and st["leaving"] and st["anim"] in ("dimout", "sheetdown"), st)
        rec("彈窗關閉", f"{nm}：退場中不再是對話框、點不到", st and st["role"] is None and st["pe"] == "none", st)
        await pg.clock.run_for(300); await pg.wait_for_timeout(100)
        rec("彈窗關閉", f"{nm}：退場後一定移除", await pg.evaluate(f'document.querySelectorAll("{sel}").length') == 0)
    # 底部面板：卡片整片從下方滑上來
    await pg.evaluate('openSos()')
    rec("彈窗打開", "底部面板從下方滑上來、背景遮罩漸暗", await pg.evaluate('getComputedStyle(document.querySelector(".sheet-modal .sm-card")).animationName') == "sheetin" and await pg.evaluate('getComputedStyle(document.querySelector(".sheet-modal")).animationName') == "dimin")
    await pg.keyboard.press("Escape"); await pg.clock.run_for(300); await pg.wait_for_timeout(100)
    await pg.evaluate('openViewer("ghibli-map.jpg","x")')
    rec("彈窗打開", "全螢幕的也從下方滑上來（不淡入）", await pg.evaluate('getComputedStyle(document.querySelector(".viewer")).animationName') == "sheetin")
    await pg.keyboard.press("Escape"); await pg.clock.run_for(300); await pg.wait_for_timeout(100)
    # 底部面板：卡片往下滑
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(300); await pg.click('.sheet-modal .sm-x')
    rec("彈窗關閉", "底部面板的卡片往下滑", await pg.evaluate('getComputedStyle(document.querySelector(".sheet-modal.leaving .sm-card")).animationName') == "sheetdown")
    # 退場中立刻再開：新的面板正常可用，舊的不會被點到
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(50)
    n = await pg.evaluate('document.querySelectorAll(".sheet-modal:not(.leaving)").length')
    await pg.evaluate('document.querySelector(".sheet-modal.leaving .sm-x").click()')
    rec("彈窗關閉", "退場中馬上再打開：新面板正常、點退場中的舊面板沒反應", n == 1 and await pg.evaluate('modals.length') == 1 and await pg.evaluate('!!document.querySelector(".sheet-modal:not(.leaving)")'))
    await pg.keyboard.press("Escape"); await pg.clock.run_for(300); await pg.wait_for_timeout(100)
    rec("彈窗關閉", "Esc 關閉後全部移除、捲動恢復", await pg.evaluate('document.querySelectorAll(".sheet-modal").length===0&&document.body.style.overflow===""'))
    # 焦點回到打開它的按鈕（退場不影響）
    await pg.click('.hud-sos'); await pg.wait_for_timeout(300); await pg.keyboard.press("Escape"); await pg.wait_for_timeout(50)
    rec("彈窗關閉", "關閉時焦點馬上回到原本的按鈕", await pg.evaluate('!!document.activeElement?.closest(".hud-sos")'))
    rec("彈窗關閉", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def acct(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('nav.tabs button[data-tab="acct"]'); await pg.wait_for_timeout(900)
    top = await pg.evaluate('document.getElementById("acct-form").getBoundingClientRect().top')
    rec("記帳", "點記帳分頁：往上滑到輸入金額（表單在畫面頂端）", 0 <= top <= 30 and await pg.evaluate('scrollY') > 0, [top, await pg.evaluate('scrollY')])
    rec("記帳", "不自動跳出鍵盤（不搶焦點）", await pg.evaluate('document.activeElement?.id') != "f-amt")
    await pg.evaluate('scrollTo(0,0)'); await pg.wait_for_timeout(200)
    await pg.click('nav.tabs button[data-tab="acct"]'); await pg.wait_for_timeout(900)
    top = await pg.evaluate('document.getElementById("acct-form").getBoundingClientRect().top')
    rec("記帳", "已經在記帳時再點一次：也回到輸入金額", 0 <= top <= 30, top)
    rec("記帳", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def days(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(500)
    await pg.click('.day-btn[data-day="3"]')
    g = await pg.evaluate('(()=>{const g=document.querySelector(".day-ghost");if(!g)return null;const ka=document.getElementById("dayBody").getAnimations().flatMap(a=>a.effect.getKeyframes().flatMap(k=>Object.keys(k))).filter(x=>!["offset","easing","composite","computedOffset"].includes(x));return {inert:g.inert,hid:g.getAttribute("aria-hidden"),ids:g.querySelectorAll("[id]").length+(g.id?1:0),props:[...new Set(ka)],one:document.querySelectorAll("#dayBody").length}})()')
    rec("換天", "舊內容往旁邊滑走、新內容同時滑進（只動 transform、不淡入淡出）", g and g["props"] == ["transform"], g)
    rec("換天", "滑走的舊內容不能點、沒有重複 id", g and g["inert"] and g["hid"] == "true" and g["ids"] == 0 and g["one"] == 1, g)
    for d in (4, 5, 6): await pg.click(f'.day-btn[data-day="{d}"]')
    n = await pg.evaluate('document.querySelectorAll(".day-ghost").length')
    await pg.wait_for_timeout(600)
    rec("換天", "連點換天：最多一個舊內容、結束後清乾淨", n <= 1 and await pg.evaluate('document.querySelectorAll(".day-ghost").length') == 0, n)
    rec("換天", "最後顯示的是點的那一天", "11/23" in await pg.evaluate('document.getElementById("dayBody").innerText') or await pg.evaluate('dayIdx') == 6, await pg.evaluate('dayIdx'))
    rec("換天", "沒有橫向捲軸", await pg.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    rec("換天", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def reduced(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.emulate_media(reduced_motion="reduce")
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('.g-home .grid .tile[data-day="2"]')
    rec("減少動態", "換頁不暫留舊頁", not await pg.evaluate('!!document.querySelector(".vt-old")'))
    rec("減少動態", "換頁不播動畫", await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).animationName') == "none")
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(100); await pg.click('.sheet-modal .sm-x')
    rec("減少動態", "彈窗關閉直接移除", await pg.evaluate('document.querySelectorAll(".sheet-modal").length') == 0)
    await ctx.close()

async def narrow(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.set_viewport_size({"width": 320, "height": 640})
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('.g-home .grid .tile[data-day="1"]')
    w = []
    for i in range(6):
        w.append(await pg.evaluate('document.documentElement.scrollWidth-innerWidth')); await pg.wait_for_timeout(40)
    rec("換頁", "320 寬：滑入的每一刻都沒有橫向捲軸", max(w) <= 0, w)
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in [pages, sheets, acct, days, reduced, narrow]:
            try: await f(b)
            except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
        await b.close()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
