# 確認 u12「各連記 5 筆少一筆」是假資料庫（localStorage 跨分頁讀改寫）的人為現象，還是 App 的問題：看缺哪一筆、重跑 4 次；並比較兩頁錯開 150ms 的結果
from uxlib import *
async def run(b, stagger):
    ctx = await newctx(b)
    T = jst(11, 19, 20)
    A = await phone(ctx, T, "zhang", "A", init=seed({**META}), wait=1000); Bp = await phone(ctx, T, "star", "B", wait=1000)
    for x in (A, Bp): await tab(x, "acct")
    async def rec5(x, tag, d0=0):
        await x.wait_for_timeout(d0)
        for i in range(5):
            await S.expopen(x); await x.fill('#f-amt', str(100 + i)); await x.fill('#f-note', f'{tag}{i}'); await x.click('#f-save'); await x.wait_for_timeout(120)
    await asyncio.gather(rec5(A, "甲"), rec5(Bp, "乙", stagger)); await A.wait_for_timeout(1000)
    cl = sorted(v["note"] for v in (await exps(A)).values()); la = sorted(await A.evaluate('expenses.map(e=>e.note)')); lb = sorted(await Bp.evaluate('expenses.map(e=>e.note)'))
    miss = [f"{t}{i}" for t in "甲乙" for i in range(5) if f"{t}{i}" not in cl]
    outA = await A.evaluate('Object.keys(outbox).length'); outB = await Bp.evaluate('Object.keys(outbox).length')
    await ctx.close(); return len(cl), miss, (la == cl, lb == cl), (outA, outB)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for st in (0, 0, 0, 0, 37, 37, 37):
            print("stagger", st, await run(b, st))
        await b.close()
asyncio.run(main())
