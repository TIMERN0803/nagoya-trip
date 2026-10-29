from common import *
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await mkctx(b); pg=await opn(ctx,ft.jst(11,19,13))
        r=await pg.evaluate('''()=>{const cs=getComputedStyle(document.documentElement);const names=[];for(const s of document.styleSheets){try{for(const r of s.cssRules){if(r.selectorText===":root"){for(const n of r.style)if(n.startsWith("--"))names.push(n)}}}catch(e){}}return [...new Set(names)].map(n=>[n,cs.getPropertyValue(n).trim()])}''')
        for n,v in r: print(n,v)
        print(await pg.evaluate('getComputedStyle(document.body).backgroundColor'))
        await ctx.close(); await b.close()
asyncio.run(main())
