# 第三批 3B 回歸測試：320px／200% 縮放（195px）不出現水平捲動、標題列不擠爆、大金額不撐破、
# 可點範圍至少 44 高、首頁「今天」對比、排序把手可用鍵盤移動
# 一律用假資料庫（synctest.mkctx 的攔截）
import asyncio
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
rec = ft.rec
B, META, seed, opn = S.B, S.META, S.seed, S.opn
DB = {**META, f"{B}/wallet/zhang": {"cashIn": 30000, "ts": 1},
      f"{B}/expenses/big": {"amt": 12345678, "cat": "buy", "who": "zhang", "split": "both", "pay": "card", "day": "11/19", "note": "大筆刷卡測試", "ts": 5},
      f"{B}/expenses/c1": {"amt": 1234567, "cat": "food", "who": "star", "split": "both", "pay": "cash", "day": "11/19", "note": "超長店名的味噌炸豬排專賣店名古屋本店", "ts": 6}}
PAGES = [("首頁", 'tab="plan";view="home"'), ("當天行程", 'tab="plan";view="day";dayIdx=2'), ("天氣", 'tab="wx"'), ("交通", 'tab="move"'),
         ("記帳", 'tab="acct"'), ("清單", 'tab="list";listSub=null'), ("行李", 'tab="list";listSub="pack"')]
HEAD = '''(()=>{const b=document.querySelector("header.bar,header.hud");const kids=[...b.querySelectorAll(":scope>*,:scope .bar-r>*")].filter(e=>e.getClientRects().length).map(e=>e.getBoundingClientRect());
 const h1=b.querySelector("h1");let lines=0;if(h1){const g=document.createRange();g.selectNodeContents(h1);lines=new Set([...g.getClientRects()].map(x=>Math.round(x.top))).size}
 const over=[...document.querySelectorAll("body *")].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&getComputedStyle(e).position!=="fixed"&&!e.closest("[style*=overflow],.days,.grid,.tl,.mood-strip,.scroll-x")}).slice(0,3).map(e=>e.className||e.tagName);
 return{sw:document.documentElement.scrollWidth,hover:kids.filter(k=>k.right>innerWidth+0.5||k.left<-0.5).length,lines,over}})()'''

async def widths(b):
    for w in [320, 360, 195]:
        ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 20), init=seed(DB)); await pg.set_viewport_size({"width": w, "height": 740})
        for name, js in PAGES:
            await pg.evaluate(js + ';render();scrollTo(0,0)'); await pg.wait_for_timeout(250)
            r = await pg.evaluate(HEAD)
            # 200% 縮放（195px）時標題可以換行（WCAG 只要求不用左右捲動）
            rec("版面", f"{w}px {name}：沒有水平捲動、標題列不超出" + ("、標題一行" if w >= 320 else ""), r["sw"] <= w and r["hover"] == 0 and (w < 320 or r["lines"] <= 1), r)
        rec("版面", f"{w}px 沒有錯誤", not pg.errs, pg.errs[:2])
        await ctx.close()
    # 大金額：總額、誰付多少、單筆金額都在畫面內
    for w in [320, 195]:
        ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 20), init=seed(DB)); await pg.set_viewport_size({"width": w, "height": 740})
        await pg.evaluate('tab="acct";render()'); await pg.wait_for_timeout(250)
        r = await pg.evaluate('(()=>{const els=[...document.querySelectorAll("#acct-sum .v,#acct-sum .r,.ex .a")];return els.map(e=>Math.round(e.getBoundingClientRect().right)).filter(x=>x>innerWidth).length})()')
        rec("版面", f"{w}px ¥12,345,678：總額、誰付多少、單筆金額都在畫面內", r == 0, r)
        await ctx.close()

TARGETS = ".pick:not([data-pick=cat] .pick),.hud-pill,.edit-btn,.leg a,.da-done,.linkbtn,.sort-btn,.chip,.bar .back,.drag-h,.hud-sos,.bar-sos,.wchip,.sync[data-sync-info]"
HIT = '''(sel)=>{const out=[];for(const e of document.querySelectorAll(sel)){const r=e.getBoundingClientRect();if(!r.width||r.top<70||r.bottom>innerHeight-110)continue;
 const cx=r.left+r.width/2,cy=r.top+r.height/2;const ok=[cy-21,cy+21].every(y=>{const h=document.elementFromPoint(cx,y);return h&&(e===h||e.contains(h))});
 if(!ok)out.push((e.className||e.tagName)+"「"+(e.innerText||e.getAttribute("aria-label")||"").trim().slice(0,10)+"」"+Math.round(r.height))}return out}'''
async def touch(b):
    for t, tz, pages in [(ft.jst(11, 19, 20), "Asia/Tokyo", PAGES), (ft.twt(10, 26, 20), "Asia/Taipei", [("出發前首頁", 'tab="plan";view="home"'), ("出發前清單", 'tab="list";listSub=null')])]:
        ctx = await S.mkctx(b, tz=tz); pg = await opn(ctx, t, init=seed(DB))
        for name, js in pages:
            await pg.evaluate(js + ';render();scrollTo(0,0)'); await pg.wait_for_timeout(500)  # 換頁時上一頁暫留 0.42 秒播退場，等它收掉再量
            bad = []
            for y in range(0, 6):
                bad += await pg.evaluate(HIT, TARGETS)
                more = await pg.evaluate('(()=>{const y=scrollY;scrollBy(0,innerHeight*0.6);return scrollY!==y})()')
                await pg.wait_for_timeout(120)
                if not more: break
            rec("觸控", f"{name}：按鈕、選項、連結的可點範圍至少 44 高", not bad, sorted(set(bad))[:6])
        await ctx.close()
    # 記帳表單的選項、錢包的模式切換
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 20), init=seed(DB))
    await pg.evaluate('tab="acct";render()'); await pg.wait_for_timeout(200)
    # 使用者決定：選項外觀維持原本高度，只把可點範圍放大到 44
    h = await pg.evaluate('[...document.querySelectorAll("#acct-form .pick")].map(e=>Math.round(e.getBoundingClientRect().height))')
    rec("觸控", "記帳選項維持原本外觀高度（小於 44）", h and max(h) < 44, sorted(set(h)))
    SEL = '#acct-form .picks:not([data-pick="cat"]) .pick'
    bad = await pg.evaluate(HIT, SEL)
    for i in range(3):
        await pg.evaluate('scrollBy(0,innerHeight*0.5)'); await pg.wait_for_timeout(120); bad += await pg.evaluate(HIT, SEL)
    rec("觸控", "記帳的付款人、分攤、付款方式：可點範圍至少 44 高", not bad, sorted(set(bad)))
    # 類別會排成兩列，可點範圍放大到列距的一半（約 38），而且不會點到另一列
    await pg.evaluate('document.querySelector(\'[data-pick="cat"]\').scrollIntoView({block:"center"})'); await pg.wait_for_timeout(120)
    r = await pg.evaluate("""(()=>{const out=[];for(const e of document.querySelectorAll('[data-pick="cat"] .pick')){const r=e.getBoundingClientRect();const cx=r.left+r.width/2,cy=r.top+r.height/2;
      const own=[cy-17,cy+17].every(y=>{const h=document.elementFromPoint(cx,y);return h&&(h===e||e.contains(h))});out.push(own)}return out})()""")
    rec("觸控", "記帳類別：可點範圍約 38 高（列距的一半）、不會點到另一列", r and all(r), r)
    await ctx.close()

def lum(c):
    c = [x / 255 for x in c]; c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
async def contrast(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 20), init=seed(DB))
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(250)
    # 首頁上所有寫著「今天」的小字（心情條、日期格），對比都要至少 4.5:1
    cs = await pg.evaluate('''[...document.querySelectorAll("#app *")].filter(e=>e.childElementCount===0&&e.textContent.trim()==="今天"&&e.getClientRects().length).map(e=>{const p=s=>s.match(/\\d+/g).slice(0,3).map(Number);
     let bg=null,n=e;while(n&&!bg){const v=getComputedStyle(n).backgroundColor;if(v&&!/rgba\\(0, 0, 0, 0\\)|transparent/.test(v))bg=p(v);n=n.parentElement}
     return{where:e.parentElement.className,fg:p(getComputedStyle(e).color),bg:bg||[255,255,255]}})''')
    out = []
    for c in cs:
        a, z = sorted([lum(c["fg"]), lum(c["bg"])], reverse=True); out.append((c["where"], round((a + 0.05) / (z + 0.05), 2)))
    rec("對比", "首頁所有「今天」小字對比至少 4.5:1", out and all(r >= 4.5 for _, r in out), out)
    await ctx.close()

async def sort_keys(b):
    P = [(f"p{i}", f"待辦{i}") for i in range(1, 5)]
    db = {**META, **{f"{B}/items/{i}": {"group": "prep", "title": t, "note": "", "due": "", "order": k + 1} for k, (i, t) in enumerate(P)}}
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 20), init=seed(db))
    await pg.evaluate('tab="list";listSub=null;render()'); await pg.wait_for_timeout(250)
    await pg.click('[data-sort-toggle=prep]'); await pg.wait_for_timeout(250)
    order = lambda: pg.evaluate('[...document.querySelectorAll("[data-group-id=prep] [data-sort-id]")].map(x=>x.dataset.sortId)')
    await pg.focus('[data-sort-id="p1"] .drag-h'); await pg.keyboard.press("ArrowDown"); await pg.wait_for_timeout(250)
    o = await order(); await pg.wait_for_timeout(100); live = await pg.evaluate('document.getElementById("sr-live")?.textContent||""')
    rec("排序鍵盤", "把手按 ↓：往下一格、焦點還在同一個把手、讀螢幕念出新位置", o[:2] == ["p2", "p1"] and await pg.evaluate('document.activeElement?.closest("[data-sort-id]")?.dataset.sortId') == "p1" and "第 2 項" in live, {"順序": o, "念": live})
    await pg.keyboard.press("End"); await pg.wait_for_timeout(250)
    rec("排序鍵盤", "End：移到最下面", (await order())[-1] == "p1")
    await pg.keyboard.press("ArrowUp"); await pg.wait_for_timeout(250)
    await pg.keyboard.press("Home"); await pg.wait_for_timeout(250)
    rec("排序鍵盤", "Home：移到最上面", (await order())[0] == "p1")
    await pg.keyboard.press("ArrowUp"); await pg.wait_for_timeout(150)
    rec("排序鍵盤", "已經在最上面再按 ↑ 不會出錯", (await order())[0] == "p1" and not pg.errs)
    await pg.keyboard.press("ArrowDown"); await pg.keyboard.press("ArrowDown"); await pg.wait_for_timeout(300)
    db2 = await S.cloud(pg); want = await order()
    got = sorted([k.split("/")[-1] for k in db2 if "/items/p" in k], key=lambda i: db2[f"{B}/items/{i}"]["order"])
    rec("排序鍵盤", "鍵盤排的順序有存到雲端", got == want, {"畫面": want, "雲端": got})
    await pg.click('[data-sort-toggle=prep]'); await pg.wait_for_timeout(250)
    rec("排序鍵盤", "按完成後清單照新順序", [x for x in await pg.evaluate('[...document.querySelectorAll("[data-group-id=prep] input[type=checkbox]")].map(x=>x.id.slice(2))') if x.startswith("p")] == want)
    rec("排序鍵盤", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in [widths, touch, contrast, sort_keys]:
            try: await f(b)
            except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
        await b.close()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
