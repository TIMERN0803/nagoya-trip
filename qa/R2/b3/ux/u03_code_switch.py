# CODE-10 行為驗證：有未同步的寫入時開 #k=另一個代碼 連結，舊寫入會不會送進新旅程
from uxlib import *
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await newctx(b)
        T = jst(11, 19, 20)
        pg = await S.opn(ctx, T, init=seed({**META}), wait=1200)
        await tab(pg, "acct")
        await pg.evaluate('__goOffline()'); await ctx.set_offline(True); await pg.evaluate('dispatchEvent(new Event("offline"))'); await pg.wait_for_timeout(300)
        await S.expopen(pg); await pg.fill('#f-amt', '3300'); await pg.fill('#f-note', '舊旅程離線記的'); await pg.click('#f-save'); await pg.wait_for_timeout(500)
        print("outbox:", await pg.evaluate('Object.keys(outbox)'), "pending:", await pg.evaluate('pendingCount()'))
        # 同步膠囊：有未同步時是否擋換代碼
        await pg.click('[data-sync-info]'); await pg.wait_for_timeout(300)
        print("點膠囊:", (await pg.inner_text('#code-info')).replace("\n"," | ") if await pg.query_selector('#code-info') else "(無)")
        await pg.close()
        await ctx.set_offline(False)
        # 使用者網路恢復後點到對方傳來的連結（另一個旅程代碼）
        pg2 = await S.opn(ctx, T, init='', url="http://localhost:8766/#k=qa-r2-other", pre='localStorage.removeItem("mocknet");', wait=1500)
        await pg2.evaluate('window.__goOnline&&__goOnline()'); await pg2.wait_for_timeout(2000)
        print("新頁面代碼:", await pg2.evaluate('localStorage.getItem("ngy:code")'), "pending:", await pg2.evaluate('pendingCount()'), "live:", await pg2.evaluate('live'))
        db = await cloud(pg2)
        old = [k for k, v in db.items() if "/expenses/" in k and v.get("note") == "舊旅程離線記的"]
        print("含該筆的路徑:", old)
        in_new = any(k.startswith("trips/qa-r2-other/") for k in old); in_old = any(k.startswith(B + "/") for k in old)
        print("新旅程裡看得到:", await pg2.evaluate('expenses.map(e=>e.note)'))
        rec("CODE-10", "舊旅程的離線記帳被送進新旅程（預期不該）", in_new, old)
        rec("CODE-10", "舊旅程也有（SDK 層持久化）", in_old, old)
        # 提示：新旅程是否有任何警告
        print("新旅程頁面訊息:", (await pg2.evaluate('document.body.innerText')).replace("\n"," ")[:200])
        await pg2.screenshot(path=SHOTS + 'u03_switch.png')
        await b.close()
    summary()
asyncio.run(main())
