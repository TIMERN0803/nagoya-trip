# KISO 整理券：11/21 卡片只留一行＋「看完整說明」，彈窗有抽券流程／注意事項／連結；11/20 20:00 提醒有「怎麼抽」入口；sanrio 整理券不受影響
import asyncio
import fulltest as ft
from playwright.async_api import async_playwright
SH='.sheet-modal:not(.leaving) .qt-sheet'
async def opened(pg):return await pg.query_selector(SH) is not None
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        a=await ft.newpage(b,ft.jst(11,21,7,0),me="zhang",code="neko-kiso");await a.wait_for_timeout(400)
        card=a.locator('ol.tl li.item',has=a.locator('h3',has_text="KISO")).first
        q=card.locator('.qt')
        ft.rec("KISO","11/21 KISO 卡片有整理券區塊",await q.count()==1)
        ft.rec("KISO","卡片主行：8:00–8:45 時段內到店",(await q.locator(".qt-main b").inner_text())=="8:00–8:45 時段內到店")
        ft.rec("KISO","卡片不列注意事項（保持乾淨）",await q.locator('.qt-rules').count()==0)
        await q.locator('[data-qt-open]').click();await a.wait_for_timeout(650)
        ft.rec("KISO","點「看完整說明」打開彈窗",await opened(a))
        t=await a.inner_text(SH)
        for k in ["整理券怎麼拿","KISO・LINE 抽券・一張最多 4 人","11/20 20:00","打開 KISO 官網抽券","在券上的時段內到店","13:00 後","12:30","一張券最多 4 人","不會叫號","LINE 取消","會被拒絕入店"]:ft.rec("KISO",f"彈窗有「{k}」",k in t)
        ft.rec("KISO","我們要走的兩步有標示",await a.evaluate('document.querySelectorAll(".qt-sheet .qt-steps li.on").length')==2)
        ft.rec("KISO","連結：官網抽券＋IG 公告，另開分頁",await a.evaluate('[...document.querySelectorAll(".qt-sheet .qt-links a")].map(x=>x.href+"|"+x.target+"|"+x.rel).join()')=="https://kiso-nagoya.my.canva.site/|_blank|noopener,https://www.instagram.com/p/DbU8VJGkbNj/|_blank|noopener")
        ft.rec("KISO","320 寬以內不橫向捲動",await a.evaluate('document.querySelector(".qt-sheet").scrollWidth<=document.querySelector(".qt-sheet").clientWidth+1'))
        await a.keyboard.press("Escape");await a.wait_for_timeout(400)
        ft.rec("KISO","Esc 關閉、焦點回到入口",not await opened(a) and await a.evaluate('!!document.activeElement&&document.activeElement.matches("[data-qt-open]")'))
        # 11/20：20:00 提醒卡
        c=await ft.newpage(b,ft.jst(11,20,19,0),me="zhang",code="neko-kiso",ctx=a.ctx);await c.wait_for_timeout(400)
        r=c.locator('ol.tl li.item',has=c.locator('h3',has_text="搶 KISO 號碼牌")).first
        ft.rec("KISO","11/20 提醒卡有 KISO 官網與「怎麼抽」",await r.locator('a.chip',has_text="KISO 官網").count()==1 and await r.locator('[data-qt-open="KISO"]').count()==1)
        await r.locator('[data-qt-open="KISO"]').click();await c.wait_for_timeout(650)
        ft.rec("KISO","從 11/20 提醒打開同一個說明",await opened(c) and "打開 KISO 官網抽券" in await c.inner_text(SH))
        await c.click('.sheet-modal',position={"x":20,"y":20});await c.wait_for_timeout(400)
        ft.rec("KISO","點背景關閉、恢復捲動",not await opened(c) and await c.evaluate('document.body.style.overflow===""'))
        # sanrio 不受影響
        s=await ft.newpage(b,ft.jst(11,23,7,0),me="zhang",code="neko-kiso",ctx=a.ctx);await s.wait_for_timeout(400)
        sq=s.locator('ol.tl li.item',has=s.locator('h3',has_text="sanrio")).first.locator('.qt')
        ft.rec("KISO","sanrio 卡片主行與兩條重點照舊",(await sq.locator('.qt-main b').inner_text())=="10:00 起到西館 B1 店門口領" and await sq.locator('.qt-rules li').count()==2)
        await sq.locator('[data-qt-open]').click();await s.wait_for_timeout(650)
        ft.rec("KISO","sanrio 彈窗沒有多出連結區",await s.query_selector(SH+' .qt-links') is None)
        await b.close()
    print("TOTAL",len(ft.R),"FAIL",sum(1 for r in ft.R if not r[2]))
asyncio.run(main())
