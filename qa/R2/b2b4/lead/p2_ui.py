# lead 重現批 2：UI-01～04 對比與字級、C-P3-6 交通連結可點範圍、VJW chip（自己量，不用 qa-ui 的 metrics.js）
import sys, os, asyncio, json
sys.path.insert(0, "/home/claude/qa-r2/work/ui"); sys.path.insert(0, "/home/claude/build/ft"); os.chdir("/home/claude/build/ft")
import fulltest as ft, synctest as S
from panels2 import FULL
from playwright.async_api import async_playwright
OUT = "/home/claude/qa-r2/work/lead/"
CR = r'''(sel,txt)=>{
 const L=c=>{const m=c.match(/[\d.]+/g).map(Number);const f=v=>{v/=255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4};return [.2126*f(m[0])+.7152*f(m[1])+.0722*f(m[2]),m[3]??1]};
 const bg=e=>{while(e){const c=getComputedStyle(e).backgroundColor;const a=c.match(/[\d.]+/g).map(Number);if((a[3]??1)>0.5)return c;e=e.parentElement}return "rgb(255,255,255)"};
 let els=[...document.querySelectorAll(sel)];if(txt)els=els.filter(e=>(e.textContent||"").trim().startsWith(txt)&&e.childElementCount==0);
 return els.slice(0,4).map(e=>{const s=getComputedStyle(e),fg=s.color,b=bg(e),[l1]=L(fg),[l2]=L(b);const r=(Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05);
  return {t:(e.textContent||"").trim().slice(0,14),fg,bg:b,ratio:+r.toFixed(2),fs:s.fontSize,fw:s.fontWeight,op:s.opacity}})}'''
async def main():
    R = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # UI-01 旅程回顧第 5 頁
        ctx = await S.mkctx(b, tz="Asia/Taipei")
        pg = await S.opn(ctx, ft.twt(11, 24, 23, 59), pre=S.seed(FULL), wait=1200)
        await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(600)
        await pg.click('[data-story-open]'); await pg.wait_for_timeout(1500)
        for i in range(4): await pg.mouse.click(350, 422); await pg.wait_for_timeout(1500)
        await pg.wait_for_timeout(2000)
        R["UI-01 page"] = await pg.evaluate('document.querySelector(".st-page")?.innerText.slice(0,20)')
        R["UI-01"] = await pg.evaluate("(" + CR + ")('.story *','星星')")
        R["UI-01 leaf"] = [x for x in R["UI-01"] if x["t"] == "星星"]
        await pg.screenshot(path=OUT + "ui01_story5.png")
        await ctx.close()
        # UI-03 回顧封面提示（11/25）
        ctx = await S.mkctx(b, tz="Asia/Taipei")
        pg = await S.opn(ctx, ft.twt(11, 25, 10, 0), pre=S.seed(FULL), wait=1200)
        await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(600)
        await pg.click('[data-story-open]'); await pg.wait_for_timeout(3000)
        R["UI-03"] = await pg.evaluate("(" + CR + ")('.story *','點')")
        await pg.screenshot(path=OUT + "ui03_cover.png")
        await ctx.close()
        # UI-02 行事曆面板、UI-04 行李進度、C-P3-6、chip
        ctx = await S.mkctx(b)
        pg = await S.opn(ctx, "2026-11-19T13:00:00+09:00", pre=S.seed(FULL), wait=1500)
        await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(600)
        await pg.click('[data-cal]'); await pg.wait_for_timeout(900)
        R["UI-02 cal"] = [x for x in await pg.evaluate("(" + CR + ")('.sheet-modal *, [role=dialog] *','')") if x["ratio"] < 4.5 and x["t"]][:6]
        await pg.screenshot(path=OUT + "ui02_cal.png")
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(500)
        await pg.evaluate('tab="list";listSub="pack";render()'); await pg.wait_for_timeout(800)
        R["UI-04 smallest"] = await pg.evaluate('''[...document.querySelectorAll("#app *")].filter(e=>e.childElementCount==0&&e.innerText&&e.innerText.trim()&&e.getBoundingClientRect().height>0).map(e=>[parseFloat(getComputedStyle(e).fontSize),e.innerText.trim().slice(0,12),e.className.baseVal??e.className]).sort((a,b)=>a[0]-b[0]).slice(0,4)''')
        # C-P3-6
        await pg.evaluate('tab="plan";view="day";dayIdx=2;render(true)'); await pg.wait_for_timeout(900)
        R["C-P3-6"] = await pg.evaluate('''(()=>{const as=[...document.querySelectorAll(".leg a")];return as.slice(0,3).map(a=>{a.scrollIntoView({block:"center"});const r=a.getBoundingClientRect(),bf=getComputedStyle(a,"::before"),x=r.left+20;let hit=[];
          for(let y=Math.floor(r.top)-6;y<=Math.ceil(r.bottom)+26;y++){const e=document.elementFromPoint(x,y);if(e&&(e===a||a.contains(e)))hit.push(y)}
          return {n:as.length,h:+r.height.toFixed(1),beforeH:bf.height,beforeTop:bf.top,beforeTf:bf.transform,hitSpan:hit.length?(hit.at(-1)-hit[0]+1):0,aboveTop:+(r.top-hit[0]).toFixed(1),belowBottom:+(hit.at(-1)-r.bottom).toFixed(1)}})})()''')
        # chip
        await pg.evaluate('tab="list";listSub="todo";render()'); await pg.wait_for_timeout(800)
        R["chip"] = await pg.evaluate('''[...document.querySelectorAll("a,button")].filter(e=>/VJW|填寫教學/.test(e.innerText)).map(a=>{const r=a.getBoundingClientRect();a.scrollIntoView({block:"center"});const r2=a.getBoundingClientRect(),x=r2.left+r2.width/2;let hit=[];for(let y=Math.floor(r2.top)-20;y<=r2.bottom+20;y++){const e=document.elementFromPoint(x,y);if(e&&(e===a||a.contains(e)))hit.push(y)}return {t:a.innerText.trim(),h:+r2.height.toFixed(1),before:getComputedStyle(a,"::before").height,hitSpan:hit.length?hit.at(-1)-hit[0]+1:0}})''')
        await ctx.close(); await b.close()
    print(json.dumps(R, ensure_ascii=False, indent=1))
asyncio.run(main())
