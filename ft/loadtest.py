# 開啟速度與開啟畫面：
# 1. 很快畫好（0.3 秒內）時開啟畫面完全不出現（不會閃一下）
# 2. 下載很慢時看得到豆花和芝麻的開啟畫面，畫好後整片往上滑走（不淡出）、之後移除
# 3. 減少動態：直接拿掉
# 4. 訊號差（網路超過 1.5 秒）時，Service Worker 先用快取打開，不會一直白畫面等
# 5. 字型樣式不擋畫面（media=print 載好才換 all）
# 一律用假資料庫（synctest.mkctx 的攔截）；慢速網站用 slowsrv.py（8768 埠）
import asyncio, subprocess, time
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
rec = ft.rec
B, META, seed, opn = S.B, S.META, S.seed, S.opn
WATCH = '''(()=>{window.__spv=false;window.__spout=false;const t=setInterval(()=>{const s=document.getElementById("splash");if(!s)return;const cs=getComputedStyle(s);if(cs.visibility==="visible")window.__spv=true;if(s.classList.contains("out"))window.__spout=cs.animationName},10);setTimeout(()=>clearInterval(t),5000)})();'''

async def fast(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META) + WATCH)
    rec("開啟畫面", "很快畫好時：開啟畫面完全不出現、已經移除", not await pg.evaluate('window.__spv') and not await pg.query_selector('#splash'), await pg.evaluate('window.__spv'))
    rec("開啟畫面", "頁面正常畫出來", await pg.query_selector('#app .view') is not None)
    rec("開啟畫面", "沒有錯誤", not pg.errs, pg.errs[:2])
    await pg.close()
    # 開啟畫面的豆花和芝麻要跟 App 裡畫的一樣：和 App 產生的 head-w／head-b 圖案逐字比對
    pg = await ctx.new_page(); await pg.route("**/*", lambda r: r.continue_())
    await pg.goto("http://localhost:8768/?split", wait_until="commit"); await pg.wait_for_selector('#app .view', timeout=10000)
    html = await pg.content()
    same = await pg.evaluate("""(h)=>{const d=new DOMParser().parseFromString(h,"text/html");const sp=d.getElementById("splash");if(!sp)return "no splash in html";
      const a=sp.querySelector(".sp-a svg").innerHTML.replaceAll("sp-rough","rough"),b=sp.querySelector(".sp-b svg").innerHTML.replaceAll("sp-rough","rough");
      return a===document.getElementById("head-w").innerHTML&&b===document.getElementById("head-b").innerHTML}""", await (await pg.request.get("http://localhost:8768/")).text())
    rec("開啟畫面", "豆花和芝麻跟 App 裡的圖一模一樣（含手繪抖動濾鏡）", same is True, same)
    rec("字型", "字型樣式不擋畫面（載好後換成 all）", await pg.evaluate('(()=>{const l=document.querySelector(\'link[href*="fonts.googleapis"]\');return l&&l.getAttribute("onload")&&l.getAttribute("onload").includes("media")})()'))
    await ctx.close()

async def slow(b, reduced=False):
    ctx = await S.mkctx(b); await ctx.add_init_script(seed(META) + WATCH)
    pg = await ctx.new_page()
    if reduced: await pg.emulate_media(reduced_motion="reduce")
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto("http://localhost:8768/?split", wait_until="commit")
    await pg.wait_for_timeout(600)
    shown = await pg.evaluate('(()=>{const s=document.getElementById("splash");return s?getComputedStyle(s).visibility:null})()')
    txt = await pg.evaluate('document.getElementById("splash")?.innerText||""')
    await pg.wait_for_selector('#app .view', timeout=10000)
    if not reduced:
        rec("開啟畫面", "下載很慢時：0.3 秒後出現豆花和芝麻的開啟畫面", shown == "visible" and "名古屋看花花" in txt and "準備行程" in txt, [shown, txt])
        await pg.wait_for_timeout(100)
        rec("開啟畫面", "畫好後豆花和芝麻跳一下、收成圓圈縮到牠們身上（不淡出）", await pg.evaluate('window.__spout') == "spout", await pg.evaluate('window.__spout'))
        kf = await pg.evaluate('[...document.styleSheets].flatMap(s=>{try{return [...s.cssRules]}catch(e){return []}}).filter(r=>r.name==="spout").map(r=>r.cssText).join("")')
        rec("開啟畫面", "退場是圓圈收合、不用透明度", "clip-path" in kf and "opacity" not in kf, kf)
        await pg.wait_for_timeout(800)
        hit = await pg.evaluate('(()=>{const e=document.elementFromPoint(innerWidth/2,innerHeight/2);return e?(e.closest("#splash")?"splash":(e.className&&e.className.baseVal!==undefined?e.className.baseVal:e.className)||e.tagName):null})()')
        rec("開啟畫面", "滑走後移除，不擋點擊", not await pg.query_selector('#splash') and hit != "splash", hit)
    else:
        rec("開啟畫面", "減少動態：畫好就直接拿掉，不滑動", not await pg.query_selector('#splash') and not await pg.evaluate('window.__spout'))
    rec("開啟畫面", "沒有錯誤" + ("（減少動態）" if reduced else ""), not errs, errs[:2])
    await ctx.close()

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
            for f, a in [(fast, ()), (slow, ()), (slow, (True,)), (sw_slow, ())]:
                try: await f(b, *a)
                except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
            await b.close()
    finally:
        srv.terminate()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
