# Service Worker：版本更新後舊快取清掉、第一次離線開啟、更新後頁面是否換成新版
# 用 /home/claude/qa/site_v44、site_v45 的「複本」在本機 8767 埠測（不動原始資料夾）
import asyncio, json, os, shutil, subprocess, time, qa_common as q
from playwright.async_api import async_playwright
ROOT="/home/claude/qa/site_live"
def deploy(v):
    if os.path.exists(ROOT): shutil.rmtree(ROOT)
    shutil.copytree(f"/home/claude/qa/site_{v}",ROOT,copy_function=shutil.copy)  # 不保留 mtime，避免 http.server 回 304
async def main():
    deploy("v44")
    srv=subprocess.Popen(["python3","-m","http.server","8767"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            ctx=await q.mkctx(b,service_workers="allow")
            await ctx.add_init_script('try{localStorage.setItem("ngy:tour","1")}catch(e){}')
            pg=await ctx.new_page(); await pg.goto("http://localhost:8767/"); await pg.wait_for_timeout(2500)
            await pg.reload(); await pg.wait_for_timeout(1500)
            ctl=await pg.evaluate('!!navigator.serviceWorker.controller')
            keys=await pg.evaluate('caches.keys()')
            q.rec("SW","第一次開啟後 SW 接管、建立 ngy-v44 快取",ctl and keys==["ngy-v44"],keys)
            # 第一次開啟就直接離線（只開過一次、沒有 reload）
            ctx2=await q.mkctx(b,service_workers="allow"); await ctx2.add_init_script('try{localStorage.setItem("ngy:tour","1")}catch(e){}')
            p2=await ctx2.new_page(); await p2.goto("http://localhost:8767/"); await p2.wait_for_timeout(2500)
            await ctx2.set_offline(True)
            try:
                await p2.reload(); await p2.wait_for_timeout(1500); t=await p2.evaluate('document.body.innerText.slice(0,30)')
            except Exception as e: t="ERR "+str(e)[:80]
            q.rec("SW","只開過一次（沒重新整理）就離線，仍能打開",("名古屋" in t),t)
            await ctx2.close()
            # 部署 v45（index.html 加上標記）
            deploy("v45")
            s=open(ROOT+"/index.html",encoding="utf8").read().replace("<title>","<title>V45-",1) if "<title>" in open(ROOT+"/index.html",encoding="utf8").read() else None
            idx=open(ROOT+"/index.html",encoding="utf8").read()
            idx=idx.replace('<body','<body data-ver="v45"',1); open(ROOT+"/index.html","w",encoding="utf8").write(idx)
            # 使用者在背景很久後回到 App：通常是重新打開
            await pg.reload(); await pg.wait_for_timeout(3000)
            v1=await pg.evaluate('document.body.dataset.ver||"v44"'); keys1=await pg.evaluate('caches.keys()')
            await pg.wait_for_timeout(6000)
            regst=await pg.evaluate('navigator.serviceWorker.getRegistration().then(r=>({active:r.active&&r.active.state,waiting:!!r.waiting,installing:!!r.installing}))')
            await pg.evaluate('navigator.serviceWorker.getRegistration().then(r=>r.update())'); await pg.wait_for_timeout(4000)
            regst2=await pg.evaluate('navigator.serviceWorker.getRegistration().then(r=>({active:r.active&&r.active.state,waiting:!!r.waiting,installing:!!r.installing}))')
            q.note("SW","新版上線後 SW 狀態（重開 6 秒後／手動 update 後）",[regst,regst2,await pg.evaluate('caches.keys()')])
            await pg.reload(); await pg.wait_for_timeout(1500)
            v2=await pg.evaluate('document.body.dataset.ver||"v44"'); keys2=await pg.evaluate('caches.keys()')
            q.rec("SW","新版上線後重開一次就是新版頁面（網路優先）",v1=="v45",{"第一次重開":v1,"第二次":v2})
            q.rec("SW","舊快取 ngy-v44 被清掉",keys2==["ngy-v45"],{"第一次重開後":keys1,"第二次":keys2})
            # 離線開啟拿到的是哪一版
            await ctx.set_offline(True); await pg.reload(); await pg.wait_for_timeout(1500)
            v3=await pg.evaluate('document.body.dataset.ver||"v44"')
            q.rec("SW","更新後離線開啟是新版",v3=="v45",v3)
            # 離線時用不存在的網址（例如 #k= 的連結加了 ?fbclid）
            try:
                await pg.goto("http://localhost:8767/?fbclid=abc#k=neko-qa"); await pg.wait_for_timeout(1500); t=await pg.evaluate('document.body.innerText.slice(0,20)')
            except Exception as e: t="ERR "+str(e)[:80]
            q.rec("SW","離線時開啟帶查詢參數的連結（?fbclid=…）仍顯示 App",("名古屋" in t),t)
            # 字型、Firebase 程式庫的快取（gstatic）：本機假程式庫不經過 SW（route 在 SW 前）→ 無法驗證
            q.note("SW","Firebase 程式庫（www.gstatic.com）快取優先策略：Playwright route 會攔在 SW 之前，本機無法驗證，列入實機測試","")
            await ctx.close(); await b.close()
    finally:
        srv.terminate()
    q.dump("sw")
asyncio.run(main())
