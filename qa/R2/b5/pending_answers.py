# R2 批 5 lead：用假資料庫回答 Codex 待確認 3（CODE-08 錯誤碼）與 5（首次種資料競態）
# 假資料庫：b5/fs_b5.js（ft/fs_offline.js 加 __reject、__itemsDelay 兩個開關）
# SDK 錯誤碼本身另以 npm 下載 @firebase/firestore 4.6.3（firebase 10.12.2 的相依版本）核對：INVALID_ARGUMENT = "invalid-argument"
import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b3', 'ux'))
from uxlib import *
FSB5 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fs_b5.js')).read()

async def code08(b):
    for code, expect_drop in [("invalid-argument", True), ("invalid_argument", True)]:
        ctx = await S.mkctx(b, fs=FSB5)
        pg = await S.opn(ctx, jst(11, 19, 12), init=seed(META), wait=1200)
        await pg.evaluate(f'window.__reject={json.dumps(code)}')
        await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '500'); await pg.fill('#f-note', '被拒收的帳'); await pg.click('#f-save'); await pg.wait_for_timeout(1200)
        st = await pg.evaluate('({pending:Object.values(outbox).filter(v=>v.d&&v.d.note==="被拒收的帳").length,canWrite})')
        rec("CODE-08", f"伺服器以 {code} 拒收：這筆不留在 outbox 一直重送", st["pending"] == 0, st)
        await ctx.close()

async def seeding(b):
    # 雲端：meta 是舊版（itemsRestore:1），對方把預設行李 k01「護照」改成「護照＋影本」
    srv = {f"{B}/settings/meta": {"itemsSeeded": True, "itemsRestore": 1},
           f"{B}/items/k01": {"group": "pack", "title": "護照＋影本", "note": "", "cat": "doc", "order": 1}}
    for label, delay, restore in [("清單快照 6 秒才到、meta 舊版", 6000, 1), ("對照：清單快照正常（30ms）、meta 舊版", 0, 1), ("對照：快照 6 秒、meta 已是 itemsRestore:2", 6000, 2)]:
        db = {**srv, f"{B}/settings/meta": {"itemsSeeded": True, "itemsRestore": restore}}
        ctx = await S.mkctx(b, fs=FSB5)
        # 新裝置：本機沒有 items（用預設清單）
        pg = await S.opn(ctx, jst(11, 10, 12), init=seed(db), pre=f'window.__itemsDelay={delay};', wait=8000)
        k01 = (await cloud(pg)).get(f"{B}/items/k01", {})
        rec("首次種資料", f"{label}：對方改過的預設行李不被本機預設值蓋回", k01.get("title") == "護照＋影本", k01)
        await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in (code08, seeding):
            try: await f(b)
            except Exception as ex: rec(f.__name__, "腳本執行", False, repr(ex)[:300])
        await b.close()
    summary()
asyncio.run(main())
