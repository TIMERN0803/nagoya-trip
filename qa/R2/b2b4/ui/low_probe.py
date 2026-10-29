from common import *
from sweep_ui import DB,M
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await mkctx(b); pg=await opn(ctx,ft.jst(11,19,13),init=seed(DB),wait=1100)
        await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(600)
        await pg.click('[data-cal]'); await pg.wait_for_timeout(800)
        m=await pg.evaluate("("+M+")()"); print(m['low'])
        print(await pg.evaluate('''()=>[...document.querySelectorAll(".sm-card small, .sm-card em")].slice(0,6).map(e=>{const c=getComputedStyle(e);return [e.tagName,e.textContent.slice(0,12),c.color,c.opacity,getComputedStyle(e.closest("[class*=cal],button,a,div")).backgroundColor,c.fontSize]})'''))
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
        await ctx.close()
        ctx=await mkctx(b,tz="Asia/Taipei"); pg=await opn(ctx,ft.twt(11,25,10),init=seed(DB),wait=1100)
        await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(600)
        await pg.click('[data-story-open]'); await pg.wait_for_timeout(900)
        print(await pg.evaluate('''()=>{const e=document.querySelector(".st-cap");const c=getComputedStyle(e);let p=e,bgs=[];for(;p;p=p.parentElement){const s=getComputedStyle(p);bgs.push([p.className.toString().slice(0,15),s.backgroundColor,s.backgroundImage.slice(0,40),s.opacity])}return [c.color,c.opacity,c.fontSize,bgs.slice(0,5)]}'''))
        await ctx.close(); await b.close()
asyncio.run(main())
