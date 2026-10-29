# R2 批 5 lead 重現：Codex 二次審查補的 CX-01～07（Codex 只有靜態推導）
# 一律假資料庫（ft/fs_offline.js）；測試代碼 qa-r2-test／qa-r2-other。
# 「兩支手機」沿用 b3/ux/uxlib.py：同一個 context 兩個頁面，ngy:* 的 localStorage 分開，假資料庫共用。
# rec(...) 的「通過」＝App 行為正確；FAIL＝Codex 說的問題重現成立。
# 執行：cd /home/claude/build/ft && python3 /home/claude/nagoya-tools/qa/R2/b5/cx_repro.py [cx01 cx02 ...]
import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b3', 'ux'))
from uxlib import *

async def go_day_with_stay(pg):
    """切到有住宿卡（訂房資料）的那一天"""
    n = await pg.evaluate('DAYS.length')
    for i in range(n):
        await pg.evaluate(f'tab="plan";view="day";dayIdx={i};stayEditing=false;render(true)'); await pg.wait_for_timeout(150)
        if await pg.query_selector('[data-stay-edit]'): return i
    return -1

# ---------- CX-01：排序把整筆舊資料批次送出 ----------
async def cx01(b):
    ctx = await newctx(b); T = jst(11, 18, 10)
    db = {**META, f"{B}/items/t1": {"group": "prep", "title": "換日圓", "note": "原備註", "due": "", "order": 1},
          f"{B}/items/t2": {"group": "prep", "title": "買網卡", "note": "", "due": "", "order": 2}}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "list")
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    # A 改 t1 標題（A 在線上，雲端已經是新標題）
    await A.click('[data-item-edit="t1"]'); await A.wait_for_timeout(300)
    await A.fill('.chk-form input[name=title]', 'A 改的標題'); await A.click('.chk-form .primary'); await A.wait_for_timeout(700)
    c0 = (await items_cloud(A))["t1"]["title"]
    # B（還沒收到）用鍵盤把 t2 往上移一格
    await Bp.click('[data-sort-toggle="prep"]'); await Bp.wait_for_timeout(400)
    await Bp.focus('[data-sort-id="t2"] .drag-h'); await Bp.keyboard.press("ArrowUp"); await Bp.wait_for_timeout(400)
    ob = await Bp.evaluate('outbox["items/t1"]||null')
    rec("CX-01", "B 排序只送 order，不帶 t1 的舊標題", not (ob and (ob.get("d") or {}).get("title") == "換日圓"), ob)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    it = await items_cloud(A)
    rec("CX-01", f"B 上線後 A 改的標題保留（B 上線前雲端={c0}）", it["t1"].get("title") == "A 改的標題", {k: (v.get("title"), v.get("order")) for k, v in it.items()})
    rec("CX-01", "排序本身有生效（t2 在前）", it["t2"].get("order") == 1 and it["t1"].get("order") == 2, None)
    rec("CX-01", "A 畫面也是 A 改的標題", "A 改的標題" in await A.evaluate('document.body.innerText'), None)
    await ctx.close()

# ---------- CX-02：訂房與旅平險共用 settings/sos，整筆寫入 ----------
SOS0 = {"order": "OLD-1", "via": "平台甲", "room": "雙床房", "ins": "舊保險公司", "insTel": "0800-000-000"}
async def cx02(b):
    # (a) 不同區塊：B 離線改訂房，A 在線上改旅平險 → B 上線後 A 的旅平險被蓋回
    ctx = await newctx(b); T = jst(11, 18, 10)
    A = await phone(ctx, T, "zhang", "A", init=seed({**META, f"{B}/settings/sos": SOS0}), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await A.click('[data-sos]'); await A.wait_for_timeout(700)
    await A.click('[data-sos-tab="emg"]'); await A.wait_for_timeout(300)
    await A.click('[data-sos-edit]'); await A.wait_for_timeout(300)
    await A.fill('[data-sos-f="insTel"]', '0800-111-111'); await A.click('[data-sos-save]'); await A.wait_for_timeout(700)
    c0 = (await cloud(A)).get(f"{B}/settings/sos", {}).get("insTel")
    di = await go_day_with_stay(Bp)
    await Bp.click('[data-stay-edit]'); await Bp.wait_for_timeout(300)
    await Bp.fill('[data-stay-form] [data-sos-f="room"]', '雙人房（加床）'); await Bp.click('[data-stay-save]'); await Bp.wait_for_timeout(400)
    ob = await Bp.evaluate('outbox["settings/sos"]||null')
    rec("CX-02a", f"B 改訂房的 outbox 不帶旅平險舊值（住宿卡在第 {di+1} 天）", not (ob and (ob.get("d") or {}).get("insTel") == "0800-000-000"), ob)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    s = (await cloud(A)).get(f"{B}/settings/sos", {})
    rec("CX-02a", f"B 上線後 A 改的旅平險保留（上線前雲端={c0}）", s.get("insTel") == "0800-111-111" and s.get("room") == "雙人房（加床）", s)
    await ctx.close()
    # (b) 同一區、兩支都在線上：B 先打開訂房表單，A 改訂單編號並存，B 再改房型存 → A 的訂單編號被表單舊值蓋回
    ctx = await newctx(b)
    A = await phone(ctx, T, "zhang", "A", init=seed({**META, f"{B}/settings/sos": SOS0}), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    await go_day_with_stay(A); await go_day_with_stay(Bp)
    await Bp.click('[data-stay-edit]'); await Bp.wait_for_timeout(300)
    await A.click('[data-stay-edit]'); await A.wait_for_timeout(300)
    await A.fill('[data-stay-form] [data-sos-f="order"]', 'NEW-2'); await A.click('[data-stay-save]'); await A.wait_for_timeout(800)
    seen = await Bp.evaluate('sosInfo.order')
    await Bp.fill('[data-stay-form] [data-sos-f="room"]', '雙人房（加床）'); await Bp.click('[data-stay-save]'); await Bp.wait_for_timeout(800)
    s = (await cloud(A)).get(f"{B}/settings/sos", {})
    rec("CX-02b", f"兩支在線上：B 存房型後 A 改的訂單編號保留（B 已收到快照 sosInfo.order={seen}）", s.get("order") == "NEW-2", s)
    await ctx.close()

# ---------- CX-03：倒數歸零的 reload 沒看草稿 ----------
# 錢包膠囊只在記帳分頁（倒數只在首頁），所以用首頁可開的「求助 → 修改旅平險」表單當草稿
async def cx03(b):
    for label, to in [("跨過 0 點、到起飛時間（11/17 日本 08:06）", jst(11, 17, 8, 6)),
                      ("對照：只跨過 0 點（11/17 日本 07:00，還沒起飛）", jst(11, 17, 7, 0))]:
        ctx = await newctx(b)
        pg = await S.opn(ctx, jst(11, 16, 23, 58), init=seed(META), wait=1200)
        await pg.evaluate('tab="plan";view="home";render(true)'); await pg.wait_for_timeout(300)
        has_cd = await pg.evaluate('!!document.getElementById("cd-s")')
        await pg.click('[data-sos]'); await pg.wait_for_timeout(700)
        await pg.click('[data-sos-tab="emg"]'); await pg.wait_for_timeout(300)
        await pg.click('[data-sos-edit]'); await pg.wait_for_timeout(300)
        await pg.fill('[data-sos-f="insTel"]', '0800-123-456')   # 焦點留在有值的輸入框
        await pg.evaluate('window.__mark=1')
        await pg.clock.set_system_time(to); await pg.wait_for_timeout(2500)
        await pg.evaluate('dayCheck()')  # 30 秒計時器也會呼叫；焦點在有值的輸入框所以不重載
        await pg.wait_for_timeout(500)
        st = await pg.evaluate('({reloaded:!window.__mark,ins:document.querySelector("[data-sos-f=insTel]")?.value||"",sosEditing:typeof sosEditing!=="undefined"&&sosEditing})')
        rec("CX-03", f"{label}：首頁有倒數 {has_cd}，旅平險草稿保留不重載", (not st["reloaded"]) and st["ins"] == "0800-123-456", st)
        await ctx.close()

# ---------- CX-04：第一次設定錢包時，reloadSoon 看不到草稿 ----------
async def cx04(b):
    for label, prep in [("第一次設定錢包（walletEdit 是 null）", None), ("對照：已設定錢包、按「補錢」", "add")]:
        lib = {"mode": "abort"}
        ctx = await S.mkctx(b, fs=FSO, lib=lib)
        db = {**META} if not prep else {**META, f"{B}/wallet/zhang": {"cashIn": 20000, "ts": 1}}
        pg = await S.opn(ctx, jst(11, 19, 20), init=seed(db) + ('localStorage.setItem("ngy:wallet",%s);' % json.dumps(json.dumps({"zhang": {"cashIn": 20000, "ts": 1}})) if prep else ''), wait=1500)
        live0 = await pg.evaluate('live')
        await tab(pg, "acct")
        await pg.click('[data-wallet-open]'); await pg.wait_for_timeout(700)
        if prep: await pg.click('[data-wallet-edit][data-mode="add"]'); await pg.wait_for_timeout(300)
        await pg.fill('.w-form input[name=amt]', '30000')
        await pg.evaluate('document.activeElement.blur()')   # 收起鍵盤
        await pg.evaluate('window.__mark=1')
        lib["mode"] = "mock"; await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(3000)
        st = await pg.evaluate('({reloaded:!window.__mark,live,amt:document.querySelector(".w-form input[name=amt]")?.value??null,busy:busyEditing(),walletEdit})')
        rec("CX-04", f"{label}：程式庫恢復時不重新整理、金額還在（開啟時 live={live0}）", not st["reloaded"] and st["amt"] == "30000", st)
        await ctx.close()

# ---------- CX-05：對方記一筆／改錢包時，錢包面板整個重畫、金額清空 ----------
async def cx05(b):
    for label, how in [("對方記一筆帳（expenses 快照）", "exp"), ("對方改自己的錢包（wallet 快照）", "wallet"), ("第一次設定、對方記一筆", "first")]:
        ctx = await newctx(b); T = jst(11, 19, 12)
        w = {} if how == "first" else {f"{B}/wallet/zhang": {"cashIn": 20000, "ts": 1}}
        A = await phone(ctx, T, "zhang", "A", init=seed({**META, **w, f"{B}/wallet/star": {"cashIn": 10000, "ts": 1}}), wait=1200)
        Bp = await phone(ctx, T, "star", "B", wait=1200)
        await tab(A, "acct")
        await A.click('[data-wallet-open]'); await A.wait_for_timeout(700)
        if how != "first": await A.click('[data-wallet-edit][data-mode="add"]'); await A.wait_for_timeout(300)
        await A.fill('.w-form input[name=amt]', '5000')
        if how == "wallet":
            await Bp.evaluate('saveWallet("star",15000)')   # 等同 B 在自己的錢包按「補錢」存檔
        else:
            await tab(Bp, "acct"); await S.expopen(Bp); await Bp.fill('#f-amt', '800'); await Bp.fill('#f-note', '咖啡'); await Bp.click('#f-save')
        await A.wait_for_timeout(1200)
        st = await A.evaluate('({amt:document.querySelector(".w-form input[name=amt]")?.value??null,focus:document.activeElement?.name||document.activeElement?.tagName,walletEdit})')
        rec("CX-05", f"{label}：A 正在填的錢包金額保留", st["amt"] == "5000", st)
        await ctx.close()

# ---------- CX-06：權限錯誤清掉代碼後輸入另一個代碼，佇列送進新旅程 ----------
OTHER = "qa-r2-other"
async def cx06(b):
    ctx = await newctx(b); T = jst(11, 19, 12)
    db = {**META, f"trips/{OTHER}/settings/meta": {"itemsSeeded": True, "itemsRestore": 2}}
    pg = await S.opn(ctx, T, init=seed(db) + f'localStorage.setItem("ngy:code","{S.CODE}");', pre="", wait=1200)
    await pg.evaluate('window.__deny=1')
    await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '1234'); await pg.fill('#f-note', '舊旅程的帳'); await pg.click('#f-save'); await pg.wait_for_timeout(1200)
    st = await pg.evaluate('({code:localStorage.getItem("ngy:code"),syncMsg,live,pending:Object.keys(outbox).length})')
    await pg.evaluate('window.__deny=0')
    await tab(pg, "list"); await pg.fill('#f-code', OTHER); await pg.click('#code-form .primary'); await pg.wait_for_timeout(2000)
    c = await cloud(pg)
    landed = [k for k, v in c.items() if "/expenses/" in k and v.get("note") == "舊旅程的帳"]
    rec("CX-06", f"權限錯誤後（{st}）輸入另一個代碼，舊佇列不會送進 {OTHER}", not any(OTHER in k for k in landed), landed)
    await ctx.close()

# ---------- CX-07：自動匯率請求還沒回來時改手動，舊回應把模式寫回自動 ----------
async def cx07(b):
    ctx = await newctx(b); T = jst(11, 19, 12)
    gate = asyncio.Event()
    async def slow(r):
        await gate.wait()
        await r.fulfill(body=json.dumps({"result": "success", "rates": {"TWD": 0.2111}}), content_type="application/json", headers={"access-control-allow-origin": "*"})
    await ctx.route("**/open.er-api.com/**", lambda r: asyncio.ensure_future(slow(r)))
    db = {**META, f"{B}/settings/rate": {"jpyTwd": 0.2, "auto": True, "ts": 1, "src": "ExchangeRate-API"}}
    pg = await S.opn(ctx, T, init=seed(db), wait=1200)
    await tab(pg, "acct"); await pg.wait_for_timeout(2500)   # 開啟 2.5 秒後 fetchRate（資料超過 6 小時）
    busy = await pg.evaluate('rateBusy')
    await pg.evaluate('(()=>{const i=document.getElementById("f-rate");i.value="0.3";i.dispatchEvent(new Event("change",{bubbles:true}))})()')
    await pg.wait_for_timeout(500)
    mid = (await cloud(pg)).get(f"{B}/settings/rate")
    gate.set(); await pg.wait_for_timeout(1500)
    st = await pg.evaluate('({rate,rateMeta})'); c = (await cloud(pg)).get(f"{B}/settings/rate")
    rec("CX-07", f"請求中（rateBusy={busy}）改手動 0.3 後，舊回應不改回自動（改完雲端={mid}）", st["rateMeta"]["auto"] is False and c.get("auto") is False and c.get("jpyTwd") == 0.3, {"local": st, "cloud": c})
    await ctx.close()

ALL = {f.__name__: f for f in (cx01, cx02, cx03, cx04, cx05, cx06, cx07)}
async def main():
    names = sys.argv[1:] or list(ALL)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for n in names:
            try: await ALL[n](b)
            except Exception as ex: rec(n, "腳本執行", False, repr(ex)[:400])
        await b.close()
    summary()
asyncio.run(main())
