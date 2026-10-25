import asyncio,datetime
from playwright.async_api import async_playwright
U=datetime.timezone.utc
CASES=[("台灣 10/24 現在",datetime.datetime(2026,10,24,9,0,tzinfo=U),"Asia/Taipei"),
("出發前一晚 11/16 23:00 台灣",datetime.datetime(2026,11,16,15,0,tzinfo=U),"Asia/Taipei"),
("起飛前 11/17 06:30 台灣",datetime.datetime(2026,11,16,22,30,tzinfo=U),"Asia/Taipei"),
("起飛後 11/17 07:06 台灣",datetime.datetime(2026,11,16,23,6,tzinfo=U),"Asia/Taipei"),
("11/17 15:00 日本",datetime.datetime(2026,11,17,6,0,tzinfo=U),"Asia/Tokyo"),
("11/18 23:30 日本",datetime.datetime(2026,11,18,14,30,tzinfo=U),"Asia/Tokyo"),
("11/24 06:00 日本",datetime.datetime(2026,11,23,21,0,tzinfo=U),"Asia/Tokyo"),
("回國 11/24 20:00 台灣",datetime.datetime(2026,11,24,12,0,tzinfo=U),"Asia/Taipei"),
("11/25 台灣",datetime.datetime(2026,11,25,4,0,tzinfo=U),"Asia/Taipei"),
("12/20 台灣",datetime.datetime(2026,12,20,4,0,tzinfo=U),"Asia/Taipei")]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,t,tz in CASES:
            ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id=tz)
            pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.clock.install(time=t)
            await pg.add_init_script('try{localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:tour","1")}catch(e){}')
            await pg.goto('http://localhost:8766/'); await pg.wait_for_timeout(700)
            first=await pg.evaluate('document.querySelector(".hero")?"首頁":"當天行程 "+(document.querySelector(".banner .when")?.textContent||"")')
            if not await pg.query_selector('.hero'):
                await pg.click('[data-home]'); await pg.wait_for_timeout(300)
            hero=await pg.evaluate('(document.querySelector(".hero .cd")?.innerText||document.querySelector(".hero .big")?.innerText||"").replace(/\\s+/g," ")')
            lbl=await pg.evaluate('document.querySelector(".hero .lbl")?.textContent')
            strip=await pg.evaluate('!!document.querySelector(".mood-strip")')
            await pg.click('.tile[data-day="1"]'); await pg.wait_for_timeout(300)
            mood=await pg.evaluate('document.querySelector("#mood")?.classList.contains("locked")?"未開放":"可填"')
            print(f"{name}: 開啟後={first} | 倒數卡={hero} {lbl} | 首頁心情區={strip} | 11/18心情={mood} | 錯誤={errs}")
            await ctx.close()
        await b.close()
asyncio.run(main())
