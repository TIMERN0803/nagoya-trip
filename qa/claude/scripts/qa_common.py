# QA 共用工具：沿用 tools 分支 ft/fulltest.py 的假資料庫，但一律自己建 context，
# 並在 context 上掛「和 newpage() 相同的攔截」＋額外擋掉 firestore.googleapis.com。
# 用法：import qa_common as q（本檔會自動把工作目錄切到 /home/claude/build/ft，因為 fulltest.py 用相對路徑讀 app.js/fs.js）
import os, sys, json, time, asyncio
FT = "/home/claude/build/ft"
os.chdir(FT); sys.path.insert(0, FT)
import fulltest as ft  # noqa: E402
SHOTS = "/home/claude/qa/shots/"
FS_OFFLINE = open("/home/claude/qa/scripts/fs_offline.js").read() if os.path.exists("/home/claude/qa/scripts/fs_offline.js") else None
R = []
def rec(area, case, ok, detail=""):
    R.append((area, case, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + area + " | " + case + (" | " + str(detail)[:400] if detail != "" else ""), flush=True)
def note(area, case, detail=""):
    R.append((area, case, None, detail)); print("NOTE " + area + " | " + case + " | " + str(detail)[:600], flush=True)
jst, twt = ft.jst, ft.twt
CODE = "neko-qa"   # 只用在本機假資料庫

async def mkctx(b, tz="Asia/Tokyo", vw=390, vh=844, dsf=1, fs=None, firebase="mock", extra=None, **kw):
    """firebase: 'mock'＝假資料庫；'abort'＝程式庫載入失敗；'500'＝回 500；'hang'＝永遠不回應；
    也可傳 dict {'mode': 'abort'} 之後改 mode 動態切換"""
    ctx = await b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=dsf, timezone_id=tz,
                              service_workers=kw.pop("service_workers", "block"), **kw)
    state = firebase if isinstance(firebase, dict) else {"mode": firebase}
    fsbody = fs or ft.FS
    async def fb_app(r):
        m = state["mode"]
        if m == "mock": await r.fulfill(body=ft.APP, content_type="text/javascript", headers={"access-control-allow-origin": "*"})
        elif m == "500": await r.fulfill(status=500, body="err")
        elif m == "hang": await asyncio.sleep(3600)
        else: await r.abort()
    async def fb_fs(r):
        m = state["mode"]
        if m == "mock": await r.fulfill(body=fsbody, content_type="text/javascript", headers={"access-control-allow-origin": "*"})
        elif m == "500": await r.fulfill(status=500, body="err")
        elif m == "hang": await asyncio.sleep(3600)
        else: await r.abort()
    # 注意：Playwright 後註冊的 route 優先，所以「全擋」要先註冊，特定的假程式庫後註冊
    await ctx.route("**/*.googleapis.com/**", lambda r: r.abort())
    await ctx.route("**/firestore.googleapis.com/**", lambda r: r.abort())  # 額外保險：絕不碰真實 Firestore
    await ctx.route("**/firebasejs/**", lambda r: r.abort())          # 其他 firebase 檔一律擋
    await ctx.route("**/firebasejs/**/firebase-app.js", fb_app)
    await ctx.route("**/firebasejs/**/firebase-firestore.js", fb_fs)
    await ctx.route("**/api.open-meteo.com/**", lambda r: r.abort())
    await ctx.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    await ctx.route("**/open.er-api.com/**", lambda r: r.abort())
    await ctx.route("**/currency-api*/**", lambda r: r.abort())
    if extra:
        for pat, h in extra: await ctx.route(pat, h)
    ctx.fbstate = state
    return ctx

def seed(db):
    return f'localStorage.setItem("mockdb",{json.dumps(json.dumps(db))});'

async def page(ctx, t, me="zhang", code=CODE, init="", url="http://localhost:8766/", wait=900):
    # 防呆：不可使用正式旅程代碼（只存雜湊，不把代碼寫進公開 repo）
    import hashlib
    assert hashlib.sha256(str(code).encode()).hexdigest()[:16] != "7c8bd32e642bdcb4"
    pg = await ft.newpage(None, t, me=me, code=code, init=init, ctx=ctx) if url == "http://localhost:8766/" else None
    if pg is None:
        pg = await ctx.new_page(); pg.errs = []
        pg.on('pageerror', lambda e: pg.errs.append(str(e)))
        await pg.clock.install(time=t)
        s = 'try{if(!sessionStorage.getItem("s")){localStorage.setItem("ngy:tour","1");' + (f'localStorage.setItem("ngy:me",{json.dumps(me)});' if me else '') + (f'localStorage.setItem("ngy:code",{json.dumps(code)});' if code else '') + init + 'sessionStorage.setItem("s",1)}}catch(e){}'
        await pg.add_init_script(s); await pg.goto(url); await pg.wait_for_timeout(wait)
        pg.ctx = ctx; pg.own = False
    return pg

async def home(pg):
    if not await pg.query_selector('.g-home'):
        if await pg.query_selector('[data-home]'): await pg.click('[data-home]')
        else: await pg.evaluate('document.querySelector("nav.tabs button[data-tab=plan]").click()')
        await pg.wait_for_timeout(300)

async def tab(pg, name):
    await pg.evaluate(f'document.querySelector("nav.tabs button[data-tab={name}]").click()'); await pg.wait_for_timeout(250)

def mockdb_js(): return 'JSON.parse(localStorage.getItem("mockdb")||"{}")'
async def mock(pg, sub=""):
    return await pg.evaluate(f'Object.fromEntries(Object.entries({mockdb_js()}).filter(([k])=>k.includes({json.dumps(sub)})))')

async def metrics(pg):
    c = await pg.context.new_cdp_session(pg)
    await c.send("Performance.enable")
    m = await c.send("Performance.getMetrics"); await c.detach()
    d = {x["name"]: x["value"] for x in m["metrics"]}
    return {"heapMB": round(d.get("JSHeapUsedSize", 0) / 1048576, 2), "listeners": int(d.get("JSEventListeners", 0)), "nodes": int(d.get("Nodes", 0)), "docs": int(d.get("Documents", 0))}

def dump(name):
    json.dump(R, open(f"/home/claude/qa/scripts/out_{name}.json", "w"), ensure_ascii=False, indent=1, default=str)
    bad = [r for r in R if r[2] is False]
    print("TOTAL", len(R), "FAIL", len(bad))
