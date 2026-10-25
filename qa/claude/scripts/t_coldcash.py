# 冷啟動時（同步還沒連上／程式庫載入失敗）記帳頁與現金餘額顯示什麼
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        st={"mode":"mock"}; ctx=await q.mkctx(b,firebase=st)
        seed={f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2},f"{B}/wallet/zhang":{"cashIn":30000,"ts":1},
              **{f"{B}/expenses/e{i}":{"amt":4000,"cat":"food","who":"zhang","split":"both","pay":"cash","day":"11/18","note":f"現金{i}","ts":i} for i in range(5)}}
        pg=await q.page(ctx,q.jst(11,19,9,0),init=q.seed(seed)); await pg.wait_for_timeout(1200); await q.tab(pg,"acct")
        online={"chip":await pg.inner_text('.wchip'),"total":(await pg.inner_text('#acct-sum')).split("\n")[1]}
        await pg.close(); st["mode"]="abort"
        pg=await ctx.new_page(); await pg.clock.install(time=q.jst(11,19,20,0)); await pg.goto('http://localhost:8766/'); await pg.wait_for_timeout(1500)
        await q.home(pg); hp=await pg.evaluate('document.querySelector(".hp-yen")?.innerText')
        await q.tab(pg,"acct")
        off={"chip":await pg.inner_text('.wchip'),"total":(await pg.inner_text('#acct-sum')).split("\n")[1],"list":(await pg.inner_text('#acct-list'))[:40],"首頁":hp}
        await pg.screenshot(path=q.SHOTS+"offline_acct_coldstart_cash.png")
        q.rec("離線冷啟動","程式庫載入失敗時，現金餘額仍應是 ¥10,000（30000−5×4000），不應顯示 ¥30,000",("¥10,000" in off["chip"]),{"連線時":online,"離線開啟":off})
        q.rec("離線冷啟動","程式庫載入失敗時，記帳頁仍看得到之前的帳",("現金" in off["list"]),off["list"])
        q.dump("coldcash"); await b.close()
asyncio.run(main())
