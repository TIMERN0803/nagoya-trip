# 11/19 犬山午餐（ngy-v66）：蕎麦正 まつい 犬山店 12:00，排在犬山城與城下町小吃之間；插圖、地圖、交通時間、行事曆檔
import asyncio
from fulltest import newpage, jst, close, rec, R
from playwright.async_api import async_playwright
ICS = open('/home/claude/nagoya-trip/nagoya-trip.ics', encoding='utf8', newline='').read().replace("\r\n ", "")
A = "犬山午餐"
N = "蕎麦正 まつい 犬山店"
PID = "ChIJeauxvQoSA2ARaoIN3R6CrUA"
Q = """()=>{const sec=[...document.querySelectorAll('.card')].filter(c=>c.offsetParent);
 const names=sec.map(c=>(c.querySelector('h3')||{}).textContent||'');
 const card=sec.find(c=>(c.querySelector('h3')||{}).textContent===%r);
 const li=card&&card.closest('li');const prev=li&&li.previousElementSibling,next=li&&li.nextElementSibling;
 const legTxt=el=>el&&el.classList.contains('leg')?el.textContent.replace(/\\s+/g,' ').trim():null;
 const legHref=el=>el&&el.classList.contains('leg')?el.querySelector('a').href:null;
 return {names,found:!!card,tag:card&&card.querySelector('.tag').textContent.trim(),
  txt:li&&li.textContent,pic:card&&card.querySelector('a.pic')&&card.querySelector('a.pic').href,
  soba:card&&!!card.querySelector('a.pic svg path[stroke="#857158"]'),
  legIn:legTxt(prev),legInHref:legHref(prev),legOut:legTxt(next),legOutHref:legHref(next),
  r:card&&card.getBoundingClientRect().right,sw:document.documentElement.scrollWidth}}""" % N
async def main():
    rec(A, "行事曆檔：11/19 12:00 午餐", f"DTSTART;TZID=Asia/Tokyo:20261119T120000\r\nDTEND;TZID=Asia/Tokyo:20261119T130000\r\nSUMMARY:{N}" in ICS)
    rec(A, "行事曆檔：說明寫午餐與營業提醒", "DESCRIPTION:午餐\\n手打冷蕎麥\\, 11:00 開、賣完就收\\, 只收現金" in ICS.replace("，", "\\, "))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (320, 390, 430):
            pg = await newpage(b, jst(11, 19, 9, 0))
            await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
            r = await pg.evaluate(Q)
            ns = r["names"]
            order = all(n in ns for n in ("犬山城", N, "城下町小吃")) and ns.index("犬山城") < ns.index(N) < ns.index("城下町小吃")
            rec(A, f"{w} 寬：排在犬山城與城下町小吃之間", r["found"] and order, ns)
            rec(A, f"{w} 寬：標籤午餐、12:00", bool(r["tag"]) and "午餐" in r["tag"] and "12:00" in (r["txt"] or ""), r["tag"])
            rec(A, f"{w} 寬：插圖是蕎麥麵、點了開 Google 地圖（含 place_id）", r["soba"] and bool(r["pic"]) and PID in r["pic"], r["pic"])
            rec(A, f"{w} 寬：犬山城 → 這間 走路約 8 分", bool(r["legIn"]) and "8" in r["legIn"] and "origin_place_id=ChIJke1IrfUOA2ARNfYDRkP6Wig" in r["legInHref"] and PID in r["legInHref"], r["legIn"])
            rec(A, f"{w} 寬：這間 → 城下町小吃 走路約 3 分", bool(r["legOut"]) and "3" in r["legOut"] and "origin_place_id=" + PID in r["legOutHref"], r["legOut"])
            rec(A, f"{w} 寬：沒有水平捲動、沒有錯誤", r["sw"] == w and not pg.errs, pg.errs)
            if w == 390:
                el = await pg.query_selector(f'.card:has(h3:text-is("{N}"))')
                await el.scroll_into_view_if_needed(); await pg.evaluate("scrollBy(0,-260)"); await pg.wait_for_timeout(400)
                await pg.screenshot(path="/tmp/inuyama_390.png")
            await close(pg)
        await b.close()
    print(f"\n{sum(1 for x in R if x[2])}/{len(R)} PASS")
asyncio.run(main())
