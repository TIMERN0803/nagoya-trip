# QA R2 體驗優化（批 A）：X1 回顧入口提前（C9a）、X2 復原時對方已新增同名的提示（C11）、X7 清單空狀態（C12）與浮動鈕捲到底（A12）
# 一律假資料庫，旅程代碼 qa-r2-test。BASE 環境變數可改網址（預設本機 8766）。
import os, json, asyncio
from phonelib import *
import reviewshot as rs
BASE = os.environ.get('BASE', 'http://localhost:8766/')
RVDB = json.loads(rs.DB.replace('trips/neko-test', B))
def jstr(x): return json.dumps(x, ensure_ascii=False)

async def home(pg):
    await pg.evaluate('document.querySelector("nav.tabs button[data-tab=plan]").click()'); await pg.wait_for_timeout(250)
    if await pg.query_selector('[data-home]'): await pg.click('[data-home]'); await pg.wait_for_timeout(700)
async def day(pg, i):
    await home(pg); await pg.click(f'.tile[data-day="{i}"]'); await pg.wait_for_timeout(800)
async def ticket_pos(pg):
    return await pg.evaluate('''(()=>{const r=document.getElementById("review");if(!r)return null;const n=r.nextElementSibling;return {next:n&&n.className,h2:n&&n.querySelector("h2")&&n.querySelector("h2").textContent}})()''')
async def mini(pg):
    return await pg.evaluate('''(()=>{const m=document.querySelector("#dayBody .rv-mini");if(!m)return null;const p=m.previousElementSibling,n=m.nextElementSibling;return {prev:p&&p.tagName+"."+p.className,next:n&&n.className,txt:m.innerText.replace(/\\n/g," ")}})()''')

async def x1(b):
    A = "X1 回顧入口（C9a）"
    ctx = await newctx(b, tz="Asia/Taipei")
    # 14:19 首頁沒有，等時間到自己出現（不用重新整理）
    pg = await phone(ctx, twt(11, 24, 14, 19), "zhang", "h1", init=seed({**META, **RVDB}), url=BASE, wait=1200)
    await home(pg)
    rec(A, "11/24 台灣 14:19 首頁沒有回顧入口", not await pg.query_selector('[data-story-open]'))
    await pg.screenshot(path=SHOTS + 'x1_home_1419.png')
    await pg.clock.run_for(90_000); await pg.wait_for_timeout(500)
    pos = await ticket_pos(pg)
    rec(A, "開著首頁過 14:20：30 秒內自己出現，在「8 天的地點」上面", pos and pos['h2'] and "8 天的地點" in pos['h2'], pos)
    await pg.screenshot(path=SHOTS + 'x1_home_1421_live.png')
    # 14:19 當天行程頁，等時間到最後一站下面出現小卡
    rec(A, "沒有 JS 錯誤（首頁）", not pg.errs, pg.errs[:2]); await pg.close()
    d = await phone(ctx, twt(11, 24, 14, 19), "zhang", "d1", url=BASE, wait=1200)
    await day(d, 7)
    rec(A, "11/24 台灣 14:19 當天行程頁沒有小卡", await mini(d) is None)
    await d.clock.run_for(60_000); await d.wait_for_timeout(500)
    m = await mini(d)
    rec(A, "開著 11/24 當天行程頁過 14:20：最後一站下面出現小卡、心情在它下面", m and m['prev'].startswith("OL.tl") and m['next'] and "mood" in m['next'], m)
    rec(A, "沒有 JS 錯誤（當天頁）", not d.errs, d.errs[:2]); await d.close()
    # 14:21 直接開
    pg = await phone(ctx, twt(11, 24, 14, 21), "zhang", "h2", url=BASE, wait=1200)
    await home(pg)
    rec(A, "11/24 台灣 14:21 打開 App 首頁就有回顧入口", await pg.query_selector('#review[data-story-open]'))
    await pg.screenshot(path=SHOTS + 'x1_home_1421.png', full_page=True)
    await day(pg, 7)
    m = await mini(pg)
    rec(A, "14:21 第 8 天頁有小卡（不是首頁那張大的，沒有重複 id）", m and not await pg.query_selector('#dayBody #review'), m)
    await pg.evaluate('scrollTo(0,document.body.scrollHeight)'); await pg.wait_for_timeout(400)
    await pg.screenshot(path=SHOTS + 'x1_day8_1421_bottom.png')
    await pg.focus('#dayBody .rv-mini'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(700)
    n = await pg.evaluate('document.querySelectorAll(".story .st-page").length')
    empty = await pg.evaluate('[...document.querySelectorAll(".story .st-page")].filter(s=>!s.innerText.trim()).length')
    rec(A, "從小卡打開回顧：7 頁、沒有空白頁", n == 7 and empty == 0, (n, empty))
    for i in range(n):
        await pg.screenshot(path=SHOTS + f'x1_story_{i+1}.png')
        if i < n - 1: await pg.click('.st-tap.next'); await pg.clock.run_for(1500); await pg.wait_for_timeout(250)
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
    rec(A, "Esc 關閉後焦點回到小卡", await pg.evaluate('document.activeElement&&document.activeElement.classList.contains("rv-mini")'))
    await day(pg, 6)
    rec(A, "第 7 天頁沒有小卡", await mini(pg) is None)
    rec(A, "沒有 JS 錯誤（14:21）", not pg.errs, pg.errs[:2]); await pg.close()
    # 旅途中、旅程後
    pg = await phone(ctx, jst(11, 23, 21, 0), "zhang", "h3", url=BASE, wait=1200)
    await home(pg); r1 = await pg.query_selector('[data-story-open]'); await day(pg, 7); r2 = await mini(pg)
    rec(A, "11/23 晚上首頁、第 8 天頁都沒有入口", not r1 and r2 is None); await pg.close()
    pg = await phone(ctx, twt(11, 26, 9, 0), "zhang", "h4", url=BASE, wait=1200)
    await home(pg); r1 = await pg.query_selector('#review'); await day(pg, 7); r2 = await mini(pg)
    rec(A, "11/26 首頁和第 8 天頁都有入口", r1 and r2, r2); await pg.close()
    await ctx.close()

async def listtxt(pg, sel): return (await pg.inner_text(sel)).replace("\n", " | ")
async def x2(b):
    A = "X2 復原提示（C11）"
    ctx = await newctx(b)
    T = jst(11, 19, 20)
    db = {**META, f"{B}/expenses/e1": {"amt": 1200, "cat": "food", "who": "zhang", "split": "both", "pay": "cash", "day": "11/19", "note": "拉麵", "ts": 1},
          f"{B}/expenses/e2": {"amt": 800, "cat": "food", "who": "zhang", "split": "both", "pay": "cash", "day": "11/19", "note": "咖啡", "ts": 2},
          f"{B}/items/b1": {"group": "buy", "title": "保濕乳液", "note": "", "due": "", "order": 1},
          f"{B}/items/b2": {"group": "buy", "title": "眼藥水", "note": "", "due": "", "order": 2}}
    Pa = await phone(ctx, T, "zhang", "A", init=seed(db), url=BASE, wait=1200)
    Pb = await phone(ctx, T, "star", "B", url=BASE, wait=1200)
    for x in (Pa, Pb): await tab(x, "acct")
    async def delx(pg, id):
        await pg.click(f'[data-del="{id}"]'); await pg.wait_for_timeout(300)
        if await pg.query_selector(f'[data-del="{id}"]'): await pg.click(f'[data-del="{id}"]')
        await pg.wait_for_timeout(600)
    async def bar(pg): return await pg.evaluate('(()=>{const v=document.querySelector(".undo-bar");return v&&{t:v.querySelector("span").textContent,btn:!v.querySelector("button").hidden,hint:v.classList.contains("hint"),h:v.getBoundingClientRect().height}})()')
    # 記帳：A 刪拉麵 → B 重記拉麵 1200 → A 復原 → 提示
    await delx(Pa, "e1")
    await S.expopen(Pb); await Pb.fill('#f-amt', '1200'); await Pb.fill('#f-note', '拉麵'); await Pb.click('#f-save'); await Pb.wait_for_timeout(800)
    await Pa.click('.undo-bar button'); await Pa.wait_for_timeout(500)
    v = await bar(Pa)
    rec(A, "記帳：復原時對方已記同名同金額 → 提示（沒有復原鈕、文字完整換行）", v and v['hint'] and not v['btn'] and "拉麵" in v['t'] and "重複" in v['t'], v)
    await Pa.screenshot(path=SHOTS + 'x2_acct_hint.png')
    await Pa.clock.run_for(6000); await Pa.wait_for_timeout(200)
    rec(A, "提示 6 秒時還在（讀得完）", await bar(Pa) is not None)
    await Pa.clock.run_for(2500); await Pa.wait_for_timeout(200)
    rec(A, "提示 8 秒後消失", await bar(Pa) is None)
    n = sum(1 for v in (await exps(Pa)).values() if v.get("note") == "拉麵")
    rec(A, "照樣復原：雲端 2 筆拉麵", n == 2, n)
    rec(A, "對方（B）沒有提示", await bar(Pb) is None)
    # 對照組：沒有同名 → 照舊只顯示（沒有提示）
    await delx(Pa, "e2"); await Pa.click('.undo-bar button'); await Pa.wait_for_timeout(500)
    rec(A, "記帳對照：沒人重記就沒有提示", await bar(Pa) is None)
    # 對照組：同名不同金額 → 不提示
    db2 = await exps(Pa); eid = [k for k, v in db2.items() if v.get("note") == "拉麵" and k != "e1"][0]
    await delx(Pa, "e1")
    await Pb.evaluate(f'document.querySelector(\'[data-edit="{eid}"]\')?.click()'); await Pb.wait_for_timeout(700)
    await Pb.fill('#f-amt', '1500'); await Pb.click('#f-save'); await Pb.wait_for_timeout(800)
    await Pa.click('.undo-bar button'); await Pa.wait_for_timeout(500)
    rec(A, "記帳對照：同名但金額不同不提示", await bar(Pa) is None, await bar(Pa))
    # 清單：A 刪保濕乳液 → B 重加 → A 復原 → 提示
    for x in (Pa, Pb): await tab(x, "list"); await x.click('[data-list-tab="buy"]'); await x.wait_for_timeout(300)
    async def delitem(pg, id):
        await pg.click(f'[data-item-edit="{id}"]'); await pg.wait_for_timeout(300)
        await pg.click(f'[data-item-del="{id}"]'); await pg.wait_for_timeout(600)
        if await pg.query_selector(f'[data-item-del="{id}"]'): await pg.click(f'[data-item-del="{id}"]'); await pg.wait_for_timeout(500)
    await delitem(Pa, "b1")
    await Pb.click('[data-item-new="buy"]'); await Pb.fill('.chk-form input[name=title]', '保濕乳液 '); await Pb.click('.chk-form .primary'); await Pb.wait_for_timeout(700)
    await Pa.click('.undo-bar button'); await Pa.wait_for_timeout(500)
    v = await bar(Pa)
    rec(A, "清單：復原時對方已新增同名（去頭尾空白比對）→ 提示", v and v['hint'] and "保濕乳液" in v['t'], v)
    await Pa.screenshot(path=SHOTS + 'x2_list_hint.png')
    ca = await listtxt(Pa, '[data-group-id=buy]')
    rec(A, "清單照樣復原：A 看到 2 條保濕乳液", ca.count("保濕乳液") == 2, ca)
    await Pa.clock.run_for(9000); await Pa.wait_for_timeout(200)
    await delitem(Pa, "b2"); await Pa.click('.undo-bar button'); await Pa.wait_for_timeout(500)
    rec(A, "清單對照：沒人重加就沒有提示", await bar(Pa) is None)
    rec(A, "沒有 JS 錯誤", not Pa.errs and not Pb.errs, (Pa.errs + Pb.errs)[:3])
    await ctx.close()

async def x7(b):
    A = "X7 清單空狀態（C12）／浮動鈕（A12）"
    ctx = await newctx(b)
    pg = await phone(ctx, jst(11, 19, 20), "zhang", "e", init=seed(META), url=BASE, wait=1200)
    await tab(pg, "list")
    for g, lab in (("prep", "待辦"), ("buy", "要買的")):
        await pg.click(f'[data-list-tab="{g}"]'); await pg.wait_for_timeout(300)
        # 刪光
        for _ in range(60):
            e = await pg.query_selector(f'[data-group-id={g}] [data-item-edit]')
            if not e: break
            id_ = await e.get_attribute('data-item-edit'); await e.click(); await pg.wait_for_timeout(200)
            await pg.click(f'[data-item-del="{id_}"]'); await pg.wait_for_timeout(250)
            if await pg.query_selector(f'[data-item-del="{id_}"]'): await pg.click(f'[data-item-del="{id_}"]'); await pg.wait_for_timeout(250)
        await pg.wait_for_timeout(5500)
        t = await pg.evaluate(f'(()=>{{const e=document.querySelector("[data-group-id={g}] .chk-empty");return e&&e.innerText.trim()}})()')
        nxt = await pg.evaluate(f'(()=>{{const e=document.querySelector("[data-group-id={g}] .chk-empty");return e&&e.nextElementSibling&&e.nextElementSibling.dataset.itemNew}})()')
        rec(A, f"{lab}全部刪光：有說明文字，「新增一項」在下面", t and nxt == g, (t, nxt))
        await pg.screenshot(path=SHOTS + f'x7_empty_{g}.png')
        await pg.click(f'[data-item-new="{g}"]'); await pg.wait_for_timeout(300)
        rec(A, f"{lab}按新增一項：表單開著時不顯示說明", not await pg.query_selector(f'[data-group-id={g}] .chk-empty'))
        await pg.fill('.chk-form input[name=title]', '測試項目'); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(500)
        rec(A, f"{lab}新增一項後說明消失", not await pg.query_selector(f'[data-group-id={g}] .chk-empty'))
    rec(A, "沒有 JS 錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
    # A12：捲到底時浮動鈕不蓋住首頁最後一列、記帳最後一筆的「刪除」（捲動途中被蓋是正常的，不檢查）
    ctx = await newctx(b)
    pg = await phone(ctx, jst(11, 19, 20), "zhang", "f", init=seed({**META, **RVDB}), url=BASE, wait=1300)
    await home(pg)
    COV = '''(([sel,fab])=>{scrollTo(0,document.documentElement.scrollHeight);const els=[...document.querySelectorAll(sel)],e=els[els.length-1],f=document.querySelector(fab);if(!e||!f)return "missing";const r=e.getBoundingClientRect();
     return [[r.left+r.width/2,r.top+r.height/2],[r.left+3,r.bottom-3],[r.right-3,r.bottom-3]].some(([x,y])=>{const h=document.elementFromPoint(x,y);return h&&f.contains(h)})})'''
    for sel in ('.g-home > *:last-child', '.grid .tile'):
        rec(A, f"首頁捲到底：浮動鈕不蓋住 {sel} 的最後一個", await pg.evaluate(COV, [sel, '.fab']) is False)
    await tab(pg, "acct"); await pg.wait_for_timeout(400)
    rec(A, "記帳捲到底：浮動鈕不蓋住最後一筆的「刪除」", await pg.evaluate(COV, ['#acct-list [data-del]', '.acct-fab']) is False)
    await ctx.close()

async def main():
    only = os.environ.get('ONLY', '')
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in (x1, x2, x7):
            if not only or f.__name__ in only.split(','): await f(b)
        await b.close()
    summary()
asyncio.run(main())
