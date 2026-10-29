# B5：減少動態時開場動畫何時消失
from uxlib import *
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for rm in ('reduce', 'no-preference'):
            ctx = await b.new_context(viewport={'width':390,'height':844}, reduced_motion=rm, service_workers='block')
            for pat in ["**/*.googleapis.com/**","**/firebasejs/**","**/api.open-meteo.com/**","**/open.er-api.com/**"]: await ctx.route(pat, lambda r: r.abort())
            pg = await ctx.new_page(); await pg.goto("http://localhost:8766/", wait_until="commit")
            for i in range(60):
                has = await pg.evaluate('!!document.getElementById("splash")')
                if not has and i > 1: print(rm, "splash 消失於約", i*50, "ms"); break
                await pg.wait_for_timeout(50)
            await ctx.close()
        await b.close()
asyncio.run(main())
