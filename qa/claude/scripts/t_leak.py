# 隔離：哪一種面板開關會讓 JSEventListeners 增加
import asyncio, qa_common as q
from playwright.async_api import async_playwright
CASES={"求助":'openSos();document.querySelector(".sheet-modal .sm-x").click()',
"錢包":'openWallet();document.querySelector(".sheet-modal .sm-x").click()',
"行事曆":'openCalSheet();document.querySelector(".sheet-modal .sm-x").click()',
"出發前設定":'openSetup();document.querySelector(".sheet-modal .sm-x").click()',
"地圖檢視器":'openViewer("ghibli-map.jpg","x");document.querySelector(".viewer:not(.out) .vclose").click()',
"給司機看":'sosShow("hotel");document.querySelector(".sos-show .sm-x").click()',
"回顧故事":'openStory();document.querySelector(".story .st-x").click()',
"首頁重畫":'render(true)'}
async def gc(pg):
    c=await pg.context.new_cdp_session(pg); await c.send("HeapProfiler.collectGarbage"); await c.detach()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,js in CASES.items():
            ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,10,12,0) if name!="回顧故事" else q.jst(11,26,12,0)); await q.home(pg)
            await pg.wait_for_timeout(400); await gc(pg); m0=await q.metrics(pg)
            for i in range(30): await pg.evaluate(js)
            await pg.wait_for_timeout(500); await gc(pg); m1=await q.metrics(pg)
            q.rec("listener 洩漏",f"{name} 開關 30 次：listeners {m0['listeners']}→{m1['listeners']}，nodes {m0['nodes']}→{m1['nodes']}",m1['listeners']-m0['listeners']<=5)
            await ctx.close()
        q.dump("leak"); await b.close()
asyncio.run(main())
