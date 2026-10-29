from common import *
import panels as P
from panels import shot,close_top,metr,W,H
B_=S.B
EMPTY={**S.META}
FULL={**S.META, f"{B_}/wallet/zhang":{"cashIn":30000,"ts":1},f"{B_}/wallet/star":{"cashIn":20000,"ts":1}}
exps={}
cats=["food","buy","trans","ticket","stay","other"]
import random;random.seed(3)
for i in range(14):
    exps[f"{B_}/expenses/x{i}"]={"amt":random.choice([380,1280,4500,12000,860]),"cat":cats[i%6],"who":["zhang","star"][i%2],"split":"both","pay":["cash","card"][i%2],"day":f"11/{17+i%7}","note":["すゞ家 鰻魚飯","超長店名的味噌炸豬排專賣店名古屋本店分店","","伴手禮"][i%4],"ts":10+i}
FULL.update(exps)
MOODS={f"{B_}/moods/11-17_zhang":{"score":5,"note":"飛機餐超好吃","ts":1},f"{B_}/moods/11-17_star":{"score":4,"note":"","ts":2},f"{B_}/moods/11-18_zhang":{"score":3,"note":"走好多路，腳好痠，但是吉卜力很值得，下次還要再來一次","ts":3}}
FULL.update(MOODS)
async def run(b,label,t,tz,db,steps,fresh=False):
    ctx=await mkctx(b,tz=tz); pg=await opn(ctx,t,init=seed(db),wait=1100); await pg.set_viewport_size({"width":W,"height":H})
    for name,js,sel in steps:
        try:
            await pg.evaluate(js); await pg.wait_for_timeout(600)
            if sel: await pg.click(sel)
            await shot(pg,f"{label}_{name}")
        except Exception as e: print("ERR",label,name,str(e)[:120])
        await close_top(pg)
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # real default seeded items: no META
        await run(b,"seed1913",ft.jst(11,19,13),"Asia/Tokyo",{},[
          ("list_prep",'tab="list";listTab="prep";listSub=null;render()',None),
          ("list_buy",'tab="list";listTab="buy";listSub=null;render()',None),
          ("pack",'tab="list";listSub="pack";render()',None),
          ("home",'tab="plan";view="home";render()',None)])
        await run(b,"empty1913",ft.jst(11,19,13),"Asia/Tokyo",EMPTY,[
          ("acct",'tab="acct";render()',None),("home",'tab="plan";view="home";render()',None)])
        await run(b,"full1913",ft.jst(11,19,20),"Asia/Tokyo",FULL,[
          ("home",'tab="plan";view="home";render()',None),
          ("acct",'tab="acct";render()',None),
          ("sync",'tab="acct";render()','[data-sync-info]'),
          ("home_scroll",'tab="plan";view="home";render();window.scrollTo(0,600)',None),
          ("day_mood",'tab="plan";view="day";dayIdx=2;render();document.querySelector("#mood")?.scrollIntoView({block:"center"})',None),
          ("sosdrv",'tab="plan";view="home";render()','[data-sos]'),
        ])
        await run(b,"rv2359",ft.twt(11,24,23,59),"Asia/Taipei",FULL,[
          ("home",'tab="plan";view="home";render()',None),
          ("story",'tab="plan";view="home";render()','[data-story-open]'),
          ("story2",'document.querySelector(".st-cap")?.click?.()',None)])
        await b.close()
if __name__=="__main__": asyncio.run(main())
