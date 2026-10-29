# R2 批 5 lead：merge 寫入遇到對方已刪除 → 雲端出現只有部分欄位的文件（修法風險，連帶檢查 CODE-04 是否可由介面觸發）
# 情境：B 離線時用「修改」改一筆帳的金額（D8 已經是只寫有改的欄位＋merge）；A 在線上刪掉同一筆；B 上線
import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b3', 'ux'))
from uxlib import *
async def run(b):
    ctx = await newctx(b); T = jst(11, 21, 20)
    e = lambda amt, day, note: {"amt": amt, "cat": "food", "who": "zhang", "split": "both", "pay": "cash", "day": day, "note": note, "ts": 1}
    db = {**META, f"{B}/expenses/e1": e(1200, "11/21", "拉麵"), f"{B}/expenses/e2": e(800, "11/20", "咖啡"), f"{B}/expenses/e3": e(500, "11/19", "飯糰")}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "acct")
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await Bp.click('.ex[data-edit="e1"]'); await Bp.wait_for_timeout(700); await Bp.fill('#f-amt', '1500'); await Bp.click('#f-save'); await Bp.wait_for_timeout(500)
    ob = await Bp.evaluate('outbox["expenses/e1"]||null')
    await A.click('[data-del="e1"]'); await A.wait_for_timeout(800)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    doc = (await cloud(A)).get(f"{B}/expenses/e1")
    rec("部分文件", f"對方刪除後，merge 修改不會在雲端留下殘缺文件（B outbox={ob}）", doc is None, doc)
    for name, pg in (("A", A), ("B", Bp)):
        await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300); await tab(pg, "acct"); await pg.wait_for_timeout(500)
        st = await pg.evaluate('({rows:document.querySelectorAll("#acct-list .ex").length,ghost:expenses.find(e=>e.id==="e1")||null,ghostRow:document.querySelector(\'.ex[data-edit="e1"]\')?.innerText.replace(/\\s+/g," ")||null,sum:document.getElementById("acct-sum")?.innerText.replace(/\\s+/g," ").slice(0,120)})')
        rec("部分文件", f"{name} 記帳頁正常顯示、沒有錯誤", not pg.errs, {**st, "errs": pg.errs[:2]})
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        try: await run(b)
        except Exception as ex: rec("部分文件", "腳本執行", False, repr(ex)[:300])
        await b.close()
    summary()
asyncio.run(main())
