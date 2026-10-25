import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-test"
PREP=[("mu","💉打疫苗","提升保護力⬆️","11/02",2),("kiso","🥖搶 KISO 號碼牌","選 8:00–8:45","11/20 20:00",3),("seat2","💺回程線上選位","JX 321","11/22 11:40",4),("imvnbc3k4","💺去程線上選位","JX 320","11/15 07:05",5)]
db={f"{B}/items/{i}":{"group":"prep","title":t,"note":n,"due":d,"links":None,"order":o} for i,t,n,d,o in PREP}
BUY=[("b1","伴手禮（小倉山莊、砂糖樹）","名鐵百貨、高島屋","",1),("b2","妙香園（抹茶）","名鐵 Sun Road","常磐の昔、初昔",2),("b3","升半（抹茶）","","芳明の白",3),("b4","新樂園（抹茶）","榮","",4),("b5","藥妝店 大國藥妝","榮","",5),("imvmfj2qv","Mont bell（星星爸羽絨外套）","","",6)]
for i,t,pl,wh,o in BUY:db[f"{B}/items/{i}"]={"group":"buy","title":t,"note":"","place":pl,"what":wh,"due":"","links":None,"order":o}
db[f"{B}/settings/meta"]={"itemsSeeded":True,"itemsRestore":2}
DB=json.dumps(db)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(10,25,12,30),tz="Asia/Taipei",ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(600)
        async def top():await pg.evaluate('(()=>{const g=document.querySelector("[data-group-id=prep]");scrollTo(0,g.getBoundingClientRect().top+scrollY-80)})()');await pg.wait_for_timeout(300)
        await top();await pg.screenshot(path='/home/claude/build/sort_1.png')
        await pg.click('[data-sort-toggle=prep]');await pg.wait_for_timeout(400);await top()
        await pg.screenshot(path='/home/claude/build/sort_2.png')
        h=await pg.query_selector('[data-sort-id="imvnbc3k4"] .drag-h');bb=await h.bounding_box();x,y=bb['x']+22,bb['y']+22
        await pg.mouse.move(x,y);await pg.mouse.down()
        for k in range(1,9):await pg.mouse.move(x,y-k*28)
        await pg.wait_for_timeout(250);await pg.screenshot(path='/home/claude/build/sort_3.png')
        for k in range(9,13):await pg.mouse.move(x,y-k*28)
        await pg.mouse.up();await pg.wait_for_timeout(200);await pg.screenshot(path='/home/claude/build/sort_4.png')
        await pg.click('[data-sort-toggle=prep]');await pg.wait_for_timeout(400);await top()
        await pg.screenshot(path='/home/claude/build/sort_5.png')
        async def btop():await pg.evaluate('(()=>{const g=document.querySelector("[data-group-id=buy]");scrollTo(0,g.getBoundingClientRect().top+scrollY-80)})()');await pg.wait_for_timeout(300)
        await btop();await pg.screenshot(path='/home/claude/build/bsort_1.png')
        await pg.click('[data-sort-toggle=buy]');await pg.wait_for_timeout(400);await btop()
        await pg.screenshot(path='/home/claude/build/bsort_2.png')
        h=await pg.query_selector('[data-sort-id="imvmfj2qv"] .drag-h');bb=await h.bounding_box();x,y=bb['x']+22,bb['y']+22
        await pg.mouse.move(x,y);await pg.mouse.down()
        for k in range(1,12):await pg.mouse.move(x,y-k*30)
        await pg.wait_for_timeout(250);await pg.screenshot(path='/home/claude/build/bsort_3.png')
        for k in range(12,17):await pg.mouse.move(x,y-k*30)
        await pg.mouse.up();await pg.wait_for_timeout(200)
        await pg.click('[data-sort-toggle=buy]');await pg.wait_for_timeout(400);await btop()
        await pg.screenshot(path='/home/claude/build/bsort_4.png')
        print(pg.errs);await b.close()
asyncio.run(main())
