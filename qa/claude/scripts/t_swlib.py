# 版本更新時，Firebase 程式庫的快取會不會被一起刪掉？更新後第一次離線開啟能不能同步？
import asyncio, os, shutil, subprocess, time, qa_common as q
from playwright.async_api import async_playwright
ROOT="/home/claude/qa/site_live"
def deploy(v):
    if os.path.exists(ROOT): shutil.rmtree(ROOT)
    shutil.copytree(f"/home/claude/qa/site_{v}",ROOT,copy_function=shutil.copy)
LIST='caches.keys().then(ks=>Promise.all(ks.map(k=>caches.open(k).then(c=>c.keys()).then(rs=>[k,rs.map(r=>r.url).filter(u=>!u.includes("localhost")).map(u=>u.split("/").pop())]))))'
async def main():
    deploy("v44"); srv=subprocess.Popen(["python3","-m","http.server","8767"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            ctx=await q.mkctx(b,service_workers="allow")
            await ctx.add_init_script(f'try{{localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code","{q.CODE}")}}catch(e){{}}')
            pg=await ctx.new_page(); await pg.goto("http://localhost:8767/"); await pg.wait_for_timeout(2500); await pg.reload(); await pg.wait_for_timeout(2500)
            c1=await pg.evaluate(LIST); live1=await pg.evaluate('live')
            q.note("SW 程式庫","v44 使用兩次後的快取內容（外部檔）",{"caches":c1,"live":live1})
            deploy("v45")
            await pg.reload(); await pg.wait_for_timeout(4000)
            c2=await pg.evaluate(LIST)
            q.note("SW 程式庫","上線 v45 後重開一次（有網路）的快取內容",c2)
            await pg.reload(); await pg.wait_for_timeout(3000)
            c3=await pg.evaluate(LIST)
            q.note("SW 程式庫","再重開一次（有網路）後的快取內容",c3)
            st="（離線開啟的同步狀態無法在本機驗證：Playwright route 在離線時仍會回應假程式庫）"
            q.rec("SW 程式庫","更新後下一次離線開啟：Firebase 程式庫仍在快取、可離線同步佇列",any("firebase" in u for k,us in c2 for u in us) ,{"快取":c2,"離線開啟狀態":st})
            await b.close()
    finally: srv.terminate(); shutil.rmtree(ROOT,ignore_errors=True)
    q.dump("swlib")
asyncio.run(main())
