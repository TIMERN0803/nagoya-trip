from common import *
import datetime as dt
B_=S.B
DB={**S.META, f"{B_}/wallet/zhang":{"cashIn":30000,"ts":1},
 f"{B_}/expenses/e1":{"amt":1280,"cat":"food","who":"zhang","split":"both","pay":"cash","day":"11/17","note":"すゞ家 鰻魚飯","ts":5},
 f"{B_}/expenses/e2":{"amt":4500,"cat":"buy","who":"star","split":"both","pay":"card","day":"11/18","note":"伴手禮","ts":6}}
M=open(OUT+'metrics.js').read()
def jst(m,d,h,mi=0):return ft.jst(m,d,h,mi)
def twt(m,d,h,mi=0):return ft.twt(m,d,h,mi)
POINTS=[("pre_1030_2000",twt(10,30,20),"Asia/Taipei"),("pre_1116_2100",twt(11,16,21),"Asia/Taipei"),("d1117_0600tw",twt(11,17,6),"Asia/Taipei")]
for d in range(17,24):
    for h in (8,13,18,22):
        if d==17 and h==8: h=9
        POINTS.append((f"d11{d}_{h:02d}00",jst(11,d,h),"Asia/Tokyo"))
POINTS+= [("d1124_0800",jst(11,24,8),"Asia/Tokyo"),("d1124_2359tw",twt(11,24,23,59),"Asia/Taipei"),("d1125_tw",twt(11,25,10),"Asia/Taipei")]
async def main():
    W=int(sys.argv[1]) if len(sys.argv)>1 else 390; H={375:812,390:844,430:932}[W]
    only=sys.argv[2].split(',') if len(sys.argv)>2 else None
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,t,tz in POINTS:
            if only and name not in only: continue
            ctx=await mkctx(b,tz=tz); pg=await opn(ctx,t,init=seed(DB),wait=1100); await pg.set_viewport_size({"width":W,"height":H}); await pg.wait_for_timeout(500)
            what=await pg.evaluate('(document.querySelector(".hero")?"home":"day")+" | "+(document.querySelector(".hero .lbl")?.textContent||document.querySelector(".banner .when")?.textContent||"")')
            await pg.screenshot(path=OUT+f'fs_{W}_{name}.png')
            m=await pg.evaluate("("+M+")()")
            print(name,what,"| sw",m['sw'],"| low",m['low'][:5],"| small",m['small'][:3],"| trunc",m['trunc'][:3],"| hscroll",m['hscroll'][:2],"| errs",pg.errs[:1],flush=True)
            await ctx.close()
        await b.close()
if __name__=="__main__": asyncio.run(main())
