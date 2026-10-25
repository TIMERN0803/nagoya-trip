import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-test"
E_=[("food",3200,"zhang","both","cash","11/17","すゞ家"),("move",1800,"star","both","card","11/18","名鐵巴士"),("ticket",7800,"zhang","both","card","11/18","吉卜力公園"),("food",4600,"star","both","cash","11/19","獅子丸"),("shop",13200,"zhang","self","card","11/21","大國藥妝"),("food",8800,"zhang","both","card","11/21","大須鮨"),("shop",8640,"star","self","card","11/22","Mont bell"),("food",2400,"star","both","cash","11/23","桂昇"),("etc",1200,"zhang","both","cash","11/20","扭蛋")]
db={f"{B}/expenses/e{i}":{"amt":a,"cat":c,"who":w,"split":sp,"pay":p,"day":d,"note":n,"ts":i} for i,(c,a,w,sp,p,d,n) in enumerate(E_)}
M={("11-17","zhang"):(4,"名古屋城好大"),("11-17","star"):(4,"味噌豬排好好吃"),("11-18","zhang"):(5,"龍貓巴士超可愛！"),("11-18","star"):(5,"魔女之谷像在電影裡"),("11-19","zhang"):(3,"走好多路"),("11-21","star"):(4,"鰻魚飯讚"),("11-21","zhang"):(4,"")}
for (d,w),(sc,n) in M.items():db[f"{B}/moods/{d}_{w}"]={"score":sc,"note":n,"ts":1,"who":w,"day":d.replace("-","/")}
db[f"{B}/wallet/zhang"]={"cashIn":40000};db[f"{B}/wallet/star"]={"cashIn":30000}
DB=json.dumps(db)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(11,25,20,0),tz="Asia/Taipei",ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        if not await pg.query_selector('.g-home'):await pg.click('[data-home]')
        await pg.wait_for_timeout(800)
        await pg.screenshot(path='/home/claude/build/rv_1.png')
        await pg.evaluate('(()=>{const e=document.getElementById("review");scrollTo(0,e.getBoundingClientRect().top+scrollY-70)})()');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/rv_2.png')
        await pg.evaluate('scrollBy(0,560)');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/rv_3.png')
        print(pg.errs);await b.close()
if __name__=="__main__":asyncio.run(main())
