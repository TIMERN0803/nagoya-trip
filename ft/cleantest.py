# 第 3 組清理（cleanup-r2，ngy-v64）：CODE-15 死碼、CODE-16 gDusk 只留一組、CODE-17 匯率邊界、CODE-18 預快取、CODE-19 esc 合併
# 畫面不變另由 stylediff.py 比對（26 個畫面逐元素 getComputedStyle＋截圖像素）。一律假資料庫，旅程代碼 qa-r2-test。
import os, json, asyncio, re, urllib.request
from phonelib import *
import fxtest as fx
BASE = os.environ.get('BASE', 'http://localhost:8766/')
SRC = urllib.request.urlopen(BASE + 'index.html').read().decode('utf-8')
SW = urllib.request.urlopen(BASE + 'sw.js').read().decode('utf-8')

async def static(b):
    A = "清理｜原始碼"
    rec(A, "CODE-16 gDusk 只定義一次，留第一組深藍→紫→橘", SRC.count('id="gDusk"') == 1 and '<linearGradient id="gDusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4A5488"/>' in SRC)
    gone = [c for c in ["function moodCtaHTML", "@keyframes sheetup", "@keyframes bob{", ".cats-bob{", ".mapcard{", ".pk-prog{", ".w-head{", ".mood-cta{", "sosEsc"] if c in SRC]
    rec(A, "CODE-15 死碼已移除（moodCtaHTML 和它專用的樣式、sheetup、bob、沒用到的類別、sosEsc）", not gone, gone)
    rec(A, "心情列仍用得到的 .mc-faces 樣式保留", ".mc-faces{" in SRC and ".mood-line .mc-faces{" in SRC)
    core = re.search(r'const CORE = \[(.*?)\]', SW).group(1)
    rec(A, "CODE-18 預快取不再列沒用到的 ghibli-map-thumb.jpg、吉卜力地圖本體仍在", "ghibli-map-thumb" not in core and "./ghibli-map.jpg" in core, core)
    _v = re.search(r'const VERSION = "ngy-v(\d+)"', SW); rec(A, "sw.js 版本 ngy-v64 以上", bool(_v) and int(_v.group(1)) >= 64, _v and _v.group(0))

async def escape(b):
    A = "清理｜CODE-19 esc 合併"
    sos = {"order": "A'B<1>", "via": 'Tom\'s "Inn"', "guest": "", "room": "雙人房 & 早餐", "pay": "", "ins": "O'Neil 產險", "insTel": "0800-000-111"}
    ctx = await newctx(b, tz="Asia/Tokyo")
    pg = await phone(ctx, jst(11, 17, 20, 0), "zhang", "e", init=seed({**META, f"{B}/settings/sos": sos}), url=BASE, wait=1500)
    if await pg.query_selector('[data-home]'): await pg.click('[data-home]'); await pg.wait_for_timeout(600)
    await pg.click('.tile[data-day="0"]'); await pg.wait_for_timeout(800)
    t = await pg.inner_text('.stay-ord')
    rec(A, "入住卡片照原樣顯示單引號、雙引號、<>、&", "A'B<1>" in t and 'Tom\'s "Inn"' in t and "雙人房 & 早餐" in t, t.replace("\n", " ")[:120])
    rec(A, "空欄位顯示「還沒填」，不會出現 null／undefined", "還沒填" in t and "null" not in t and "undefined" not in t)
    rec(A, "文字沒有被當成 HTML（dd 裡沒有多出元素）", not await pg.query_selector('.stay-ord dd *'))
    await pg.click('[data-stay-edit]'); await pg.wait_for_timeout(400)
    v = await pg.input_value('[data-stay-form] [data-sos-f=via]'); o = await pg.input_value('[data-stay-form] [data-sos-f=order]')
    rec(A, "編輯表單的值和原本一樣（含引號）", v == 'Tom\'s "Inn"' and o == "A'B<1>", (v, o))
    await pg.click('[data-stay-save]'); await pg.wait_for_timeout(500)
    c = await cloud(pg); s2 = c.get(f"{B}/settings/sos", {})
    rec(A, "沒改就存：雲端內容不變", s2.get("via") == 'Tom\'s "Inn"' and s2.get("order") == "A'B<1>", s2)
    await pg.click('[data-home]') if await pg.query_selector('[data-home]') else None; await pg.wait_for_timeout(600)
    await pg.click('[data-sos] >> nth=0'); await pg.wait_for_timeout(700)
    if await pg.query_selector('[data-sos-tab="emg"]'): await pg.click('[data-sos-tab="emg"]'); await pg.wait_for_timeout(300)
    t2 = await pg.inner_text('.sos')
    rec(A, "求助面板旅平險名稱照原樣顯示 O'Neil", "O'Neil 產險" in t2, t2.replace("\n", " ")[:100])
    rec(A, "沒有 JS 錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def rate(b):
    A = "清理｜CODE-17 匯率邊界"
    for v, ok in ((0.5, True), (0.1, True), (0.50001, False)):
        ctx = await fx.ctx_with(b, er={"result": "success", "rates": {"TWD": v}}, ca={"date": "2026-10-24", "jpy": {"twd": v}})
        a = await phone(ctx, jst(11, 20, 20, 0), "zhang", f"r{v}", url=BASE, wait=1500)
        await fx.settle(a); await fx.acct(a)
        got = await a.input_value('#f-rate')
        rec(A, f"自動抓到 {v}：{'接受（和手動範圍 0.1～0.5 一致）' if ok else '超出範圍不採用'}", (got == f"{v:.4f}".rstrip("0").rstrip(".") or got == f"{v:.4f}") if ok else got != f"{v:.4f}", got)
        await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in (static, escape, rate): await f(b)
        await b.close()
    summary()
asyncio.run(main())
