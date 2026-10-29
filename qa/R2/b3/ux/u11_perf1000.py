# E5：千筆記帳——只記錄數字（不判問題）。首屏、記帳頁出現、記一筆面板開啟、記一筆後清單更新。沙箱效能有限，3 次取值
import time
from uxlib import *
def mkdb(n):
    db = {**META}
    days = ["11/17","11/18","11/19","11/20","11/21","11/22","11/23","11/24"]
    cats = ["food","shop","go","stay","fun","etc"]
    for i in range(n):
        db[f"{B}/expenses/x{i}"] = {"amt": 100 + (i*37) % 9000, "cat": cats[i%6] if cats[i%6] in ("food","shop") else "food", "who": "zhang" if i%2 else "star", "split": "both" if i%3 else "self", "pay": "cash" if i%2 else "card", "day": days[i%8], "note": f"品項{i}", "ts": 1000+i}
    return db
async def poll(pg, js, limit=15000):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < limit/1000:
        if await pg.evaluate(js): return round((time.perf_counter()-t0)*1000)
        await pg.wait_for_timeout(10)
    return None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for n in (0, 1000):
            rows = []
            for r in range(3):
                ctx = await S.mkctx(b)
                pg = await ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)))
                await pg.add_init_script(S.LAUNCHED)
                await pg.add_init_script('try{localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code","qa-r2-test");localStorage.setItem("mockdb",%s)}catch(e){}' % json.dumps(json.dumps(mkdb(n))))
                t0 = time.perf_counter(); await pg.goto("http://localhost:8766/"); gt = round((time.perf_counter()-t0)*1000)
                first = await poll(pg, '!!document.querySelector(".view .hero, .view .sheet")')
                await pg.wait_for_timeout(1500)  # 等同步快照進來
                t1 = time.perf_counter(); await pg.click('nav.tabs button[data-tab=acct]')
                acct = await poll(pg, f'document.querySelectorAll("#acct-list .ex").length>={min(n,1) if n else 0} && !!document.getElementById("acct-list")')
                if n: await poll(pg, f'document.querySelectorAll("#acct-list .ex").length=={n}')
                acct_full = round((time.perf_counter()-t1)*1000)
                await pg.wait_for_timeout(800)
                t2 = time.perf_counter(); await pg.click('[data-exp-new]')
                openp = await poll(pg, '!!document.querySelector(".exp-sheet #f-amt")&&document.activeElement&&document.activeElement.id==="f-amt"')
                await pg.fill('#f-amt', '1234'); await pg.fill('#f-note', '千筆後新增')
                t3 = time.perf_counter(); await pg.click('#f-save')
                upd = await poll(pg, 'document.getElementById("acct-list").innerText.includes("千筆後新增")')
                total = await pg.evaluate('document.querySelector(".total, #acct-sum, .acct-total")?.innerText||""')
                rows.append((first, acct_full, openp, upd))
                print(f"n={n} run{r}: 首屏 {first}ms | 記帳頁清單完整 {acct_full}ms | 記一筆面板開啟(含焦點) {openp}ms | 記下後清單出現 {upd}ms | DOM列={await pg.evaluate('document.querySelectorAll(\"#acct-list .ex\").length')} | errs={len(pg.errs)}")
                rd = await pg.evaluate('(()=>{const t=performance.now();for(let i=0;i<5;i++)renderAcct();return Math.round((performance.now()-t)/5)})()')
                print(f'   goto(load)={gt}ms；renderAcct() 單次主執行緒 {rd}ms（pg.clock 已安裝，performance.now 為假時鐘時此值可能為 0）')
                await ctx.close()
        await b.close()
asyncio.run(main())
