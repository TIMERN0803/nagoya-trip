# 開啟動畫與開啟速度：
# 1. App 重新開啟時：豆花和芝麻（只有貓咪，沒有字）在畫面正中央點頭，從開啟算起約 1.2 秒淡出 0.4 秒露出首頁（點一下跳過是 0.2 秒）
# 2. 載入本來就超過 1.2 秒：畫好就立刻淡出，不會再多等
# 3. 點一下跳過；同一次使用中重新整理不再播；減少動態直接拿掉
# 4. iOS 啟動圖：各尺寸都有、和開啟動畫同一個畫面
# 5. 訊號差（網路超過 1.5 秒）時，Service Worker 先用快取打開；字型樣式不擋畫面
# 一律用假資料庫（synctest.mkctx 的攔截）；慢速網站用 slowsrv.py（8768 埠）
import asyncio, subprocess, time, os, re
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
from PIL import Image
rec = ft.rec
B, META, seed, opn = S.B, S.META, S.seed, S.opn
SITE = "/home/claude/nagoya-trip"
# 記錄開啟動畫的時間點（從開啟算起的毫秒）：第一次看到、開始收、移除
WATCH = '''(()=>{window.__sp={};const t=setInterval(()=>{const s=document.getElementById("splash"),n=Math.round(performance.now());if(!s){if(window.__sp.seen&&!window.__sp.gone)window.__sp.gone=n;return}if(!window.__sp.seen)window.__sp.seen=n;if(s.classList.contains("out")&&!window.__sp.out){window.__sp.out=n;window.__sp.anim=getComputedStyle(s).animationName}},10);setTimeout(()=>clearInterval(t),6000)})();'''
SP = 'window.__sp'

async def launch(b, url="http://localhost:8766/", reduced=False, keep=False):
    ctx = await S.mkctx(b); await ctx.add_init_script(seed(META) + 'try{localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code","%s")}catch(e){}' % S.CODE + WATCH)
    pg = await ctx.new_page(); pg.errs = []; pg.on("pageerror", lambda e: pg.errs.append(str(e)))
    if reduced: await pg.emulate_media(reduced_motion="reduce")
    await pg.goto(url, wait_until="commit")
    return ctx, pg

async def normal(b):
    ctx, pg = await launch(b)
    await pg.wait_for_timeout(500)
    st = await pg.evaluate('(()=>{const s=document.getElementById("splash");return s?{vis:getComputedStyle(s).visibility,txt:s.innerText.trim(),cats:s.querySelectorAll(".sp-a,.sp-b").length,app:!!document.querySelector("#app .view")}:null})()')
    rec("開啟動畫", "App 開啟時馬上出現，只有中間的豆花和芝麻（沒有字）", st and st["vis"] == "visible" and st["txt"] == "" and st["cats"] == 2, st)
    rec("開啟動畫", "頁面在後面已經畫好（動畫只是蓋著，不是在等）", st and st["app"], st)
    r = await pg.evaluate('(()=>{const s=document.querySelector("#splash svg").getBoundingClientRect();return {cx:Math.round(s.left+s.width/2-innerWidth/2),cy:Math.round(s.top+s.height/2-innerHeight/2)}})()')
    rec("開啟動畫", "豆花和芝麻在畫面正中央（和 iOS 啟動圖對齊）", abs(r["cx"]) <= 1 and abs(r["cy"]) <= 1, r)
    await pg.wait_for_timeout(1700)
    sp = await pg.evaluate(SP)
    rec("開啟動畫", "從開啟算起約 1.2 秒開始淡出（1.15～1.45 秒）", sp.get("out") and 1150 <= sp["out"] <= 1450, sp)
    rec("開啟動畫", "淡出（只動透明度）約 0.4 秒後移除、不擋點擊", sp.get("anim") == "spfade" and sp.get("gone") and sp["gone"] - sp["out"] <= 1000 and not await pg.query_selector('#splash'), sp)
    kf = await pg.evaluate('[...document.styleSheets].flatMap(s=>{try{return [...s.cssRules]}catch(e){return []}}).filter(r=>r.name==="spfade").map(r=>r.cssText).join("")')
    rec("開啟動畫", "淡出只動透明度（GPU 合成、不重新排版）", "opacity" in kf and "clip-path" not in kf and "transform" not in kf, kf)
    # 同一次使用中重新整理（例如網路恢復自動重新整理）：不再播
    await pg.reload(); await pg.wait_for_timeout(300)
    rec("開啟動畫", "同一次使用中重新整理：不再播", not await pg.query_selector('#splash'))
    rec("開啟動畫", "沒有錯誤", not pg.errs, pg.errs[:2])
    # 字型、豆花和芝麻跟 App 裡的圖一模一樣
    rec("字型", "字型樣式不擋畫面（載好後換成 all）", await pg.evaluate('(()=>{const l=document.querySelector(\'link[href*="fonts.googleapis"]\');return l&&l.getAttribute("onload")&&l.getAttribute("onload").includes("media")})()'))
    same = await pg.evaluate("""(h)=>{const d=new DOMParser().parseFromString(h,"text/html");const sp=d.getElementById("splash");if(!sp)return "no splash in html";
      const a=sp.querySelector(".sp-a svg").innerHTML.replaceAll("sp-rough","rough"),b=sp.querySelector(".sp-b svg").innerHTML.replaceAll("sp-rough","rough");
      return a===document.getElementById("head-w").innerHTML&&b===document.getElementById("head-b").innerHTML}""", await (await pg.request.get("http://localhost:8766/")).text())
    rec("開啟動畫", "豆花和芝麻跟 App 裡的圖一模一樣（含手繪抖動濾鏡）", same is True, same)
    await ctx.close()

async def skip(b):
    ctx, pg = await launch(b)
    await pg.wait_for_selector('#app .view'); await pg.wait_for_timeout(250)
    await pg.mouse.click(200, 200)
    sp = await pg.evaluate(SP); await pg.wait_for_timeout(50); sp = await pg.evaluate(SP)
    rec("開啟動畫", "點一下就跳過：馬上快速淡出", sp.get("out") and sp["out"] < 1000, sp)
    await pg.wait_for_timeout(800)
    rec("開啟動畫", "跳過後很快就能用", not await pg.query_selector('#splash'))
    await ctx.close()
    # 畫面還沒畫好就點：畫好立刻收
    ctx, pg = await launch(b, "http://localhost:8768/?split")
    await pg.wait_for_selector('#splash'); await pg.wait_for_timeout(300); await pg.mouse.click(200, 200)
    await pg.wait_for_selector('#app .view', timeout=10000); await pg.wait_for_timeout(80)
    sp = await pg.evaluate(SP); ready = await pg.evaluate('Math.round(performance.now())')
    rec("開啟動畫", "還沒畫好就點跳過：畫好立刻淡出", sp.get("out") is not None, sp)
    await ctx.close()

async def slow(b, reduced=False):
    ctx, pg = await launch(b, "http://localhost:8768/?split", reduced=reduced)
    await pg.wait_for_selector('#app .view', timeout=10000)
    t_ready = await pg.evaluate('Math.round(performance.now())')
    await pg.wait_for_timeout(900)
    sp = await pg.evaluate(SP)
    if not reduced:
        rec("開啟動畫", "載入本來就慢（超過 1.2 秒）：畫好就淡出，不再多等", sp.get("out") and sp["out"] - t_ready <= 150 and t_ready >= 1150, {"畫好": t_ready, **sp})
        page_src = await (await pg.request.get("http://localhost:8766/")).text()
        rec("開啟動畫", "結束不另外跳一下、不播收合", not any(k in page_src for k in ("sphop", "spout")))
    else:
        rec("開啟動畫", "減少動態：時間到直接拿掉、不淡出", sp.get("gone") and not sp.get("out"), sp)
    rec("開啟動畫", "沒有錯誤" + ("（減少動態）" if reduced else ""), not pg.errs, pg.errs[:2])
    await ctx.close()

async def startup_images(b):
    html = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    tags = re.findall(r'<link rel="apple-touch-startup-image" media="\(device-width: (\d+)px\) and \(device-height: (\d+)px\) and \(-webkit-device-pixel-ratio: (\d)\) and \(orientation: portrait\)" href="([^"]+)">', html)
    bad = []
    for w, h, d, f in tags:
        p = os.path.join(SITE, f)
        if not os.path.exists(p): bad.append(f + " 不存在"); continue
        im = Image.open(p)
        if im.size != (int(w) * int(d), int(h) * int(d)): bad.append(f"{f} 尺寸 {im.size}")
    rec("啟動圖", "iOS 啟動圖：iPhone SE 到 Pro Max 各尺寸都有、像素尺寸正確", len(tags) >= 11 and not bad, {"張數": len(tags), "問題": bad})
    # 啟動圖和開啟動畫同一個畫面：402×874@3 時，貓咪的位置一樣（比對中間一列像素的非米色範圍）
    ctx, pg = await launch(b)
    await pg.set_viewport_size({"width": 402, "height": 874}); await pg.wait_for_timeout(150)
    await pg.evaluate('document.querySelectorAll("#splash .sp-a,#splash .sp-b").forEach(e=>e.style.animation="none")')
    shot = "/tmp/claude-0/-home-claude/3424b5fd-29a2-5a06-a9e1-4e1d3697a3c3/scratchpad/sp_live.png"
    await pg.screenshot(path=shot); await ctx.close()
    def span(im, scale):
        im = im.convert("RGB"); W, H = im.size; y = H // 2; xs = [x for x in range(W) if sum(abs(a - b) for a, b in zip(im.getpixel((x, y)), (248, 243, 236))) > 60]
        return (round(min(xs) / scale), round(max(xs) / scale)) if xs else None
    a = span(Image.open(shot), 1); s3 = span(Image.open(os.path.join(SITE, "splash/402x874@3.png")), 3)
    rec("啟動圖", "啟動圖和開啟動畫的貓咪位置一樣（按下圖示到動畫接得起來）", a and s3 and abs(a[0] - s3[0]) <= 2 and abs(a[1] - s3[1]) <= 2, {"動畫": a, "啟動圖": s3})

async def sw_slow(b):
    ctx = await S.mkctx(b, sw="allow")
    await ctx.add_init_script('try{localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code","%s")}catch(e){}' % S.CODE)
    pg = await ctx.new_page(); await pg.goto("http://localhost:8768/"); await pg.wait_for_timeout(2500); await pg.reload(); await pg.wait_for_timeout(2500)
    ctl = await pg.evaluate('!!navigator.serviceWorker.controller')
    await pg.evaluate('fetch("/__slow?on=1")'); await pg.wait_for_timeout(200)
    t0 = time.time(); await pg.reload(wait_until="commit"); await pg.wait_for_selector('#app .view', timeout=15000); dt = time.time() - t0
    rec("訊號差", "網路超過 1.5 秒時先用快取打開（3 秒內看到畫面，不等 4 秒）", ctl and dt < 3.0, {"SW": ctl, "秒": round(dt, 2)})
    await pg.evaluate('fetch("/__slow?on=0")'); await pg.wait_for_timeout(4500)
    t0 = time.time(); await pg.reload(); await pg.wait_for_selector('#app .view', timeout=15000); dt = time.time() - t0
    rec("訊號差", "網路正常時照樣拿最新版、很快打開", dt < 3.0, round(dt, 2))
    await ctx.close()

async def main():
    srv = subprocess.Popen(["python3", "/home/claude/build/ft/slowsrv.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            for f, a in [(normal, ()), (skip, ()), (slow, ()), (slow, (True,)), (startup_images, ()), (sw_slow, ())]:
                try: await f(b, *a)
                except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
            await b.close()
    finally:
        srv.terminate()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
