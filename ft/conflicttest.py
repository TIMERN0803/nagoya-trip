# conflicttest：兩人同時改同一筆、同步佇列與讀取檢查（QA R2 修正階段 F1、F2、F3、F5、F7、G1、G2、G3、G4、G5）
# 一律假資料庫（ft/fs_offline.js）；旅程代碼 qa-r2-test／qa-r2-other。兩支手機用 phonelib.py。
#  F1 隨身只寫 carry　F2 清單編輯／排序／訂房／旅平險只送改的欄位　F3 殘缺文件不顯示、壞資料不讓畫面壞掉
#  F5 錢包面板重畫保留輸入　F7 匯率舊回應不蓋手動　G1 invalid-argument　G2 刪打包項目連 @人 一起刪
#  G3 outbox 綁旅程代碼　G4 暫時性失敗退避重送　G5 links 只放行 https
import sys
from phonelib import *

OTHER = "qa-r2-other"
async def go_day_with_stay(pg):
    n = await pg.evaluate('DAYS.length')
    for i in range(n):
        await pg.evaluate(f'tab="plan";view="day";dayIdx={i};stayEditing=false;render(true)'); await pg.wait_for_timeout(150)
        if await pg.query_selector('[data-stay-edit]'): return i
    return -1

# ---- F1 ----
async def f1(b):
    ctx = await newctx(b); T = jst(11, 21, 20)
    db = {**META, f"{B}/expenses/e1": {"amt": 6000, "cat": "shop", "who": "star", "split": "both", "pay": "card", "day": "11/21", "note": "藥妝", "ts": 1, "tf": True}}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "acct")
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await A.click('.ex[data-edit="e1"]'); await A.wait_for_timeout(700); await A.fill('#f-amt', '7500'); await A.click('#f-save'); await A.wait_for_timeout(800)
    await Bp.click('[data-carry="e1"]'); await Bp.wait_for_timeout(300)
    ob = await Bp.evaluate('outbox["expenses/e1"]||null')
    rec("F1", "按「隨身」只送 carry（merge），不帶金額與備註", bool(ob) and ob.get("m") == 1 and list((ob.get("d") or {}).keys()) == ["carry"], ob)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    e = (await exps(A))["e1"]
    rec("F1", "對方改的 7500 保留，carry 也生效", e.get("amt") == 7500 and e.get("carry") is True, e)
    await ctx.close()

# ---- F2a：清單編輯 ----
async def f2a(b):
    ctx = await newctx(b); T = jst(11, 18, 10)
    db = {**META, f"{B}/items/t1": {"group": "prep", "title": "換日圓", "note": "原備註", "due": "", "order": 1}}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "list")
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await A.click('[data-item-edit="t1"]'); await A.wait_for_timeout(300); await A.fill('.chk-form input[name=title]', 'A 改的標題'); await A.click('.chk-form .primary'); await A.wait_for_timeout(700)
    await Bp.click('[data-item-edit="t1"]'); await Bp.wait_for_timeout(300); await Bp.fill('.chk-form input[name=note]', 'B 改的備註'); await Bp.click('.chk-form .primary'); await Bp.wait_for_timeout(400)
    ob = await Bp.evaluate('outbox["items/t1"]||null')
    rec("F2a", "改備註只送 note（merge）", bool(ob) and ob.get("m") == 1 and list((ob.get("d") or {}).keys()) == ["note"], ob)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    it = (await items_cloud(A))["t1"]
    rec("F2a", "上線後標題（A）與備註（B）都在，順序沒被動", it.get("title") == "A 改的標題" and it.get("note") == "B 改的備註" and it.get("order") == 1, it)
    # 沒改任何東西就按存檔：不送、不留 outbox
    await Bp.click('[data-item-edit="t1"]'); await Bp.wait_for_timeout(300); await Bp.click('.chk-form .primary'); await Bp.wait_for_timeout(400)
    rec("F2a", "打開編輯但沒改就存：不產生寫入", await Bp.evaluate('Object.keys(outbox).length') == 0, await Bp.evaluate('Object.keys(outbox)'))
    # 新增仍是整筆
    await Bp.click('[data-item-new="prep"]'); await Bp.wait_for_timeout(300); await Bp.fill('.chk-form input[name=title]', '新項目'); await Bp.click('.chk-form .primary'); await Bp.wait_for_timeout(700)
    new = [v for k, v in (await items_cloud(A)).items() if v.get("title") == "新項目"]
    rec("F2a", "新增是整筆（有 group、order）", len(new) == 1 and new[0].get("group") == "prep" and new[0].get("order") >= 2, new)
    await ctx.close()

# ---- F2b：排序 ----
async def f2b(b):
    ctx = await newctx(b); T = jst(11, 18, 10)
    db = {**META, f"{B}/items/t1": {"group": "prep", "title": "換日圓", "note": "原備註", "due": "", "order": 1},
          f"{B}/items/t2": {"group": "prep", "title": "買網卡", "note": "", "due": "", "order": 2}}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "list")
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await A.click('[data-item-edit="t1"]'); await A.wait_for_timeout(300); await A.fill('.chk-form input[name=title]', 'A 改的標題'); await A.click('.chk-form .primary'); await A.wait_for_timeout(700)
    await Bp.click('[data-sort-toggle="prep"]'); await Bp.wait_for_timeout(400)
    await Bp.focus('[data-sort-id="t2"] .drag-h'); await Bp.keyboard.press("ArrowUp"); await Bp.wait_for_timeout(400)
    ob = await Bp.evaluate('outbox["items/t1"]||null')
    rec("F2b", "排序只送 order（merge）", bool(ob) and ob.get("m") == 1 and list((ob.get("d") or {}).keys()) == ["order"], ob)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    it = await items_cloud(A)
    rec("F2b", "上線後 A 改的標題保留、順序生效", it["t1"].get("title") == "A 改的標題" and it["t2"].get("order") == 1 and it["t1"].get("order") == 2, {k: (v.get("title"), v.get("order")) for k, v in it.items()})
    rec("F2b", "B 的畫面在排序後仍是完整項目（有標題）", "買網卡" in await Bp.evaluate('document.body.innerText') and "A 改的標題" in await Bp.evaluate('document.body.innerText'), None)
    await ctx.close()

# ---- F2c：訂房／旅平險 ----
SOS0 = {"order": "OLD-1", "via": "平台甲", "room": "雙床房", "ins": "舊保險公司", "insTel": "0800-000-000"}
async def f2c(b):
    ctx = await newctx(b); T = jst(11, 18, 10)
    A = await phone(ctx, T, "zhang", "A", init=seed({**META, f"{B}/settings/sos": SOS0}), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await A.click('[data-sos]'); await A.wait_for_timeout(700)
    await A.click('[data-sos-tab="emg"]'); await A.wait_for_timeout(300); await A.click('[data-sos-edit]'); await A.wait_for_timeout(300)
    await A.fill('[data-sos-f="insTel"]', '0800-111-111'); await A.click('[data-sos-save]'); await A.wait_for_timeout(700)
    await go_day_with_stay(Bp)
    await Bp.click('[data-stay-edit]'); await Bp.wait_for_timeout(300)
    await Bp.fill('[data-stay-form] [data-sos-f="room"]', '雙人房（加床）'); await Bp.click('[data-stay-save]'); await Bp.wait_for_timeout(400)
    ob = await Bp.evaluate('outbox["settings/sos"]||null')
    rec("F2c", "改訂房只送 room（merge）", bool(ob) and ob.get("m") == 1 and list((ob.get("d") or {}).keys()) == ["room"], ob)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1500)
    s = (await cloud(A)).get(f"{B}/settings/sos", {})
    rec("F2c", "上線後 A 改的旅平險電話與 B 改的房型都在", s.get("insTel") == "0800-111-111" and s.get("room") == "雙人房（加床）" and s.get("order") == "OLD-1", s)
    await ctx.close()
    # 兩支都在線上：B 先打開表單、A 改訂單編號，B 存房型不能把訂單編號蓋回
    ctx = await newctx(b)
    A = await phone(ctx, T, "zhang", "A", init=seed({**META, f"{B}/settings/sos": SOS0}), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    await go_day_with_stay(A); await go_day_with_stay(Bp)
    await Bp.click('[data-stay-edit]'); await Bp.wait_for_timeout(300)
    await A.click('[data-stay-edit]'); await A.wait_for_timeout(300)
    await A.fill('[data-stay-form] [data-sos-f="order"]', 'NEW-2'); await A.click('[data-stay-save]'); await A.wait_for_timeout(800)
    await Bp.fill('[data-stay-form] [data-sos-f="room"]', '雙人房（加床）'); await Bp.click('[data-stay-save]'); await Bp.wait_for_timeout(800)
    s = (await cloud(A)).get(f"{B}/settings/sos", {})
    rec("F2c", "兩支都在線上：B 存房型後訂單編號仍是 A 改的", s.get("order") == "NEW-2" and s.get("room") == "雙人房（加床）", s)
    # 清空也算改
    await Bp.click('[data-stay-edit]'); await Bp.wait_for_timeout(300); await Bp.fill('[data-stay-form] [data-sos-f="via"]', ''); await Bp.click('[data-stay-save]'); await Bp.wait_for_timeout(800)
    s = (await cloud(A)).get(f"{B}/settings/sos", {})
    rec("F2c", "清空欄位會送出（空字串）", s.get("via") == "", s)
    await ctx.close()

# ---- F3：讀取檢查 ----
async def f3(b):
    ctx = await newctx(b); T = jst(11, 21, 20)
    db = {**META, f"{B}/expenses/e1": {"amt": 1200, "cat": "food", "who": "star", "split": "both", "pay": "cash", "day": "11/21", "note": "拉麵", "ts": 1}}
    A = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await tab(x, "acct")
    await Bp.evaluate('__goOffline()'); await Bp.wait_for_timeout(200)
    await Bp.click('.ex[data-edit="e1"]'); await Bp.wait_for_timeout(700); await Bp.fill('#f-amt', '1500'); await Bp.click('#f-save'); await Bp.wait_for_timeout(500)
    await A.click('.ex[data-edit="e1"]'); await A.wait_for_timeout(700); await A.click('[data-exp-del]'); await A.wait_for_timeout(700)
    await Bp.evaluate('__goOnline()'); await Bp.wait_for_timeout(1800)
    cl = (await exps(A)).get("e1")
    ui = {x: await x.evaluate('({rows:expenses.length,body:document.body.innerText})') for x in (A, Bp)}
    ghost = [await x.query_selector('.ex[data-edit="e1"]') is not None for x in (A, Bp)]
    rec("F3", "對方刪除＋這邊改金額：殘缺帳目不顯示（雲端有 {amt}，兩支手機都沒有這一筆）", all(v["rows"] == 0 for v in ui.values()) and not any(ghost), {"cloud": cl, "rows": [v["rows"] for v in ui.values()]})
    # 之後記一筆正常帳：總額只算正常的
    await S.expopen(Bp); await Bp.fill('#f-amt', '800'); await Bp.fill('#f-note', '咖啡'); await Bp.click('#f-save'); await Bp.wait_for_timeout(900)
    t = await Bp.evaluate('document.body.innerText')
    rec("F3", "之後記的帳照常計算，殘缺帳目不進總額（旅程總花費 ¥800）", "旅程總花費 ¥800" in t.replace("\n", " ") or "¥800" in t, t[:120].replace("\n", " "))
    rec("F3", "沒有頁面錯誤", not Bp.errs and not A.errs, (Bp.errs + A.errs)[:2])
    await ctx.close()
    # 心情壞 score、缺 day 的帳、缺欄位的清單：畫面不壞
    ctx = await newctx(b)
    db = {**META, f"{B}/moods/11-21_zhang": {"score": 99, "note": "壞資料"}, f"{B}/moods/11-20_star": {"score": "x"},
          f"{B}/moods/11-19_zhang": {"score": 4, "note": "好的"},
          f"{B}/expenses/x1": {"amt": 500, "cat": "food", "who": "zhang"}, f"{B}/expenses/x2": {"amt": 700, "cat": "food", "who": "zhang", "split": "both", "pay": "cash", "day": "11/21", "note": "正常", "ts": 2},
          f"{B}/items/bad1": {"order": 1}}
    pg = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1500)
    ok = []
    for t_ in ("plan", "acct", "list"):
        await tab(pg, t_); ok.append(len(await pg.inner_text('body')) > 50)
    await pg.evaluate('tab="plan";view="home";render(true)'); await pg.wait_for_timeout(300)
    await pg.evaluate('tab="plan";view="day";dayIdx=4;render(true)'); await pg.wait_for_timeout(300)
    st = await pg.evaluate('({moods:Object.keys(moods),exp:expenses.map(e=>e.id),items:items.filter(x=>x.id==="bad1").length})')
    rec("F3", "壞 score、缺 day／付款人的帳、缺欄位的清單項目：跳過，首頁與各分頁照常畫出來", not pg.errs and all(ok) and st["moods"] == ["11-19_zhang"] and st["exp"] == ["x2"] and st["items"] == 0, {"errs": pg.errs[:2], **st})
    await ctx.close()

# ---- F5：錢包輸入不被重畫清掉 ----
async def f5(b):
    for label, how in [("對方記一筆帳", "exp"), ("對方改自己的錢包", "wallet"), ("第一次設定、對方記一筆", "first")]:
        ctx = await newctx(b); T = jst(11, 19, 12)
        w = {} if how == "first" else {f"{B}/wallet/zhang": {"cashIn": 20000, "ts": 1}}
        A = await phone(ctx, T, "zhang", "A", init=seed({**META, **w, f"{B}/wallet/star": {"cashIn": 10000, "ts": 1}}), wait=1200)
        Bp = await phone(ctx, T, "star", "B", wait=1200)
        await tab(A, "acct"); await A.click('[data-wallet-open]'); await A.wait_for_timeout(700)
        if how != "first": await A.click('[data-wallet-edit][data-mode="add"]'); await A.wait_for_timeout(300)
        await A.fill('.w-form input[name=amt]', '5000')
        if how == "wallet": await Bp.evaluate('saveWallet("star",15000)')
        else:
            await tab(Bp, "acct"); await S.expopen(Bp); await Bp.fill('#f-amt', '800'); await Bp.fill('#f-note', '咖啡'); await Bp.click('#f-save')
        await A.wait_for_timeout(1200)
        st = await A.evaluate('({amt:document.querySelector(".w-form input[name=amt]")?.value??null,focus:document.activeElement?.name||document.activeElement?.tagName})')
        rec("F5", f"{label}：正在填的金額與焦點保留", st["amt"] == "5000" and st["focus"] == "amt", st)
        await ctx.close()
    # 存檔後表單消失、不會殘留舊值
    ctx = await newctx(b); T = jst(11, 19, 12)
    A = await phone(ctx, T, "zhang", "A", init=seed({**META, f"{B}/wallet/zhang": {"cashIn": 20000, "ts": 1}}), wait=1200)
    await tab(A, "acct"); await A.click('[data-wallet-open]'); await A.wait_for_timeout(700); await A.click('[data-wallet-edit][data-mode="add"]'); await A.wait_for_timeout(300)
    await A.fill('.w-form input[name=amt]', '5000'); await A.click('.w-form .primary'); await A.wait_for_timeout(700)
    rec("F5", "存檔後表單收起、錢包金額更新為 25,000", await A.query_selector('.w-form input[name=amt]') is None and "25,000" in await A.evaluate('document.body.innerText'), None)
    await ctx.close()

# ---- F7：匯率 ----
async def f7(b):
    ctx = await newctx(b); T = jst(11, 19, 12)
    gate = asyncio.Event()
    async def slow(r):
        await gate.wait()
        await r.fulfill(body=json.dumps({"result": "success", "rates": {"TWD": 0.2111}}), content_type="application/json", headers={"access-control-allow-origin": "*"})
    await ctx.route("**/open.er-api.com/**", lambda r: asyncio.ensure_future(slow(r)))
    db = {**META, f"{B}/settings/rate": {"jpyTwd": 0.2, "auto": True, "ts": 1, "src": "ExchangeRate-API"}}
    pg = await S.opn(ctx, T, init=seed(db), wait=1200)
    await tab(pg, "acct"); await pg.wait_for_timeout(2500)
    await pg.evaluate('(()=>{const i=document.getElementById("f-rate");i.value="0.3";i.dispatchEvent(new Event("change",{bubbles:true}))})()')
    await pg.wait_for_timeout(500)
    gate.set(); await pg.wait_for_timeout(1500)
    c = (await cloud(pg)).get(f"{B}/settings/rate")
    st = await pg.evaluate('({rate,auto:rateMeta.auto})')
    rec("F7", "請求中改手動 0.3：舊回應回來後仍是手動 0.3（本機與雲端）", st["auto"] is False and st["rate"] == 0.3 and c.get("auto") is False and c.get("jpyTwd") == 0.3, {"local": st, "cloud": c})
    # 按「改回自動」之後會抓到新匯率
    await pg.click('[data-rate-auto]'); await pg.wait_for_timeout(2000)
    c = (await cloud(pg)).get(f"{B}/settings/rate")
    rec("F7", "改回自動後抓到新匯率 0.2111 並寫回雲端", c.get("auto") is True and abs(c.get("jpyTwd") - 0.2111) < 1e-6, c)
    await ctx.close()

# ---- G1：invalid-argument ----
async def g1(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 12), init=seed(META), wait=1200)
    await pg.evaluate('window.__reject="invalid-argument"')
    await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '500'); await pg.fill('#f-note', '被拒收的帳'); await pg.click('#f-save'); await pg.wait_for_timeout(1200)
    st = await pg.evaluate('({pending:Object.values(outbox).filter(v=>v.d&&v.d.note==="被拒收的帳").length,canWrite,bar:document.querySelector(".undo-bar span")?.textContent||""})')
    rec("G1", "invalid-argument：這筆不留在 outbox、App 仍可寫入、跳出一句提示", st["pending"] == 0 and st["canWrite"] is True and "不接受" in st["bar"], st)
    await pg.evaluate('window.__reject=0')
    await S.expopen(pg); await pg.fill('#f-amt', '300'); await pg.fill('#f-note', '之後正常的帳'); await pg.click('#f-save'); await pg.wait_for_timeout(1000)
    ok = any(v.get("note") == "之後正常的帳" for k, v in (await cloud(pg)).items() if "/expenses/" in k)
    rec("G1", "之後的記帳照常送出", ok, None)
    await ctx.close()

# ---- G2：刪打包項目連 @人 一起刪 ----
async def g2(b):
    ctx = await newctx(b); T = jst(11, 18, 10)
    db = {**META, f"{B}/items/k01": {"group": "pack", "title": "護照", "note": "", "cat": "doc", "order": 1},
          f"{B}/checks/k01@zhang": {"done": True}, f"{B}/checks/k01@star": {"done": True}}
    pg = await phone(ctx, T, "zhang", "A", init=seed(db), wait=1500)
    await pg.evaluate('tab="list";listSub="pack";render(true)'); await pg.wait_for_timeout(400)
    await pg.evaluate('deleteItem("k01")'); await pg.wait_for_timeout(800)
    c = await cloud(pg)
    left = [k for k in c if "k01" in k]
    rec("G2", "刪除後雲端沒有 k01、k01@zhang、k01@star", not left, left)
    await pg.click('.undo-bar button'); await pg.wait_for_timeout(900)
    c = await cloud(pg)
    back = sorted(k.split(B + "/")[1] for k in c if "k01" in k)
    rec("G2", "5 秒內復原：項目與兩個人的勾選都回來", back == ["checks/k01@star", "checks/k01@zhang", "items/k01"] and c[f"{B}/checks/k01@zhang"].get("done") is True, back)
    await ctx.close()

# ---- G3：outbox 綁旅程代碼 ----
async def g3(b):
    ctx = await newctx(b); T = jst(11, 19, 20)
    pg = await S.opn(ctx, T, init=seed({**META}), wait=1200)
    await tab(pg, "acct")
    await pg.evaluate('__goOffline()'); await ctx.set_offline(True); await pg.evaluate('dispatchEvent(new Event("offline"))'); await pg.wait_for_timeout(300)
    await S.expopen(pg); await pg.fill('#f-amt', '3300'); await pg.fill('#f-note', '舊旅程離線記的'); await pg.click('#f-save'); await pg.wait_for_timeout(500)
    stamped = await pg.evaluate('Object.values(outbox).map(v=>v.c||"")')
    rec("G3", "離線時寫的變更記下所屬代碼", stamped == [S.CODE], stamped)
    await pg.close(); await ctx.set_offline(False)
    pg2 = await S.opn(ctx, T, init='', url="http://localhost:8766/#k=" + OTHER, pre='localStorage.removeItem("mocknet");', wait=1500)
    await pg2.evaluate('window.__goOnline&&__goOnline()'); await pg2.wait_for_timeout(2000)
    c = await cloud(pg2)
    landed = [k for k, v in c.items() if "/expenses/" in k and v.get("note") == "舊旅程離線記的"]
    st = await pg2.evaluate('({code:localStorage.getItem("ngy:code"),own:pendingCount(),foreign:foreignCount(),shown:expenses.map(e=>e.note)})')
    rec("G3", "開另一個代碼的連結：舊旅程的離線記帳不會送進新旅程、也不顯示在新旅程", not any(OTHER in k for k in landed) and st["shown"] == [] and st["code"] == OTHER and st["foreign"] == 1 and st["own"] == 0, {"landed": landed, **st})
    await tab(pg2, "acct"); await pg2.wait_for_timeout(300)   # 同步膠囊和面板在記帳、清單分頁
    if not await pg2.query_selector('#code-info'): await pg2.click('[data-sync-info]'); await pg2.wait_for_timeout(300)
    info = (await pg2.inner_text('#code-info')) if await pg2.query_selector('#code-info') else ""
    rec("G3", "同步面板有「換代碼後留在原本旅程」與「屬於另一個旅程，沒有送出」的說明＋丟掉按鈕", "屬於另一個旅程，沒有送出" in info and await pg2.query_selector('[data-ob-drop]') is not None, info.replace("\n", " | "))
    await pg2.screenshot(path=SHOTS + 'g3_panel.png')
    await pg2.click('[data-ob-drop]'); await pg2.wait_for_timeout(300)
    asked = await pg2.evaluate('foreignCount()') == 1 and "確定丟掉" in await pg2.inner_text('#code-info')
    await pg2.click('[data-ob-drop]'); await pg2.wait_for_timeout(300)
    rec("G3", "丟掉這些變更要按兩次，第二次才真的丟", asked and await pg2.evaluate('foreignCount()') == 0, None)
    await ctx.close()
    # 回到原本的代碼：留下的變更還在、會送出
    ctx = await newctx(b)
    pg = await S.opn(ctx, T, init=seed({**META}), wait=1200)
    await tab(pg, "acct"); await pg.evaluate('__goOffline()'); await ctx.set_offline(True); await pg.evaluate('dispatchEvent(new Event("offline"))'); await pg.wait_for_timeout(300)
    await S.expopen(pg); await pg.fill('#f-amt', '1000'); await pg.fill('#f-note', '留在原旅程'); await pg.click('#f-save'); await pg.wait_for_timeout(500)
    await pg.close(); await ctx.set_offline(False)
    pg2 = await S.opn(ctx, T, init='', url="http://localhost:8766/#k=" + OTHER, pre='localStorage.removeItem("mocknet");', wait=1500)
    await pg2.evaluate('localStorage.setItem("ngy:code","%s")' % S.CODE); await pg2.reload(); await pg2.wait_for_timeout(1500)
    await pg2.evaluate('window.__goOnline&&__goOnline()'); await pg2.wait_for_timeout(2000)
    c = await cloud(pg2)
    rec("G3", "換回原本的代碼：留在原旅程的變更照常送出", any(k.startswith(B + "/") and v.get("note") == "留在原旅程" for k, v in c.items() if "/expenses/" in k), None)
    await ctx.close()

# ---- G4：暫時性失敗退避重送 ----
async def g4(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 12), init=seed(META), wait=1200)
    await pg.evaluate('window.__reject="unavailable"')
    await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '640'); await pg.fill('#f-note', '暫時送不出去'); await pg.click('#f-save'); await pg.wait_for_timeout(800)
    n0 = await pg.evaluate('Object.keys(outbox).length')
    await pg.evaluate('window.__reject=0')
    # 第一次退避是 5 秒
    await pg.wait_for_timeout(6500)
    got = [k for k, v in (await cloud(pg)).items() if "/expenses/" in k and v.get("note") == "暫時送不出去"]
    rec("G4", "unavailable 失敗後 5 秒內自動重送，只送出一筆", n0 == 1 and len(got) == 1 and await pg.evaluate('Object.keys(outbox).length') == 0, {"before": n0, "cloud": got})
    await ctx.close()

# ---- G5：links 只放行 https ----
async def g5(b):
    ctx = await newctx(b)
    db = {**META, f"{B}/items/L1": {"group": "prep", "title": "有連結的待辦", "note": "", "order": 1, "links": [["壞連結", "javascript:alert(1)"], ["資料連結", "data:text/html,x"], ["好連結", "https://example.com/a"]]}}
    pg = await S.opn(ctx, jst(11, 18, 10), init=seed(db), wait=1500)
    await tab(pg, "list"); await pg.wait_for_timeout(400)
    hrefs = await pg.evaluate('[...document.querySelectorAll(".chk-row a.chip")].map(a=>a.getAttribute("href"))')
    txt = await pg.evaluate('document.body.innerText')
    rec("G5", "javascript:／data: 網址不會變成連結，https 連結照舊", hrefs == ["https://example.com/a"] and "壞連結" in txt and not pg.errs, {"hrefs": hrefs, "errs": pg.errs[:2]})
    await ctx.close()

ALL = [f1, f2a, f2b, f2c, f3, f5, f7, g1, g2, g3, g4, g5]
async def main():
    names = sys.argv[1:]
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in ALL:
            if names and f.__name__ not in names: continue
            try: await f(b)
            except Exception as ex: rec(f.__name__, "腳本執行", False, repr(ex)[:300])
        await b.close()
    summary()
asyncio.run(main())
