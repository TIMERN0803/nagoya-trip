# 程式庫已在快取（載入很快），但手機訊號差：connect() 裡的 getDocFromServer 要等 N 秒才回應／失敗。
# 這段期間 db 還是 null，使用者的操作只存在本機；連上後會不會被雲端快照蓋掉？
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
FSO=open("/home/claude/qa/scripts/fs_offline.js").read()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for delay in [3000,10000]:
            ctx=await q.mkctx(b,fs=FSO)
            seed={f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2},f"{B}/items/p1":{"group":"prep","title":"換日圓","note":"","due":"","order":1},f"{B}/wallet/zhang":{"cashIn":20000,"ts":1}}
            pg=await q.page(ctx,q.jst(11,19,9,0),init=q.seed(seed)); await pg.wait_for_timeout(1200); await pg.close()
            pg=await ctx.new_page(); pg.errs=[]
            await pg.add_init_script(f'window.__serverDelay={delay};')
            await pg.clock.install(time=q.jst(11,19,20,0)); await pg.goto('http://localhost:8766/'); await pg.wait_for_timeout(500)
            await q.tab(pg,"list"); s0=await pg.evaluate('document.querySelector(".sync,#code-form")?.innerText.replace(/\\s+/g," ")')
            await pg.check('#c-p1')
            await pg.click('[data-item-new="buy"]'); await pg.fill('.chk-form input[name=title]','訊號差時新增'); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(150)
            await pg.click('.wchip') if await pg.query_selector('.wchip') else None
            await q.tab(pg,"acct"); await pg.click('.wchip'); await pg.wait_for_timeout(150)
            if await pg.locator('.ws [data-wallet-edit][data-mode="add"]').count(): await pg.click('.ws [data-wallet-edit][data-mode="add"]')
            await pg.fill('.ws .w-form input','10000'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(150); await pg.click('.ws .sm-x')
            el=await pg.evaluate('performance.now()')
            await pg.wait_for_timeout(delay+2500)
            after=await pg.evaluate('({live,done:done.p1===true,item:items.some(x=>x.title==="訊號差時新增"),wallet:cashIn("zhang")})')
            srv=await q.mock(pg,"")
            cloud={"done":(srv.get(f"{B}/checks/p1") or {}).get("done"),"item":any(v.get("title")=="訊號差時新增" for k,v in srv.items() if "/items/" in k),"wallet":(srv.get(f"{B}/wallet/zhang") or {}).get("cashIn")}
            q.note("訊號差",f"server 延遲 {delay/1000:.0f}s：開啟後清單頁狀態",s0)
            q.rec("訊號差",f"server 延遲 {delay/1000:.0f}s：連線前勾的待辦，連上後仍勾著且已上傳",after["done"] and cloud["done"]==True,{"畫面":after["done"],"雲端":cloud["done"]})
            q.rec("訊號差",f"server 延遲 {delay/1000:.0f}s：連線前新增的要買，連上後仍在且已上傳",after["item"] and cloud["item"],{"畫面":after["item"],"雲端":cloud["item"]})
            q.rec("訊號差",f"server 延遲 {delay/1000:.0f}s：連線前補的錢（20000+10000），連上後仍是 30000",after["wallet"]==30000 and cloud["wallet"]==30000,{"畫面":after["wallet"],"雲端":cloud["wallet"]})
            await ctx.close()
        q.dump("slowserver"); await b.close()
asyncio.run(main())
