# 11/17 午餐改成 つばめパン＆Milk 尼ヶ坂本店（ngy-v70）：取代名駅店；排在飯店與名古屋城之間；插圖、地圖、交通時間；11/23 名駅店外帶不受影響
import asyncio
from fulltest import newpage, jst, close, rec, R
from playwright.async_api import async_playwright
A = "11/17 つばめパン"
N = "つばめパン＆Milk 尼ヶ坂本店"
OLD = "つばめパン＆Milk 名駅店"
PID = "ChIJF9_6-GRxA2ARAF326QqzWeo"
OLD_PID = "ChIJJX5mDJx3A2ARRkSisgKVHXU"
HOTEL_PID = "ChIJ74aBvtd2A2AR8TRTA-QLXZM"
Q = """(N)=>{const sec=[...document.querySelectorAll('.card')].filter(c=>c.offsetParent);
 const names=sec.map(c=>(c.querySelector('h3')||{}).textContent||'');
 const card=sec.find(c=>(c.querySelector('h3')||{}).textContent===N);
 const li=card&&card.closest('li');const prev=li&&li.previousElementSibling,next=li&&li.nextElementSibling;
 const legTxt=el=>el&&el.classList.contains('leg')?el.textContent.replace(/\\s+/g,' ').trim():null;
 const legHref=el=>el&&el.classList.contains('leg')?el.querySelector('a').href:null;
 return {names,found:!!card,tag:card&&card.querySelector('.tag').textContent.trim(),
  txt:li&&li.textContent,pic:card&&card.querySelector('a.pic')&&card.querySelector('a.pic').href,
  bread:card&&card.querySelector('a.pic svg g').innerHTML.length>40,
  legIn:legTxt(prev),legInHref:legHref(prev),legOut:legTxt(next),legOutHref:legHref(next),
  sw:document.documentElement.scrollWidth}}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (320, 390, 430):
            pg = await newpage(b, jst(11, 17, 12, 0))
            await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
            r = await pg.evaluate(Q, N)
            ns = r["names"]
            order = all(n in ns for n in ("名古屋燈光圖書飯店", N, "名古屋城")) and ns.index("名古屋燈光圖書飯店") < ns.index(N) < ns.index("名古屋城")
            rec(A, f"{w} 寬：11/17 是尼ヶ坂本店、排在飯店與名古屋城之間", r["found"] and order and OLD not in ns, ns)
            rec(A, f"{w} 寬：標籤午餐、寫尼ケ坂站旁", bool(r["tag"]) and "午餐" in r["tag"] and "尼ケ坂站" in (r["txt"] or ""), r["tag"])
            rec(A, f"{w} 寬：有麵包插圖、點了開 Google 地圖（新 place_id）", r["bread"] and bool(r["pic"]) and PID in r["pic"] and OLD_PID not in r["pic"], r["pic"])
            rec(A, f"{w} 寬：飯店 → 這間 電車約 25 分", bool(r["legIn"]) and "電車約 25 分" in r["legIn"] and "origin_place_id=" + HOTEL_PID in r["legInHref"] and "destination_place_id=" + PID in r["legInHref"], r["legIn"])
            rec(A, f"{w} 寬：這間 → 名古屋城東門 走路約 20 分", bool(r["legOut"]) and "走路約 20 分" in r["legOut"] and "origin_place_id=" + PID in r["legOutHref"] and "travelmode=walking" in r["legOutHref"], r["legOut"])
            rec(A, f"{w} 寬：沒有水平捲動、沒有錯誤", r["sw"] == w and not pg.errs, pg.errs)
            if w == 390:
                el = await pg.query_selector(f'.card:has(h3:text-is("{N}"))')
                await el.scroll_into_view_if_needed(); await pg.evaluate("scrollBy(0,-200)"); await pg.wait_for_timeout(400)
                await pg.screenshot(path="/tmp/tsubame_390.png")
            await close(pg)
            # 11/23 名駅店外帶不受影響
            pg = await newpage(b, jst(11, 23, 9, 0))
            await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
            r = await pg.evaluate(Q, OLD)
            rec(A, f"{w} 寬：11/23 外帶仍是名駅店（舊 place_id）", r["found"] and bool(r["pic"]) and OLD_PID in r["pic"] and N not in r["names"], r["names"])
            await close(pg)
        await b.close()
    print(f"\n{sum(1 for x in R if x[2])}/{len(R)} PASS")
asyncio.run(main())
