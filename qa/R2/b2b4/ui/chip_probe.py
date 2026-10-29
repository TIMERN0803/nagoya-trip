from common import *
JS='''()=>{const out=[];for(const e of document.querySelectorAll("a,button")){const t=(e.innerText||"").trim();if(!/^(VJW|填寫教學)$/.test(t))continue;const r=e.getBoundingClientRect();const cs=getComputedStyle(e);const b=getComputedStyle(e,"::before");
 const cx=r.left+r.width/2;let up=0,dn=0;for(let d=0;d<60;d++){const h=document.elementFromPoint(cx,r.top-d);if(h&&(h===e||e.contains(h)))up=d;const g=document.elementFromPoint(cx,r.bottom+d-0.01);if(g&&(g===e||e.contains(g)))dn=d}
 out.push({t,cls:e.className,h:r.height,w:r.width,top:r.top,bg:cs.backgroundColor,before:[b.content,b.height,b.top,b.transform],hitUp:up,hitDown:dn,total:r.height+up+dn,parent:e.parentElement.className})}return out}'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for w,hh in [(390,844),(375,812),(430,932)]:
            ctx=await mkctx(b,tz="Asia/Taipei"); pg=await opn(ctx, ft.twt(10,30,20)); await pg.set_viewport_size({"width":w,"height":hh})
            await pg.evaluate('tab="list";listTab="prep";render();scrollTo(0,0)'); await pg.wait_for_timeout(800)
            r=await pg.evaluate(JS); print(w,"list/prep",r)
            if w==390:
                await pg.evaluate('document.querySelector(".chip")?.scrollIntoView({block:"center"})'); await pg.wait_for_timeout(200)
                await pg.screenshot(path=OUT+f'chips_list_{w}.png')
            # setup sheet
            await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(700)
            if await pg.query_selector('[data-setup-open]'):
                await pg.click('[data-setup-open]'); await pg.wait_for_timeout(700)
                r=await pg.evaluate(JS); print(w,"setup sheet",r)
                await pg.screenshot(path=OUT+f'setup_sheet_{w}.png')
            await ctx.close()
        await b.close()
asyncio.run(main())
