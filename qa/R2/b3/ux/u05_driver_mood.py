# 批 3 指定 5：給司機看（C4）與心情（寫、改、兩人同時）
from uxlib import *
async def driver(b):
    ctx = await newctx(b, fs=None) if False else await S.mkctx(b)
    pg = await S.opn(ctx, jst(11, 19, 13), init=seed(META), wait=1200)
    await pg.click('[data-sos]'); await pg.wait_for_timeout(700)
    await pg.dblclick('.sos-quick [data-sos-show]'); await pg.wait_for_timeout(900)
    n = await pg.locator('.sos-show:not(.leaving)').count()
    rec("C4 給司機看", "連點（雙擊）只開 1 層", n == 1, n)
    # 點大字不關
    box = await pg.locator('.sos-show .s-big').bounding_box()
    await pg.mouse.click(box['x'] + 20, box['y'] + 10); await pg.wait_for_timeout(400)
    await pg.mouse.click(5, 400); await pg.wait_for_timeout(400)
    rec("C4 給司機看", "點大字與空白處不關閉", await pg.locator('.sos-show:not(.leaving)').count() == 1)
    # Tab 限制
    seq = []
    for i in range(6):
        await pg.keyboard.press("Tab"); seq.append(await pg.evaluate('document.activeElement.closest(".sos-show")?"in":(document.activeElement.className||document.activeElement.tagName)'))
    print("Tab x6 焦點:", seq)
    rec("C4 給司機看", "Tab 留在全螢幕層內", all(s == "in" for s in seq), seq)
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(500)
    rec("C4 給司機看", "Esc 關閉", await pg.locator('.sos-show:not(.leaving)').count() == 0)
    print("Esc 後焦點:", await pg.evaluate('document.activeElement.className||document.activeElement.tagName'))
    rec("C4 給司機看", "關閉後焦點回到求助面板內的按鈕", await pg.evaluate('!!document.activeElement.closest(".sheet-modal")'))
    # 直接按 × 關
    await pg.click('.sos-quick [data-sos-show]'); await pg.wait_for_timeout(700); await pg.click('.sos-show .sm-x'); await pg.wait_for_timeout(500)
    rec("C4 給司機看", "× 關閉", await pg.locator('.sos-show:not(.leaving)').count() == 0)
    # 直接在求助面板連按 Enter 兩次
    await pg.focus('.sos-quick [data-sos-show]'); await pg.keyboard.press("Enter"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(800)
    rec("C4 給司機看", "Enter 連按兩次只開 1 層", await pg.locator('.sos-show:not(.leaving)').count() == 1, await pg.locator('.sos-show:not(.leaving)').count())
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(400)
    # 橫拿
    await pg.set_viewport_size({'width': 844, 'height': 390}); await pg.wait_for_timeout(300)
    await pg.click('.sos-quick [data-sos-show]'); await pg.wait_for_timeout(800)
    m = await pg.evaluate('(()=>{const v=document.querySelector(".sos-show");const x=document.querySelector(".sos-show .sm-x").getBoundingClientRect();return{sh:v.scrollHeight,ch:v.clientHeight,xr:x.right,xt:x.top,ox:getComputedStyle(v).overflowY}})()')
    print("橫拿:", m)
    await pg.evaluate('document.querySelector(".sos-show").scrollTo(0,9999)'); await pg.wait_for_timeout(200)
    st = await pg.evaluate('document.querySelector(".sos-show").scrollTop')
    rec("C4 給司機看", "橫拿可捲動（內容比畫面高時 scrollTop>0）", m['sh'] <= m['ch'] or st > 0, {**m, "scrollTop": st})
    await pg.screenshot(path=SHOTS + 'u05_driver_landscape.png')
    # 層開著時按瀏覽器返回／切分頁？ 層開著時背後 App 重畫 (render) 不影響
    await pg.evaluate('render(true)'); await pg.wait_for_timeout(300)
    rec("C4 給司機看", "背後重畫（同步來資料）不會關掉層", await pg.locator('.sos-show:not(.leaving)').count() == 1)
    rec("C4 給司機看", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
async def mood(b):
    ctx = await newctx(b)
    T = jst(11, 19, 21)
    A = await phone(ctx, T, "zhang", "A", init=seed(META), wait=1200)
    Bp = await phone(ctx, T, "star", "B", wait=1200)
    for x in (A, Bp): await x.evaluate('tab="plan";view="day";dayIdx=2;render()'); await x.wait_for_timeout(500)
    # A 開始寫（選分數、打字、點空白處離開焦點），B 先送出
    await A.click('#mood .fbtn[data-score="4"]'); await A.fill('#mood-note', 'A 打到一半的心情'); await A.evaluate('document.activeElement.blur()')
    await Bp.click('#mood .fbtn[data-score="5"]'); await Bp.fill('#mood-note', 'B 的心情'); await Bp.click('#mood-form .primary'); await Bp.wait_for_timeout(900)
    v = await A.evaluate('({note:document.getElementById("mood-note")?.value,sc:document.querySelector("#mood .fbtn.on")?.dataset.score,txt:document.getElementById("mood").innerText.replace(/\\n/g," ")})')
    print("A 畫面:", v)
    rec("心情", "B 送出時 A 打到一半的字與分數還在", v["note"] == "A 打到一半的心情" and v["sc"] == "4", v)
    rec("心情", "A 看得到 B 的心情", "B 的心情" in v["txt"], v["txt"][:120])
    await A.click('#mood-form .primary'); await A.wait_for_timeout(800)
    for nm, x in (("A", A), ("B", Bp)):
        t = (await x.inner_text('#mood')).replace("\n", " ")
        rec("心情", f"{nm} 畫面看到兩人的心情", "A 打到一半的心情" in t and "B 的心情" in t, t[:150])
    # 同時改自己的（互不影響）＋ A 刪除自己的、B 刪除復原
    await A.click('[data-mood-edit]'); await A.wait_for_timeout(300); await A.fill('#mood-note', 'A 改過'); 
    await Bp.click('[data-mood-edit]'); await Bp.wait_for_timeout(300); await Bp.fill('#mood-note', 'B 改過')
    await A.click('#mood-form .primary'); await Bp.click('#mood-form .primary'); await A.wait_for_timeout(900)
    db = await cloud(A)
    ms = {k.split('/')[-1]: v["note"] for k, v in db.items() if "/moods/" in k}
    rec("心情", "同時各改自己的：雲端兩筆都是新內容", ms.get("11-19_zhang") == "A 改過" and ms.get("11-19_star") == "B 改過", ms)
    # 對方正在編輯時被刪
    await Bp.click('[data-mood-edit]'); await Bp.wait_for_timeout(300); await Bp.fill('#mood-note', 'B 編輯到一半')
    await A.click('[data-mood-edit]'); await A.wait_for_timeout(300)
    # A 刪自己（只影響 A）
    await A.click('[data-mood-del]'); await A.wait_for_timeout(300)
    if await A.query_selector('[data-mood-del]'): await A.click('[data-mood-del]')
    await A.wait_for_timeout(900)
    t = (await Bp.inner_text('#mood')).replace("\n", " ")
    print("B（編輯中）看到:", t[:160], "| 欄位:", await Bp.input_value('#mood-note') if await Bp.query_selector('#mood-note') else None)
    rec("心情", "A 刪自己的心情，B 編輯中的草稿不被洗掉", await Bp.query_selector('#mood-note') is not None and await Bp.input_value('#mood-note') == "B 編輯到一半")
    rec("心情", "沒有錯誤", not A.errs and not Bp.errs, (A.errs + Bp.errs)[:3])
    await A.screenshot(path=SHOTS + 'u05_mood_A.png')
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in (driver, mood):
            try: await f(b)
            except Exception as e: rec("執行", f.__name__, False, repr(e)[:300])
        await b.close()
    summary()
asyncio.run(main())
