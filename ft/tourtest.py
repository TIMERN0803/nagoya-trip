# 使用教學測試
import asyncio
import fulltest as ft
from playwright.async_api import async_playwright
NEW='localStorage.removeItem("ngy:tour");'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",init=NEW)
        await pg.clock.run_for(1000);await pg.wait_for_timeout(300)
        ft.rec("T 使用教學","第一次打開會出現教學",await pg.query_selector('.tour'))
        ft.rec("T 使用教學","共 5 頁、第一頁點亮",len(await pg.query_selector_all('.tour-slide'))==5 and await pg.evaluate('document.querySelectorAll(".tour-dots i.on").length==1&&document.querySelector(".tour-dots i").classList.contains("on")'))
        for i in range(4):await pg.click('[data-tour-next]');await pg.clock.run_for(600);await pg.wait_for_timeout(500)
        ft.rec("T 使用教學","按下一步到最後一頁",await pg.evaluate('[...document.querySelectorAll(".tour-dots i")].pop().classList.contains("on")'))
        ft.rec("T 使用教學","最後一頁按鈕是「開始設定這支手機」、略過隱藏",(await pg.inner_text('[data-tour-next]'))=="開始設定這支手機" and await pg.evaluate('document.querySelector("[data-tour-skip]").hidden'))
        await pg.click('[data-tour-next]');await pg.wait_for_timeout(400)
        ft.rec("T 使用教學","按下去關掉教學、打開出發前設定",not await pg.query_selector('.tour') and await pg.query_selector('.su-sheet'))
        ft.rec("T 使用教學","記住已經看過",await pg.evaluate('localStorage.getItem("ngy:tour")')=="1")
        await pg.click('[data-tour-open]');await pg.wait_for_timeout(400)
        ft.rec("T 使用教學","設定清單裡的「看使用教學」可以再打開",await pg.query_selector('.tour') and not await pg.query_selector('.su-sheet'))
        await pg.keyboard.press('Escape');await pg.wait_for_timeout(200)
        ft.rec("T 使用教學","Esc 可以關閉",not await pg.query_selector('.tour'))
        await pg.reload();await pg.clock.run_for(1500);await pg.wait_for_timeout(400)
        ft.rec("T 使用教學","看過之後重新打開不會再出現",not await pg.query_selector('.tour'))
        # 略過
        q=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",init=NEW)
        await q.clock.run_for(1000);await q.wait_for_timeout(300)
        await q.click('[data-tour-skip]');await q.wait_for_timeout(200)
        ft.rec("T 使用教學","按略過直接關閉並記住",not await q.query_selector('.tour') and await q.evaluate('localStorage.getItem("ngy:tour")')=="1" and not await q.query_selector('.su-sheet'))
        # 左右滑
        w=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",init=NEW)
        await w.clock.run_for(1000);await w.wait_for_timeout(300)
        await w.evaluate('(()=>{const t=document.querySelector(".tour-track");t.scrollLeft=t.clientWidth*2;t.dispatchEvent(new Event("scroll"))})()');await w.clock.run_for(200);await w.wait_for_timeout(300)
        ft.rec("T 使用教學","左右滑動時圓點跟著換頁",await w.evaluate('[...document.querySelectorAll(".tour-dots i")].findIndex(d=>d.classList.contains("on"))')==2)
        ft.rec("T 使用教學","教學蓋在最上層，背景不能捲動",await w.evaluate('document.body.style.overflow')=="hidden")
        # 出發後：最後一頁是「開始使用」
        d=await ft.newpage(b,ft.jst(11,18,9,0),init=NEW)
        await d.clock.run_for(1000);await d.wait_for_timeout(300)
        for i in range(4):await d.click('[data-tour-next]');await d.clock.run_for(600);await d.wait_for_timeout(400)
        ft.rec("T 使用教學","旅途中最後一頁是「開始使用」",(await d.inner_text('[data-tour-next]'))=="開始使用")
        await d.click('[data-tour-next]');await d.wait_for_timeout(300)
        ft.rec("T 使用教學","旅途中按完直接進 App、不開設定",not await d.query_selector('.tour') and not await d.query_selector('.su-sheet'))
        errs=pg.errs+q.errs+w.errs+d.errs
        ft.rec("T 使用教學","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
