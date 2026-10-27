# 第二批修正的回歸測試（v44 獨立測試）：金額輸入、記帳編輯預設值、兩人同時改同一筆、去程航班時區、
# 進行中卡片與最後一天文案、過期待辦、匯率、旅平險分機、旅程代碼、沒選身分、現金超支、連點
# 一律用假資料庫（ft/fs.js、ft/fs_offline.js），自建 context 的攔截沿用 synctest.mkctx
import asyncio, json
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
rec = ft.rec
B, META, seed, opn, tab, cloud, mkctx = S.B, S.META, S.seed, S.opn, S.tab, S.cloud, S.mkctx
EXP = lambda **k: {"amt": 3000, "cat": "food", "who": "zhang", "split": "both", "pay": "cash", "day": "11/19", "note": "午餐", "ts": 1, **k}
async def exps(pg): return {k.split("/")[-1]: v for k, v in (await cloud(pg)).items() if "/expenses/" in k}
async def home(pg):
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(250)

async def amount(b):
    ctx = await mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await tab(pg, "acct"); await S.expopen(pg)
    for raw, err in [("1.5", "小數"), ("12.5", "小數"), ("-100", "負數"), ("1e3", "只能輸入數字"), ("1.5萬", "例如"), ("999999999", "最多"), ("12,34", "逗號"), ("0", "請先輸入金額"), ("   ", "請先輸入金額")]:
        n = len(await exps(pg))
        await pg.fill('#f-amt', raw); await pg.fill('#f-note', '不該存'); await pg.click('#f-save'); await pg.wait_for_timeout(150)
        m = await pg.inner_text('#f-msg'); v = await pg.input_value('#f-amt')
        rec("金額", f"「{raw}」不寫入、保留原值、提示原因", len(await exps(pg)) == n and err in m and v == raw, {"訊息": m, "欄位": v})
    await pg.fill('#f-amt', ''); await pg.type('#f-amt', '１２３'); v = await pg.input_value('#f-amt')
    rec("金額", "全形數字輸入時轉成半形", v == "123", v)
    for raw, want in [("１２３", 123), ("3,000", 3000), ("¥1,200", 1200), ("99,999,999", 99999999), ("4999", 4999)]:
        await S.expopen(pg); await pg.fill('#f-amt', raw); await pg.fill('#f-note', f"ok{raw}"); await pg.click('#f-save'); await pg.wait_for_timeout(200)
        got = [v["amt"] for v in (await exps(pg)).values() if v.get("note") == f"ok{raw}"]
        rec("金額", f"「{raw}」存成 {want}", got == [want], got)
        await pg.wait_for_timeout(500)
    await S.expopen(pg); await pg.fill('#f-amt', '5,000'); tf = await pg.is_visible('#f-tf-row')
    rec("金額", "千分位 5,000 也會出現免稅開關", tf)
    await S.expclose(pg)
    # 錢包
    await pg.click('.wchip'); await pg.wait_for_timeout(200)
    await pg.fill('.ws .w-form input', '1.5萬'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(200)
    e = await pg.evaluate('document.getElementById("w-err")?.innerText')
    rec("金額", "錢包「1.5萬」不寫入並提示", "例如" in (e or "") and await pg.evaluate('cashIn("zhang")') == 0, e)
    await pg.fill('.ws .w-form input', '３０，０００'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(200)
    rec("金額", "錢包全形「３０，０００」存成 30000", await pg.evaluate('cashIn("zhang")') == 30000 and not await pg.query_selector('.ws .w-form'))
    await pg.click('.ws [data-wallet-edit][data-mode="add"]'); await pg.fill('.ws .w-form input', '99999999'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(200)
    e = await pg.evaluate('document.getElementById("w-err")?.innerText')
    rec("金額", "錢包補錢後總額超過上限：不寫入並提示", "最多" in (e or "") and await pg.evaluate('cashIn("zhang")') == 30000, e)
    rec("金額", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def edit_defaults(b):
    ctx = await mkctx(b)
    pg = await opn(ctx, ft.jst(11, 21, 12), init=seed({**META, f"{B}/expenses/s1": EXP(who="star", split="self", day="11/18", pay="card", note="星星的")}))
    await tab(pg, "acct")
    await pg.click('.ex[data-edit="s1"]'); await pg.wait_for_timeout(200)
    await pg.fill('#f-amt', '2500'); await pg.click('#f-save'); await pg.wait_for_timeout(300)
    d = await pg.evaluate('({who:draft.who,split:draft.split,day:draft.day,pay:draft.pay})')
    rec("編輯", "改完星星 11/18 的帳，新帳預設回到自己、平分、付現、今天", d == {"who": "zhang", "split": "both", "day": "11/21", "pay": "cash"}, d)
    s1 = (await exps(pg))["s1"]
    rec("編輯", "只改金額：雲端金額 2500，其他欄位不變", s1["amt"] == 2500 and s1["who"] == "star" and s1["day"] == "11/18" and s1["note"] == "星星的", s1)
    await pg.click('.ex[data-edit="s1"]'); await pg.wait_for_timeout(600); await S.expclose(pg)
    d = await pg.evaluate('({who:draft.who,day:draft.day,amt:draft.amt})')
    rec("編輯", "沒改就關掉修改面板後回到預設", d == {"who": "zhang", "day": "11/21", "amt": ""}, d)
    await ctx.close()

async def conflict(b):
    db = {**META, f"{B}/expenses/e1": EXP()}
    ctx = await mkctx(b)
    a = await opn(ctx, ft.jst(11, 19, 20), init=seed(db)); s = await opn(ctx, ft.jst(11, 19, 20))
    for x in (a, s): await tab(x, "acct")
    await a.click('.ex[data-edit="e1"]'); await s.click('.ex[data-edit="e1"]'); await a.wait_for_timeout(200)
    await a.fill('#f-amt', '3200'); await a.click('#f-save'); await a.wait_for_timeout(600)
    sv = await s.input_value('#f-amt'); sm = await s.inner_text('#f-msg')
    rec("同時修改", "對方改了金額：自己表單帶入最新金額並提示", sv == "3200" and "對方剛改過" in sm, {"金額": sv, "訊息": sm})
    await s.fill('#f-note', '午餐（含飲料）'); await s.click('#f-save'); await s.wait_for_timeout(600)
    e = (await exps(a))["e1"]
    rec("同時修改", "A 改金額、B 改備註：雲端兩個都保留", e["amt"] == 3200 and e["note"] == "午餐（含飲料）", e)
    # 同時改：B 表單已經改了金額（沒存），A 存了別的金額 → B 的修改不被換掉，B 存的是 B 的
    await a.click('.ex[data-edit="e1"]'); await s.click('.ex[data-edit="e1"]'); await a.wait_for_timeout(200)
    await s.fill('#f-amt', '5000')
    await a.fill('#f-note', 'A 改備註'); await a.click('#f-save'); await a.wait_for_timeout(600)
    rec("同時修改", "自己已經改過的欄位不會被對方的值換掉", await s.input_value('#f-amt') == "5000")
    await s.click('#f-save'); await s.wait_for_timeout(600)
    e = (await exps(a))["e1"]
    rec("同時修改", "B 存金額 5000、A 的備註保留", e["amt"] == 5000 and e["note"] == "A 改備註", e)
    # 刪除中
    await s.click('.ex[data-edit="e1"]'); await s.wait_for_timeout(200)
    await a.click('[data-del="e1"]'); await a.wait_for_timeout(300)
    if await a.query_selector('[data-del="e1"]'): await a.click('[data-del="e1"]')
    await a.wait_for_timeout(5800)
    st = await s.evaluate('({editing:editingId,msg:document.getElementById("acct-note")?.innerText||"",open:!!document.querySelector(".exp-sheet:not(.leaving)")})')
    rec("同時修改", "對方刪掉正在修改的帳：關掉修改面板並提示", st["editing"] is None and "對方刪掉" in st["msg"] and not st["open"], st)
    await S.expopen(s); await s.fill('#f-amt', '3100'); await s.fill('#f-note', '新的一筆'); await s.click('#f-save'); await s.wait_for_timeout(500)
    rec("同時修改", "被刪掉的那筆不會被寫回來", "e1" not in await exps(a))
    rec("同時修改", "沒有錯誤", not a.errs and not s.errs, (a.errs + s.errs)[:2])
    await ctx.close()
    # 離線時修改：恢復後只寫有改的欄位
    ctx = await mkctx(b, fs=S.FSO)
    a = await opn(ctx, ft.jst(11, 19, 20), init=seed({**META, f"{B}/expenses/e2": EXP(note="晚餐")}), wait=1200)
    await tab(a, "acct"); await a.evaluate('__goOffline()')
    await a.click('.ex[data-edit="e2"]'); await a.wait_for_timeout(200); await a.fill('#f-amt', '4100'); await a.click('#f-save'); await a.wait_for_timeout(300)
    await a.evaluate(f'''(()=>{{const d=JSON.parse(localStorage.getItem("mockdb"));d["{B}/expenses/e2"].note="對方改的備註";localStorage.setItem("mockdb",JSON.stringify(d))}})()''')
    await a.evaluate('__goOnline()'); await a.wait_for_timeout(800)
    e = (await exps(a))["e2"]
    rec("同時修改", "離線改金額、對方同時改備註：恢復後兩個都保留", e["amt"] == 4100 and e["note"] == "對方改的備註", e)
    await ctx.close()

async def times(b):
    for t, want_now, flag in [(ft.twt(11, 17, 5, 30), "1 小時 35 分後", "next"), (ft.twt(11, 17, 6, 30), "35 分後", "next"), (ft.twt(11, 17, 6, 10), "55 分後", "next")]:
        ctx = await mkctx(b, tz="Asia/Taipei"); pg = await opn(ctx, t, init=seed(META))
        v = await pg.evaluate('(()=>{const s=dayStatus(DAYS[0]);return{now:document.querySelector(".nowcard")?.innerText.replace(/\\s+/g," "),f:s.st[0],fab:document.querySelector(".fab")?.innerText.replace(/\\s+/g," ")}})()')
        rec("時區", f"台灣 {t:%H:%M}：JX 320 是「接下來」、{want_now}", v["f"] == flag and want_now in (v["now"] or "") and "JX 320" in (v["now"] or ""), v)
        await ctx.close()
    ctx = await mkctx(b); pg = await opn(ctx, ft.jst(11, 17, 21), init=seed(META))
    v = await pg.evaluate('document.querySelector(".nowcard")?.innerText.replace(/\\s+/g," ")')
    rec("時區", "11/17 21:00 晚餐進行中：卡片寫「進行中 すゞ家」，不是都走完了", "進行中" in (v or "") and "すゞ家" in (v or "") and "都走完了" not in (v or ""), v)
    await ctx.close()
    ctx = await mkctx(b); pg = await opn(ctx, ft.jst(11, 17, 22, 30), init=seed(META))
    v = await pg.evaluate('document.querySelector(".nowcard")?.innerText.replace(/\\s+/g," ")')
    rec("時區", "11/17 22:30 都結束後才顯示「都走完了」", "都走完了" in (v or ""), v)
    await ctx.close()
    ctx = await mkctx(b); pg = await opn(ctx, ft.jst(11, 24, 15), init=seed(META)); await home(pg)
    v = await pg.evaluate('document.body.innerText')
    rec("時區", "11/24 15:00 不再寫「今天才剛開始」", "今天才剛開始" not in v and "回到家後" in v)
    await ctx.close()

async def overdue(b):
    items = {f"{B}/items/{k}": {"group": "prep", "title": t, "note": "", "due": d, "order": i + 1} for i, (k, t, d) in enumerate([("a", "過期13小時", "11/18 23:00"), ("c", "過期3天", "11/16"), ("d", "已勾的過期", "11/16"), ("f", "下個月", "12/01")])}
    ctx = await mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed({**META, **items, f"{B}/checks/d": {"done": True}})); await home(pg)
    al = await pg.evaluate('document.getElementById("due-alerts")?.innerText||""')
    rec("過期待辦", "過期 13 小時、3 天的都還在首頁", "過期13小時" in al and "過期3天" in al, al.replace("\n", " ")[:200])
    rec("過期待辦", "已勾的、還很久的不出現", "已勾的過期" not in al and "下個月" not in al)
    await pg.click('#due-alerts [data-done-id="c"]'); await pg.wait_for_timeout(300)
    al = await pg.evaluate('document.getElementById("due-alerts")?.innerText||""')
    rec("過期待辦", "按「完成」後才消失", "過期3天" not in al)
    await ctx.close()

async def rate(b):
    ctx = await mkctx(b, fs=S.FSO); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed({**META, f"{B}/settings/rate": {"jpyTwd": 0.21, "auto": False, "ts": 5}}), wait=1200)
    await tab(pg, "acct")
    for bad in ["9.9", "0.0001", "abc"]:
        await pg.fill('#f-rate', bad); await pg.dispatch_event('#f-rate', 'change'); await pg.wait_for_timeout(200)
        r = await pg.evaluate('({rate,v:document.getElementById("f-rate").value,n:document.querySelector(".rate-note")?.innerText})')
        rec("匯率", f"手動輸入 {bad} 不採用並提示範圍", r["rate"] == 0.21 and "0.1～0.5" in (r["n"] or ""), r)
    await pg.fill('#f-rate', '0.22'); await pg.dispatch_event('#f-rate', 'change'); await pg.wait_for_timeout(300)
    rec("匯率", "0.22 可以用、雲端存成手動", (await cloud(pg)).get(f"{B}/settings/rate", {}).get("jpyTwd") == 0.22)
    await pg.evaluate('__goOffline()')
    await pg.click('[data-rate-auto]'); await pg.wait_for_timeout(300)
    await pg.evaluate('__goOnline()'); await pg.wait_for_timeout(500)
    rt = (await cloud(pg)).get(f"{B}/settings/rate", {})
    await pg.reload(); await pg.wait_for_timeout(1500); await tab(pg, "acct")
    n = await pg.evaluate('document.querySelector(".rate-note")?.innerText||""')
    rec("匯率", "離線按「改回自動」：雲端改成自動，重開後仍是自動", rt.get("auto") is True and "手動" not in n, {"雲端": rt, "重開": n})
    await ctx.close()

async def tel_and_cash(b):
    ctx = await mkctx(b)
    pg = await opn(ctx, ft.jst(11, 19, 12), init=seed({**META, f"{B}/settings/sos": {"ins": "國泰", "insTel": "+886-2-2755-1299 #3"}, f"{B}/wallet/zhang": {"cashIn": 10000, "ts": 1},
                                                         f"{B}/expenses/x": EXP(amt=12500, note="大筆現金")}))
    await pg.evaluate("openSos()"); await pg.wait_for_timeout(300); await pg.click("[data-sos-tab=emg]"); await pg.wait_for_timeout(300)
    hrefs = await pg.evaluate('[...document.querySelectorAll(".sos-tel")].map(a=>a.getAttribute("href")).filter(Boolean)')
    rec("求助", "旅平險電話分機用「,」隔開", "tel:+886227551299,3" in hrefs, hrefs[-2:])
    await pg.evaluate('document.querySelector(".sheet-modal .sm-x")?.click()'); await pg.wait_for_timeout(350)
    await tab(pg, "acct"); chip = await pg.inner_text('.wchip')
    await pg.click('.wchip'); await pg.wait_for_timeout(200); hero = await pg.inner_text('.ws-hero')
    await home(pg); hp = await pg.evaluate('document.querySelector(".hp-yen")?.innerText||""')
    allt = chip + hero + hp
    rec("現金", "超支時寫「超支 ¥2,500」，不出現 ¥-", "超支 ¥2,500" in chip and "超支 ¥2,500" in hero and "¥-" not in allt, [chip, hero, hp])
    rec("現金", "超支時提示可能記錯付款方式（不是快用完了）", "記錯付款方式" in hero and "快用完了" not in hero, hero)
    await ctx.close()

async def code_flow(b):
    # 格式錯
    ctx = await mkctx(b); pg = await opn(ctx, ft.twt(11, 5, 20), init='localStorage.removeItem("ngy:code");')
    await tab(pg, "list"); await pg.fill('#f-code', 'neko qa'); await pg.click('#code-form .primary'); await pg.wait_for_timeout(800)
    s = await pg.evaluate(S.SYNC)
    rec("代碼", "含空白的代碼：提示格式，不連線", "不能有空白" in s and await pg.evaluate('localStorage.getItem("ngy:code")') is None, s)
    # 打錯（旅程不存在）→ 提示，不寫入任何資料
    await pg.fill('#f-code', 'neko-typo'); await pg.click('#code-form .primary'); await pg.wait_for_timeout(1200)
    s = await pg.evaluate('document.getElementById("new-trip")?.innerText||""'); db = await cloud(pg)
    rec("代碼", "不存在的旅程：問要不要開新旅程", "找不到" in s and "開新旅程" in s, s)
    rec("代碼", "確認前不寫任何資料、不算連上", not any(k.startswith("trips/neko-typo/") for k in db) and not await pg.evaluate('live'), [k for k in db][:3])
    await pg.click('[data-newtrip-no]'); await pg.wait_for_timeout(300)
    rec("代碼", "「重新輸入」回到代碼表單", await pg.query_selector('#f-code') is not None)
    await pg.fill('#f-code', 'neko-typo'); await pg.click('#code-form .primary'); await pg.wait_for_timeout(1200)
    await pg.click('[data-newtrip-ok]'); await pg.wait_for_timeout(1500)
    db = await cloud(pg)
    rec("代碼", "「開新旅程」後連上並建立清單", await pg.evaluate('live') and "trips/neko-typo/settings/meta" in db)
    await ctx.close()
    # 已存在的旅程：直接連上
    ctx = await mkctx(b); pg = await opn(ctx, ft.twt(11, 5, 20), init=seed(META) + 'localStorage.removeItem("ngy:code");')
    await tab(pg, "list"); await pg.fill('#f-code', S.CODE); await pg.click('#code-form .primary'); await pg.wait_for_timeout(1500)
    rec("代碼", "輸入存在的旅程代碼：直接連上", await pg.evaluate('live') and not await pg.query_selector('#new-trip'))
    # 看代碼／換代碼
    await pg.click('[data-sync-info]'); await pg.wait_for_timeout(200)
    info = await pg.evaluate('document.getElementById("code-info")?.innerText||""')
    rec("代碼", "點同步膠囊看得到目前代碼後 4 碼", "sync" in info and "neko-sync" not in info, info.replace("\n", " "))
    await pg.click('[data-code-change]'); await pg.wait_for_timeout(300)
    rec("代碼", "「換一個代碼」回到代碼表單、停止同步", await pg.query_selector('#f-code') is not None and not await pg.evaluate('live'))
    rec("代碼", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
    # 有變更還沒同步時不能換代碼
    ctx = await mkctx(b, fs=S.FSO); pg = await opn(ctx, ft.twt(11, 5, 20), init=seed(META), wait=1200)
    await pg.evaluate('__goOffline()'); await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '100'); await pg.click('#f-save'); await pg.wait_for_timeout(400)
    await pg.click('[data-sync-info]'); await pg.wait_for_timeout(200)
    info = await pg.evaluate('document.getElementById("code-info")?.innerText||""')
    rec("代碼", "還有變更沒同步時不提供換代碼", "還沒同步" in info and not await pg.query_selector('[data-code-change]'), info.replace("\n", " "))
    await ctx.close()

async def no_me(b):
    ctx = await mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META) + 'localStorage.removeItem("ngy:me");')
    await tab(pg, "acct"); await S.expopen(pg)
    sel = await pg.evaluate('document.querySelector("[data-pick=who] [aria-pressed=true]")?.dataset.v||null')
    rec("身分", "沒選身分時「誰付的」不預設阿彰", sel is None, sel)
    await pg.fill('#f-amt', '800'); await pg.fill('#f-note', '星星第一筆'); await pg.click('#f-save'); await pg.wait_for_timeout(200)
    rec("身分", "沒選誰付的：提示且不寫入", "誰付的" in await pg.inner_text('#f-msg') and not any(v.get("note") == "星星第一筆" for v in (await exps(pg)).values()))
    await pg.click('[data-pick="who"] [data-v="star"]'); await pg.click('#f-save'); await pg.wait_for_timeout(300)
    rows = [v for v in (await exps(pg)).values() if v.get("note") == "星星第一筆"]
    rec("身分", "選了星星後記成星星付", len(rows) == 1 and rows[0]["who"] == "star", rows)
    await ctx.close()

async def rapid(b):
    ctx = await mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await tab(pg, "list"); await pg.click('[data-list-tab="buy"]'); await pg.wait_for_timeout(200); await pg.click('[data-item-new="buy"]'); await pg.fill('.chk-form input[name=title]', '連點')
    await pg.evaluate('(()=>{const b=document.querySelector(".chk-form .primary");for(let i=0;i<10;i++)b.click()})()'); await pg.wait_for_timeout(600)
    rec("連點", "「新增」同一輪點 10 次只新增 1 筆", sum(1 for k, v in (await cloud(pg)).items() if "/items/" in k and v.get("title") == "連點") == 1)
    await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '450'); await pg.fill('#f-note', '連點記帳')
    await pg.evaluate('(()=>{const b=document.getElementById("f-save");b.click();b.click();b.click()})()'); await pg.wait_for_timeout(300)
    m = await pg.evaluate(S.NOTE)
    rec("連點", "「記下這筆」連點只記 1 筆，訊息仍是已記下", sum(1 for v in (await exps(pg)).values() if v.get("note") == "連點記帳") == 1 and "已記下" in m, m)
    await ctx.close()
    ctx = await mkctx(b); pg = await opn(ctx, ft.jst(11, 17, 23, 30), init=seed(META))
    await home(pg)
    await pg.evaluate('(()=>{window.__opens=[];window.open=function(){window.__opens.push(1);return null}})()')
    if await pg.query_selector('.fab:not([hidden])'):
        await pg.evaluate('(()=>{const f=document.querySelector(".fab");for(let i=0;i<10;i++)f.click()})()'); await pg.wait_for_timeout(200)
        rec("連點", "「回家」連點 10 次只開 1 次地圖", len(await pg.evaluate('window.__opens')) == 1, await pg.evaluate('window.__opens'))
    else: rec("連點", "找得到「回家」按鈕", False)
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in [amount, edit_defaults, conflict, times, overdue, rate, tel_and_cash, code_flow, no_me, rapid]:
            try: await f(b)
            except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
        await b.close()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
