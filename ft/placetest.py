# 地點精修測試：每個地點都綁 Google 地點 ID，「前往」和路線都直接開到那家店
import asyncio,json,re
from urllib.parse import urlparse,parse_qs
import fulltest as ft
from playwright.async_api import async_playwright
ALLOW_NO_PID={"阿彰：men's NEELU 名古屋"}
async def main():
    D=ft.DAYS
    noid=[f'{d["d"]} {it["n"]}' for d in D for it in d["items"] if it.get("map") and not it.get("pid") and it["n"] not in ALLOW_NO_PID]
    ft.rec("L 地點精修","每個有地圖的地點都有 Google 地點 ID（men's NEELU 除外）",not noid,noid)
    bad=[it["pid"] for d in D for it in d["items"] if it.get("pid") and not re.fullmatch(r"ChIJ[\w-]{23}",it["pid"])]
    ft.rec("L 地點精修","地點 ID 格式正確",not bad,bad)
    sakae=[it for it in D[0]["items"] if it["n"]=="榮"][0]
    ft.rec("L 地點精修","「榮」導到 Oasis 21 並註明起點","オアシス21" in sakae["map"] and "Oasis 21" in sakae.get("p",""))
    async with async_playwright() as p:
        b=await p.chromium.launch()
        errs=[];miss=[];legbad=[];nleg=0
        for i,d in enumerate(D):
            m,dd=map(int,d["d"].split("/"))
            pg=await ft.newpage(b,ft.jst(m,dd,6,0))
            links=await pg.evaluate('[...document.querySelectorAll("ol.tl li.item")].map(li=>({n:li.querySelector("h3").innerText,h:[...li.querySelectorAll("a[href*=\'google.com/maps/search\']")].map(a=>a.href)}))')
            for it,l in zip(d["items"],links):
                if it.get("pid"):
                    ok=any(parse_qs(urlparse(h).query).get("query_place_id")==[it["pid"]] for h in l["h"])
                    if not ok:miss.append(f'{d["d"]} {it["n"]}')
            legs=await pg.evaluate('[...document.querySelectorAll("li.leg a")].map(a=>a.href)')
            for h in legs:
                nleg+=1;q=parse_qs(urlparse(h).query)
                if "destination_place_id" not in q and "destination" in q:
                    legbad.append(q["destination"][0])
            errs+=pg.errs;await ft.close(pg)
        ft.rec("L 地點精修","每個地點的地圖連結都帶 query_place_id",not miss,miss)
        ft.rec("L 地點精修",f"交通路線都帶終點 ID（共 {nleg} 段，自訂起訖點的除外）",len(legbad)<=3,legbad)
        pg=await ft.newpage(b,ft.twt(10,25,13,0),tz="Asia/Taipei")
        if not await pg.query_selector('.g-home'):await pg.click('[data-home]')
        await pg.click('[data-sos]');await pg.wait_for_timeout(300)
        h=await pg.evaluate('[...document.querySelectorAll(".sos a")].find(a=>a.textContent.includes("地圖")).href')
        ft.rec("L 地點精修","求助頁飯店「地圖」也帶地點 ID","query_place_id=ChIJ74aBvtd2A2AR8TRTA-QLXZM" in h,h)
        errs+=pg.errs
        ft.rec("L 地點精修","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
