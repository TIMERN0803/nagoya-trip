# 11/18 吉卜力公園交通：從飯店直接搭地鐵東山線＋Linimo，不再走到名古屋車站搭名鐵巴士
import asyncio
from urllib.parse import urlparse,parse_qs
import fulltest as ft
from playwright.async_api import async_playwright
GHIBLI_PID="ChIJs9ADAkVnA2ARixLFaXpLFjY"
async def main():
    D=ft.DAYS;day=[d for d in D if d["d"]=="11/18"][0]
    names=[it["n"] for it in day["items"]]
    ft.rec("G 吉卜力交通","第一項是伏見站搭地鐵東山線",names[0]=="伏見站搭地鐵東山線",names)
    ft.rec("G 吉卜力交通","行程資料不再有名鐵巴士",not any("巴士" in it["n"]+it.get("p","") or "バス" in it.get("map","") for it in day["items"]))
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await ft.newpage(b,ft.jst(11,18,7,30));await pg.wait_for_timeout(300)
        if not await pg.query_selector('ol.tl'):
            await pg.evaluate('location.hash=""');await pg.wait_for_timeout(200)
        r=await pg.evaluate('''()=>{const li=[...document.querySelectorAll("ol.tl li.item")];const f=li[0];const leg=document.querySelector("ol.tl li.leg");
          return {first:f&&f.querySelector("h3").innerText,p:f&&(f.querySelector("p")||{}).innerText,pic:f&&f.querySelector(".pic svg")?.innerHTML.length,
                  leg:leg&&leg.innerText.replace(/\\s+/g," "),href:leg&&leg.querySelector("a").href,body:document.body.innerText}}''')
        ft.rec("G 吉卜力交通","卡片顯示伏見站搭地鐵，寫明換 Linimo 和出門時間",r["first"]=="伏見站搭地鐵東山線" and "Linimo" in (r["p"] or "") and "8:20" in (r["p"] or ""),r["p"])
        ft.rec("G 吉卜力交通","卡片有電車插圖",bool(r["pic"]),r["pic"])
        ft.rec("G 吉卜力交通","交通段顯示電車約 55 分、東山線換 Linimo","電車約 55 分" in (r["leg"] or "") and "Linimo" in (r["leg"] or ""),r["leg"])
        q=parse_qs(urlparse(r["href"] or "").query)
        ft.rec("G 吉卜力交通","路線從飯店出發、終點帶吉卜力公園地點 ID、大眾運輸",
               q.get("origin")==["ランプライトブックスホテル名古屋"] and q.get("destination_place_id")==[GHIBLI_PID] and q.get("travelmode")==["transit"],q)
        ft.rec("G 吉卜力交通","頁面上看不到名鐵巴士","名鐵巴士" not in r["body"] and "名古屋車站 4 樓" not in r["body"])
        ft.rec("G 吉卜力交通","沒有 JS 錯誤",not pg.errs,pg.errs[:2])
        await ft.close(pg);await b.close()
    bad=[x for x in ft.R if not x[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
