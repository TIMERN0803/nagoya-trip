from common import *
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await mkctx(b); pg=await opn(ctx, ft.jst(11,19,13))
        await pg.evaluate('tab="plan";view="day";'); 
        print(await pg.evaluate('typeof render+" "+(typeof day)+" "+(typeof view)'))
        # find day page
        await pg.click('[data-home]') if await pg.query_selector('[data-home]') else None
        await pg.wait_for_timeout(300)
        print(await pg.evaluate('document.body.className+" | "+[...document.querySelectorAll("[data-day]")].length'))
        await pg.screenshot(path=OUT+'probe_home.png')
        await ctx.close(); await b.close()
asyncio.run(main())
