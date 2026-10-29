# lead 重現批 4：CODE-01（scene 注入）、CODE-03（心情 score 不合法）、CODE-05（.sos-show/.story 實際動畫）
import asyncio, sys, json, urllib.parse
sys.path.insert(0, "/home/claude/build/ft")
import os; os.chdir("/home/claude/build/ft")
import synctest as st
from playwright.async_api import async_playwright

T = "2026-11-18T09:00:00+09:00"
async def main():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # CODE-01
        ctx = await st.mkctx(b)
        pay = '"><img src=x onerror="window.__xss=1">'
        pg = await st.opn(ctx, T, url="http://localhost:8766/?scene=" + urllib.parse.quote(pay), wait=1500)
        out["CODE-01 __xss"] = await pg.evaluate("window.__xss||0")
        out["CODE-01 injected img"] = await pg.evaluate('document.querySelectorAll(".hero img[src=x], svg.scene ~ img, img[src=\'x\']").length')
        out["CODE-01 errs"] = pg.errs[:3]
        # 也試一般 scene 值是否正常（對照組）
        pg2 = await st.opn(ctx, T, url="http://localhost:8766/?scene=dinner", wait=1200)
        out["scene=dinner period"] = await pg2.evaluate('document.querySelector("svg.scene")?.dataset.period')
        await ctx.close()
        # CODE-03：雲端有一筆 score:0 的心情
        ctx = await st.mkctx(b)
        db = {st.B + "/moods/11-17_xing": {"score": 0, "note": "x", "ts": 1, "who": "xing", "day": "11/17"}}
        db.update(st.META)
        pg = await st.opn(ctx, T, pre=st.seed(db), wait=2000)
        out["CODE-03 errs"] = pg.errs[:3]
        out["CODE-03 home has mood strip"] = await pg.evaluate('!!document.querySelector(".mood-strip")')
        out["CODE-03 home text len"] = await pg.evaluate('document.getElementById("app")?.innerText.length||0')
        await ctx.close()
        # CODE-05：實際套用的動畫名稱
        ctx = await st.mkctx(b)
        pg = await st.opn(ctx, T)
        out["CODE-05 anim"] = await pg.evaluate('''["sos-show","story","viewer","sheet-modal"].map(c=>{const d=document.createElement("div");d.className=c;document.body.appendChild(d);const s=getComputedStyle(d);const r=c+": "+s.animationName+" "+s.animationDuration;d.remove();return r})''')
        await ctx.close(); await b.close()
    print(json.dumps(out, ensure_ascii=False, indent=1))
asyncio.run(main())
