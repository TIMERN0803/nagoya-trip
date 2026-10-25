# 情境測試：時間 × 時區 × 狀態（首頁、當天行程頁、浮動按鈕、nowcard、提醒）
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
SNAP='''(()=>{const f=document.querySelector(".fab");return {view:document.querySelector(".g-home")?"home":"day "+(document.querySelector(".banner .when")?.textContent||""),
 now:document.querySelector(".nowcard")?.innerText.replace(/\\s+/g," ")||"",
 flags:[...document.querySelectorAll("ol.tl li.item")].map(li=>(li.querySelector(".t")?.innerText||"")+":"+(li.className.match(/s-(\\w+)/)||[,""])[1]).filter(s=>!s.endsWith(":")),
 fab:f.hidden?null:f.innerText.replace(/\\s+/g," ")}})()'''
HOME='''(()=>({hero:document.querySelector(".hero")?.innerText.replace(/\\s+/g," ").slice(0,90),todayTile:[...document.querySelectorAll(".tile.today")].map(t=>t.dataset.day),setup:!!document.querySelector(".setup-entry"),strip:!!document.querySelector(".mood-strip"),review:!!document.querySelector(".rv-ticket"),due:document.querySelector("#due-alerts")?.innerText.replace(/\\s+/g," ")||"",fab:document.querySelector(".fab").hidden?null:document.querySelector(".fab").innerText.replace(/\\s+/g," ")}))()'''
CASES=[
 ("10/25 18:00 TW 剛裝好",q.twt(10,25,18,0),"Asia/Taipei"),
 ("11/16 22:59 TW 出發前一晚",q.twt(11,16,22,59),"Asia/Taipei"),
 ("11/16 23:01 TW（日本已 11/17 00:01）",q.twt(11,16,23,1),"Asia/Taipei"),
 ("11/16 23:59 TW",q.twt(11,16,23,59),"Asia/Taipei"),
 ("11/17 00:01 TW",q.twt(11,17,0,1),"Asia/Taipei"),
 ("11/17 05:30 TW 出門去機場",q.twt(11,17,5,30),"Asia/Taipei"),
 ("11/17 06:10 TW 機場報到",q.twt(11,17,6,10),"Asia/Taipei"),
 ("11/17 06:50 TW 登機口",q.twt(11,17,6,50),"Asia/Taipei"),
 ("11/17 12:00 JST 抵達",q.jst(11,17,12,0),"Asia/Tokyo"),
 ("11/17 17:30 JST 傍晚",q.jst(11,17,17,30),"Asia/Tokyo"),
 ("11/17 21:00 JST 晚餐",q.jst(11,17,21,0),"Asia/Tokyo"),
 ("11/17 22:30 JST 回家",q.jst(11,17,22,30),"Asia/Tokyo"),
 ("11/18 13:00 JST 吉卜力",q.jst(11,18,13,0),"Asia/Tokyo"),
 ("11/18 08:30 JST 去吉卜力途中",q.jst(11,18,8,30),"Asia/Tokyo"),
 ("11/21 21:30 JST 彈性夜晚",q.jst(11,21,21,30),"Asia/Tokyo"),
 ("11/21 22:10 JST",q.jst(11,21,22,10),"Asia/Tokyo"),
 ("11/18 23:59 JST",q.jst(11,18,23,59),"Asia/Tokyo"),
 ("11/19 00:01 JST",q.jst(11,19,0,1),"Asia/Tokyo"),
 ("11/24 07:30 JST 機場",q.jst(11,24,7,30),"Asia/Tokyo"),
 ("11/24 15:00 JST 起飛後",q.jst(11,24,15,0),"Asia/Tokyo"),
 ("11/25 10:00 TW",q.twt(11,25,10,0),"Asia/Taipei"),
 ("12/10 TW",q.twt(12,10,20,0),"Asia/Taipei"),
 ("手機台灣時區 11/18 13:00 JST",q.jst(11,18,13,0),"Asia/Taipei"),
 ("手機台灣時區 11/17 22:30 JST",q.jst(11,17,22,30),"Asia/Taipei"),
 ("手機台灣時區 11/20 07:30 JST（台灣 06:30）",q.jst(11,20,7,30),"Asia/Taipei"),
]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,t,tz in CASES:
            ctx=await q.mkctx(b,tz=tz); pg=await q.page(ctx,t)
            s=await pg.evaluate(SNAP); await q.home(pg); h=await pg.evaluate(HOME)
            q.note("情境",name,{"open":s["view"],"now":s["now"],"flags":s["flags"],"home":h})
            if pg.errs:q.rec("情境",name+" JS 錯誤",False,pg.errs[:3])
            await ctx.close()
        # JX 320 是台灣時間 07:05，但行程頁的狀態用日本時間判斷 → 檢查 11/17 早上 nowcard 是否以台灣時間計算
        for lab,t,real_left in [("TW 05:30",q.twt(11,17,5,30),95),("TW 06:00",q.twt(11,17,6,0),65),("TW 06:30",q.twt(11,17,6,30),35)]:
            ctx=await q.mkctx(b,tz="Asia/Taipei"); pg=await q.page(ctx,t)
            s=await pg.evaluate(SNAP)
            fl=[f for f in s["flags"] if f.startswith("07:05")]
            await q.home(pg); fab=await pg.evaluate('document.querySelector(".fab").hidden?null:document.querySelector(".fab").innerText.replace(/\\s+/g," ")')
            ok=("JX 320" in s["now"]) and (f"{real_left//60} 小時 {real_left%60} 分後" in s["now"] if real_left>=60 else f"{real_left} 分後" in s["now"])
            q.rec("JX320 時區",f"{lab} 去程航班剩 {real_left} 分（nowcard 應以台灣時間計）",ok,{"now":s["now"],"flag":fl,"fab":fab})
            if lab=="TW 06:30": await pg.screenshot(path=q.SHOTS+"time_jx320_0630.png")
            await ctx.close()
        # 跨午夜：11/18 23:59 開著，跑 2 分鐘
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,18,23,59,))
        await q.home(pg); before=await pg.evaluate(HOME)
        await pg.clock.run_for(120000); await pg.wait_for_timeout(1500)
        try:
            s=await pg.evaluate(SNAP); await q.home(pg); after=await pg.evaluate(HOME)
            q.rec("跨午夜","11/18 23:59 開著首頁 → 00:01 自動換成 D3","D3" in (after["hero"] or ""),{"before":before["hero"],"after":after["hero"],"open":s["view"]})
        except Exception as e:q.rec("跨午夜","跨午夜後讀取",False,str(e)[:200])
        await ctx.close()
        # 長時間開著（App 在背景整晚）：11/17 21:00 首頁 → 每 10 分鐘 run_for，直到 11/18 09:00
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,17,21,0)); await q.home(pg)
        seq=[]
        for k in range(72):
            await pg.clock.run_for(600000); 
            if k%6==5:
                await pg.wait_for_timeout(200)
                try:
                    v=await pg.evaluate('({hero:document.querySelector(".hero")?.innerText.replace(/\\s+/g," ").slice(0,40),view:document.querySelector(".g-home")?"home":"day",fab:document.querySelector(".fab").hidden?null:document.querySelector(".fab").innerText.replace(/\\s+/g," "),scene:document.querySelector(".hero .scene")?.dataset.period})')
                except Exception as e:v=str(e)[:60]
                seq.append(((k+1)*10,v))
        q.note("整晚開著","11/17 21:00 起每小時快照",seq)
        await ctx.close()
        q.dump("time")
        await b.close()
asyncio.run(main())
