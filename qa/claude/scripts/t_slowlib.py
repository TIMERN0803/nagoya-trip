# 網路很慢：Firebase 程式庫晚 N 秒才載入完成（例如日本街頭訊號差、剛開 App）
# 在這段時間內的操作（db 還是 null）會不會在連上之後被雲端蓋掉？
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for delay in [4000, 12000]:
            gate=asyncio.Event()
            ctx=await q.mkctx(b)
            async def slow(r, body):
                await gate.wait()
                await r.fulfill(body=body,content_type="text/javascript",headers={"access-control-allow-origin":"*"})
            await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:asyncio.ensure_future(slow(r,q.ft.APP)))
            await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:asyncio.ensure_future(slow(r,q.ft.FS)))
            seed={f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2},f"{B}/items/p1":{"group":"prep","title":"換日圓","note":"","due":"","order":1},
                  f"{B}/items/b1":{"group":"buy","title":"ういろう","note":"","due":"","order":101},f"{B}/wallet/zhang":{"cashIn":20000,"ts":1},
                  f"{B}/expenses/old":{"amt":1000,"cat":"food","who":"star","split":"both","pay":"card","day":"11/18","note":"星星昨天記的","ts":1}}
            # 先在有網路時用過一次（本機有快取），再「慢網路」重開
            pg0=await ctx.new_page(); await pg0.clock.install(time=q.jst(11,19,9,0))
            gate.set()
            await pg0.add_init_script('try{if(!sessionStorage.getItem("s")){localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code","%s");localStorage.setItem("mockdb",%s);sessionStorage.setItem("s",1)}}catch(e){}'%(q.CODE,json.dumps(json.dumps(seed))))
            await pg0.goto('http://localhost:8766/'); await pg0.wait_for_timeout(1500); await pg0.close()
            gate.clear()
            pg=await ctx.new_page(); pg.errs=[]; pg.on('pageerror',lambda e:pg.errs.append(str(e)))
            await pg.clock.install(time=q.jst(11,19,20,0)); await pg.goto('http://localhost:8766/'); await pg.wait_for_timeout(600)
            await q.tab(pg,"list"); s0=await pg.evaluate('document.querySelector(".sync,#code-form")?.innerText.replace(/\\s+/g," ")')
            await pg.screenshot(path=q.SHOTS+f"slowlib_{delay}_list.png")
            await pg.check('#c-p1'); await pg.wait_for_timeout(100)
            await pg.click('[data-item-new="buy"]'); await pg.fill('.chk-form input[name=title]','慢網路時新增'); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(200)
            await q.tab(pg,"acct"); await pg.fill('#f-amt','2200'); await pg.fill('#f-note','慢網路記帳'); await pg.click('#f-save'); await pg.wait_for_timeout(200)
            await pg.click('.wchip'); await pg.wait_for_timeout(200)
            if await pg.locator('.ws [data-wallet-edit][data-mode="add"]').count(): await pg.click('.ws [data-wallet-edit][data-mode="add"]')
            await pg.fill('.ws .w-form input','10000'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(200); await pg.click('.ws .sm-x')
            await pg.evaluate('tab="plan";view="day";dayIdx=todayIdx;render()'); await pg.wait_for_timeout(200)
            await pg.click('#mood .fbtn[data-score="5"]'); await pg.fill('#mood-note','慢網路心情'); await pg.click('#mood-form .primary'); await pg.wait_for_timeout(200)
            before=await pg.evaluate('({done:done.p1===true,item:items.some(x=>x.title==="慢網路時新增"),exp:expenses.some(e=>e.note==="慢網路記帳"),oldExp:expenses.some(e=>e.id==="old"),wallet:cashIn("zhang"),mood:!!moods["11-19_zhang"]})')
            # 網路終於通了
            gate.set(); await pg.wait_for_timeout(3000)
            # 對方此時新增一筆（觸發一次 items 快照）
            await pg.evaluate('db&&db.collection("items").doc().set({group:"buy",title:"對方新增",order:999})'); await pg.wait_for_timeout(800)
            after=await pg.evaluate('({live,done:done.p1===true,item:items.some(x=>x.title==="慢網路時新增"),exp:expenses.some(e=>e.note==="慢網路記帳"),wallet:cashIn("zhang"),mood:!!moods["11-19_zhang"]})')
            srv=await q.mock(pg,"")
            cloud={"勾選":(srv.get(f"{B}/checks/p1") or {}).get("done"),"要買":any(v.get("title")=="慢網路時新增" for k,v in srv.items() if "/items/" in k),
                   "記帳":any(v.get("note")=="慢網路記帳" for k,v in srv.items() if "/expenses/" in k),"錢包":(srv.get(f"{B}/wallet/zhang") or {}).get("cashIn"),"心情":f"{B}/moods/11-19_zhang" in srv}
            q.note("慢網路",f"程式庫延遲 {delay/1000:.0f} 秒：載入前清單頁狀態",s0)
            q.note("慢網路",f"延遲 {delay/1000:.0f} 秒：載入前本機看到昨天星星記的帳嗎",before["oldExp"])
            for k,bk,ck,exp in [("勾選待辦","done","勾選",True),("新增要買","item","要買",True),("記帳","exp","記帳",True),("錢包補錢","wallet","錢包",30000),("心情","mood","心情",True)]:
                ok=after[bk]==exp and cloud[ck]==exp
                q.rec("慢網路",f"延遲 {delay/1000:.0f} 秒：連線前的「{k}」連上後仍在畫面且已上傳",ok,{"連線前畫面":before[bk],"連線後畫面":after[bk],"雲端":cloud[ck]})
            await q.tab(pg,"list"); await pg.screenshot(path=q.SHOTS+f"slowlib_{delay}_after.png")
            await ctx.close()
        q.dump("slowlib"); await b.close()
asyncio.run(main())
