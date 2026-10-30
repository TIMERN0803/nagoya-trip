# 清理前後「畫面不變」比對：同一組狀態在兩個網址各開一次，逐元素比 getComputedStyle（全部屬性）＋自己的文字，再比截圖像素
# 用法：OLD=http://localhost:8766/ NEW=http://localhost:8770/ python3 stylediff.py
import os, json, asyncio, hashlib
from phonelib import *
import reviewshot as rs
from PIL import Image, ImageChops
OLD = os.environ.get('OLD', 'http://localhost:8766/'); NEW = os.environ.get('NEW', 'http://localhost:8770/')
OUT = os.environ.get('OUT', '/home/claude/build/shots_diff/'); os.makedirs(OUT, exist_ok=True)
RVDB = json.loads(rs.DB.replace('trips/neko-test', B))
SNAP = r'''(()=>{const out=[];const all=document.querySelectorAll("body *");let n=0;
for(const e of all){if(e.closest("defs,symbol,linearGradient,radialGradient"))continue;const cs=getComputedStyle(e);const pp=[];for(let i=0;i<cs.length;i++){const k=cs[i];pp.push(k+":"+cs.getPropertyValue(k))}pp.sort();const st=pp.join(";")
 const own=[...e.childNodes].filter(x=>x.nodeType===3).map(x=>x.nodeValue).join("").trim();
 const r=e.getBoundingClientRect();
 out.push([e.tagName+(e.id?"#"+e.id:"")+(typeof e.className==="string"&&e.className?"."+e.className.trim().replace(/\s+/g,"."):""),own.slice(0,40),st,[r.x,r.y,r.width,r.height].map(v=>Math.round(v)).join(",")])}
return out})()'''
async def tabgo(pg, t):
    await pg.evaluate(f'document.querySelector("nav.tabs button[data-tab={t}]").click()'); await pg.wait_for_timeout(800)
async def home(pg):
    await tabgo(pg, "plan")
    if await pg.query_selector('[data-home]'): await pg.click('[data-home]'); await pg.wait_for_timeout(800)
async def esc_(pg): await pg.keyboard.press('Escape'); await pg.wait_for_timeout(600)

# 每個情境：(名稱, 時間, 時區, 種資料, 動作清單)；動作是 async fn(pg) → 依序做、每步之後拍一次
def scenarios():
    S = []
    async def h(pg): await home(pg)
    async def cal(pg): await pg.click('[data-cal]'); await pg.wait_for_timeout(800)
    async def day3(pg): await esc_(pg); await pg.click('.tile[data-day="2"]'); await pg.wait_for_timeout(900)
    async def wx(pg): await tabgo(pg, "wx")
    async def mv(pg): await tabgo(pg, "move")
    async def ac(pg): await tabgo(pg, "acct")
    async def wal(pg): await pg.click('[data-wallet-open] >> nth=0'); await pg.wait_for_timeout(800)
    async def exn(pg): await esc_(pg); await pg.click('[data-exp-new]'); await pg.wait_for_timeout(800)
    async def ls(pg): await esc_(pg); await tabgo(pg, "list")
    async def lsbuy(pg): await pg.click('[role=tab]:nth-child(2), .ltabs button:nth-child(2)'); await pg.wait_for_timeout(600)
    async def pack(pg): await pg.click('[data-pack-open]'); await pg.wait_for_timeout(800)
    async def sos(pg): await home(pg); await pg.click('[data-sos] >> nth=0'); await pg.wait_for_timeout(900)
    async def sosshow(pg):
        b = await pg.query_selector('[data-sos-show]')
        if b: await b.click(); await pg.wait_for_timeout(900)
    async def story(pg): await pg.click('#review[data-story-open]'); await pg.wait_for_timeout(1000)
    async def nxt(pg): await pg.click('.st-tap.next'); await pg.clock.run_for(2500); await pg.wait_for_timeout(400)
    async def map_(pg):
        await esc_(pg); await home(pg); b = await pg.query_selector('[data-map], .pic[data-viewer], [data-viewer]')
        if b: await b.click(); await pg.wait_for_timeout(900)
    S.append(("trip", jst(11, 19, 20, 0), "Asia/Tokyo", True, [("home", h), ("cal", cal), ("day3", day3), ("wx", wx), ("move", mv), ("acct", ac), ("wallet", wal), ("expnew", exn), ("list", ls), ("buy", lsbuy), ("sos", sos), ("sosshow", sosshow), ("map", map_)]))
    S.append(("pre", twt(11, 10, 20, 0), "Asia/Taipei", False, [("home", h), ("list", ls), ("pack", pack)]))
    S.append(("dusk", jst(11, 20, 18, 30), "Asia/Tokyo", True, [("home", h)]))
    S.append(("night", jst(11, 21, 22, 30), "Asia/Tokyo", True, [("home", h)]))
    S.append(("review", twt(11, 24, 14, 21), "Asia/Taipei", True, [("home", h), ("story1", story)] + [(f"story{i}", nxt) for i in range(2, 8)]))
    return S

def cmp(a, b):
    d = []
    if len(a) != len(b): d.append(f"元素數不同 {len(a)} vs {len(b)}")
    for x, y in zip(a, b):
        if x[0] != y[0] or x[1] != y[1]: d.append(f"結構/文字不同：{x[0]}「{x[1]}」 vs {y[0]}「{y[1]}」"); continue
        if x[3] != y[3]: d.append(f"位置不同：{x[0]} {x[3]} vs {y[3]}")
        if x[2] != y[2]:
            i = next(j for j in range(min(len(x[2]), len(y[2]))) if x[2][j] != y[2][j]) if x[2][:min(len(x[2]),len(y[2]))] != y[2][:min(len(x[2]),len(y[2]))] else min(len(x[2]), len(y[2]))
            diff = (x[2][max(0,i-80):i+60], y[2][max(0,i-80):i+60])
            d.append(f"樣式不同：{x[0]} {diff}")
    return d

async def run(b, base, tag):
    res = {}
    for name, t, tz, rv, steps in scenarios():
        if os.environ.get('ONLY') and name not in os.environ['ONLY'].split(','): continue
        ctx = await newctx(b, tz=tz)
        pg = await phone(ctx, t, "zhang", name, init=seed({**META, **RVDB}) if rv else seed({}), url=base, wait=2500)
        for sn, fn in steps:
            try: await fn(pg)
            except Exception as e: res[f"{name}/{sn}"] = ("ERR", str(e)[:120]); continue
            await pg.wait_for_timeout(300)
            await pg.evaluate('document.getAnimations().forEach(a=>{try{const t=a.effect&&a.effect.getComputedTiming();if(t&&t.iterations===Infinity){a.pause();a.currentTime=0}else a.finish()}catch(e){}})')
            await pg.wait_for_timeout(100)
            res[f"{name}/{sn}"] = await pg.evaluate(SNAP)
            await pg.screenshot(path=f"{OUT}{tag}_{name}_{sn}.png", animations="disabled")
        res[f"{name}/errs"] = pg.errs
        await ctx.close()
    return res

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        A = await run(b, OLD, "old"); Bn = await run(b, NEW, "new"); C = await run(b, OLD, "old2")
        await b.close()
    bad = 0
    for k in A:
        if k.endswith("/errs"):
            ok = not A[k] and not Bn[k]; rec("清理前後", f"{k} 沒有 JS 錯誤", ok, (A[k][:1], Bn[k][:1])); bad += not ok; continue
        if isinstance(A[k], tuple) or isinstance(Bn[k], tuple):
            rec("清理前後", f"{k} 兩邊都做得到", A[k] == Bn[k], (A[k] if isinstance(A[k], tuple) else "ok", Bn[k] if isinstance(Bn[k], tuple) else "ok")); continue
        d = cmp(A[k], Bn[k])
        n = k.replace("/", "_")
        im1 = Image.open(f"{OUT}old_{n}.png").convert("RGB"); im2 = Image.open(f"{OUT}new_{n}.png").convert("RGB")
        im3 = Image.open(f"{OUT}old2_{n}.png").convert("RGB")
        px = ImageChops.difference(im1, im2).getbbox() if im1.size == im2.size else "size"
        noise = ImageChops.difference(im1, im3).getbbox() if im1.size == im3.size else "size"
        dc = cmp(A[k], C[k])
        rec("清理前後", f"{k}：{len(A[k])} 個元素樣式、位置、文字全部相同；截圖像素相同（舊版自己重跑會變的地方不算）", not d and (px is None or noise is not None), (d[:3], px, "舊版重跑", noise, len(dc)))
    summary()
asyncio.run(main())
