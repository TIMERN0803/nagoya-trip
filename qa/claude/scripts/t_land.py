import asyncio, qa_common as q
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await q.mkctx(b,vw=844,vh=390,dsf=2); pg=await q.page(ctx,q.jst(11,19,21,0)); await q.home(pg)
        await pg.evaluate('sosShow("hotel")'); await pg.wait_for_timeout(300)
        r=await pg.evaluate('(()=>{const v=document.querySelector(".sos-show");const s=getComputedStyle(v);v.scrollTop=-999;const a=v.scrollTop;v.scrollTop=999;return {ov:s.overflowY,top:Math.round(v.querySelector(".s-lead").getBoundingClientRect().top),canScroll:v.scrollTop!==a,sh:v.scrollHeight,ch:v.clientHeight}})()')
        q.rec("求助","橫向 844×390「給司機看」最上面的日文句「この住所までお願いします。」看得到或捲得到",r["top"]>=0 or (r["canScroll"] and r["ov"] in("auto","scroll")),r)
        await pg.evaluate('document.querySelector(".sos-show").scrollTop=0'); await pg.screenshot(path=q.SHOTS+"sos_hotel_show_landscape.png")
        q.dump("land"); await b.close()
asyncio.run(main())
