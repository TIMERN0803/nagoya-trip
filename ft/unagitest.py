# 鰻魚改訂（ngy-v67）：11/21 午餐改炭燒富士鰻魚 總店 13:00 訂位（一休，預約資訊 icon 列）、11/23 晚餐改熱田うなぎ 天 伏見；插圖、地圖、交通時間、行事曆檔
import asyncio
from fulltest import newpage, jst, close, rec, R
from playwright.async_api import async_playwright
ICS = open('/home/claude/nagoya-trip/nagoya-trip.ics', encoding='utf8', newline='').read().replace("\r\n ", "")
A = "鰻魚改訂"
L = "炭燒富士鰻魚 總店"
LPID = "ChIJJflGL6VwA2ARLO3QB-ruz4c"
D = "熱田うなぎ 天 伏見"
DPID = "ChIJ2WPawLV3A2AR1xmLIaXjDqo"
Q = """(n)=>{const sec=[...document.querySelectorAll('.card')].filter(c=>c.offsetParent);
 const names=sec.map(c=>(c.querySelector('h3')||{}).textContent||'');
 const card=sec.find(c=>(c.querySelector('h3')||{}).textContent===n);
 const li=card&&card.closest('li');const prev=li&&li.previousElementSibling,next=li&&li.nextElementSibling;
 const legTxt=el=>el&&el.classList.contains('leg')?el.textContent.replace(/\\s+/g,' ').trim():null;
 const legHref=el=>el&&el.classList.contains('leg')?el.querySelector('a').href:null;
 const rsv=card&&card.querySelector('.rsv');
 return {names,found:!!card,tag:card&&card.querySelector('.tag').textContent.trim(),
  jp:card&&card.querySelector('.jp')&&card.querySelector('.jp').textContent,
  txt:li&&li.textContent,pic:card&&card.querySelector('a.pic')&&card.querySelector('a.pic').href,
  unagi:card&&card.querySelector('a.pic svg')&&card.querySelector('a.pic svg').innerHTML.length,
  rsv:rsv&&rsv.textContent.replace(/\\s+/g,' ').trim(),rsvR:rsv&&rsv.getBoundingClientRect().right,
  cardR:card&&card.getBoundingClientRect().right,
  legIn:legTxt(prev),legInHref:legHref(prev),legOut:legTxt(next),legOutHref:legHref(next),
  all:document.body.textContent,sw:document.documentElement.scrollWidth}}"""
async def main():
    rec(A, "行事曆檔：11/21 13:00 炭燒富士鰻魚", f"DTSTART;TZID=Asia/Tokyo:20261121T130000\r\nDTEND;TZID=Asia/Tokyo:20261121T140000\r\nSUMMARY:{L}" in ICS)
    rec(A, "行事曆檔：寫午餐預約、日文店名、13:00、2 位、預約 ID", "DESCRIPTION:午餐預約\\n炭焼うな富士 本店\\n鰻魚飯\\, 一休訂位\\n已預約 13:00・2 位・預約 ID IR0563167387" in ICS.replace("，", "\\, "))
    rec(A, "行事曆檔：舊的熱田うなぎ 天 11:00 已移除", "20261121T110000" not in ICS and "SUMMARY:熱田うなぎ 天\r\n" not in ICS)
    rec(A, "行事曆檔：沒有訂位人姓名或信箱", "@gmail" not in ICS and "様" not in ICS)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (320, 390, 430):
            pg = await newpage(b, jst(11, 21, 9, 0))
            await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
            r = await pg.evaluate(Q, L); ns = r["names"]
            order = all(n in ns for n in ("熱田神宮", L, "大須商店街")) and ns.index("熱田神宮") < ns.index(L) < ns.index("大須商店街")
            rec(A, f"{w} 寬 11/21：排在熱田神宮與大須商店街之間、舊店不在", r["found"] and order and "熱田うなぎ 天" not in ns, ns)
            rec(A, f"{w} 寬 11/21：標籤午餐預約、13:00、日文店名", bool(r["tag"]) and "午餐預約" in r["tag"] and "13:00" in (r["txt"] or "") and r["jp"] == "炭焼うな富士 本店", (r["tag"], r["jp"]))
            rec(A, f"{w} 寬 11/21：預約資訊 13:00、2 位、IR0563167387，不超出卡片", r["rsv"] == "時間13:00人數2 位預約 IDIR0563167387" and r["rsvR"] <= r["cardR"] + 0.5, r["rsv"])
            rec(A, f"{w} 寬 11/21：鰻魚插圖、點了開 Google 地圖（含 place_id）", bool(r["unagi"]) and bool(r["pic"]) and LPID in r["pic"], r["pic"])
            rec(A, f"{w} 寬 11/21：熱田神宮 → 這間 地鐵約 30 分", bool(r["legIn"]) and "地鐵約 30 分" in r["legIn"] and "origin_place_id=ChIJ3abhnht6A2ARu-Y4yDEWlao" in r["legInHref"] and LPID in r["legInHref"], r["legIn"])
            rec(A, f"{w} 寬 11/21：這間 → 大須商店街 地鐵約 20 分", bool(r["legOut"]) and "地鐵約 20 分" in r["legOut"] and "origin_place_id=" + LPID in r["legOutHref"], r["legOut"])
            rec(A, f"{w} 寬 11/21：沒有訂位人姓名或信箱、沒有水平捲動、沒有錯誤", "@gmail" not in r["all"] and r["sw"] == w and not pg.errs, pg.errs)
            if w == 390:
                el = await pg.query_selector(f'.card:has(h3:text-is("{L}"))')
                await el.scroll_into_view_if_needed(); await pg.evaluate("scrollBy(0,-260)"); await pg.wait_for_timeout(400)
                await pg.screenshot(path="/tmp/unagi_1121_390.png")
            await close(pg)
            pg = await newpage(b, jst(11, 23, 9, 0))
            await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
            r = await pg.evaluate(Q, D); ns = r["names"]
            rec(A, f"{w} 寬 11/23：晚餐是熱田うなぎ 天 伏見、排最後、桂昇不在", r["found"] and ns and ns[-1] == D and "桂昇" not in ns, ns)
            rec(A, f"{w} 寬 11/23：標籤晚餐、營業到 20:00", bool(r["tag"]) and "晚餐" in r["tag"] and "營業到 20:00" in (r["txt"] or ""), r["tag"])
            rec(A, f"{w} 寬 11/23：鰻魚插圖、地圖含 place_id", bool(r["unagi"]) and bool(r["pic"]) and DPID in r["pic"], r["pic"])
            rec(A, f"{w} 寬 11/23：つばめパン → 這間 地鐵約 13 分", bool(r["legIn"]) and "地鐵約 13 分" in r["legIn"] and "origin_place_id=ChIJJX5mDJx3A2ARRkSisgKVHXU" in r["legInHref"] and DPID in r["legInHref"], r["legIn"])
            rec(A, f"{w} 寬 11/23：沒有水平捲動、沒有錯誤", r["sw"] == w and not pg.errs, pg.errs)
            if w == 390:
                el = await pg.query_selector(f'.card:has(h3:text-is("{D}"))')
                await el.scroll_into_view_if_needed(); await pg.evaluate("scrollBy(0,-300)"); await pg.wait_for_timeout(400)
                await pg.screenshot(path="/tmp/unagi_1123_390.png")
            await close(pg)
        await b.close()
    print(f"\n{sum(1 for x in R if x[2])}/{len(R)} PASS")
asyncio.run(main())
