# 餐廳人均花費（eat-price）：19 間餐廳在行程卡上顯示「人均 ¥…・約 NT$…」，數字是食べログ口コミ集計、依用餐時段取午或晚
# 台幣用 App 目前的匯率換算、取整到 10 元；城下町小吃與非餐廳項目不顯示；320／390／430 不超出卡片、不水平捲動
import asyncio
from fulltest import newpage, jst, close, rec, R
from playwright.async_api import async_playwright
A = "人均"
WANT = {  # 店名: (下限, 上限)，下限 0 = 「以內」
    "11/17": {"つばめパン＆Milk 尼ヶ坂本店": (1000, 2000), "すゞ家 赤門店": (2000, 3000)},
    "11/18": {"伏見屋 飛騨牛 別邸": (10000, 15000)},
    "11/19": {"コンパル サンロード店": (1000, 2000), "蕎麦正 まつい 犬山店": (1000, 2000), "麵家 獅子丸": (1000, 2000)},
    "11/20": {"イトウ珈琲喫茶室": (0, 1000), "挽き肉のトリコ": (2000, 3000)},
    "11/21": {"KISO": (1000, 2000), "炭燒富士鰻魚 總店": (6000, 8000), "大須鮨": (6000, 8000), "ふみ屋 錦店": (3000, 4000)},
    "11/22": {"New Poppy": (0, 1000), "nuu": (1000, 2000), "風舎 常滑店": (0, 1000), "西条園抹茶カフェ": (0, 1000), "Yellow 則武新町店": (1000, 2000)},
    "11/23": {"伏見町 POPEYE": (2000, 3000), "熱田うなぎ 天 伏見": (3000, 4000)},
}
Q = """()=>[...document.querySelectorAll('.item .card')].filter(c=>c.offsetParent).map(c=>{const p=c.querySelector('.pr');return {name:c.querySelector('h3').textContent,
  pr:p&&{b:p.querySelector('b').textContent,s:p.querySelector('span').textContent,icon:p.querySelector('use').getAttribute('href'),hid:p.querySelector('svg').getAttribute('aria-hidden'),
  r:p.getBoundingClientRect().right,fs:Math.min(...[...p.querySelectorAll('b,span')].map(e=>parseFloat(getComputedStyle(e).fontSize)))},cardR:c.getBoundingClientRect().right}})"""
f = lambda n: f"{n:,}"
def expect(lo, hi, rate):
    tw = lambda n: f(round(n * rate / 10) * 10)
    if lo: return f"人均 ¥{f(lo)}–{f(hi)}", f"約 NT$ {tw(lo)}–{tw(hi)}"
    return f"人均 ¥{f(hi)} 以內", f"約 NT$ {tw(hi)} 以內"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        n = 0
        for d, want in WANT.items():
            m, dd = map(int, d.split("/"))
            for w in (320, 390, 430):
                pg = await newpage(b, jst(m, dd, 7, 0))
                await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(600)
                cards = await pg.evaluate(Q); rate = await pg.evaluate("rate")
                sw = await pg.evaluate("document.documentElement.scrollWidth")
                names = {c["name"]: c for c in cards}
                if w == 390:
                    for name, (lo, hi) in want.items():
                        c = names.get(name); jp, tw = expect(lo, hi, rate)
                        ok = bool(c and c["pr"]) and c["pr"]["b"] == jp and c["pr"]["s"] == tw and c["pr"]["icon"] == "#i-cash" and c["pr"]["hid"] == "true"
                        rec(A, f"{d} {name}：{jp}・{tw}", ok, c and c["pr"]); n += ok
                    extra = [c["name"] for c in cards if c["pr"] and c["name"] not in want]
                    rec(A, f"{d}：其他項目（景點、交通、城下町小吃等）沒有人均", not extra, extra)
                    rec(A, f"{d}：字級 ≥ 12", all(c["pr"]["fs"] >= 12 for c in cards if c["pr"]))
                rec(A, f"{d} {w} 寬：人均不超出卡片、沒有水平捲動", sw == w and all(c["pr"]["r"] <= c["cardR"] + 0.5 for c in cards if c["pr"]), sw)
                rec(A, f"{d} {w} 寬：沒有錯誤", not pg.errs, pg.errs)
                await close(pg)
        rec(A, "19 間餐廳都有人均", n == 19, n)
        # 匯率改了，台幣跟著換算
        pg = await newpage(b, jst(11, 21, 7, 0))
        await pg.wait_for_timeout(600); await pg.evaluate("rate=0.25;render(true)"); await pg.wait_for_timeout(300)
        rate = await pg.evaluate("rate")
        c = {x["name"]: x for x in await pg.evaluate(Q)}.get("炭燒富士鰻魚 總店")
        rec(A, f"匯率 {rate}：台幣用目前匯率換算", bool(c and c["pr"]) and c["pr"]["s"] == expect(6000, 8000, rate)[1], c and c["pr"])
        await close(pg)
        await b.close()
    print(f"\n{sum(1 for x in R if x[2])}/{len(R)} PASS")
asyncio.run(main())
