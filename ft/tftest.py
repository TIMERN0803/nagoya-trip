# 免稅提醒與退稅清單測試
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-tf"
async def exps(pg):
    db=json.loads(await pg.evaluate('localStorage.getItem("mockdb")'));return {k:v for k,v in db.items() if "/expenses/" in k}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        a=await ft.newpage(b,ft.jst(11,21,20,0),me="zhang",code="neko-tf")
        s=await ft.newpage(b,ft.jst(11,21,20,0),me="star",code="neko-tf",ctx=a.ctx)
        await a.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await a.wait_for_timeout(400)
        await a.click('[data-list-tab="buy"]');await a.wait_for_timeout(300)
        ft.rec("X 免稅","要買的上方有免稅提醒","稅前滿 ¥5,000" in await a.inner_text('[data-group-id=buy]') and "護照" in await a.inner_text('[data-group-id=buy] .tf-tip'))
        await a.click('nav.tabs button[data-tab="acct"]');await a.wait_for_timeout(400)
        ft.rec("X 免稅","沒有免稅的帳時不顯示退稅清單",await a.evaluate('document.getElementById("tf-list").hidden'))
        await ft.openexp(a);await a.fill('#f-amt','3000')
        ft.rec("X 免稅","金額未滿 ¥5,000 不顯示免稅開關",await a.evaluate('document.getElementById("f-tf-row").hidden'))
        await a.fill('#f-amt','6600')
        ft.rec("X 免稅","滿 ¥5,000 出現免稅開關",not await a.evaluate('document.getElementById("f-tf-row").hidden'))
        await a.click('[data-tf-toggle]');await a.fill('#f-note','大國藥妝');await a.click('[data-pick="cat"] [data-v="shop"]')
        await a.click('#f-save');await a.wait_for_timeout(600)
        e=list((await exps(a)).values())
        ft.rec("X 免稅","存進雲端時標記免稅",len(e)==1 and e[0].get("tf") is True,e)
        await ft.openexp(a)
        ft.rec("X 免稅","存完再記一筆：開關回到關閉、隱藏",await a.evaluate('document.getElementById("f-tf-row").hidden && document.querySelector(".exp-sheet:not(.leaving) [data-tf-toggle]").getAttribute("aria-pressed")==="false"'))
        await a.click('[data-exp-x]');await a.wait_for_timeout(400)
        ft.rec("X 免稅","記帳列表有「免稅」標籤","免稅" in await a.inner_text('#acct-list'))
        t=await a.inner_text('#tf-list')
        ft.rec("X 免稅","退稅清單出現，預估可退約 ¥600","約 ¥600" in t and "大國藥妝" in t and "0 / 1" in t,t[:80])
        await a.click('[data-carry]');await a.wait_for_timeout(500)
        e=list((await exps(a)).values())
        ft.rec("X 免稅","勾「隨身」寫進雲端、計數 1/1",e[0].get("carry") is True and "1 / 1" in await a.inner_text('#tf-list'))
        await s.click('nav.tabs button[data-tab="acct"]');await s.wait_for_timeout(600)
        ft.rec("X 免稅","星星的手機也看到退稅清單和勾選","1 / 1" in await s.inner_text('#tf-list'))
        # 未滿 5000 的帳不能標免稅
        await ft.openexp(a);await a.fill('#f-amt','4000');await a.click('#f-save');await a.wait_for_timeout(500)
        ft.rec("X 免稅","一般的帳不會進退稅清單",(await a.inner_text('#tf-list')).count("¥4,000")==0 and len(await exps(a))==2)
        # 修改免稅那筆：保留隨身、可以取消免稅
        await a.click('.ex[data-edit]:has(.tf-badge)');await a.wait_for_timeout(600)
        ft.rec("X 免稅","修改時帶入免稅開關",await a.evaluate('document.querySelector("[data-tf-toggle]").getAttribute("aria-pressed")')=="true")
        await a.fill('#f-amt','7700');await a.click('#f-save');await a.wait_for_timeout(500)
        tfe=[v for v in (await exps(a)).values() if v.get("tf")]
        ft.rec("X 免稅","改金額後仍是免稅、保留隨身勾選",len(tfe)==1 and tfe[0]["amt"]==7700 and tfe[0].get("carry") is True and "約 ¥700" in await a.inner_text('#tf-list'))
        await a.click('.ex[data-edit]:has(.tf-badge)');await a.wait_for_timeout(600)
        await a.click('[data-tf-toggle]');await a.click('#f-save');await a.wait_for_timeout(500)
        ft.rec("X 免稅","取消免稅後從退稅清單移除",await a.evaluate('document.getElementById("tf-list").hidden'))
        # 刪除後復原保留免稅
        await a.click('.ex[data-edit]:has-text("¥7,700")');await a.wait_for_timeout(600)
        await a.click('[data-tf-toggle]');await a.click('#f-save');await a.wait_for_timeout(500)
        await a.click('.ex[data-edit]:has(.tf-badge)');await a.wait_for_timeout(600)
        await a.click('[data-exp-del]');await a.wait_for_timeout(500)  # 修改面板裡的「刪除這筆」
        await a.click('.undo-bar button');await a.wait_for_timeout(600)
        ft.rec("X 免稅","刪除後復原，免稅標記還在",not await a.evaluate('document.getElementById("tf-list").hidden'))
        # 11/24 機場行程
        d=await ft.newpage(b,ft.jst(11,24,6,0),me="zhang",code="neko-tf",ctx=a.ctx)
        await d.wait_for_timeout(400)
        txt=await d.inner_text('ol.tl')
        ft.rec("X 免稅","11/24 行程有「先辦退稅，再託運」，排在登機前","先辦退稅，再託運" in txt and txt.index("先辦退稅，再託運")<txt.index("JX 321"))
        await d.click('[data-go-tf]');await d.wait_for_timeout(600)
        ft.rec("X 免稅","「看退稅清單」切到記帳並顯示清單",await d.query_selector('#tf-list:not([hidden])') and await d.evaluate('Math.abs(document.getElementById("tf-list").getBoundingClientRect().top)<300'))
        errs=a.errs+s.errs+d.errs
        ft.rec("X 免稅","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
