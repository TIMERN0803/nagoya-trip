import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
base="trips/neko-test"
BUY=[("b1","伴手禮（小倉山莊、砂糖樹）","📍高島屋"),("b2","妙香園（抹茶）","📍名鐵 Sun Road 🍵常磐の昔、初昔"),("b3","升半（抹茶）","🍵芳明の白"),("b4","新樂園（抹茶）","📍榮"),("b5","藥妝店 大國藥妝","📍榮"),("imvmfj2qv","Mont bell（星星爸羽絨外套）","📍榮")]
srv={f"{base}/items/{k}":{"group":"buy","title":t,"note":n,"order":100+i} for i,(k,t,n) in enumerate(BUY)}
srv[f"{base}/settings/meta"]={"itemsSeeded":True,"itemsRestore":2}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(10,25,10),ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(json.dumps(srv))});')
        await pg.wait_for_timeout(800)
        hud=await pg.evaluate('document.querySelector(".hud-row").innerText.replace(/\\s+/g," ")')
        ft.rec("要買的","首頁順序：待辦、要買的、花費",hud.startswith("0 / 0 0 / 6"),hud)
        await pg.evaluate('scrollTo(0,0)');await pg.screenshot(path='/home/claude/build/buy_home.png',clip={'x':0,'y':0,'width':390,'height':200})
        await pg.click('.hp-buy');await pg.wait_for_timeout(700)
        top=await pg.evaluate('Math.round(document.querySelector("[data-group-id=buy]").getBoundingClientRect().top)')
        ft.rec("要買的","點了直接定錨到要買的區塊",60<top<200,top)
        await pg.screenshot(path='/home/claude/build/buy_anchor.png')
        rows=await pg.evaluate('[...document.querySelectorAll("[data-group-id=buy] .chk-row")].map(r=>[...r.querySelectorAll(".bi-row")].map(x=>x.className.split(" ")[1]+":"+x.innerText.trim()).join(" | "))')
        ft.rec("要買的","舊備註自動拆成地點和品項",rows[1]=="bi-place:名鐵 Sun Road | bi-what:常磐の昔、初昔" and rows[2]=="bi-what:芳明の白" and rows[0]=="bi-place:高島屋",rows[:3])
        href=await pg.evaluate('document.querySelector(".bi-place").href')
        ft.rec("要買的","地點可以點開 Google 地圖","google.com/maps" in href and "%E9%AB%98%E5%B3%B6%E5%B1%8B" in href,href)
        await pg.screenshot(path='/home/claude/build/buy_list.png')
        await pg.click('[data-item-edit="b2"]');await pg.wait_for_timeout(300)
        v=await pg.evaluate('[document.querySelector("[name=place]").value,document.querySelector("[name=what]").value]')
        ft.rec("要買的","編輯時帶入拆好的地點和品項",v==["名鐵 Sun Road","常磐の昔、初昔"],v)
        await pg.evaluate('document.querySelector(".chk.editing").scrollIntoView({block:"center"})');await pg.screenshot(path='/home/claude/build/buy_form.png')
        await pg.fill('[name=what]','常磐の昔、初昔、抹茶粉');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
        d=await pg.evaluate(f'JSON.parse(localStorage.getItem("mockdb"))["{base}/items/b2"]')
        ft.rec("要買的","儲存成獨立欄位",d.get("place")=="名鐵 Sun Road" and d.get("what")=="常磐の昔、初昔、抹茶粉" and d.get("note")=="",d)
        await pg.click('[data-item-new="buy"]');await pg.fill('.chk-form input[name=title]','白色戀人');await pg.fill('[name=place]','中部國際機場');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
        txt=await pg.evaluate('[...document.querySelectorAll("[data-group-id=buy] .chk-row")].pop().innerText.replace(/\\s+/g," ")')
        ft.rec("要買的","新增時只填地點也正常顯示","中部國際機場" in txt,txt)
        ft.rec("要買的","沒有錯誤",not pg.errs,pg.errs[:2])
        await b.close()
if __name__=="__main__":asyncio.run(main())
