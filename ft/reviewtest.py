# 旅程回顧測試
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
import reviewshot as rs
async def home(pg):
    if not await pg.query_selector('.g-home'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for lab,t,tz in [("出發前 10/25",ft.twt(10,25,13,0),"Asia/Taipei"),("旅途中 11/20",ft.jst(11,20,20,0),"Asia/Tokyo"),("回國當天 11/24 上午",ft.jst(11,24,9,0),"Asia/Tokyo")]:
            pg=await ft.newpage(b,t,tz=tz);await home(pg)
            ft.rec("R 旅程回顧",f"{lab} 不顯示回顧",not await pg.query_selector('#review'));await ft.close(pg)
        init=f'localStorage.setItem("mockdb",{json.dumps(rs.DB)});'
        pg=await ft.newpage(b,ft.twt(11,25,20,0),tz="Asia/Taipei",init=init);await home(pg);await pg.wait_for_timeout(600)
        r=await pg.query_selector('#review');t=await r.inner_text() if r else ""
        ft.rec("R 旅程回顧","11/25 旅程結束後首頁出現回顧",bool(r))
        tot=sum(e[1] for e in rs.E_)
        ft.rec("R 旅程回顧","總花費正確",f"¥{tot:,}" in t,tot)
        ft.rec("R 旅程回顧","心情則數正確（7 則）","7 則" in t)
        ft.rec("R 旅程回顧","花費分類前三名：購物、餐飲、門票",t.index("購物")<t.index("餐飲")<t.index("門票"))
        ft.rec("R 旅程回顧","分帳結果和記帳頁一致","星星要給阿彰 ¥6,100" in t)
        ft.rec("R 旅程回顧","現金用掉的金額（阿彰 ¥4,400）","¥4,400" in t)
        ft.rec("R 旅程回顧","最開心的一天是 11/18 吉卜力公園，附兩人留言","11/18" in t and "吉卜力公園" in t and "龍貓巴士超可愛" in t)
        w=await pg.evaluate('[...document.querySelectorAll("#review .rv-bar i")].reduce((a,i)=>a+parseFloat(i.style.width),0)')
        ft.rec("R 旅程回顧","分類長條加起來是 100%",abs(w-100)<0.1,w)
        ft.rec("R 旅程回顧","總花費不會被截斷",await pg.evaluate('(()=>{const b=document.querySelector(".rv-stat.total b");return b.scrollWidth<=b.clientWidth})()'))
        await pg.click('#review .rv-best');await pg.wait_for_timeout(400)
        ft.rec("R 旅程回顧","點最開心的一天進到那天的行程",await pg.evaluate('document.getElementById("dayCount")?.textContent.includes("第 2 天")'))
        await pg.click('[data-home]');await pg.wait_for_timeout(300)
        await pg.click('#review [data-scroll-strip]');await pg.wait_for_timeout(500)
        ft.rec("R 旅程回顧","「看每天的心情」捲到心情格子",await pg.evaluate('(()=>{const r=document.querySelector(".mood-strip").getBoundingClientRect();return r.top>=0&&r.top<innerHeight*0.6})()'))
        await pg.click('#review [data-go="acct"]');await pg.wait_for_timeout(400)
        ft.rec("R 旅程回顧","「看完整記帳」切到記帳",await pg.query_selector('#acct-sum'))
        errs=pg.errs
        # 沒有任何資料
        e=await ft.newpage(b,ft.twt(11,26,9,0),tz="Asia/Taipei",code="neko-empty");await home(e)
        t=await e.inner_text('#review') if await e.query_selector('#review') else ""
        ft.rec("R 旅程回顧","沒有記帳和心情時也正常顯示，不出現空的區塊","¥0" in t and "花在哪裡" not in t and "最開心" not in t and "看每天的心情" not in t,t[:80])
        errs+=e.errs
        # 小螢幕
        s=await ft.newpage(b,ft.twt(11,25,20,0),tz="Asia/Taipei",init=init);await s.set_viewport_size({'width':320,'height':640});await home(s);await s.wait_for_timeout(500)
        ft.rec("R 旅程回顧","小手機不會橫向捲動",await s.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        errs+=s.errs
        ft.rec("R 旅程回顧","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
