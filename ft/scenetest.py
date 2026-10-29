# 首頁插圖網址參數 ?scene=（R2 批 4 CODE-01）：只接受五個時段名稱，其他值忽略、不會被寫進 HTML
# 一律假資料庫（synctest.mkctx）；出發前直接看首頁、旅途中切回首頁各測一次
import asyncio, json, urllib.parse
import synctest as st
from playwright.async_api import async_playwright
R = []
def rec(ok, name, info=""):
    R.append(ok); print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + str(info)), flush=True)

PAYS = ['"><img src=x onerror="window.__xss=1">',
        "x\" onload=\"window.__xss=1",
        "<svg onload=window.__xss=1>",
        "javascript:window.__xss=1"]
Q = '({p:document.querySelector(".hero svg.scene")?.dataset.period, x:window.__xss||0, img:document.querySelectorAll(".scene-wrap img").length, hero:!!document.querySelector(".hero")})'
HOURS = {"morning": 8, "noon": 12, "afternoon": 15, "dinner": 18, "night": 23}

async def home(ctx, t, url, trip):
    pg = await st.opn(ctx, t, pre=st.seed(st.META), url=url, wait=1500)
    if trip:
        await pg.evaluate('tab="plan";view="home";render(true)'); await pg.wait_for_timeout(700)
    return pg

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await st.mkctx(b)
        for label, t, trip in [("出發前", "2026-10-30T10:00:00+08:00", False), ("旅途中", "2026-11-18T09:00:00+09:00", True)]:
            # 五個合法值照網址顯示
            for k in HOURS:
                pg = await home(ctx, t, "http://localhost:8766/?scene=" + k, trip)
                r = await pg.evaluate(Q); rec(r["p"] == k and not pg.errs, f"{label} ?scene={k} 顯示對應插圖", r); await pg.close()
            # 不合法值：不執行、不插入元素、插圖退回目前時段
            now = await home(ctx, t, "http://localhost:8766/", trip)
            want = (await now.evaluate(Q))["p"]; await now.close()
            for pay in PAYS + ["Night", "evening", ""]:
                pg = await home(ctx, t, "http://localhost:8766/?scene=" + urllib.parse.quote(pay), trip)
                await pg.wait_for_timeout(300)
                r = await pg.evaluate(Q)
                rec(r["x"] == 0 and r["img"] == 0 and r["hero"] and r["p"] == want and not pg.errs,
                    f"{label} ?scene={pay[:24]!r} 忽略，顯示目前時段 {want}", r)
                await pg.close()
        await ctx.close(); await b.close()
    print(f"\n{sum(R)}/{len(R)} passed")
asyncio.run(main())
