from common import *
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await mkctx(b); pg=await opn(ctx, ft.jst(11,19,13))
        await pg.evaluate('tab="plan";view="day";dayIdx=2;render();scrollTo(0,0)'); await pg.wait_for_timeout(800)
        await pg.evaluate('''window.__o=[];window.open=(...a)=>{__o.push(a[0]);return null};
          document.addEventListener("click",e=>{const a=e.target.closest&&e.target.closest(".leg a");if(a){e.preventDefault();__o.push("A-click:"+a.getAttribute("href"))}},true)''')
        for idx in [0,1]:
            for off in [-4,-3,-1,0.5,20,39,41,42,43,44,46,50,60]:
                await pg.evaluate('(i)=>document.querySelectorAll(".leg a")[i].scrollIntoView({block:"center"})',idx); await pg.wait_for_timeout(120)
                R=await pg.evaluate('(i)=>{const r=document.querySelectorAll(".leg a")[i].getBoundingClientRect();return [r.left,r.top]}',idx)
                x=R[0]+20;y=R[1]+off
                await pg.evaluate('window.__o=[]')
                el=await pg.evaluate('([x,y])=>{const h=document.elementFromPoint(x,y);return h?(h.className||h.tagName)+"":""}',[x,y])
                await pg.mouse.click(x,y); await pg.wait_for_timeout(60)
                o=await pg.evaluate('window.__o')
                print(f"leg{idx} y=top{off:+}: elementFromPoint={el[:20]!r} -> {o}")
        await ctx.close(); await b.close()
asyncio.run(main())
