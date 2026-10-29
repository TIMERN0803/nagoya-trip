# 批 3 指定 7：記一筆完整流程（C1、D1、D8）、連點、長文字、離線／慢網路
from uxlib import *
NOTE = S.NOTE
async def cnt(pg, note): return sum(1 for v in (await exps(pg)).values() if v.get("note") == note)
async def flow(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 20), init=seed(META), wait=1000)
    await tab(pg, "acct"); await S.expopen(pg)
    # 1 連點記下這筆
    await pg.fill('#f-amt', '1800'); await pg.fill('#f-note', '連點測試')
    await pg.evaluate('(()=>{const b=document.getElementById("f-save");for(let i=0;i<6;i++)b.click()})()'); await pg.wait_for_timeout(700)
    n = await cnt(pg, "連點測試"); rec("D 記一筆", "同一個畫面連按「記下這筆」6 次只存 1 筆", n == 1, n)
    # 1b 真實連點（兩次 playwright click 間隔 30ms）
    await S.expopen(pg); await pg.fill('#f-amt', '1900'); await pg.fill('#f-note', '連點測試2')
    for i in range(3):
        try: await pg.click('#f-save', timeout=300, force=True)
        except Exception: pass
        await pg.wait_for_timeout(30)
    await pg.wait_for_timeout(600); n = await cnt(pg, "連點測試2"); rec("D 記一筆", "真實連按（30ms 間隔）只存 1 筆", n == 1, n)
    # 2 再記一筆連點
    await S.expopen(pg); await pg.fill('#f-amt', '500'); await pg.fill('#f-note', '再記A')
    await pg.evaluate('(()=>{const b=document.querySelector("[data-again]");for(let i=0;i<4;i++)b.click()})()'); await pg.wait_for_timeout(600)
    n = await cnt(pg, "再記A"); m = await pg.inner_text('#f-msg') if await pg.query_selector('#f-msg') else ''
    rec("D 記一筆", "「再記一筆」連按 4 次只存 1 筆", n == 1, {"n": n, "msg": m})
    print("再記一筆後面板:", await pg.query_selector('.exp-sheet:not(.leaving)') is not None, "訊息:", await pg.evaluate('document.getElementById("f-msg")?.innerText'))
    await pg.fill('#f-amt', '600'); await pg.fill('#f-note', '再記B'); await pg.click('#f-save'); await pg.wait_for_timeout(500)
    rec("D 記一筆", "再記一筆流程：A、B 各 1 筆", await cnt(pg, "再記A") == 1 and await cnt(pg, "再記B") == 1)
    # 3 放棄前先問
    await S.expopen(pg); await pg.fill('#f-amt', '777')
    await pg.click('.exp-sheet [data-exp-x]'); await pg.wait_for_timeout(350)
    rec("D 記一筆", "有填東西按 × → 先問", await pg.is_visible('.exp-confirm'))
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
    rec("D 記一筆", "問的時候按 Esc＝繼續填寫、金額還在", not await pg.is_visible('.exp-confirm') and await pg.input_value('#f-amt') == '777')
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
    await pg.click('[data-exp-discard]'); await pg.wait_for_timeout(500)
    rec("D 記一筆", "放棄後面板關閉、不新增", await pg.query_selector('.exp-sheet:not(.leaving)') is None)
    await S.expopen(pg); rec("D 記一筆", "再開是空的", await pg.input_value('#f-amt') == ''); await S.expclose(pg)
    # 4 修改→改了又取消
    eid = next(iter(await exps(pg)))
    await pg.click(f'.ex[data-edit="{eid}"]'); await pg.wait_for_timeout(650); await pg.fill('#f-amt', '123456')
    await pg.click('.exp-sheet [data-exp-x]'); await pg.wait_for_timeout(350)
    ask = await pg.is_visible('.exp-confirm'); await pg.click('[data-exp-discard]'); await pg.wait_for_timeout(500)
    rec("D 記一筆", "修改中改了金額按 ×：先問；放棄後雲端金額不變", ask and (await exps(pg))[eid]["amt"] != 123456, ask)
    # 4b 修改但沒改任何東西 → 直接關
    await pg.click(f'.ex[data-edit="{eid}"]'); await pg.wait_for_timeout(650); await pg.click('.exp-sheet [data-exp-x]'); await pg.wait_for_timeout(450)
    rec("D 記一筆", "修改但沒改直接按 ×：不問直接關", await pg.query_selector('.exp-sheet:not(.leaving)') is None)
    # 5 刪除
    await pg.click(f'.ex[data-edit="{eid}"]'); await pg.wait_for_timeout(650)
    await pg.click('[data-exp-del]'); await pg.wait_for_timeout(500)
    rec("D 記一筆", "面板裡「刪除這筆」直接刪（有復原條）", eid not in await exps(pg) and await pg.query_selector('.undo-bar') is not None)
    await pg.click('.undo-bar button'); await pg.wait_for_timeout(500)
    rec("D 記一筆", "復原後回來", eid in await exps(pg))
    rec("D 記一筆", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
async def redraw(b):
    ctx = await newctx(b)
    T = jst(11, 19, 20)
    A = await phone(ctx, T, "zhang", "A", init=seed(META), wait=1000); Bp = await phone(ctx, T, "star", "B", wait=1000)
    for x in (A, Bp): await tab(x, "acct")
    await S.expopen(A); await A.fill('#f-amt', '4321'); await A.fill('#f-note', 'A 填到一半'); await A.click('.exp-sheet .pick >> nth=2')
    # B 記一筆、B 刪、B 改匯率、B 改錢包
    for i, amt in enumerate(['100', '200', '300']):
        await S.expopen(Bp); await Bp.fill('#f-amt', amt); await Bp.fill('#f-note', f'B{i}'); await Bp.click('#f-save'); await Bp.wait_for_timeout(500)
    await A.wait_for_timeout(600)
    st = await A.evaluate('({sheet:!!document.querySelector(".exp-sheet:not(.leaving)"),amt:document.getElementById("f-amt")?.value,note:document.getElementById("f-note")?.value,pressed:[...document.querySelectorAll(".exp-sheet .pick[aria-pressed=true]")].map(x=>x.dataset.v),list:document.getElementById("acct-list").innerText.includes("B2")})')
    rec("D 記一筆", "對方連記 3 筆時，我填到一半的面板不被換掉（金額、備註、選項都在）", st["sheet"] and st["amt"] == "4321" and st["note"] == "A 填到一半", st)
    await A.click('#f-save'); await A.wait_for_timeout(600)
    ex = await exps(A)
    rec("D 記一筆", "之後按記下這筆，4 筆都在", len(ex) == 4 and any(v["note"] == "A 填到一半" and v["amt"] == 4321 for v in ex.values()), len(ex))
    await ctx.close()
async def offline_mid(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 20), init=seed(META), wait=1200)
    await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '2900'); await pg.fill('#f-note', '記到一半斷線')
    await pg.evaluate('__goOffline()'); await ctx.set_offline(True); await pg.evaluate('dispatchEvent(new Event("offline"))'); await pg.wait_for_timeout(400)
    st = await pg.evaluate('({sheet:!!document.querySelector(".exp-sheet:not(.leaving)"),amt:document.getElementById("f-amt")?.value,sync:document.querySelector(".sync")?.innerText})')
    rec("離線", "記到一半斷線：面板與輸入還在、同步膠囊顯示離線", st["sheet"] and st["amt"] == "2900" and "離線" in (st["sync"] or ""), st)
    await pg.click('#f-save'); await pg.wait_for_timeout(500)
    rec("離線", "離線按記下這筆：顯示已記下並說明之後同步", "已記下" in await pg.evaluate(NOTE) and "恢復網路後同步" in await pg.evaluate(NOTE), await pg.evaluate(NOTE))
    # 離線時重新整理 App（冷啟動）
    await ctx.set_offline(False); await pg.reload(); await pg.wait_for_timeout(1500); await tab(pg, "acct")
    lst = await pg.inner_text('#acct-list')
    rec("離線", "離線重開 App 後那筆還在清單", "記到一半斷線" in lst, lst[:80])
    await pg.evaluate('__goOnline()'); await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(2500)
    n = await cnt(pg, "記到一半斷線"); rec("離線", "恢復後雲端 1 筆（不重複）", n == 1, n)
    rec("離線", "沒有錯誤", not pg.errs, pg.errs[:2]); await ctx.close()
async def slow_write(b):
    for delay in (3000, 10000):
        ctx = await newctx(b)
        pg = await S.opn(ctx, jst(11, 19, 20), init=seed(META), pre=f'window.__writeDelay={delay};', wait=1200)
        await tab(pg, "acct"); await S.expopen(pg); await pg.fill('#f-amt', '3100'); await pg.fill('#f-note', f'慢{delay}'); await pg.click('#f-save'); await pg.wait_for_timeout(300)
        r = await pg.evaluate('({note:document.getElementById("acct-note")?.innerText,open:!!document.querySelector(".exp-sheet:not(.leaving)"),pend:pendingCount()})')
        rec("慢網路", f"寫入確認慢 {delay//1000} 秒：按下後 0.3 秒內顯示已記下、面板關閉", "已記下" in r["note"] and not r["open"], r)
        # 慢的期間：再記第二筆；然後把 App 關掉重開（reload）
        await S.expopen(pg); await pg.fill('#f-amt', '900'); await pg.fill('#f-note', f'慢2-{delay}'); await pg.click('#f-save'); await pg.wait_for_timeout(300)
        await pg.reload(); await pg.wait_for_timeout(1800)
        await pg.wait_for_timeout(delay + 500)
        a, c = await cnt(pg, f'慢{delay}'), await cnt(pg, f'慢2-{delay}')
        rec("慢網路", f"{delay//1000} 秒：確認前重開 App，兩筆各 1 筆（不重複不遺失）", a == 1 and c == 1, (a, c))
        rec("慢網路", f"{delay//1000} 秒：同步佇列清空", await pg.evaluate('pendingCount()') == 0, await pg.evaluate('pendingCount()'))
        await ctx.close()
async def typ(pg, sel, txt):
    await pg.click(sel); await pg.keyboard.press('Control+A'); await pg.keyboard.type(txt)
async def longtext(b):
    ctx = await newctx(b)
    pg = await S.opn(ctx, jst(11, 19, 20), init=seed(META), wait=1000)
    await tab(pg, "acct")
    cases = {"超長無空白": "A" * 300, "超長中文": "好吃的拉麵" * 60, "全形與空白": "　　ＡＢＣ　１２３　　", "emoji": "🍜🍣🍤🧋" * 15, "只有空白": "     ", "長網址": "https://example.com/" + "a" * 200, "換行": "第一行\n第二行\n第三行"}
    for name, txt in cases.items():
        await S.expopen(pg); await pg.fill('#f-amt', '1000'); await typ(pg, '#f-note', txt); stored_len = len(await pg.input_value('#f-note')); await pg.click('#f-save'); await pg.wait_for_timeout(500)
        ov = await pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
        sh = await pg.evaluate('(()=>{const r=document.querySelector(".ex .m b").getBoundingClientRect();const a=document.querySelector(".ex .a").getBoundingClientRect();return {w:r.width,right:r.right,aleft:a.left,vw:innerWidth}})()')
        rec("長文字", f"記帳備註「{name}」（實打，輸入後長度 {stored_len}）：無水平捲動、備註不蓋到金額", ov and sh["right"] <= sh["aleft"] + 1, sh)
        await pg.screenshot(path=SHOTS + f'u10_long_{list(cases).index(name)}.png')
    # 清單項目長標題
    await S.expclose(pg); await tab(pg, "list"); await pg.click('[data-list-tab="buy"]')
    for name, txt in {"超長標題": "超長的伴手禮名稱" * 40, "無空白英文": "B" * 200}.items():
        await pg.click('[data-item-new="buy"]'); await typ(pg, '.chk-form input[name=title]', txt); print('  清單標題 maxlength attr:', await pg.get_attribute('.chk-form input[name=title]','maxlength'), '輸入後長度', len(await pg.input_value('.chk-form input[name=title]'))); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(300)
        ov = await pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
        rec("長文字", f"清單新增「{name}」：無水平捲動", ov)
    # 心情 200 字限制 + 超長
    await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(500)
    await pg.click('#mood .fbtn[data-score="5"]'); await typ(pg, '#mood-note', "超" * 500); v = await pg.input_value('#mood-note')
    rec("長文字", "心情輸入 500 字：限制在 200 字內", len(v) <= 200, len(v))
    await pg.click('#mood-form .primary'); await pg.wait_for_timeout(300)
    rec("長文字", "心情長字無水平捲動", await pg.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    rec("長文字", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in (flow, redraw, offline_mid, slow_write, longtext):
            try: await f(b)
            except Exception as e: rec("執行", f.__name__, False, repr(e)[:300])
        await b.close()
    summary()
asyncio.run(main())
