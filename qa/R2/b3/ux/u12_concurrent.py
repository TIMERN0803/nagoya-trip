# 批 3 必測：兩人同時操作——同時記帳、同時勾同一待辦、同時刪同一筆、同時改同一待辦（含一方暫時收不到）
from uxlib import *
async def view(pg, sel): return (await pg.inner_text(sel)).replace("\n", " | ")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await newctx(b)
        T = jst(11, 19, 20)
        db = {**META, f"{B}/items/t1": {"group": "prep", "title": "換日圓", "note": "原備註", "due": "", "order": 1},
              f"{B}/expenses/d1": {"amt": 800, "cat": "food", "who": "zhang", "split": "both", "pay": "cash", "day": "11/19", "note": "共同刪除", "ts": 5}}
        A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200); Bp = await phone(ctx, T, "star", "B", wait=1200)
        for x in (A, Bp): await tab(x, "acct")
        # 1 同時各記 5 筆
        async def rec5(x, tag):
            for i in range(5):
                await S.expopen(x); await x.fill('#f-amt', str(100 + i)); await x.fill('#f-note', f'{tag}{i}'); await x.click('#f-save'); await x.wait_for_timeout(120)
        await asyncio.gather(rec5(A, "甲"), rec5(Bp, "乙")); await A.wait_for_timeout(900)
        ea, eb = await exps(A), None
        print('A.__writes', await A.evaluate('window.__writes'), 'B.__writes', await Bp.evaluate('window.__writes'), '雲端筆數', len(ea), '缺:', [f'{t}{i}' for t in '甲乙' for i in range(5) if f'{t}{i}' not in [v['note'] for v in ea.values()]])
        la = await A.evaluate('expenses.length'); lb = await Bp.evaluate('expenses.length')
        rec("兩人同時", "各連記 5 筆：雲端 11 筆（含原有 1 筆），兩支手機畫面都是 11 筆", len(ea) == 11 and la == lb == 11, (len(ea), la, lb))
        sa = await A.evaluate('expenses.reduce((s,e)=>s+e.amt,0)'); sb_ = await Bp.evaluate('expenses.reduce((s,e)=>s+e.amt,0)')
        rec("兩人同時", "兩支手機總額一致", sa == sb_, (sa, sb_))
        # 2 同時刪除同一筆
        async def delx(x):
            await x.click('[data-del="d1"]'); await x.wait_for_timeout(200)
            if await x.query_selector('[data-del="d1"]'): await x.click('[data-del="d1"]')
        await asyncio.gather(delx(A), delx(Bp)); await A.wait_for_timeout(700)
        ex = await exps(A); rec("兩人同時", "同時刪除同一筆：雲端沒有、兩邊畫面都沒有、沒有錯誤", "d1" not in ex and not await A.evaluate('expenses.some(e=>e.id==="d1")') and not await Bp.evaluate('expenses.some(e=>e.id==="d1")') and not A.errs and not Bp.errs, (A.errs + Bp.errs)[:2])
        # 兩邊都有復原條：A 復原、B 也復原
        await A.click('.undo-bar button'); await A.wait_for_timeout(600)
        print("A 復原後 B 的畫面有 d1:", await Bp.evaluate('expenses.some(e=>e.id==="d1")'), "| B 復原條還在:", await Bp.query_selector('.undo-bar') is not None)
        await Bp.click('.undo-bar button'); await Bp.wait_for_timeout(600)
        n = sum(1 for k in (await exps(A)) if k == "d1"); rec("兩人同時", "A、B 都按復原：雲端仍只有 1 筆 d1", n == 1 and await A.evaluate('expenses.filter(e=>e.id==="d1").length') == 1, n)
        # 3 同時勾同一待辦
        for x in (A, Bp): await tab(x, "list")
        async def chk(x):
            await x.evaluate('document.querySelector("#c-t1").click()')
        await asyncio.gather(chk(A), chk(Bp)); await A.wait_for_timeout(800)
        sa = await A.evaluate('done.t1===true'); sb_ = await Bp.evaluate('done.t1===true'); cl = (await cloud(A)).get(f"{B}/checks/t1")
        print("同時勾 → A 畫面", sa, "B 畫面", sb_, "雲端", cl)
        rec("兩人同時", "同時按同一待辦（各自本地先反轉）：兩支手機最後一致", sa == sb_ == ((cl or {}).get("done") is True), (sa, sb_, cl))
        # 4 同時改同一待辦：A 改標題、B（暫時收不到）改備註
        await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(100)
        await A.click('[data-item-edit="t1"]'); await A.wait_for_timeout(300); await A.fill('.chk-form input[name=title]', 'A 改的標題'); await A.click('.chk-form .primary'); await A.wait_for_timeout(600)
        await Bp.click('[data-item-edit="t1"]'); await Bp.wait_for_timeout(300); await Bp.fill('.chk-form input[name=note]', 'B 改的備註'); await Bp.click('.chk-form .primary'); await Bp.wait_for_timeout(400)
        await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1200)
        it = (await items_cloud(A))["t1"]
        print("待辦同時改（B 離線改備註、A 改標題）→ 雲端:", it, "| A 畫面:", await A.evaluate('items.find(x=>x.id==="t1")?.title+"/"+items.find(x=>x.id==="t1")?.note'), "| B 畫面:", await Bp.evaluate('items.find(x=>x.id==="t1")?.title+"/"+items.find(x=>x.id==="t1")?.note'))
        rec("兩人同時", "A 改待辦標題、B（暫時收不到）改同一待辦備註：兩個修改都保留（記帳有 D8，待辦沒有）", it.get("title") == "A 改的標題" and it.get("note") == "B 改的備註", it)
        rec("兩人同時", "沒有錯誤", not A.errs and not Bp.errs, (A.errs + Bp.errs)[:3])
        await ctx.close(); await b.close()
    summary()
asyncio.run(main())
