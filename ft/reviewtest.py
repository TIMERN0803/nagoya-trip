# 旅程回顧（故事模式）測試
import asyncio,json
import fulltest as ft
import reviewshot as rs
from playwright.async_api import async_playwright
async def home(pg):
    if not await pg.query_selector('.g-home'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
async def cur(pg):return await pg.evaluate('[...document.querySelectorAll(".st-page")].findIndex(s=>s.classList.contains("on"))')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for lab,t,tz in [("出發前 10/25",ft.twt(10,25,13,0),"Asia/Taipei"),("旅途中 11/20",ft.jst(11,20,20,0),"Asia/Tokyo"),("回國當天 11/24 上午",ft.jst(11,24,9,0),"Asia/Tokyo")]:
            pg=await ft.newpage(b,t,tz=tz);await home(pg)
            ft.rec("R 旅程回顧",f"{lab} 不顯示回顧入口",not await pg.query_selector('[data-story-open]'));await ft.close(pg)
        init=f'localStorage.setItem("mockdb",{json.dumps(rs.DB)});'
        ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id="Asia/Taipei",accept_downloads=True)
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(11,25,20,0),tz="Asia/Taipei",init=init,ctx=ctx);await home(pg);await pg.wait_for_timeout(600)
        ft.rec("R 旅程回顧","旅程結束後首頁出現電影票入口",await pg.query_selector('.rv-ticket[data-story-open]'))
        await pg.click('[data-story-open]');await pg.wait_for_timeout(300)
        cls=await pg.evaluate('[...document.querySelectorAll(".st-page")].map(s=>s.className.split(" ")[1])')
        ft.rec("R 旅程回顧","7 頁依序：開場、集章、心情、最開心、對戰、收據、總結",cls==["pg-open","pg-stamp","pg-mood","pg-best","pg-vs","pg-rcpt","pg-sum"],cls)
        ft.rec("R 旅程回顧","打開時在第 1 頁、進度條 7 段",await cur(pg)==0 and len(await pg.query_selector_all('.st-bars i'))==7)
        await pg.click('.st-tap.next');await pg.clock.run_for(1500);await pg.wait_for_timeout(300)
        ft.rec("R 旅程回顧","點右邊到下一頁，集章頁數字跳到 32",await cur(pg)==1 and await pg.inner_text('.pg-stamp [data-count]')=="32")
        ft.rec("R 旅程回顧","8 個戳章",len(await pg.query_selector_all('.pg-stamp .stamp'))==8)
        await pg.click('.st-tap.prev');await pg.wait_for_timeout(200)
        ft.rec("R 旅程回顧","點左邊回上一頁",await cur(pg)==0)
        await pg.click('.st-tap.next');await pg.click('.st-tap.next');await pg.wait_for_timeout(300)
        ft.rec("R 旅程回顧","心情曲線：兩條線、7 個點",len(await pg.query_selector_all('.pg-mood svg.ln path'))==2 and len(await pg.query_selector_all('.pg-mood .pt'))==7)
        inside=await pg.evaluate('(()=>{const c=document.querySelector(".note").getBoundingClientRect();return [...document.querySelectorAll(".pg-mood .pt")].every(p=>{const r=p.getBoundingClientRect();return r.left>=c.left&&r.right<=c.right&&r.top>=c.top&&r.bottom<=c.bottom})})()')
        ft.rec("R 旅程回顧","心情的點都在筆記本紙內",inside)
        await pg.click('.st-tap.next');await pg.wait_for_timeout(200)
        t=await pg.inner_text('.pg-best')
        ft.rec("R 旅程回顧","最開心的一天：11/18 吉卜力公園＋兩人留言","吉卜力公園" in t and "龍貓巴士超可愛" in t and "魔女之谷" in t)
        await pg.click('.st-tap.next');await pg.wait_for_timeout(200)
        t=await pg.inner_text('.pg-vs')
        ft.rec("R 旅程回顧","對戰卡：付了多少、現金、心情則數","¥34,200" in t and "¥17,440" in t and "¥4,400" in t and "4 則" in t and "3 則" in t)
        await pg.click('.st-tap.next');await pg.wait_for_timeout(1400)
        t=await pg.inner_text('.pg-rcpt')
        ft.rec("R 旅程回顧","收據：分類、合計、台幣、分帳都看得到","¥51,640" in t and "NT$" in t and "星星要給阿彰 ¥6,100" in t)
        vis=await pg.evaluate('(()=>{const r=document.querySelector(".rcpt"),b=r.querySelector(".rc-thx").getBoundingClientRect(),w=r.getBoundingClientRect();return b.bottom<=w.bottom&&getComputedStyle(r).transform==="none"})()')
        ft.rec("R 旅程回顧","收據整張印出來、沒有被遮住",vis)
        await pg.click('.st-tap.next');await pg.wait_for_timeout(200)
        ft.rec("R 旅程回顧","最後一頁是總結，沒有下一頁",await cur(pg)==6 and await pg.evaluate('document.querySelector(".st-tap.next").hidden'))
        async with pg.expect_download() as dl:
            await pg.click('[data-story-save]')
        d=await dl.value;path=await d.path();data=open(path,'rb').read()
        import struct
        w,h=struct.unpack('>II',data[16:24]) if data[:8]==b'\x89PNG\r\n\x1a\n' else (0,0)
        ft.rec("R 旅程回顧","存成圖片：下載 1080×1350 的 PNG",d.suggested_filename=="名古屋回顧.png" and (w,h)==(1080,1350),(d.suggested_filename,w,h))
        open('/home/claude/build/rv_saved.png','wb').write(data)
        await pg.wait_for_timeout(300)
        ft.rec("R 旅程回顧","存完顯示提示","已存成圖片" in await pg.inner_text('.st-msg'))
        await pg.click('[data-story-again]');await pg.wait_for_timeout(200)
        ft.rec("R 旅程回顧","「再看一次」回到第 1 頁",await cur(pg)==0)
        await pg.keyboard.press('Escape');await pg.wait_for_timeout(200)
        ft.rec("R 旅程回顧","Esc 關閉、背景恢復捲動",not await pg.query_selector('.story') and await pg.evaluate('document.body.style.overflow')=="")
        errs=pg.errs
        e=await ft.newpage(b,ft.twt(11,26,9,0),tz="Asia/Taipei",code="neko-empty");await home(e)
        await e.click('[data-story-open]');await e.wait_for_timeout(300)
        cls=await e.evaluate('[...document.querySelectorAll(".st-page")].map(s=>s.className.split(" ")[1])')
        ft.rec("R 旅程回顧","沒有記帳和心情時，跳過心情、最開心、對戰、收據",cls==["pg-open","pg-stamp","pg-sum"],cls)
        errs+=e.errs
        sm=await ft.newpage(b,ft.twt(11,25,20,0),tz="Asia/Taipei",init=init);await sm.set_viewport_size({'width':320,'height':568});await home(sm)
        await sm.click('[data-story-open]');await sm.wait_for_timeout(300)
        bad=[]
        for i in range(7):
            ov=await sm.evaluate('(()=>{const s=document.querySelector(".st-page.on");if(document.documentElement.scrollWidth>innerWidth)return false;if(s.classList.contains("pg-sum")){s.scrollTop=9999;const b=s.querySelector("[data-story-save]").getBoundingClientRect();return getComputedStyle(s).overflowY==="auto"&&b.bottom<=innerHeight}return s.scrollHeight<=s.clientHeight+2})()')
            if not ov:bad.append(i+1)
            if i<6:await sm.click('.st-tap.next');await sm.wait_for_timeout(250)
        ft.rec("R 旅程回顧","小手機（320×568）每一頁都放得下，總結頁捲得到存圖按鈕",not bad,bad)
        errs+=sm.errs
        ft.rec("R 旅程回顧","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
