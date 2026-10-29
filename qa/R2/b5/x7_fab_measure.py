# X7／A12 浮動鈕量測：390／375／430 寬，(1) 首頁 11/19 日本 20:00「8 天的地點」今天那格 (2) 記帳頁最後一筆的「刪除」
# 捲到底時用 elementFromPoint 看該元素的中心與四角是不是浮動鈕；另掃捲動途中（每 40px）有沒有被蓋到。只量、不改。
import os, sys, json, asyncio
sys.path.insert(0, '/home/claude/build/ft'); os.chdir('/home/claude/build/ft')
from phonelib import *
import reviewshot as rs
BASE = os.environ.get('BASE', 'http://localhost:8766/')
RVDB = json.loads(rs.DB.replace('trips/neko-test', B))
PROBE = '''(([sel,fabSel])=>{const el=document.querySelector(sel),fab=document.querySelector(fabSel);if(!el)return {err:"no target"};
 const r=el.getBoundingClientRect(),pts=[[r.left+r.width/2,r.top+r.height/2],[r.left+3,r.top+3],[r.right-3,r.top+3],[r.left+3,r.bottom-3],[r.right-3,r.bottom-3]];
 const hit=pts.map(([x,y])=>{if(y<0||y>innerHeight)return "off";const e=document.elementFromPoint(x,y);return fab&&e&&fab.contains(e)?"FAB":"ok"});
 const f=fab&&fab.getBoundingClientRect();return {hit,center:hit[0],any:hit.includes("FAB"),el:[Math.round(r.top),Math.round(r.bottom)],fab:f&&[Math.round(f.top),Math.round(f.bottom),Math.round(f.left),Math.round(f.right)],vh:innerHeight}})'''
async def measure(pg, sel, fab):
    await pg.evaluate('scrollTo(0,document.documentElement.scrollHeight)'); await pg.wait_for_timeout(400)
    bottom = await pg.evaluate(PROBE, [sel, fab])
    H = await pg.evaluate('document.documentElement.scrollHeight-innerHeight'); mid = []
    for y in range(0, H + 1, 40):
        await pg.evaluate(f'scrollTo(0,{y})'); await pg.wait_for_timeout(30)
        r = await pg.evaluate(PROBE, [sel, fab])
        if r.get('any'): mid.append(y)
    return bottom, mid
async def main():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (390, 375, 430):
            ctx = await newctx(b)
            pg = await phone(ctx, jst(11, 19, 20), "zhang", f"m{w}", init=seed({**META, **RVDB}), url=BASE, wait=1300)
            await pg.set_viewport_size({'width': w, 'height': 844}); await pg.wait_for_timeout(400)
            await pg.evaluate('document.querySelector("nav.tabs button[data-tab=plan]").click()'); await pg.wait_for_timeout(300)
            if await pg.query_selector('[data-home]'): await pg.click('[data-home]'); await pg.wait_for_timeout(800)
            home_b, home_mid = await measure(pg, '.tile.today', '.fab')
            await pg.screenshot(path=SHOTS + f'x7_fab_home_{w}.png')
            await tab(pg, "acct"); await pg.wait_for_timeout(500)
            last = await pg.evaluate('(()=>{const a=[...document.querySelectorAll("#acct-list [data-del]")];const e=a[a.length-1];e.id="__last_del";return e.dataset.del})()')
            acct_b, acct_mid = await measure(pg, '#__last_del', '.acct-fab')
            await pg.screenshot(path=SHOTS + f'x7_fab_acct_{w}.png')
            out[w] = {"home_today_tile_bottom": home_b, "home_scroll_covered_at": home_mid, "acct_last_del_bottom": acct_b, "acct_scroll_covered_at": acct_mid, "errs": pg.errs[:2]}
            await ctx.close()
        await b.close()
    for w, o in out.items():
        print(w, "首頁今天格 捲到底:", {k: o["home_today_tile_bottom"].get(k) for k in ("hit", "el", "fab")}, "捲動途中被蓋 scrollY:", o["home_scroll_covered_at"])
        print(w, "記帳最後一筆刪除 捲到底:", {k: o["acct_last_del_bottom"].get(k) for k in ("hit", "el", "fab")}, "捲動途中被蓋 scrollY:", o["acct_scroll_covered_at"], o["errs"])
asyncio.run(main())
