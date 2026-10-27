# 同步與離線回歸測試（v44 獨立測試第一批：C-P0-1、C-P0-2、C-P1-1、C-P1-2、C-P1-6、Codex 心情刪除，另含 C-P2-1、C-P2-2 狀態顯示）
# 一律用假資料庫：ft/fs.js（一般）、ft/fs_offline.js（模擬 Firestore 離線行為、慢伺服器、權限錯誤）
# 自建 context 都先掛上和 fulltest.newpage() 一樣的攔截，另外擋掉所有 googleapis（絕不碰真實 Firestore）
# SW 項目會把目前網站複製到暫存資料夾、在 8767 埠開伺服器
import asyncio, json, os, shutil, subprocess, tempfile, time
import fulltest as ft
from playwright.async_api import async_playwright
CODE = "neko-sync"
B = "trips/" + CODE
FSO = open("fs_offline.js").read()
SITE = "/home/claude/nagoya-trip"
SYNC = '(()=>{const s=document.querySelector(".sync, #code-form");return s?s.innerText.replace(/\\s+/g," "):"(無)"})()'
META = {f"{B}/settings/meta": {"itemsSeeded": True, "itemsRestore": 2}}
rec = ft.rec

async def mkctx(b, fs=None, lib=None, tz="Asia/Tokyo", sw="block"):
    """lib：{"mode": "mock"|"abort"|"gate"}，可在測試中途改；gate 模式等 lib["gate"] 這個 Event"""
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id=tz, service_workers=sw)
    st = lib if lib is not None else {"mode": "mock"}
    body = {"app": ft.APP, "fs": fs or ft.FS}
    def handler(kind):
        async def h(r):
            m = st["mode"]
            if m == "gate": await st["gate"].wait(); m = "mock"
            if m == "mock": await r.fulfill(body=body[kind], content_type="text/javascript", headers={"access-control-allow-origin": "*"})
            else: await r.abort()
        return lambda r: asyncio.ensure_future(h(r))
    # Playwright 後註冊的 route 優先：全擋放前面，假程式庫放後面
    await ctx.route("**/*.googleapis.com/**", lambda r: r.abort())
    await ctx.route("**/firestore.googleapis.com/**", lambda r: r.abort())
    await ctx.route("**/firebasejs/**", lambda r: r.abort())
    await ctx.route("**/firebasejs/**/firebase-app.js", handler("app"))
    await ctx.route("**/firebasejs/**/firebase-firestore.js", handler("fs"))
    for pat in ["**/api.open-meteo.com/**", "**/fonts.googleapis.com/**", "**/fonts.gstatic.com/**", "**/open.er-api.com/**", "**/currency-api*/**"]:
        await ctx.route(pat, lambda r: r.abort())
    ctx.lib = st
    return ctx

async def expopen(pg):
    """記帳分成清單頁和「記一筆」填寫面板：面板沒開就按「記一筆」"""
    if not await pg.query_selector('.exp-sheet:not(.leaving) #f-amt'):
        await pg.click('[data-exp-new]'); await pg.wait_for_timeout(600)
async def expclose(pg):
    """關掉填寫面板；有填東西會先問，選「放棄」"""
    if await pg.query_selector('.exp-sheet:not(.leaving)'):
        await pg.click('.exp-sheet:not(.leaving) [data-exp-x]'); await pg.wait_for_timeout(350)
        if await pg.is_visible('.exp-sheet:not(.leaving) .exp-confirm'): await pg.click('[data-exp-discard]')
        await pg.wait_for_timeout(350)
NOTE = 'document.getElementById("acct-note")?.innerText||""'
async def opn(ctx, t, init="", pre="", url="http://localhost:8766/", wait=900):
    pg = await ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    await pg.clock.install(time=t)
    if pre: await pg.add_init_script(pre)
    s = 'try{if(!sessionStorage.getItem("s")){localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code",%s);%ssessionStorage.setItem("s",1)}}catch(e){}' % (json.dumps(CODE), init)
    await pg.add_init_script(s)
    await pg.goto(url); await pg.wait_for_timeout(wait)
    return pg

def seed(db): return 'localStorage.setItem("mockdb",%s);' % json.dumps(json.dumps(db))
async def cloud(pg): return await pg.evaluate('JSON.parse(localStorage.getItem("mockdb")||"{}")')
async def tab(pg, name): await pg.evaluate(f'document.querySelector("nav.tabs button[data-tab={name}]").click()'); await pg.wait_for_timeout(250)

async def do_ops(pg, tag, mood_day=2):
    """勾待辦、新增要買、記帳、錢包補 10000、寫心情（全部在 UI 上操作）"""
    await tab(pg, "list")
    cid = await pg.evaluate('document.querySelector("[data-group-id=prep] .chk input:not(:checked)")?.id')
    await pg.check('#' + cid); await pg.wait_for_timeout(100)
    await pg.click('[data-list-tab="buy"]'); await pg.wait_for_timeout(100)
    await pg.click('[data-item-new="buy"]'); await pg.fill('.chk-form input[name=title]', tag + "要買"); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(150)
    await tab(pg, "acct"); await expopen(pg); await pg.fill('#f-amt', '2200'); await pg.fill('#f-note', tag + "記帳"); await pg.click('#f-save'); await pg.wait_for_timeout(400)
    msg = await pg.evaluate(NOTE)
    await pg.click('.wchip'); await pg.wait_for_timeout(200)
    if await pg.locator('.ws [data-wallet-edit][data-mode="add"]').count(): await pg.click('.ws [data-wallet-edit][data-mode="add"]')
    await pg.fill('.ws .w-form input', '10000'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(200)
    if await pg.query_selector('.ws .sm-x'): await pg.click('.ws .sm-x')
    await pg.evaluate(f'tab="plan";view="day";dayIdx={mood_day};render()'); await pg.wait_for_timeout(250)
    await pg.click('#mood .fbtn[data-score="5"]'); await pg.fill('#mood-note', tag + "心情"); await pg.click('#mood-form .primary'); await pg.wait_for_timeout(200)
    return cid[2:], msg

async def state(pg, tag, cid, mood_key="11-19_zhang"):
    return await pg.evaluate('''([t,c,mk])=>({done:done[c]===true,item:items.some(x=>x.title===t+"要買"),exp:expenses.some(e=>e.note===t+"記帳"),wallet:cashIn("zhang"),mood:!!moods[mk]})''', [tag, cid, mood_key])

def cloud_state(db, tag, cid, mood_key="11-19_zhang"):
    return {"done": (db.get(f"{B}/checks/{cid}") or {}).get("done") is True,
            "item": any(v.get("title") == tag + "要買" for k, v in db.items() if "/items/" in k),
            "exp": sum(1 for k, v in db.items() if "/expenses/" in k and v.get("note") == tag + "記帳"),
            "wallet": (db.get(f"{B}/wallet/zhang") or {}).get("cashIn"),
            "mood": f"{B}/moods/{mood_key}" in db}

def check_all(area, label, loc, cl, wallet):
    for k, name in [("done", "勾選待辦"), ("item", "新增要買"), ("exp", "記帳"), ("wallet", "錢包補錢"), ("mood", "心情")]:
        want = wallet if k == "wallet" else True
        ok = loc[k] == want and (cl[k] == 1 if k == "exp" else cl[k] == want)
        rec(area, f"{label}：{name}畫面還在、雲端有（記帳只有 1 筆）", ok, {"畫面": loc[k], "雲端": cl[k]})

BASE = {**META, f"{B}/items/p1": {"group": "prep", "title": "換日圓", "note": "", "due": "", "order": 1},
        f"{B}/items/srv1": {"group": "buy", "title": "星星之前加的", "note": "", "due": "", "order": 150},
        f"{B}/wallet/zhang": {"cashIn": 20000, "ts": 1},
        f"{B}/expenses/old": {"amt": 1000, "cat": "food", "who": "star", "split": "both", "pay": "card", "day": "11/18", "note": "星星昨天記的", "ts": 1}}

async def slow_server(b):
    """C-P0-1：程式庫已快取、伺服器慢 3 秒：連線確認前的操作不會被雲端蓋掉"""
    for delay in [3000, 10000]:
        ctx = await mkctx(b, fs=FSO)
        pg = await opn(ctx, ft.jst(11, 19, 9), init=seed(BASE), wait=1200); await pg.close()
        pg = await opn(ctx, ft.jst(11, 19, 20), pre=f'window.__serverDelay={delay};', wait=400)
        await tab(pg, "list"); s0 = await pg.evaluate(SYNC)
        rec("伺服器慢", f"{delay//1000} 秒：等待時顯示「連線中…」，不是代碼表單", "連線中" in s0 and "旅行代碼" not in s0, s0)
        cid, _ = await do_ops(pg, "慢伺服器")
        await pg.wait_for_timeout(delay + 1500)
        check_all("伺服器慢", f"{delay//1000} 秒", await state(pg, "慢伺服器", cid), cloud_state(await cloud(pg), "慢伺服器", cid), 30000)
        await tab(pg, "acct"); s1 = await pg.evaluate(SYNC)
        rec("伺服器慢", f"{delay//1000} 秒：伺服器回應後顯示「同步中」", "同步中" in s1, s1)
        rec("伺服器慢", f"{delay//1000} 秒：同步佇列已清空", await pg.evaluate('pendingCount()') == 0)
        rec("伺服器慢", f"{delay//1000} 秒：沒有錯誤", not pg.errs, pg.errs[:2])
        await ctx.close()

async def slow_lib(b):
    """C-P0-1：程式庫晚 4 秒才載入：等待期間的操作、等待中顯示連線中、看得到之前的帳"""
    lib = {"mode": "mock", "gate": asyncio.Event()}
    ctx = await mkctx(b, lib=lib)
    pg = await opn(ctx, ft.jst(11, 19, 9), init=seed(BASE), wait=1500); await pg.close()
    lib["mode"] = "gate"
    pg = await opn(ctx, ft.jst(11, 19, 20), wait=500)
    await tab(pg, "list"); s0 = await pg.evaluate(SYNC)
    rec("程式庫慢", "載入中顯示「連線中…」，不是代碼表單（代碼已存好）", "連線中" in s0 and "旅行代碼" not in s0, s0)
    rec("程式庫慢", "載入中記帳頁看得到之前的帳（本機副本）", await pg.evaluate('expenses.some(e=>e.id==="old")'))
    cid, msg = await do_ops(pg, "慢程式庫")
    rec("程式庫慢", "載入中記帳：顯示已記下並說明之後同步", "已記下" in msg and "恢復網路後同步" in msg, msg)
    lib["gate"].set(); await pg.wait_for_timeout(2500)
    # 對方此時新增一筆（觸發快照）
    await pg.evaluate('db&&db.collection("items").doc().set({group:"buy",title:"對方新增",order:999})'); await pg.wait_for_timeout(800)
    check_all("程式庫慢", "連上後", await state(pg, "慢程式庫", cid), cloud_state(await cloud(pg), "慢程式庫", cid), 30000)
    rec("程式庫慢", "對方新增的也看得到", await pg.evaluate('items.some(x=>x.title==="對方新增")'))
    rec("程式庫慢", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def lib_fail(b):
    """C-P0-2：離線開 App（程式庫載入失敗）→ 本機記 → 網路恢復自動重連並上傳 → 重開仍在"""
    lib = {"mode": "mock"}
    ctx = await mkctx(b, lib=lib)
    pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(BASE), wait=1200); await pg.close()
    lib["mode"] = "abort"
    pg = await opn(ctx, ft.jst(11, 19, 20), wait=1500)
    await tab(pg, "list"); s0 = await pg.evaluate(SYNC)
    rec("離線開啟", "狀態顯示離線、會自動同步", "離線" in s0 and "同步中" not in s0, s0)
    cid, msg = await do_ops(pg, "離線")
    rec("離線開啟", "記帳顯示「已記下（恢復網路後同步）」", "已記下" in msg and "恢復網路後同步" in msg, msg)
    lib["mode"] = "mock"
    await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(3000)
    rec("離線開啟", "收到 online 後自動重新連上（不用關 App）", await pg.evaluate('live'), await pg.evaluate('({live,syncMsg})'))
    check_all("離線開啟", "恢復網路後", await state(pg, "離線", cid), cloud_state(await cloud(pg), "離線", cid), 30000)
    rec("離線開啟", "自動重新整理後回到原本的行程頁", await pg.evaluate('tab==="plan"&&view==="day"&&dayIdx===2'), await pg.evaluate('({tab,view,dayIdx})'))
    await pg.reload(); await pg.wait_for_timeout(2500)
    check_all("離線開啟", "重開 App 後", await state(pg, "離線", cid), cloud_state(await cloud(pg), "離線", cid), 30000)
    rec("離線開啟", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def lib_fail_typing(b):
    """C-P0-2：網路恢復時正在輸入，不會重新整理吃掉輸入；輸入完才重新整理"""
    lib = {"mode": "abort"}
    ctx = await mkctx(b, lib=lib)
    pg = await opn(ctx, ft.jst(11, 19, 20), init=seed(BASE), wait=1200)
    await tab(pg, "acct"); await expopen(pg); await pg.fill('#f-amt', '777'); await pg.focus('#f-note')
    await pg.evaluate('window.__mark=1')
    lib["mode"] = "mock"; await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(1500)
    kept = await pg.evaluate('({mark:window.__mark===1,amt:document.getElementById("f-amt")?.value})')
    rec("離線開啟", "正在輸入金額時不會自動重新整理", kept["mark"] and kept["amt"] == "777", kept)
    await pg.fill('#f-note', '輸入中'); await pg.click('#f-save'); await pg.wait_for_timeout(200)
    await pg.evaluate('document.activeElement?.blur()')
    await pg.clock.fast_forward("00:16"); await pg.wait_for_timeout(2500)
    after = await pg.evaluate('({mark:window.__mark===1,live})')
    rec("離線開啟", "輸入完成後自動重新整理並連上", not after["mark"] and after["live"], after)
    rec("離線開啟", "輸入中記的帳有上傳", any(v.get("note") == "輸入中" for k, v in (await cloud(pg)).items() if "/expenses/" in k))
    await ctx.close()

async def offline_cached(b):
    """C-P1-1、C-P2-1：程式庫已快取、手機離線：狀態、樂觀更新、不重複寫入"""
    ctx = await mkctx(b, fs=FSO)
    pg = await opn(ctx, ft.jst(11, 19, 12), init=seed({**META, f"{B}/wallet/zhang": {"cashIn": 20000, "ts": 1}}), wait=1200)
    await tab(pg, "acct"); s = await pg.evaluate(SYNC)
    rec("離線", "連線時顯示「同步中」", "同步中" in s, s)
    await pg.evaluate('__goOffline()'); await ctx.set_offline(True); await pg.evaluate('dispatchEvent(new Event("offline"))'); await pg.wait_for_timeout(200)
    s = await pg.evaluate(SYNC); cls = await pg.evaluate('document.querySelector(".sync").className')
    rec("離線", "手機離線時不顯示綠色「同步中」", "同步中" not in s and "離線" in s and " on" not in cls, {"文字": s, "class": cls})
    await expopen(pg); await pg.fill('#f-amt', '3000'); await pg.fill('#f-note', '拉麵'); await pg.click('#f-save'); await pg.wait_for_timeout(500)
    r = await pg.evaluate('({msg:document.getElementById("acct-note").innerText,open:!!document.querySelector(".exp-sheet:not(.leaving)")})')
    rec("離線", "按「記下這筆」立刻出現已記下、面板關閉（不等雲端）", "已記下" in r["msg"] and not r["open"], r)
    await tab(pg, "plan"); await tab(pg, "acct"); await expopen(pg)
    rec("離線", "再打開記一筆是空的（不會再按一次）", await pg.evaluate('document.getElementById("f-amt").value') == "")
    await pg.click('#f-save'); await pg.wait_for_timeout(200)
    rec("離線", "空白再按只提示輸入金額", "請先輸入金額" in await pg.inner_text('#f-msg'))
    await expclose(pg)
    await pg.click('.wchip'); await pg.wait_for_timeout(200)
    await pg.click('.ws [data-wallet-edit][data-mode="add"]'); await pg.fill('.ws .w-form input', '10000'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(300)
    rec("離線", "「加進錢包」後表單立刻關閉", not await pg.query_selector('.ws .w-form'))
    if await pg.query_selector('.ws .sm-x'): await pg.click('.ws .sm-x')
    await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(250)
    await pg.click('#mood .fbtn[data-score="4"]'); await pg.fill('#mood-note', '犬山好好玩'); await pg.click('#mood-form .primary'); await pg.wait_for_timeout(300)
    rec("離線", "送出心情後切到已送出", not await pg.query_selector('#mood-form'))
    await pg.evaluate('tab="plan";view="day";dayIdx=0;render()'); await pg.wait_for_timeout(250)
    if await pg.query_selector('[data-stay-edit]'):
        await pg.click('[data-stay-edit]'); await pg.wait_for_timeout(150)
        await pg.fill('[data-stay-form] input[data-sos-f="room"]', '雙人房'); await pg.click('[data-stay-save]'); await pg.wait_for_timeout(300)
        rec("離線", "儲存訂房資料後表單關閉", not await pg.query_selector('[data-stay-form]'))
    else: rec("離線", "找得到訂房資料編輯", False)
    pend = await pg.evaluate('pendingCount()')
    rec("離線", "離線時變更留在同步佇列", pend >= 4, pend)
    await pg.evaluate('__goOnline()'); await ctx.set_offline(False); await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(1500)
    db = await cloud(pg)
    rec("離線", "恢復後雲端拉麵只有 1 筆", sum(1 for k, v in db.items() if "/expenses/" in k and v.get("note") == "拉麵") == 1)
    rec("離線", "恢復後雲端錢包是 30000（不會重複加）", (db.get(f"{B}/wallet/zhang") or {}).get("cashIn") == 30000, db.get(f"{B}/wallet/zhang"))
    rec("離線", "恢復後心情、訂房資料都上傳", f"{B}/moods/11-19_zhang" in db and (db.get(f"{B}/settings/sos") or {}).get("room") == "雙人房")
    await tab(pg, "acct"); s = await pg.evaluate(SYNC)
    rec("離線", "恢復後回到「同步中」、佇列清空", "同步中" in s and await pg.evaluate('pendingCount()') == 0, s)
    rec("離線", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
    # 冷啟動時已離線
    ctx = await mkctx(b, fs=FSO)
    pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META) + 'localStorage.setItem("mocknet","0");', wait=1500)
    await tab(pg, "list"); s = await pg.evaluate(SYNC)
    rec("離線", "離線冷啟動顯示離線、不是同步中", "離線" in s and "同步中" not in s, s)
    await ctx.close()

async def cold_cash(b):
    """C-P1-2：程式庫載入失敗時，記帳頁和現金餘額用本機副本"""
    lib = {"mode": "mock"}
    ctx = await mkctx(b, lib=lib)
    sd = {**META, f"{B}/wallet/zhang": {"cashIn": 30000, "ts": 1}, **{f"{B}/expenses/e{i}": {"amt": 4000, "cat": "food", "who": "zhang", "split": "both", "pay": "cash", "day": "11/18", "note": f"現金{i}", "ts": i + 1} for i in range(5)}}
    pg = await opn(ctx, ft.jst(11, 19, 9), init=seed(sd), wait=1200); await pg.close()
    lib["mode"] = "abort"
    pg = await opn(ctx, ft.jst(11, 19, 20), wait=1500)
    await tab(pg, "acct")
    chip = await pg.inner_text('.wchip'); lst = await pg.inner_text('#acct-list')
    rec("離線現金", "離線開啟時現金餘額 ¥10,000（不是 ¥30,000）", "¥10,000" in chip, chip)
    rec("離線現金", "離線開啟時看得到之前的 5 筆帳", all(f"現金{i}" in lst for i in range(5)), lst[:60])
    await ctx.close()

async def mood_delete(b):
    """Codex 心情刪除：對方刪掉的心情，本機（含重新整理後）也要消失"""
    ctx = await mkctx(b)
    a = await opn(ctx, ft.jst(11, 18, 21), init=seed(META))
    await a.click('#mood .fbtn[data-score="5"]'); await a.fill('#mood-form textarea', '要被刪掉的心情'); await a.click('#mood-form .primary'); await a.wait_for_timeout(200)
    key = next(k for k in await cloud(a) if '/moods/' in k)
    await a.evaluate('''async key=>{const F=await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js');await F.deleteDoc(F.doc({},key))}''', key)
    await a.wait_for_timeout(300)
    rec("心情刪除", "對方刪除後本機每日心情消失", "要被刪掉的心情" not in await a.locator('#mood').inner_text())
    await a.reload(); await a.wait_for_timeout(1200)
    rec("心情刪除", "重新整理後也不會回來", not await a.evaluate('Object.values(moods).some(m=>m&&m.note==="要被刪掉的心情")'))
    # 自己尚未送達的心情不會被快照刪掉
    await a.evaluate('outbox["moods/11-19_zhang"]={d:{score:3,note:"還沒送達",ts:1,who:"zhang",day:"11/19"},s:1};obSave()')
    await a.evaluate('db.collection("items").doc().set({group:"buy",title:"觸發",order:1})'); await a.wait_for_timeout(300)
    await a.evaluate('db.collection("moods").onSnapshot(s=>{window.__ms=s.docs.map(d=>d.id)})'); await a.wait_for_timeout(200)
    rec("心情刪除", "快照會保留自己還沒送達的心情", "11-19_zhang" in (await a.evaluate('window.__ms') or []))
    rec("心情刪除", "沒有錯誤", not a.errs, a.errs[:2])
    await ctx.close()

async def bad_code(b):
    """代碼沒有權限：退回代碼表單，期間的變更留在佇列（換對代碼後送出）"""
    ctx = await mkctx(b, fs=FSO)
    pg = await opn(ctx, ft.jst(11, 19, 12), pre='window.__deny=1;', init=seed(META), wait=1200)
    await tab(pg, "list"); s = await pg.evaluate(SYNC)
    rec("代碼錯誤", "顯示「旅行代碼不對」表單", "旅行代碼不對" in s, s)
    await tab(pg, "acct"); await expopen(pg); await pg.fill('#f-amt', '500'); await pg.fill('#f-note', '代碼錯時記的'); await pg.click('#f-save'); await pg.wait_for_timeout(300)
    rec("代碼錯誤", "期間記的帳留在佇列", await pg.evaluate('Object.values(outbox).some(v=>v.d&&v.d.note==="代碼錯時記的")'))
    await pg.evaluate('window.__deny=0')
    await tab(pg, "list"); await pg.fill('#f-code', CODE); await pg.click('#code-form .primary'); await pg.wait_for_timeout(1500)
    db = await cloud(pg)
    rec("代碼錯誤", "換對代碼後連上並送出", await pg.evaluate('live') and any(v.get("note") == "代碼錯時記的" for k, v in db.items() if "/expenses/" in k))
    rec("代碼錯誤", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def deep_link(b):
    """直接開 #acct、#list 不會出錯（初始畫面等全部程式載入完才切分頁）"""
    for h in ["acct", "list", "wx", "move"]:
        ctx = await mkctx(b)
        pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META), url=f"http://localhost:8766/#{h}", wait=1200)
        rec("直接開分頁", f"#{h} 開在該分頁、沒有錯誤", await pg.evaluate('tab') == h and not pg.errs, {"tab": await pg.evaluate('tab'), "errs": pg.errs[:2]})
        await ctx.close()

LIST = 'caches.keys().then(ks=>Promise.all(ks.map(k=>caches.open(k).then(c=>c.keys()).then(rs=>[k,rs.map(r=>r.url).filter(u=>!u.includes("localhost")).map(u=>u.split("/").pop())]))))'
async def sw_lib(b):
    """C-P1-6：版本更新時，字型與 Firebase 程式庫的快取不會被刪掉；舊版快取裡的程式庫會搬過來；其他網站的快取不動"""
    root = tempfile.mkdtemp(prefix="ngy-sw-")
    def deploy(ver):
        shutil.rmtree(root, ignore_errors=True)
        files = subprocess.run(["git", "ls-files"], cwd=SITE, capture_output=True, text=True).stdout.split()
        for f in files:
            os.makedirs(os.path.dirname(os.path.join(root, f)) or root, exist_ok=True); shutil.copy(os.path.join(SITE, f), os.path.join(root, f))
        sw = open(os.path.join(root, "sw.js")).read()
        import re; open(os.path.join(root, "sw.js"), "w").write(re.sub(r'ngy-v\d+', ver, sw))
    deploy("ngy-v9001")
    srv = subprocess.Popen(["python3", "-m", "http.server", "8767"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        ctx = await mkctx(b, sw="allow")
        await ctx.add_init_script('try{localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code","%s")}catch(e){}' % CODE)
        pg = await ctx.new_page(); await pg.goto("http://localhost:8767/"); await pg.wait_for_timeout(2500); await pg.reload(); await pg.wait_for_timeout(2500)
        c1 = dict(await pg.evaluate(LIST))
        rec("SW 程式庫", "程式庫存在獨立的 ngy-lib 快取", any("firebase" in u for u in c1.get("ngy-lib", [])), c1)
        # 模擬舊版留下的快取：舊版本號快取裡有程式庫、另外有別的網站的快取
        await pg.evaluate('''async()=>{const c=await caches.open("ngy-v9000");await c.put("https://www.gstatic.com/firebasejs/9.0.0/old-lib.js",new Response("x"));await c.put("http://localhost:8767/old.html",new Response("x"));
          const o=await caches.open("other-app");await o.put("http://localhost:8767/keep.txt",new Response("x"))}''')
        deploy("ngy-v9002")
        await pg.reload(); await pg.wait_for_timeout(4000)
        c2 = dict(await pg.evaluate(LIST))
        rec("SW 程式庫", "更新後第一次開啟，程式庫仍在快取", any("firebase" in u for u in c2.get("ngy-lib", [])), c2)
        rec("SW 程式庫", "舊版本快取刪掉、只留新版", "ngy-v9001" not in c2 and "ngy-v9000" not in c2 and "ngy-v9002" in c2, list(c2))
        rec("SW 程式庫", "舊版快取裡的程式庫搬到 ngy-lib", "old-lib.js" in c2.get("ngy-lib", []), c2.get("ngy-lib"))
        rec("SW 程式庫", "不刪別的網站的快取", "other-app" in c2, list(c2))
        await ctx.close()
    finally:
        srv.terminate(); shutil.rmtree(root, ignore_errors=True)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in [slow_server, slow_lib, lib_fail, lib_fail_typing, offline_cached, cold_cash, mood_delete, bad_code, deep_link, sw_lib]:
            try: await f(b)
            except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
        await b.close()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
