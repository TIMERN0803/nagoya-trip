# 出發前手機設定測試
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-setup"
def dbget(pg):return pg.evaluate('JSON.parse(localStorage.getItem("mockdb")||"{}")')
async def home(pg):
    if not await pg.query_selector('.g-home'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        a=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",me="zhang",code="neko-setup",init='Object.defineProperty(Notification,"permission",{get:()=>"granted"});Notification.requestPermission=async()=>"granted";')
        s=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",me="star",code="neko-setup",ctx=a.ctx)
        for q in (a,s):await home(q);await q.clock.run_for(2500);await q.wait_for_timeout(500)
        ft.rec("P 出發前設定","出發前首頁有設定卡片",await a.query_selector('.setup-entry'))
        db=await dbget(a)
        ft.rec("P 出發前設定","自動打勾：選好我是誰、連上同步（寫進雲端）",db.get(f"{B}/checks/su-me@zhang",{}).get("done") and db.get(f"{B}/checks/su-sync@zhang",{}).get("done"))
        ft.rec("P 出發前設定","瀏覽器裡不會誤判成已加到主畫面",not db.get(f"{B}/checks/su-home@zhang"))
        await a.click('[data-setup-open]');await a.wait_for_timeout(400)
        t=await a.inner_text('.su-sheet')
        ft.rec("P 出發前設定","清單共 8 項",len(await a.query_selector_all('.su-row'))==8)
        ft.rec("P 出發前設定","標示這是誰的手機","阿彰這支手機" in t)
        # 手動打勾
        await a.click('[data-setup-ck="net"]');await a.wait_for_timeout(400)
        db=await dbget(a)
        ft.rec("P 出發前設定","手動打勾寫進雲端",db.get(f"{B}/checks/su-net@zhang",{}).get("done") is True)
        await a.click('[data-setup-ck="net"]');await a.wait_for_timeout(400)
        db=await dbget(a)
        ft.rec("P 出發前設定","再按一次取消打勾",db.get(f"{B}/checks/su-net@zhang",{}).get("done") is False)
        await a.click('[data-setup-ck="offline"]');await a.wait_for_timeout(400)
        # 對方手機看到
        await s.wait_for_timeout(400)
        ft.rec("P 出發前設定","星星的首頁卡片看得到阿彰的進度（3/8）","3/8" in await s.inner_text('.setup-entry'),await s.inner_text('.setup-entry'))
        await s.click('[data-setup-open]');await s.wait_for_timeout(300)
        ft.rec("P 出發前設定","星星打開是星星自己的清單，開飛航模式那項顯示阿彰「好了」",await s.evaluate('(()=>{const r=document.querySelector("[data-setup-ck=offline]").closest(".su-row");return !r.classList.contains("done")&&r.querySelector(".su-other").textContent.includes("好了")})()'))
        await s.click('.su-sheet .sm-head .sm-x');await s.wait_for_timeout(350)
        # 打開求助頁會自動打勾
        await a.click('[data-setup-act="sos"]');await a.wait_for_timeout(400)
        ft.rec("P 出發前設定","按「打開」會開求助頁",await a.query_selector('.sos'))
        await a.click('.sos .sm-head .sm-x');await a.wait_for_timeout(350)
        db=await dbget(a)
        ft.rec("P 出發前設定","看過求助頁自動打勾",db.get(f"{B}/checks/su-sos@zhang",{}).get("done") is True)
        # 開提醒
        await a.click('[data-setup-open]');await a.wait_for_timeout(300)
        await a.click('[data-setup-act="notify"]');await a.wait_for_timeout(600)
        db=await dbget(a)
        ft.rec("P 出發前設定","按「開啟」打開 App 內提醒並打勾",await a.evaluate('localStorage.getItem("ngy:notify")')=="1" and db.get(f"{B}/checks/su-notify@zhang",{}).get("done") is True)
        await a.click('[data-setup-act="cal"]');await a.wait_for_timeout(300)
        ft.rec("P 出發前設定","按「設定」打開行事曆說明",await a.query_selector('[aria-label="加到手機行事曆"]'))
        errs=a.errs+s.errs
        # 拒絕通知權限時不會誤判
        q=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",me="zhang",code="neko-deny")
        await home(q);await q.click('[data-setup-open]');await q.wait_for_timeout(300)
        await q.click('[data-setup-act="notify"]');await q.wait_for_timeout(600)
        db=await dbget(q)
        ft.rec("P 出發前設定","通知權限被拒絕時不會自動打勾",not db.get("trips/neko-deny/checks/su-notify@zhang",{}).get("done"))
        errs+=q.errs
        # 沒網路打開過：自動打勾
        o=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",me="zhang",code="neko-off",init='Object.defineProperty(navigator,"onLine",{get:()=>false});')
        await home(o);await o.clock.run_for(2500);await o.wait_for_timeout(500)
        f=await o.evaluate('JSON.parse(localStorage.getItem("ngy:suFlags")||"{}")')
        ft.rec("P 出發前設定","沒網路時打開過，會記下「開飛航模式打開一次」",f.get("offline")==1,f)
        errs+=o.errs
        # 主畫面模式
        h=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",me="star",code="neko-home",init='Object.defineProperty(navigator,"standalone",{get:()=>true});')
        await home(h);await h.clock.run_for(2500);await h.wait_for_timeout(500)
        db=await dbget(h)
        ft.rec("P 出發前設定","從主畫面打開時，自動確認「加到主畫面」",db.get("trips/neko-home/checks/su-home@star",{}).get("done") is True)
        errs+=h.errs
        # 沒選我是誰
        n=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",me=None,code="neko-nome")
        await home(n);await n.click('[data-setup-open]');await n.wait_for_timeout(300)
        ft.rec("P 出發前設定","還沒選我是誰：先請他選",len(await n.query_selector_all('[data-setup-me]'))==2)
        await n.click('[data-setup-me="star"]');await n.wait_for_timeout(500)
        ft.rec("P 出發前設定","選好後顯示星星的清單","星星這支手機" in await n.inner_text('.su-sheet'))
        errs+=n.errs
        # 出發後不顯示
        d=await ft.newpage(b,ft.jst(11,17,9,0),me="zhang",code="neko-setup")
        await home(d)
        ft.rec("P 出發前設定","11/17 出發後首頁不再顯示",not await d.query_selector('.setup-entry'))
        errs+=d.errs
        ft.rec("P 出發前設定","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
