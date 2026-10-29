from common import *
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await mkctx(b); pg=await opn(ctx, ft.jst(11,19,13))
        await pg.evaluate('tab="plan";view="day";dayIdx=2;render();scrollTo(0,0)'); await pg.wait_for_timeout(800)
        legs=await pg.evaluate('''()=>[...document.querySelectorAll(".leg a")].map((a,i)=>{const r=a.getBoundingClientRect();const cs=getComputedStyle(a,"::before");return {i,top:r.top+scrollY,h:r.height,w:r.width,bh:cs.height,btop:cs.top,tf:cs.transform}})''')
        print(len(legs),legs[:3])
        await pg.screenshot(path=OUT+'legs_390.png',full_page=True)
        res=[]
        for i in range(len(legs)):
            await pg.evaluate('(i)=>{const a=document.querySelectorAll(".leg a")[i];a.scrollIntoView({block:"center"})}',i); await pg.wait_for_timeout(150)
            r=await pg.evaluate('''(i)=>{const a=document.querySelectorAll(".leg a")[i];const R=a.getBoundingClientRect();const cx=R.left+Math.min(R.width/2,30);
              const hits=[];for(let y=Math.floor(R.top)-26;y<=Math.ceil(R.bottom)+26;y++){const h=document.elementFromPoint(cx,y);const own=h&&(h===a||a.contains(h));hits.push([y-R.top,own?"A":(h?(h.className||h.tagName).toString().slice(0,18):"-")])}
              // compress
              const own=hits.filter(x=>x[1]==="A").map(x=>x[0]);
              const below=hits.filter(x=>x[0]>=R.height).map(x=>x[1]);
              return {h:R.height,ownMin:Math.min(...own),ownMax:Math.max(...own),belowFirst:hits.filter(x=>x[0]>=R.height).slice(0,6)}}''',i)
            res.append(r)
        for i,r in enumerate(res): print(i,r)
        await ctx.close(); await b.close()
asyncio.run(main())
