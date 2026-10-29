# CODE-11 行為驗證：A 改金額送出，B（暫時收不到 A 的修改）按「隨身」→ A 的金額會不會被蓋回舊值
from uxlib import *
async def run(b, variant):
    ctx = await newctx(b)
    T = jst(11, 21, 20)
    db = {**META, f"{B}/expenses/e1": {"amt": 6000, "cat": "shop", "who": "star", "split": "both", "pay": "card", "day": "11/21", "note": "藥妝", "ts": 1, "tf": True}}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "acct")
    # B 暫時收不到（離線／晚收到）
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    if variant == "amt":
        await A.click('.ex[data-edit="e1"]'); await A.wait_for_timeout(700); await A.fill('#f-amt', '7500'); await A.click('#f-save'); await A.wait_for_timeout(700)
    elif variant == "note":
        await A.click('.ex[data-edit="e1"]'); await A.wait_for_timeout(700); await A.fill('#f-note', '藥妝（A 改的備註）'); await A.click('#f-save'); await A.wait_for_timeout(700)
    e = (await exps(A))["e1"]; print(variant, "A 改完雲端:", e)
    print("B 看到:", (await Bp.evaluate('expenses.find(x=>x.id==="e1")')))
    sel = '[data-carry="e1"]'
    print("B 有退稅清單按鈕:", await Bp.query_selector(sel) is not None)
    await Bp.click(sel); await Bp.wait_for_timeout(300)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1200)
    e2 = (await exps(A))["e1"]; print(variant, "B 隨身 + 上線後雲端:", e2)
    ok = e2.get("amt") == (7500 if variant == "amt" else 6000) and e2.get("carry") is True and (variant != "note" or e2["note"].startswith("藥妝（A"))
    rec("CODE-11", f"{variant}：A 的修改在 B 按隨身後仍保留", ok, e2)
    sa = await A.evaluate('expenses.find(x=>x.id==="e1")'); sb = await Bp.evaluate('expenses.find(x=>x.id==="e1")')
    print("A 畫面:", sa, "\nB 畫面:", sb)
    # 兩人畫面是否一致、A 是否被告知
    print("A 畫面清單:", (await A.inner_text('#acct-list')).replace("\n"," | "))
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for v in ["amt", "note"]: await run(b, v)
        await b.close()
    summary()
asyncio.run(main())
