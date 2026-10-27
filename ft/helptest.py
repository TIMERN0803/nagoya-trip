# 第三批 3A 回歸測試：首頁和當天行程頁有求助（其他頁不放，使用者決定）、求助面板的飯店捷徑、「給司機看」只有按 × 或 Esc 才關閉、
# 橫向可捲動、所有面板的 aria-modal／焦點／Esc／Tab 限制、地圖檢視器、窄螢幕標題列不擠爆
# 一律用假資料庫（synctest.mkctx 的攔截）
import asyncio
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
rec = ft.rec
B, META, seed, opn, tab = S.B, S.META, S.seed, S.opn, S.tab
WALLET = {**META, f"{B}/wallet/zhang": {"cashIn": 30000, "ts": 1}}
async def home(pg): await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(700)  # 換頁轉場 0.5 秒
async def day(pg, i=2): await pg.evaluate(f'tab="plan";view="day";dayIdx={i};render()'); await pg.wait_for_timeout(700)
async def pack(pg):
    await pg.evaluate('tab="list";listSub="pack";render()'); await pg.wait_for_timeout(700)
PAGES = [("首頁", home), ("當天行程", day), ("天氣", lambda p: tab(p, "wx")), ("交通", lambda p: tab(p, "move")), ("記帳", lambda p: tab(p, "acct")), ("清單", lambda p: tab(p, "list")), ("行李", pack)]
active = 'document.activeElement?(document.activeElement.className||document.activeElement.tagName):""'

async def entry(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 20), init=seed(WALLET))
    for name, go in PAGES:
        await go(pg)
        n = await pg.evaluate('[...document.querySelectorAll("[data-sos]")].filter(e=>{const r=e.getBoundingClientRect();return r.width>=44&&r.height>=44&&r.top>=0&&r.right<=innerWidth}).length')
        if name in ("首頁", "當天行程"): rec("求助入口", f"{name}：看得到求助按鈕（至少 44×44）", n >= 1, n)
        else: rec("求助入口", f"{name}：不放求助（標題列保持簡單）", n == 0, n)
    # 從當天行程頁到給司機看：2 下
    await day(pg)
    await pg.click('.bar [data-sos]'); await pg.wait_for_timeout(300)
    q = await pg.evaluate('document.querySelector(".sos-quick")?.innerText.replace(/\\s+/g," ")||""')
    rec("求助入口", "求助面板一打開最上面就是飯店地址捷徑", "飯店地址給司機看" in q and "ランプライト" in q, q)
    await pg.click('.sos-quick .sq-main'); await pg.wait_for_timeout(300)
    t = await pg.evaluate('document.querySelector(".sos-show")?.innerText||""')
    rec("求助入口", "行程頁按 2 下就是給司機看的飯店地址", "この住所までお願いします" in t and "錦1丁目13-18" in t, t[:60])
    await pg.click('.sos-show .sm-x'); await pg.wait_for_timeout(350)
    q2 = await pg.evaluate('document.querySelector(".sos").innerText')
    rec("求助入口", "日常日文分頁不出現緊急電話", "緊急電話" not in q2 and "110" not in q2)
    await pg.click('[data-sos-tab="emg"]'); await pg.wait_for_timeout(200)
    rec("求助入口", "緊急分頁最上面就是飯店「給司機看」", await pg.evaluate('(()=>{const b=document.querySelector(".sos [data-sos-show=hotel]");return !!b&&b.getBoundingClientRect().top<innerHeight*0.7})()'))
    rec("求助入口", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def driver(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 20), init=seed(META))
    await day(pg); await pg.click('.bar [data-sos]'); await pg.wait_for_timeout(300)
    await pg.click('.sos-quick .sq-main'); await pg.wait_for_timeout(300)
    f = await pg.evaluate(active)
    rec("給司機看", "打開後焦點在大字上（讀螢幕會讀地址）", "s-body" in f, f)
    rec("給司機看", "aria-modal、名稱是飯店地址", await pg.evaluate('(()=>{const v=document.querySelector(".sos-show");return v.getAttribute("aria-modal")==="true"&&/飯店地址/.test(v.getAttribute("aria-label"))})()'))
    for sel in ['.s-big', '.s-lead', '.s-mid', '.s-zh']:
        await pg.click(f'.sos-show {sel}'); await pg.wait_for_timeout(120)
        rec("給司機看", f"點到 {sel} 不會關閉", await pg.query_selector('.sos-show') is not None)
    await pg.mouse.click(30, 820); await pg.wait_for_timeout(120)
    rec("給司機看", "點到空白處不會關閉", await pg.query_selector('.sos-show') is not None)
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(350)
    rec("給司機看", "Esc 只關掉全螢幕，求助面板還在", not await pg.query_selector('.sos-show') and await pg.query_selector('.sheet-modal .sos') is not None)
    rec("給司機看", "關閉後焦點回到求助面板裡", await pg.evaluate('!!document.activeElement?.closest(".sheet-modal")'), await pg.evaluate(active))
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(350)
    rec("給司機看", "再按 Esc 關掉求助面板，焦點回到求助按鈕", not await pg.query_selector('.sheet-modal') and await pg.evaluate('!!document.activeElement?.matches("[data-sos]")'), await pg.evaluate(active))
    # 直向：內容放得下時置中、× 點得到
    await pg.click('.bar [data-sos]'); await pg.wait_for_timeout(300); await pg.click('.sos-quick .sq-main'); await pg.wait_for_timeout(300)
    p = await pg.evaluate('(()=>{const v=document.querySelector(".sos-show"),b=v.querySelector(".s-body").getBoundingClientRect(),x=v.querySelector(".sm-x").getBoundingClientRect();return{top:Math.round(b.top),bot:Math.round(b.bottom),vh:innerHeight,scroll:v.scrollHeight>v.clientHeight,xr:Math.round(x.right),xt:Math.round(x.top)}})()')
    rec("給司機看", "直向 390×844：內容置中、不用捲動", p["top"] > 72 and p["bot"] < p["vh"] and not p["scroll"], p)
    await pg.click('.sos-show .sm-x'); await pg.wait_for_timeout(350)
    rec("給司機看", "按 × 關閉", not await pg.query_selector('.sos-show'))
    # 橫向：第一行看得到、可以捲到底、捲動時 × 一直在
    for w, h in [(844, 390), (667, 375), (568, 320)]:
        await pg.set_viewport_size({"width": w, "height": h}); await pg.wait_for_timeout(150)
        await pg.click('.sos-quick .sq-main'); await pg.wait_for_timeout(300)
        a = await pg.evaluate('(()=>{const v=document.querySelector(".sos-show"),l=v.querySelector(".s-lead").getBoundingClientRect();return{lead:Math.round(l.top),sh:v.scrollHeight,ch:v.clientHeight}})()')
        await pg.evaluate('document.querySelector(".sos-show").scrollTop=9999'); await pg.wait_for_timeout(100)
        z = await pg.evaluate('(()=>{const v=document.querySelector(".sos-show"),s=v.querySelector(".s-say").getBoundingClientRect(),x=v.querySelector(".sm-x").getBoundingClientRect(),hit=document.elementFromPoint(x.x+x.width/2,x.y+x.height/2);return{say:Math.round(s.bottom),vh:innerHeight,xhit:!!hit?.closest(".sm-x"),ltop:Math.round(v.querySelector(".s-lead").getBoundingClientRect().right)}})()')
        rec("給司機看", f"橫向 {w}×{h}：「この住所までお願いします」在畫面內", 0 <= a["lead"] < h, a)
        rec("給司機看", f"橫向 {w}×{h}：捲到底看得到播放按鈕、× 點得到", z["say"] <= z["vh"] and z["xhit"], z)
        await pg.click('.sos-show .sm-x'); await pg.wait_for_timeout(350)
    rec("給司機看", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

SHEETS = [("求助", "[data-sos]", ".sheet-modal .sos"), ("錢包", "[data-wallet-open]", ".sheet-modal .ws"), ("出發前設定", "[data-setup-open]", ".sheet-modal .su-sheet")]
async def sheets(b):
    ctx = await S.mkctx(b, tz="Asia/Taipei"); pg = await opn(ctx, ft.twt(10, 26, 18), init=seed(WALLET))
    await home(pg)
    for name, opener, inside in SHEETS:
        await pg.focus(opener); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(300)
        ok = await pg.query_selector(inside) is not None
        st = await pg.evaluate('(()=>{const v=document.querySelector(".sheet-modal");return{modal:v?.getAttribute("aria-modal"),role:v?.getAttribute("role"),inside:!!document.activeElement?.closest(".sheet-modal")}})()')
        rec("面板", f"{name}：鍵盤打開、aria-modal、焦點在面板裡", ok and st["modal"] == "true" and st["role"] == "dialog" and st["inside"], st)
        outside = 0
        for i in range(40):
            await pg.keyboard.press("Tab")
            if not await pg.evaluate('!!document.activeElement?.closest(".sheet-modal")'): outside += 1
        for i in range(10):
            await pg.keyboard.press("Shift+Tab")
            if not await pg.evaluate('!!document.activeElement?.closest(".sheet-modal")'): outside += 1
        rec("面板", f"{name}：Tab／Shift+Tab 不會跑到面板後面", outside == 0, outside)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(350)
        back = await pg.evaluate(f'!!document.activeElement?.matches({opener!r})')
        rec("面板", f"{name}：Esc 關閉、焦點回到原本的按鈕", not await pg.query_selector('.sheet-modal') and back, await pg.evaluate(active))
    # 行事曆從出發前設定裡打開：疊兩層，Esc 一層一層關
    await pg.evaluate('openSetup()'); await pg.wait_for_timeout(250); await pg.evaluate('openCalSheet()'); await pg.wait_for_timeout(250)
    n2 = await pg.evaluate('document.querySelectorAll(".sheet-modal").length')
    await pg.keyboard.press("Escape"); await pg.clock.run_for(300); await pg.wait_for_timeout(350)
    n1 = await pg.evaluate('document.querySelectorAll(".sheet-modal").length')
    await pg.keyboard.press("Escape"); await pg.clock.run_for(300); await pg.wait_for_timeout(350)
    n0 = await pg.evaluate('document.querySelectorAll(".sheet-modal").length')
    rec("面板", "兩層面板：Esc 一次關一層", [n2, n1, n0] == [2, 1, 0], [n2, n1, n0])
    # 點背景關閉仍然有效、按 × 關閉後焦點回去
    await pg.click('[data-sos]'); await pg.wait_for_timeout(250); await pg.mouse.click(195, 10); await pg.wait_for_timeout(350)
    rec("面板", "點面板外的暗處仍可關閉", not await pg.query_selector('.sheet-modal'))
    # 正在輸入時按 Esc：關閉面板（不會卡住）
    await pg.click('[data-wallet-open]'); await pg.wait_for_timeout(250)
    await pg.click('.ws [data-wallet-edit][data-mode="add"]'); await pg.wait_for_timeout(350); await pg.focus('.ws .w-form input'); await pg.keyboard.press("Escape"); await pg.wait_for_timeout(350)
    rec("面板", "錢包輸入中按 Esc 也能關閉", not await pg.query_selector('.sheet-modal'))
    rec("面板", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def viewer(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 18, 12), init=seed(META))
    await day(pg, 1)
    await pg.click('[data-map]'); await pg.wait_for_timeout(300)
    rec("地圖檢視器", "打開後焦點在關閉鈕、aria-modal", await pg.evaluate('document.activeElement?.classList.contains("vclose")&&document.querySelector(".viewer").getAttribute("aria-modal")==="true"'))
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(350)
    rec("地圖檢視器", "Esc 關閉、焦點回到地圖按鈕", not await pg.query_selector('.viewer') and await pg.evaluate('!!document.activeElement?.closest("[data-map]")'), await pg.evaluate(active))
    c = await ctx.new_cdp_session(pg); await c.send("Performance.enable")
    async def L():
        await c.send("HeapProfiler.collectGarbage"); m = await c.send("Performance.getMetrics"); return {x["name"]: x["value"] for x in m["metrics"]}["JSEventListeners"]
    a = await L()
    for i in range(30): await pg.evaluate('openViewer("ghibli-map.jpg","x");document.querySelector(".viewer:not(.leaving) .vclose").click()')
    for i in range(20): await pg.evaluate('openSos();document.querySelector(".sheet-modal:not(.leaving) .sm-x").click();openWallet();document.querySelector(".sheet-modal:not(.leaving) .sm-x").click()')
    # 關閉有 0.18 秒退場動畫（測試用假時鐘），先讓計時器跑完再量
    await pg.clock.run_for(300); await pg.wait_for_timeout(300); z = await L()
    rec("地圖檢視器", "連續開關 30 次地圖＋40 次面板：沒有殘留畫面、listener 不增加", abs(z - a) <= 5 and await pg.evaluate('document.querySelectorAll(".viewer,.sheet-modal").length') == 0 and await pg.evaluate('modals.length') == 0, [a, z])
    await c.detach(); await ctx.close()
    # 出發前、沒有任何按鈕有焦點時連續開關（上次會讓每個面板留住前一個面板）
    for nm, js, t in [("求助", 'openSos();document.querySelector(".sheet-modal:not(.leaving) .sm-x").click()', ft.jst(11, 10, 12)), ("錢包", 'openWallet();document.querySelector(".sheet-modal:not(.leaving) .sm-x").click()', ft.jst(11, 10, 12)),
                      ("出發前設定", 'openSetup();document.querySelector(".sheet-modal:not(.leaving) .sm-x").click()', ft.jst(11, 10, 12)), ("給司機看", 'sosShow("hotel");document.querySelector(".sos-show:not(.leaving) .sm-x").click()', ft.jst(11, 10, 12)),
                      ("地圖", 'openViewer("ghibli-map.jpg","x");document.querySelector(".viewer:not(.leaving) .vclose").click()', ft.jst(11, 10, 12)), ("回顧故事", 'openStory();document.querySelector(".story:not(.leaving) .st-x").click()', ft.jst(11, 26, 12))]:
        ctx = await S.mkctx(b); pg = await opn(ctx, t, init=seed(META)); await home(pg)
        c = await ctx.new_cdp_session(pg); await c.send("Performance.enable")
        a = await L2(c)
        for i in range(30): await pg.evaluate(js)
        await pg.clock.run_for(300); await pg.wait_for_timeout(400); z = await L2(c)
        rec("記憶體", f"{nm}：沒有焦點時連續開關 30 次，listener 不增加", z - a <= 3, [a, z])
        await c.detach(); await ctx.close()
async def L2(c):
    await c.send("HeapProfiler.collectGarbage"); m = await c.send("Performance.getMetrics"); return {x["name"]: x["value"] for x in m["metrics"]}["JSEventListeners"]

async def narrow(b):
    for w in [320, 360, 390]:
        ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 20), init=seed(WALLET))
        await pg.set_viewport_size({"width": w, "height": 740}); await pg.wait_for_timeout(150)
        for name, go in [x for x in PAGES[1:] if x[0] != "記帳"]:  # 記帳頁 320px 的擁擠留到 3B 一起處理
            await go(pg)
            r = await pg.evaluate('(()=>{const b=document.querySelector("header.bar");const kids=[...b.querySelectorAll(":scope>*,:scope .bar-r>*")].filter(e=>e.getClientRects().length).map(e=>e.getBoundingClientRect());const over=kids.filter(k=>k.right>innerWidth+0.5||k.left<-0.5).length;const tall=b.getBoundingClientRect().height;const h1=b.querySelector("h1");let lines=0;if(h1){const g=document.createRange();g.selectNodeContents(h1);lines=new Set([...g.getClientRects()].map(x=>Math.round(x.top))).size}return{sw:document.documentElement.scrollWidth,over,tall:Math.round(tall),lines}})()')
            rec("窄螢幕", f"{w}px {name}：標題列沒有超出畫面、沒有水平捲動、標題一行", r["over"] == 0 and r["sw"] <= w and r["lines"] <= 1 and r["tall"] <= 64, r)
        rec("窄螢幕", f"{w}px 沒有錯誤", not pg.errs, pg.errs[:2])
        await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in [entry, driver, sheets, viewer, narrow]:
            try: await f(b)
            except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
        await b.close()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
