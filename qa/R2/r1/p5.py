import asyncio,sys
sys.path.insert(0,'/home/claude/qa/scripts')
import qa_common as q
from playwright.async_api import async_playwright
JS='''(()=>{const out=[];
for(const b of document.querySelectorAll("button,a")){if((b.innerText||"").trim()!=="送出")continue;const cs=getComputedStyle(b);out.push({k:"送出",dis:b.disabled,color:cs.color,bg:cs.backgroundColor,cls:b.className})}
for(const a of document.querySelectorAll("a.chip, .leg a, a[href*='maps/dir']")){const r=a.getBoundingClientRect();if(!r.width)continue;
 const hit=["::before","::after"].map(p=>{const s=getComputedStyle(a,p);return s.content!=="none"?{p,pos:s.position,inset:s.inset,top:s.top,bottom:s.bottom,h:s.height,minH:s.minHeight}:null}).filter(Boolean);
 // 實際點得到的範圍：從元素中心往上下探測
 const cx=r.x+r.width/2;let up=0,dn=0;for(let d=0;d<30;d++){const e=document.elementFromPoint(cx,r.top-d);if(e&&(e===a||a.contains(e)))up=d;else break}
 for(let d=0;d<30;d++){const e=document.elementFromPoint(cx,r.bottom+d);if(e&&(e===a||a.contains(e)))dn=d;else break}
 out.push({k:(a.innerText||"").trim().slice(0,12),w:Math.round(r.width),h:Math.round(r.height),hitH:Math.round(r.height)+up+dn,pseudo:hit})}
return out})()'''
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for t in (q.jst(11,19,12,0), q.twt(11,10,20,0)):
      ctx=await q.mkctx(b); pg=await q.page(ctx,t); await pg.wait_for_timeout(500)
      for view in ("home","day"):
        if view=="day":
          await pg.evaluate('document.querySelector("[data-day]")?.click()'); await pg.wait_for_timeout(800)
        r=await pg.evaluate(JS); seen=set()
        for x in r:
          key=x["k"]
          if key in seen: continue
          seen.add(key); print(t.isoformat()[:16],view,x,flush=True)
      await ctx.close()
    await b.close()
asyncio.run(main())
