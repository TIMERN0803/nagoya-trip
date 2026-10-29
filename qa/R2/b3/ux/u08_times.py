# 批 3 指定 6：極端時間（靜態各時間點＋App 開著跨午夜）。phone tz＝Asia/Tokyo 或 Asia/Taipei
from uxlib import *
OBS = '''(()=>{const t=s=>(document.querySelector(s)?.innerText||"").replace(/\\s+/g," ").trim().slice(0,70);
 return{today:todayIdx,dayIdx,tab,view,hero:t(".hero"),cd:!!document.getElementById("cd-s"),story:!!document.querySelector("[data-story-open]"),fab:t(".fab"),now:t(".nowcard"),ox:document.documentElement.scrollWidth<=innerWidth,
 moodStrip:!!document.querySelector(".mood-strip"),scene:document.querySelector(".hero .scene")?.dataset.period||""}})()'''
POINTS = [
 ("11/16 23:59 JST", jst(11,16,23,59), "Asia/Tokyo"), ("11/17 00:00 JST", jst(11,17,0,0), "Asia/Tokyo"), ("11/17 00:00 JST 手機台灣時區", jst(11,17,0,0), "Asia/Taipei"),
 ("11/17 06:00 台灣(=07:00 JST) 手機台灣", twt(11,17,6,0), "Asia/Taipei"), ("11/17 07:06 台灣(起飛後)", twt(11,17,7,6), "Asia/Taipei"),
 ("11/17 23:59 JST", jst(11,17,23,59), "Asia/Tokyo"), ("11/18 00:01 JST", jst(11,18,0,1), "Asia/Tokyo"),
 ("11/24 15:00 JST", jst(11,24,15,0), "Asia/Tokyo"), ("11/24 22:30 JST(台灣 21:30)", jst(11,24,22,30), "Asia/Taipei"), ("11/24 23:59 JST", jst(11,24,23,59), "Asia/Tokyo"),
 ("11/25 00:30 JST(台灣 23:30 還是 11/24)", jst(11,25,0,30), "Asia/Taipei"), ("11/25 10:00 JST", jst(11,25,10,0), "Asia/Tokyo"), ("11/25 10:00 台灣時區", jst(11,25,10,0), "Asia/Taipei"),
 ("12/01 12:00 JST", jst(12,1,12,0), "Asia/Tokyo"), ("12/25 12:00 台灣", twt(12,25,12,0), "Asia/Taipei"), ("2027/01/05 12:00 台灣", __import__('datetime').datetime(2027,1,5,12,tzinfo=__import__('datetime').timezone(__import__('datetime').timedelta(hours=8))), "Asia/Taipei")]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, t, tz in POINTS:
            ctx = await S.mkctx(b, tz=tz)
            pg = await S.opn(ctx, t, init=seed(META), wait=1000)
            o = await pg.evaluate(OBS)
            print(f"{name:40s} err={len(pg.errs)} {o}")
            if pg.errs: print("   ERR:", pg.errs[:2])
            await pg.screenshot(path=SHOTS + 'u08_' + name.split(" ")[0].replace("/", "-") + f'_{tz[-5:]}_{t.strftime("%H%M")}.png')
            # 各分頁都點一遍
            bad = []
            for tb in ["wx", "move", "acct", "list", "plan"]:
                try: await tab(pg, tb)
                except Exception as e: bad.append(tb)
            rec("極端時間", f"{name}：各分頁切換無錯誤", not pg.errs and not bad, (pg.errs + bad)[:2])
            await ctx.close()
        await b.close()
    summary()
asyncio.run(main())
