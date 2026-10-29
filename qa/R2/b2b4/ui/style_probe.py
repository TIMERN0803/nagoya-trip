from common import *
from sweep_ui import DB
JS='''()=>{const res={sos:[],borders:{},pick:[],h:[]};
 for(const e of document.querySelectorAll(".hud-sos,.bar-sos,[data-sos]")){const r=e.getBoundingClientRect();if(!r.width)continue;const cs=getComputedStyle(e);const svg=e.querySelector("svg");res.sos.push({cls:e.className.toString(),h:r.height,w:r.width,color:cs.color,border:cs.borderTopColor,bw:cs.borderTopWidth,shadow:cs.boxShadow,svgc:svg?getComputedStyle(svg).color:null,txt:e.innerText.trim()})}
 for(const e of document.querySelectorAll("body *")){const r=e.getBoundingClientRect();if(!r.width||r.height<30||e.closest("svg"))continue;const cs=getComputedStyle(e);if(parseFloat(cs.borderTopWidth)>=2&&cs.borderTopStyle==="solid"){const k=cs.borderTopColor+" | "+cs.boxShadow.slice(0,60);(res.borders[k]=res.borders[k]||[]).push((e.className||e.tagName).toString().slice(0,18))}}
 for(const k in res.borders){const a=res.borders[k];res.borders[k]=a.length+" x "+[...new Set(a)].slice(0,6).join(",")}
 for(const e of document.querySelectorAll(".pick")){const r=e.getBoundingClientRect();if(!r.width)continue;const cs=getComputedStyle(e);res.pick.push([e.textContent.trim().slice(0,5),e.className.toString(),cs.backgroundColor,cs.borderTopWidth+" "+cs.borderTopColor,cs.color,Math.round(r.height)])}
 return res}'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await mkctx(b); pg=await opn(ctx,ft.jst(11,19,13),init=seed(DB),wait=1100)
        for name,js in [("home",'tab="plan";view="home"'),("day",'tab="plan";view="day";dayIdx=2'),("acct",'tab="acct"'),("list",'tab="list";listSub=null'),("wx",'tab="wx"'),("move",'tab="move"')]:
            await pg.evaluate(js+';render();scrollTo(0,0)'); await pg.wait_for_timeout(800)
            r=await pg.evaluate(JS); print("==",name); print(" sos",r['sos']); 
            for k,v in r['borders'].items(): print("  border",k,"->",v)
        await pg.evaluate('tab="acct";render()'); await pg.wait_for_timeout(700); await pg.click('[data-exp-new]'); await pg.wait_for_timeout(800)
        r=await pg.evaluate(JS); print("== exp sheet picks"); 
        for x in r['pick']: print(" ",x)
        await ctx.close(); await b.close()
asyncio.run(main())
