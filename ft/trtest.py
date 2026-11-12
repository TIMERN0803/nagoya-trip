# 退稅流程（新制）說明面板測試：三個入口、依日期標出現在這一段、內容、關閉與焦點、看退稅清單
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-tr"
DB=json.dumps({f"{B}/expenses/a":{"amt":13200,"cat":"shop","who":"zhang","split":"self","pay":"card","day":"11/21","note":"大國藥妝","ts":1,"tf":True}})
SH='.sheet-modal:not(.leaving) .tr-sheet'
async def opened(pg):return await pg.query_selector(SH) is not None
async def close(pg):await pg.click(SH+' .sm-x');await pg.wait_for_timeout(400)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # 旅途中（11/21）
        a=await ft.newpage(b,ft.jst(11,21,20,0),me="zhang",code="neko-tr",init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        await a.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await a.wait_for_timeout(400)
        await a.click('[data-list-tab="buy"]');await a.wait_for_timeout(300)
        ft.rec("退稅流程","要買的免稅提醒有「退稅怎麼辦」",await a.query_selector('.tf-tip [data-tr-open]') is not None)
        await a.click('.tf-tip [data-tr-open]');await a.wait_for_timeout(650)
        ft.rec("退稅流程","從要買的打開面板",await opened(a))
        t=await a.inner_text(SH)
        for k in ["先付含稅價","稅前 ¥5,000","90 天內出境","託運之後就不能辦了","Customs_WiFi_For_TaxRefund","jcustoms","綠色","紅色","退稅手續","免税手続きはできますか？","整張退不到"]:
            ft.rec("退稅流程",f"內容有「{k}」",k in t)
        ft.rec("退稅流程","五段依序：出發前→買東西→前一晚→回國那天→回到台灣",await a.evaluate('[...document.querySelectorAll(".tr-sheet [data-tr-ph]")].map(e=>e.dataset.trPh).join()')=="pre,shop,pack,fly,home")
        ft.rec("退稅流程","11/21 標出「買東西的時候」是現在",await a.evaluate('[...document.querySelectorAll(".tr-sheet .tr-ph.on")].map(e=>e.dataset.trPh).join()')=="shop" and "現在" in await a.inner_text(SH+' .tr-ph.on h4'))
        ft.rec("退稅流程","買東西期間從頭看（不自動捲）",await a.evaluate('document.querySelector(".tr-sheet").scrollTop')==0)
        ft.rec("退稅流程","外部連結另開分頁",await a.evaluate('[...document.querySelectorAll(".tr-sheet a[href^=http]")].every(x=>x.target==="_blank"&&x.rel.includes("noopener"))'))
        await a.keyboard.press("Escape");await a.wait_for_timeout(400)
        ft.rec("退稅流程","Esc 關閉，焦點回到入口",not await opened(a) and await a.evaluate('document.activeElement&&document.activeElement.matches("[data-tr-open]")'))
        # 記帳頁的退稅清單入口
        await a.click('nav.tabs button[data-tab="acct"]');await a.wait_for_timeout(500)
        ft.rec("退稅流程","記帳的退稅清單底部有入口",await a.query_selector('#tf-list .tr-more[data-tr-open]') is not None)
        await a.click('#tf-list [data-tr-open]');await a.wait_for_timeout(650)
        ft.rec("退稅流程","從記帳打開面板",await opened(a))
        await a.click('.sheet-modal',position={"x":20,"y":20});await a.wait_for_timeout(400)
        ft.rec("退稅流程","點背景關閉",not await opened(a) and a.evaluate and await a.evaluate('document.body.style.overflow===""'))
        # 11/24 回國那天：行程入口、自動捲到機場、看退稅清單
        d=await ft.newpage(b,ft.jst(11,24,7,30),me="zhang",code="neko-tr",init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        await d.wait_for_timeout(400)
        ft.rec("退稅流程","11/24 行程有「退稅怎麼辦」",await d.query_selector('ol.tl [data-tr-open]') is not None)
        await d.click('ol.tl [data-tr-open]');await d.wait_for_timeout(650)
        ft.rec("退稅流程","11/24 標出「回國那天」",await d.evaluate('document.querySelector(".tr-sheet .tr-ph.on")?.dataset.trPh')=="fly")
        ft.rec("退稅流程","11/24 打開直接捲到機場那段",await d.evaluate('(()=>{const c=document.querySelector(".tr-sheet"),o=c.querySelector(".tr-ph.on"),h=c.querySelector(".sm-head");const r=o.getBoundingClientRect().top-h.getBoundingClientRect().bottom;return c.scrollTop>0&&r>=0&&r<40})()'))
        ft.rec("退稅流程","捲動後標題列有陰影",await d.evaluate('document.querySelector(".tr-sheet>.sm-head").classList.contains("shade")'))
        await d.click(SH+' [data-go-tf]');await d.wait_for_timeout(700)
        ft.rec("退稅流程","面板裡「看退稅清單」關閉面板並切到記帳",not await opened(d) and await d.query_selector('#tf-list:not([hidden])') is not None and await d.evaluate('document.body.style.overflow===""'))
        # 出發前、回到台灣後
        e=await ft.newpage(b,ft.jst(11,10,12,0),me="zhang",code="neko-tr",ctx=a.ctx)
        await e.evaluate('openTrSheet()');await e.wait_for_timeout(650)
        ft.rec("退稅流程","出發前標出「出發前」",await e.evaluate('document.querySelector(".tr-sheet .tr-ph.on")?.dataset.trPh')=="pre")
        f=await ft.newpage(b,ft.jst(11,26,12,0),me="zhang",code="neko-tr",ctx=a.ctx)
        await f.evaluate('openTrSheet()');await f.wait_for_timeout(650)
        ft.rec("退稅流程","回國後標出「回到台灣」",await f.evaluate('document.querySelector(".tr-sheet .tr-ph.on")?.dataset.trPh')=="home")
        g=await ft.newpage(b,ft.jst(11,23,21,0),me="zhang",code="neko-tr",ctx=a.ctx)
        await g.evaluate('openTrSheet()');await g.wait_for_timeout(650)
        ft.rec("退稅流程","11/23 標出「回國前一晚」",await g.evaluate('document.querySelector(".tr-sheet .tr-ph.on")?.dataset.trPh')=="pack")
        # 320 寬度不橫向捲動
        await g.set_viewport_size({"width":320,"height":640});await g.wait_for_timeout(300)
        ft.rec("退稅流程","320 寬度面板沒有橫向捲動",await g.evaluate('(()=>{const c=document.querySelector(".tr-sheet");return c.scrollWidth<=c.clientWidth+1})()'))
        errs=a.errs+d.errs+e.errs+f.errs+g.errs
        ft.rec("退稅流程","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
