# 換頁與彈窗轉場：往深一層從右進、返回從左進、同層切換上浮；同步重畫不播；彈窗關閉有退場動畫且一定會移除；
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
    rec("換頁", "轉場只動 opacity 和 transform", set(await pg.evaluate(props)) <= {"opacity", "transform"} and await pg.evaluate(props), await pg.evaluate(props))
    sw = await pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
    rec("換頁", "滑入過程中沒有橫向捲軸", sw)
    await pg.wait_for_timeout(300)
    await pg.click('[data-home]'); c = await pg.evaluate(cls)
    rec("換頁", "當天行程按返回：從左邊滑進（go-back）", "go-back" in c, c)
    await pg.wait_for_timeout(300)
    await pg.click('nav.tabs button[data-tab="wx"]'); c = await pg.evaluate(cls)
    rec("換頁", "切底部分頁：上浮淡入（go-tab）", "go-tab" in c, c)
    await pg.wait_for_timeout(300)
    await pg.click('nav.tabs button[data-tab="list"]'); await pg.wait_for_timeout(300)
    await pg.evaluate('listSub="pack";render()'); c = await pg.evaluate(cls)
    rec("換頁", "清單進行李頁：從右邊滑進", "go-fwd" in c, c)
    await pg.wait_for_timeout(300)
    await pg.evaluate('render(true)'); c = await pg.evaluate(cls)
    rec("換頁", "同步資料進來重畫（keep）：不播轉場", "go-" not in c and await pg.evaluate('document.querySelector("#app .view").style.animationName==="none"||document.querySelector("#app .view").style.animation.includes("none")'), c)
    await pg.evaluate('render()'); c = await pg.evaluate(cls)
    rec("換頁", "同一頁重畫：不帶方向（只有原本的淡入）", "go-" not in c, c)
    # 轉場結束後 .view 沒有殘留位移（sticky、固定元素位置正常）
    await pg.wait_for_timeout(400)
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
        rec("彈窗關閉", f"{nm}：按關閉後先播退場（淡出）", st and st["leaving"] and st["anim"] == "fadeout", st)
        rec("彈窗關閉", f"{nm}：退場中不再是對話框、點不到", st and st["role"] is None and st["pe"] == "none", st)
        await pg.clock.run_for(250); await pg.wait_for_timeout(100)
        rec("彈窗關閉", f"{nm}：退場後一定移除", await pg.evaluate(f'document.querySelectorAll("{sel}").length') == 0)
    # 底部面板：卡片往下滑
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(300); await pg.click('.sheet-modal .sm-x')
    rec("彈窗關閉", "底部面板的卡片往下滑", await pg.evaluate('getComputedStyle(document.querySelector(".sheet-modal.leaving .sm-card")).animationName') == "sheetdown")
    # 退場中立刻再開：新的面板正常可用，舊的不會被點到
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(50)
    n = await pg.evaluate('document.querySelectorAll(".sheet-modal:not(.leaving)").length')
    await pg.evaluate('document.querySelector(".sheet-modal.leaving .sm-x").click()')
    rec("彈窗關閉", "退場中馬上再打開：新面板正常、點退場中的舊面板沒反應", n == 1 and await pg.evaluate('modals.length') == 1 and await pg.evaluate('!!document.querySelector(".sheet-modal:not(.leaving)")'))
    await pg.keyboard.press("Escape"); await pg.clock.run_for(250); await pg.wait_for_timeout(100)
    rec("彈窗關閉", "Esc 關閉後全部移除、捲動恢復", await pg.evaluate('document.querySelectorAll(".sheet-modal").length===0&&document.body.style.overflow===""'))
    # 焦點回到打開它的按鈕（退場不影響）
    await pg.click('.hud-sos'); await pg.wait_for_timeout(300); await pg.keyboard.press("Escape"); await pg.wait_for_timeout(50)
    rec("彈窗關閉", "關閉時焦點馬上回到原本的按鈕", await pg.evaluate('!!document.activeElement?.closest(".hud-sos")'))
    rec("彈窗關閉", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def reduced(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.emulate_media(reduced_motion="reduce")
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('.g-home .grid .tile[data-day="2"]')
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
        for f in [pages, sheets, reduced, narrow]:
            try: await f(b)
            except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
        await b.close()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
