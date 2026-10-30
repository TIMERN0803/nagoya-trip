# 行程卡預約資訊（ngy-v65）：時間、人數、預約 ID 用 icon 一列呈現（11/23 伏見町 POPEYE、11/18 伏見屋），行事曆檔同步
import asyncio, re
from fulltest import newpage, jst, close, rec, R
from playwright.async_api import async_playwright
ICS = open('/home/claude/nagoya-trip/nagoya-trip.ics', encoding='utf8', newline='').read().replace("\r\n ", "")
A = "預約"
Q = """()=>[...document.querySelectorAll('.rsv')].map(u=>{const card=u.closest('.card');return {name:card.querySelector('h3').textContent,
  tag:card.querySelector('.tag').textContent.trim(),
  items:[...u.children].map(l=>({icon:(l.querySelector('use')||{}).getAttribute?.('href'),hid:l.querySelector('svg').getAttribute('aria-hidden'),label:l.querySelector('.k').textContent,txt:l.textContent,r:l.getBoundingClientRect().right})),
  cardR:card.getBoundingClientRect().right,sw:document.documentElement.scrollWidth}})"""
CASES = [("伏見町 POPEYE", jst(11, 23, 7, 30), "早餐預約", [("#i-clock", "時間", "9:00"), ("#i-people", "人數", "2 位"), ("#k-ticket", "預約 ID", "NNVPQV")]),
         ("伏見屋 飛騨牛 別邸", jst(11, 18, 8, 0), "晚餐預約", [("#i-clock", "時間", "19:30"), ("#i-people", "人數", "2 位")])]
async def main():
    rec(A, "行事曆檔：POPEYE 寫早餐預約、9:00、2 位、預約 ID", "DESCRIPTION:早餐預約\\n已預約 9:00・2 位・預約 ID NNVPQV" in ICS)
    rec(A, "行事曆檔：伏見屋 寫 19:30、2 位", "已預約 19:30・2 位" in ICS)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, t, tag, want in CASES:
            for w in (320, 390, 430):
                pg = await newpage(b, t)
                await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
                rs = [x for x in await pg.evaluate(Q) if x["name"] == name]
                r = rs[0] if rs else None
                got = r and [(i["icon"], i["label"], i["txt"][len(i["label"]):]) for i in r["items"]]
                rec(A, f"{name} {w} 寬：標籤{tag}、icon 與內容", bool(r) and r["tag"] == tag and got == want and all(i["hid"] == "true" for i in r["items"]), got)
                rec(A, f"{name} {w} 寬：不超出卡片、沒有水平捲動", bool(r) and r["sw"] == w and all(i["r"] <= r["cardR"] for i in r["items"]))
                rec(A, f"{name} {w} 寬：沒有錯誤", not pg.errs, pg.errs)
                await close(pg)
        await b.close()
    print(f"\n{sum(1 for x in R if x[2])}/{len(R)} PASS")
asyncio.run(main())
