# 11/23 升半茶店換成 sanrio house 名古屋 PARCO 店（ngy-v68）：10:00、整理券怎麼拿（預設展開，可收起）、地圖、交通時間、行事曆檔
import asyncio
from fulltest import newpage, jst, close, rec, R
from playwright.async_api import async_playwright
ICS = open('/home/claude/nagoya-trip/nagoya-trip.ics', encoding='utf8', newline='').read().replace("\r\n ", "")
A = "sanrio house"
N = "sanrio house 名古屋 PARCO 店"
PID = "ChIJE8jefwBxA2ARQxQOIfwvqLk"
POPEYE = "ChIJ75UdoKt3A2AR2s1j5yzSBHc"
Q = """(n)=>{const sec=[...document.querySelectorAll('.card')].filter(c=>c.offsetParent);
 const names=sec.map(c=>(c.querySelector('h3')||{}).textContent||'');
 const card=sec.find(c=>(c.querySelector('h3')||{}).textContent===n);
 const li=card&&card.closest('li');const prev=li&&li.previousElementSibling,next=li&&li.nextElementSibling;
 const legTxt=el=>el&&el.classList.contains('leg')?el.textContent.replace(/\\s+/g,' ').trim():null;
 const legHref=el=>el&&el.classList.contains('leg')?el.querySelector('a').href:null;
 const q=card&&card.querySelector('details.qt'),sm=q&&q.querySelector('summary');
 const lum=c=>{const m=c.match(/[\\d.]+/g).map(Number);const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(m[0])+.7152*f(m[1])+.0722*f(m[2])};
 const bgOf=el=>{for(let e=el;e;e=e.parentElement){const b=getComputedStyle(e).backgroundColor;if(b&&!/rgba\\(0, 0, 0, 0\\)|transparent/.test(b))return b}return 'rgb(255,255,255)'};
 const ratio=el=>{const a=lum(getComputedStyle(el).color),b=lum(bgOf(el));return +((Math.max(a,b)+.05)/(Math.min(a,b)+.05)).toFixed(2)};
 const texts=q?[...q.querySelectorAll('b,small,span.qt-t,li,.qt-h')].filter(e=>e.offsetParent&&e.textContent.trim()):[];
 return {names,found:!!card,tag:card&&card.querySelector('.tag').textContent.trim(),
  time:li&&li.querySelector('.t').textContent.trim(),jp:card&&card.querySelector('.jp')&&card.querySelector('.jp').textContent,
  p:card&&card.querySelector('p')&&card.querySelector('p').textContent,
  pic:card&&card.querySelector('a.pic')&&card.querySelector('a.pic').href,
  legIn:legTxt(prev),legInHref:legHref(prev),legOut:legTxt(next),legOutHref:legHref(next),
  qt:!!q,open:q&&q.open,sum:sm&&sm.textContent.replace(/\\s+/g,' ').trim(),sumH:sm&&sm.getBoundingClientRect().height,
  steps:q?[...q.querySelectorAll('.qt-steps li')].map(l=>[l.className,l.textContent.replace(/\\s+/g,' ').trim()]):[],
  rules:q?[...q.querySelectorAll('.qt-rules li')].map(l=>[l.className,l.textContent.trim()]):[],
  bodyVis:q&&q.querySelector('.qt-body').checkVisibility(),
  minFont:texts.length?Math.min(...texts.map(e=>parseFloat(getComputedStyle(e).fontSize))):null,
  minRatio:texts.length?Math.min(...texts.map(ratio)):null,
  qtR:q&&q.getBoundingClientRect().right,qtL:q&&q.getBoundingClientRect().left,picB:card&&card.querySelector('.pic')&&card.querySelector('.pic').getBoundingClientRect().bottom,qtT:q&&q.getBoundingClientRect().top,
  cardR:card&&card.getBoundingClientRect().right,cardL:card&&card.getBoundingClientRect().left,
  periods:q?(q.textContent.match(/。/g)||[]).length:0,
  route:document.body.textContent,sw:document.documentElement.scrollWidth}}"""
async def main():
    rec(A, "行事曆檔：11/23 10:00 sanrio house 名古屋 PARCO 店", f"DTSTART;TZID=Asia/Tokyo:20261123T100000\r\nDTEND;TZID=Asia/Tokyo:20261123T110000\r\nSUMMARY:{N}" in ICS)
    rec(A, "行事曆檔：說明寫整理券兩個時段與一人一張", "整理券：9:30–9:50 在西館外面排；10:00 起 到西館 B1 店門口領（一人一張・發完就結束）" in ICS)
    rec(A, "行事曆檔：升半茶店已移除", "升半茶店" not in ICS)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (320, 390, 430):
            pg = await newpage(b, jst(11, 23, 8, 0))
            await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
            r = await pg.evaluate(Q, N); ns = r["names"]
            order = all(n in ns for n in ("伏見町 POPEYE", N, "沢村 名古屋")) and ns.index("伏見町 POPEYE") < ns.index(N) < ns.index("沢村 名古屋")
            rec(A, f"{w} 寬：排在 POPEYE 與沢村之間、升半茶店不在", r["found"] and order and not any("升半" in n for n in ns), ns)
            rec(A, f"{w} 寬：10:00、標籤購物、西館 B1、先領整理券", r["time"] == "10:00" and bool(r["tag"]) and "購物" in r["tag"] and r["jp"] == "名古屋PARCO 西館 B1" and "先領整理券" in (r["p"] or ""), (r["time"], r["tag"], r["jp"], r["p"]))
            rec(A, f"{w} 寬：點插圖開 Google 地圖（含 place_id）", bool(r["pic"]) and PID in r["pic"], r["pic"])
            rec(A, f"{w} 寬：POPEYE → 這間 走路約 18 分", bool(r["legIn"]) and "走路約 18 分" in r["legIn"] and "origin_place_id=" + POPEYE in r["legInHref"] and PID in r["legInHref"], r["legIn"])
            rec(A, f"{w} 寬：這間 → 沢村 地鐵約 20 分", bool(r["legOut"]) and "地鐵約 20 分" in r["legOut"] and "origin_place_id=" + PID in r["legOutHref"], r["legOut"])
            rec(A, f"{w} 寬：整理券預設展開，標題寫重點，可點高度 ≥ 44", r["qt"] and r["open"] and r["bodyVis"] and r["sum"] == "整理券怎麼拿一人一張・發完就結束" and r["sumH"] >= 44, (r["sum"], r["sumH"], r["open"]))
            rec(A, f"{w} 寬：整理券在插圖下方、不超出卡片", r["qtT"] >= r["picB"] - 0.5 and r["qtR"] <= r["cardR"] + 0.5 and r["qtL"] >= r["cardL"], (r["qtT"], r["picB"]))
            st = r["steps"]
            rec(A, f"{w} 寬：兩個時段，10:00 那段標出來", r["open"] and r["bodyVis"] and len(st) == 2 and st[0][0] == "" and st[0][1].startswith("9:30–9:50在西館外面排") and st[1][0] == "on" and st[1][1].startswith("10:00 起到西館 B1 店門口領"), st)
            ru = r["rules"]
            rec(A, f"{w} 寬：注意事項 5 條，「發完就結束」用警示色", len(ru) == 5 and ru[0][0] == "warn" and "發完就結束" in ru[0][1] and all(c == "" for c, _ in ru[1:]) and "兩個人都要去領" in ru[1][1], ru)
            rec(A, f"{w} 寬：字級 ≥ 12、對比 ≥ 4.5、沒有句號", r["minFont"] >= 12 and r["minRatio"] >= 4.5 and r["periods"] == 0, (r["minFont"], r["minRatio"]))
            rec(A, f"{w} 寬：展開後不超出卡片、沒有水平捲動、沒有錯誤", r["qtR"] <= r["cardR"] + 0.5 and r["sw"] == w and not pg.errs, pg.errs)
            await pg.click(f'.card:has(h3:text-is("{N}")) details.qt summary'); await pg.wait_for_timeout(200)
            r = await pg.evaluate(Q, N)
            rec(A, f"{w} 寬：點標題收起來", not r["open"] and not r["bodyVis"])
            await pg.click(f'.card:has(h3:text-is("{N}")) details.qt summary'); await pg.wait_for_timeout(200)
            r = await pg.evaluate(Q, N)
            rec(A, f"{w} 寬：再點一次打開", r["open"] and r["bodyVis"])
            if w == 390:
                el = await pg.query_selector(f'.card:has(h3:text-is("{N}"))')
                await el.scroll_into_view_if_needed(); await pg.evaluate("scrollBy(0,-200)"); await pg.wait_for_timeout(300)
                await pg.screenshot(path="/tmp/sanrio_open_390.png")
            await close(pg)
        await b.close()
    print(f"\n{sum(1 for x in R if x[2])}/{len(R)} PASS")
asyncio.run(main())
