# 首頁待辦提醒：顯示期限最近的那一則（不受清單排序影響）
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-next"
P=[("a","💺去程線上選位","JX 320","11/15 07:05",1),("b","💉打疫苗","","11/02",2),("c","🥖搶 KISO 號碼牌","","11/20 20:00",3),("d","沒有期限的事","","",4)]
db={f"{B}/items/{i}":{"group":"prep","title":t,"note":n,"due":d,"links":None,"order":o} for i,t,n,d,o in P}
db[f"{B}/settings/meta"]={"itemsSeeded":True,"itemsRestore":2}
INIT=f'localStorage.setItem("mockdb",{json.dumps(json.dumps(db))});'
async def pill(pg):
    if not await pg.query_selector('.g-home'):
        if await pg.query_selector('[data-home]'):await pg.click('[data-home]')
        else:await pg.click('nav.tabs button[data-tab="plan"]')
        await pg.wait_for_timeout(300)
    el=await pg.query_selector('.hero .chip.coral');return (await el.inner_text()).strip() if el else ""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await ft.newpage(b,ft.twt(10,25,16,0),tz="Asia/Taipei",code="neko-next",init=INIT);await pg.wait_for_timeout(500)
        t=await pill(pg)
        ft.rec("N 首頁待辦","清單第一個是 11/15，首頁仍顯示期限最近的 11/02 打疫苗","11/02" in t and "打疫苗" in t,t)
        pg2=await ft.newpage(b,ft.twt(11,3,9,0),tz="Asia/Taipei",code="neko-next",init=INIT,ctx=pg.ctx);await pg2.wait_for_timeout(500)
        t=await pill(pg2)
        ft.rec("N 首頁待辦","11/02 過了還沒勾，首頁換成下一則 11/15（過期的交給上方紅色提醒）","11/15" in t,t)
        await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(400)
        await pg.check('#c-b');await pg.wait_for_timeout(400)
        t=await pill(pg)
        ft.rec("N 首頁待辦","勾掉打疫苗後換成 11/15 去程線上選位","11/15" in t and "去程" in t,t)
        pg3=await ft.newpage(b,ft.twt(11,16,9,0),tz="Asia/Taipei",code="neko-next",init=INIT,ctx=pg.ctx);await pg3.wait_for_timeout(500)
        t=await pill(pg3)
        ft.rec("N 首頁待辦","11/16 時顯示 11/20 KISO（已過期的不顯示在這裡）","11/20" in t,t)
        errs=pg.errs+pg2.errs+pg3.errs
        ft.rec("N 首頁待辦","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
