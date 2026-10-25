# 使用教學測試：框住實際畫面＋貓咪對話框
import asyncio
import fulltest as ft
from playwright.async_api import async_playwright
NEW='localStorage.removeItem("ngy:tour");'
async def hole_on(pg,sel):
    return await pg.evaluate('''([sel])=>{const h=document.querySelector(".coach-hole").getBoundingClientRect(),el=[...document.querySelectorAll(sel)].find(e=>e.getClientRects().length);if(!el)return false;const r=el.getBoundingClientRect();return Math.abs(h.left-(r.left-6))<3&&Math.abs(h.top-(r.top-6))<3&&r.top>=0&&r.bottom<=innerHeight}''',[sel])
async def tip_ok(pg):
    return await pg.evaluate('''(()=>{const t=document.querySelector(".coach-tip").getBoundingClientRect(),h=document.querySelector(".coach-hole").getBoundingClientRect();const overlap=!(t.bottom<=h.top+2||t.top>=h.bottom-2);return t.top>=0&&t.bottom<=innerHeight&&!overlap})()''')
async def nxt(pg):await pg.click("[data-coach-next]");await pg.clock.run_for(500);await pg.wait_for_timeout(500)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",init=NEW)
        await pg.clock.run_for(1200);await pg.wait_for_timeout(450)
        ft.rec("T 使用教學","第一次打開會出現教學",await pg.query_selector('.coach'))
        exp=[(".hud-badge","豆花和芝麻","w"),(".hud-sos","求助","b"),('.g-home .grid .tile[data-day]',"點一天","w"),('[data-group-id="prep"] [data-sort-toggle]',"排序","b"),(".setup-entry","設定好","w")]
        for i,(sel,word,cat) in enumerate(exp):
            t=await pg.inner_text('.coach-bub p')
            ft.rec("T 使用教學",f"第 {i+1} 步框住實際按鈕（{sel}）",await hole_on(pg,sel))
            ft.rec("T 使用教學",f"第 {i+1} 步對話框不擋住框起來的地方、在畫面內",await tip_ok(pg))
            ft.rec("T 使用教學",f"第 {i+1} 步文字簡短（{len(t)} 字）",word in t and len(t)<=32,t)
            ft.rec("T 使用教學",f"第 {i+1} 步換{'豆花' if cat=='w' else '芝麻'}說話",await pg.evaluate('document.querySelector(".coach-cat use").getAttribute("href")')=="#head-"+cat)
            if i==3:ft.rec("T 使用教學","第 4 步自動切到清單分頁",await pg.query_selector('nav.tabs button[data-tab="list"][aria-selected="true"]') or await pg.query_selector('[data-group-id="prep"]'))
            if i<4:await nxt(pg)
        ft.rec("T 使用教學","最後一步按鈕是「開始設定」、沒有略過",(await pg.inner_text('[data-coach-next]'))=="開始設定" and await pg.evaluate('document.querySelector("[data-coach-skip]").hidden'))
        await pg.click('[data-coach-next]');await pg.wait_for_timeout(400)
        ft.rec("T 使用教學","結束後回到首頁、打開出發前設定",not await pg.query_selector('.coach') and await pg.query_selector('.su-sheet') and await pg.query_selector('.g-home'))
        ft.rec("T 使用教學","記住已經看過",await pg.evaluate('localStorage.getItem("ngy:tour")')=="1")
        await pg.click('[data-tour-open]');await pg.wait_for_timeout(500)
        ft.rec("T 使用教學","設定清單裡的「看使用教學」可以再打開",await pg.query_selector('.coach') and not await pg.query_selector('.su-sheet'))
        await pg.keyboard.press('Escape');await pg.wait_for_timeout(300)
        ft.rec("T 使用教學","Esc 可以關閉、背景恢復捲動",not await pg.query_selector('.coach') and await pg.evaluate('document.body.style.overflow')=="")
        await pg.reload();await pg.clock.run_for(1500);await pg.wait_for_timeout(400)
        ft.rec("T 使用教學","看過之後重新打開不會再出現",not await pg.query_selector('.coach'))
        # 略過（在清單那一步略過也要回到首頁）
        q=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",init=NEW)
        await q.clock.run_for(1200);await q.wait_for_timeout(400)
        for i in range(3):await nxt(q)
        await q.click('[data-coach-skip]');await q.wait_for_timeout(300)
        ft.rec("T 使用教學","略過：關閉、記住、回到首頁、不打開設定",not await q.query_selector('.coach') and await q.evaluate('localStorage.getItem("ngy:tour")')=="1" and await q.query_selector('.g-home') and not await q.query_selector('.su-sheet'))
        # 旅途中
        d=await ft.newpage(b,ft.jst(11,18,10,0),init=NEW)
        await d.clock.run_for(1200);await d.wait_for_timeout(450)
        await nxt(d);await nxt(d)
        ft.rec("T 使用教學","旅途中第 3 步框住「今天」那格",await hole_on(d,'.g-home .grid .tile.today'))
        await nxt(d);await nxt(d)
        ft.rec("T 使用教學","旅途中最後一步框住「下一站」按鈕",await hole_on(d,'.fab'))
        ft.rec("T 使用教學","旅途中最後一步按鈕是「開始使用」",(await d.inner_text('[data-coach-next]'))=="開始使用")
        await d.click('[data-coach-next]');await d.wait_for_timeout(300)
        ft.rec("T 使用教學","旅途中按完直接進 App、不開設定",not await d.query_selector('.coach') and not await d.query_selector('.su-sheet'))
        # 小螢幕
        sm=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei",init=NEW)
        await sm.set_viewport_size({'width':320,'height':568});await sm.clock.run_for(1200);await sm.wait_for_timeout(450)
        ok=True
        for i in range(5):
            ok=ok and await tip_ok(sm)
            if i<4:await nxt(sm)
        ft.rec("T 使用教學","小手機（320×568）每一步對話框都在畫面內、不擋住",ok)
        errs=pg.errs+q.errs+d.errs+sm.errs
        ft.rec("T 使用教學","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
