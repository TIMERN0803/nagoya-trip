# CODE-03 重現：雲端心情 score 不合法時，首頁與當天頁是否還能畫出來
import asyncio, sys, os, json
sys.path.insert(0,"/home/claude/build/ft"); os.chdir("/home/claude/build/ft")
import synctest as st
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for sc in [3,0,"abc",None]:
      ctx=await st.mkctx(b)
      db=dict(st.META); db[st.B+"/moods/11-17_star"]={"score":sc,"note":"x","ts":1,"who":"star","day":"11/17"}
      pg=await st.opn(ctx,"2026-11-18T20:00:00+09:00",pre=st.seed(db),wait=2000)
      day=await pg.evaluate('({mood:!!document.getElementById("mood"), len:document.getElementById("app").innerText.length})')
      await pg.evaluate('tab="plan";view="home";try{render(true)}catch(e){window.__e=String(e)}'); await pg.wait_for_timeout(800)
      home=await pg.evaluate('({strip:!!document.querySelector(".mood-strip"), hero:!!document.querySelector(".hero"), len:document.getElementById("app").innerText.length, e:window.__e||""})')
      await pg.evaluate('try{tab="plan";view="day";dayIdx=0;render(true)}catch(e){window.__e2=String(e)}'); await pg.wait_for_timeout(800)
      d17=await pg.evaluate('({mood:!!document.getElementById("mood"), len:document.getElementById("app").innerText.length, e:window.__e2||""})')
      mv=await pg.evaluate("JSON.stringify(moods)"); txt=await pg.evaluate("document.getElementById(\"mood\")?.innerText.slice(0,80)"); print("moods=",mv,"txt=",repr(txt)); print("score=",sc,"| 當天頁",day,"| 首頁",home,"| 11/17頁",d17,"| pageerror",pg.errs[:2])
      await ctx.close()
    await b.close()
asyncio.run(main())
