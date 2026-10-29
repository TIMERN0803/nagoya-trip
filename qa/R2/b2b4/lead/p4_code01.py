# CODE-01 重現：?scene= 注入（出發前直接開首頁；旅途中切回首頁）
import asyncio, sys, os, json, urllib.parse
sys.path.insert(0,"/home/claude/build/ft"); os.chdir("/home/claude/build/ft")
import synctest as st
from playwright.async_api import async_playwright
PAY='"><img src=x onerror="window.__xss=document.title||1">'
Q='({p:document.querySelector("svg.scene")?.dataset.period, x:window.__xss||0, img:document.querySelectorAll(".scene-wrap img").length})'
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); ctx=await st.mkctx(b)
    for label,t in [("出發前 10/30","2026-10-30T10:00:00+08:00"),("旅途中 11/18 切回首頁","2026-11-18T09:00:00+09:00")]:
      for u in ["http://localhost:8766/?scene=dinner","http://localhost:8766/?scene="+urllib.parse.quote(PAY)]:
        pg=await st.opn(ctx,t,pre=st.seed(st.META),url=u,wait=2000)
        if "旅途中" in label:
          await pg.evaluate('try{tab="plan";view="home";render(true)}catch(e){document.querySelector("[data-home],.back")?.click()}'); await pg.wait_for_timeout(900)
        r=await pg.evaluate(Q); print(label, "payload" if "img" in u else "dinner", json.dumps(r,ensure_ascii=False), pg.errs[:2])
        if "img" in u: await pg.screenshot(path="/home/claude/qa-r2/work/lead/code01_%s.png"%("pre" if "出發" in label else "trip"))
        await pg.close()
    await b.close()
asyncio.run(main())
