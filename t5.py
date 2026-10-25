import asyncio,json
from playwright.async_api import async_playwright
APP=open('/home/claude/build/mock/app.js').read();FS=open('/home/claude/build/mock/fs.js').read()
async def run(b,label,server,local_items=None):
    ctx=await b.new_context(viewport={'width':390,'height':844})
    await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    init='try{if(!sessionStorage.getItem("s")){localStorage.clear();localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:code","neko-test");localStorage.setItem("mockdb",%s);%s sessionStorage.setItem("s",1)}}catch(e){}'%(json.dumps(json.dumps(server)),('localStorage.setItem("ngy:items",%s);'%json.dumps(json.dumps(local_items))) if local_items is not None else '')
    await pg.add_init_script(init)
    await pg.goto('http://localhost:8766/'); await pg.wait_for_timeout(1500)
    srv=await pg.evaluate('Object.keys(JSON.parse(localStorage.getItem("mockdb"))).filter(k=>k.includes("/items/")).length')
    await pg.click('nav.tabs button[data-tab="list"]'); await pg.wait_for_timeout(300)
    shown=await pg.evaluate('document.querySelectorAll(".chk-row").length')
    await pg.click('[data-item-new="buy"]'); await pg.fill('.chk-form input[name=title]','測試新增'); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(500)
    shown2=await pg.evaluate('document.querySelectorAll(".chk-row").length')
    srv2=await pg.evaluate('Object.keys(JSON.parse(localStorage.getItem("mockdb"))).filter(k=>k.includes("/items/")).length')
    print(f"{label}: 開啟後 伺服器 {srv} 項／畫面 {shown} 項 → 新增一項後 伺服器 {srv2} 項／畫面 {shown2} 項 {errs}")
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        base="trips/neko-test"
        await run(b,"重現：伺服器只有同行者新增的 1 項",{f"{base}/items/i1":{"group":"buy","title":"同行者新增","note":"","due":"","order":200}},local_items=[])
        await run(b,"伺服器有 1 項但已標記上傳過",{f"{base}/items/i1":{"group":"buy","title":"同行者新增","note":"","due":"","order":200},f"{base}/settings/meta":{"itemsSeeded":True}},local_items=[])
        await run(b,"全新：伺服器空的",{})
        await run(b,"已修好後再開：使用者刪掉 1 項不會被加回",{**{f"{base}/items/{k}":{"group":"prep","title":k,"order":i} for i,k in enumerate(["vjw","seat1","mu","kiso","b1","b2","b3","b4","b5"])},f"{base}/settings/meta":{"itemsSeeded":True,"itemsRestore":1}})
        await b.close()
asyncio.run(main())
