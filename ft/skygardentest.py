# 11/19 晚上 Sky Promenade 改成大名古屋大廈 5F 空中花園（ngy-v71）：排在麵家 獅子丸之後、插圖、地圖、交通時間
import asyncio
from fulltest import newpage, jst, close, rec, R
from playwright.async_api import async_playwright
A = "11/19 空中花園"
N = "5F 空中花園"
PID = "ChIJR4hJQM53A2ARwg4uzRWt0IU"
SHISHI = "ChIJtWEoR-l2A2ARyai0CWUxIDM"
Q = """(N)=>{const sec=[...document.querySelectorAll('.card')].filter(c=>c.offsetParent);
 const names=sec.map(c=>(c.querySelector('h3')||{}).textContent||'');
 const card=sec.find(c=>(c.querySelector('h3')||{}).textContent===N);
 const li=card&&card.closest('li');const prev=li&&li.previousElementSibling;
 return {names,found:!!card,txt:li&&li.textContent,tag:card&&card.querySelector('.tag').textContent.trim(),
  pic:card&&card.querySelector('a.pic')&&card.querySelector('a.pic').href,
  art:card&&card.querySelector('a.pic svg g').innerHTML.length>40,
  legIn:prev&&prev.classList.contains('leg')?prev.textContent.replace(/\\s+/g,' ').trim():null,
  legInHref:prev&&prev.classList.contains('leg')?prev.querySelector('a').href:null,
  html:document.body.innerHTML.includes('Sky Promenade'),sw:document.documentElement.scrollWidth}}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (320, 390, 430):
            pg = await newpage(b, jst(11, 19, 18, 0))
            await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
            r = await pg.evaluate(Q, N)
            ns = r["names"]
            rec(A, f"{w} 寬：11/19 最後一站是空中花園、排在麵家 獅子丸之後", r["found"] and ns[-1] == N and ns[-2] == "麵家 獅子丸", ns)
            rec(A, f"{w} 寬：沒有 Sky Promenade 了", not r["html"])
            rec(A, f"{w} 寬：標籤景點、有日文名與免費說明", bool(r["tag"]) and "景點" in r["tag"] and "大名古屋ビルヂング" in (r["txt"] or "") and "大名古屋大廈" in (r["txt"] or "") and "免費" in (r["txt"] or ""), r["tag"])
            rec(A, f"{w} 寬：有插圖、點了開 Google 地圖（place_id）", r["art"] and bool(r["pic"]) and PID in r["pic"], r["pic"])
            rec(A, f"{w} 寬：獅子丸 → 這裡 走路約 12 分", bool(r["legIn"]) and "走路約 12 分" in r["legIn"] and "origin_place_id=" + SHISHI in r["legInHref"] and "destination_place_id=" + PID in r["legInHref"], r["legIn"])
            rec(A, f"{w} 寬：沒有水平捲動、沒有錯誤", r["sw"] == w and not pg.errs, pg.errs)
            if w == 390:
                el = await pg.query_selector(f'.card:has(h3:text-is("{N}"))')
                await el.scroll_into_view_if_needed(); await pg.evaluate("scrollBy(0,-260)"); await pg.wait_for_timeout(400)
                await pg.screenshot(path="/tmp/skygarden_390.png")
            await close(pg)
        await b.close()
    print(f"\n{sum(1 for x in R if x[2])}/{len(R)} PASS")
asyncio.run(main())
