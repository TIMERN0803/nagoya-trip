# 使用體驗走查：第一次用的星星、街頭單手網路不穩的阿彰（390×844 @2x 截圖）
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
S=q.SHOTS+"ux_"
async def fresh(b,t,tz="Asia/Taipei",hash="",init=""):
    ctx=await q.mkctx(b,tz=tz,dsf=2)
    pg=await ctx.new_page(); pg.errs=[]; pg.on('pageerror',lambda e:pg.errs.append(str(e)))
    await pg.clock.install(time=t)
    if init: await pg.add_init_script('try{if(!sessionStorage.getItem("s")){'+init+'sessionStorage.setItem("s",1)}}catch(e){}')
    await pg.goto('http://localhost:8766/'+hash); await pg.wait_for_timeout(1200)
    return ctx,pg
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # ===== 星星：收到連結第一次打開（出發前） =====
        ctx,pg=await fresh(b,q.twt(11,5,20,0),hash=f"#k={q.CODE}",init=q.seed({f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2}}))
        await pg.clock.run_for(1500); await pg.wait_for_timeout(500)
        await pg.screenshot(path=S+"star_01_first_open.png")
        st=await pg.evaluate('({code:localStorage.getItem("ngy:code"),hash:location.hash,me:localStorage.getItem("ngy:me"),live,coach:!!document.querySelector(".coach"),coachText:document.querySelector(".coach-bub p")?.innerText})')
        q.note("星星首次","連結 #k= 開啟後",st)
        steps=[]
        for i in range(6):
            if not await pg.query_selector('[data-coach-next]'): break
            steps.append(await pg.inner_text('.coach-bub p')); await pg.screenshot(path=S+f"star_02_tour_{i}.png")
            await pg.click('[data-coach-next]'); await pg.clock.run_for(600); await pg.wait_for_timeout(400)
        q.note("星星首次","教學步驟文字",steps)
        await pg.wait_for_timeout(300); await pg.screenshot(path=S+"star_03_after_tour.png")
        su=await pg.evaluate('document.querySelector(".su-sheet")?.innerText.replace(/\\s+/g," ").slice(0,200)')
        q.note("星星首次","教學結束後畫面（出發前設定）",su)
        if await pg.query_selector('[data-setup-me="star"]'):
            await pg.click('[data-setup-me="star"]'); await pg.wait_for_timeout(1700)
        await pg.screenshot(path=S+"star_04_setup_list.png")
        rows=await pg.evaluate('[...document.querySelectorAll(".su-row")].map(r=>(r.classList.contains("done")?"✔ ":"□ ")+r.querySelector(".su-txt b").innerText)')
        q.note("星星首次","選身分後設定清單（自動打勾）",rows)
        await pg.click('.su-sheet .sm-x'); await pg.wait_for_timeout(200)
        await q.home(pg); await pg.evaluate('scrollTo(0,0)'); await pg.screenshot(path=S+"star_05_home_pre.png",full_page=True)
        await ctx.close()
        # 沒有連結、只拿到代碼
        ctx,pg=await fresh(b,q.twt(11,5,20,0),init='localStorage.setItem("ngy:tour","1");')
        await q.tab(pg,"list"); await pg.screenshot(path=S+"star_06_list_codeform.png")
        await q.tab(pg,"acct"); await pg.screenshot(path=S+"star_07_acct_no_me.png")
        who=await pg.evaluate('document.querySelector("[data-pick=who] [aria-pressed=true]")?.dataset.v')
        q.note("星星首次","沒選身分時記帳「誰付的」預設",who)
        await pg.fill('#f-code','NEKO-QA ') if await pg.query_selector('#f-code') else None
        await ctx.close()
        # 輸入錯的代碼（大小寫/空白）
        ctx,pg=await fresh(b,q.twt(11,5,20,0),init='localStorage.setItem("ngy:tour","1");')
        await q.tab(pg,"list"); await pg.fill('#f-code','neko qa'); await pg.click('#code-form .primary'); await pg.wait_for_timeout(1500)
        cd=await pg.evaluate('localStorage.getItem("ngy:code")'); s=await pg.evaluate('document.querySelector(".sync,#code-form")?.innerText.replace(/\\s+/g," ")')
        q.rec("代碼","輸入含空白的代碼「neko qa」：應提示格式錯誤（不應存成無效代碼卡在連線中）","連線中" not in (s or ""),{"存下的代碼":cd,"狀態":s})
        await pg.screenshot(path=S+"code_with_space.png")
        await ctx.close()
        # 換代碼/離開旅程：有沒有地方可以改
        ctx,pg=await fresh(b,q.twt(11,5,20,0),init=f'localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","star");localStorage.setItem("ngy:code","neko-typo");')
        await q.tab(pg,"list"); has=await pg.evaluate('!!document.querySelector("#code-form")')
        await pg.screenshot(path=S+"code_typo_stuck.png")
        q.rec("代碼","代碼打錯（不存在的旅程也會連上，變成另一個空旅程）時有辦法看到／更換目前代碼",has,{"狀態":await pg.evaluate('document.querySelector(".sync")?.innerText')})
        await ctx.close()
        # ===== 阿彰：旅途中 =====
        seed={f"{B}/wallet/zhang":{"cashIn":30000,"ts":1}}
        ctx=await q.mkctx(b,dsf=2); pg=await q.page(ctx,q.jst(11,19,8,30),init=q.seed(seed))
        await pg.screenshot(path=S+"zhang_01_open_morning.png")
        await q.home(pg); await pg.evaluate('scrollTo(0,0)'); await pg.screenshot(path=S+"zhang_02_home_morning.png")
        await q.tab(pg,"wx"); await pg.screenshot(path=S+"zhang_03_weather.png")
        await pg.evaluate('tab="plan";view="day";dayIdx=todayIdx;render()'); await pg.wait_for_timeout(200)
        legs=await pg.evaluate('[...document.querySelectorAll(".leg a")].map(a=>[a.innerText.replace(/\\s+/g," "),a.href])')
        q.note("阿彰","當天行程交通連結",legs[:3])
        first=await pg.evaluate('(()=>{const a=document.querySelector("#it-0 a.pic,#it-0 .chip");return a?[a.innerText,a.href]:null})()')
        q.note("阿彰","第一站的地圖連結",first)
        await pg.evaluate('document.getElementById("it-1").scrollIntoView({block:"center"})'); await pg.screenshot(path=S+"zhang_04_day_leg.png")
        # 結帳：記一筆現金含免稅
        await q.tab(pg,"acct"); await pg.screenshot(path=S+"zhang_05_acct_top.png")
        await pg.fill('#f-amt','8800'); await pg.click('[data-pick="cat"] [data-v="shop"]'); await pg.fill('#f-note','松坂屋'); await pg.click('[data-tf-toggle]')
        await pg.screenshot(path=S+"zhang_06_acct_form_filled.png",full_page=True)
        save=await pg.evaluate('(()=>{const r=document.getElementById("f-save").getBoundingClientRect();return {top:Math.round(r.top),bottom:Math.round(r.bottom),vh:innerHeight}})()')
        q.note("阿彰","記帳「記下這筆」按鈕位置（未捲動時）",save)
        await pg.click('#f-save'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=S+"zhang_07_acct_saved.png")
        # 鍵盤彈出：金額欄 focus 時 viewport 變小
        await pg.evaluate('scrollTo(0,0)'); await pg.set_viewport_size({"width":390,"height":470}); await pg.focus('#f-amt'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=S+"zhang_08_acct_keyboard.png")
        await pg.set_viewport_size({"width":390,"height":844})
        # 求助 → 給司機看
        await q.home(pg); await pg.click('[data-sos]'); await pg.wait_for_timeout(200); await pg.screenshot(path=S+"zhang_09_sos_default.png")
        steps=["點求助","預設在日常日文，要切到「緊急求助」","往下找飯店卡","按「給司機看」"]
        await pg.click('[data-sos-tab="emg"]'); await pg.wait_for_timeout(200); await pg.screenshot(path=S+"zhang_10_sos_emg.png")
        await pg.click('[data-sos-show="hotel"]'); await pg.wait_for_timeout(200); await pg.screenshot(path=S+"zhang_11_hotel_show.png")
        q.note("阿彰","迷路時從首頁到「給司機看」需要的點擊數",{"點擊":3,"步驟":steps})
        await pg.evaluate('document.querySelector(".sos-show").remove();document.querySelector(".sheet-modal").remove();sosSheet=null;document.body.style.overflow=""')
        # 晚上回家
        await ctx.close()
        ctx=await q.mkctx(b,dsf=2); pg=await q.page(ctx,q.jst(11,19,22,30),init=q.seed(seed)); await q.home(pg)
        await pg.screenshot(path=S+"zhang_12_night_home.png")
        await pg.evaluate('(()=>{window._op=[];window.open=(u)=>{window._op.push(u);return null}})()'); await pg.click('.fab'); u=await pg.evaluate('window._op.slice(-1)[0]')
        q.note("阿彰","回家導航網址",u)
        await pg.evaluate('gotoMood(todayIdx)'); await pg.wait_for_timeout(400); await pg.screenshot(path=S+"zhang_13_mood.png")
        await q.tab(pg,"list"); await pg.click('[data-pack-open]'); await pg.wait_for_timeout(200); await pg.screenshot(path=S+"zhang_14_pack.png")
        await ctx.close()
        # 最後一天
        db=dict(seed); db[f"{B}/expenses/t1"]={"amt":8800,"cat":"shop","who":"zhang","split":"both","pay":"cash","day":"11/22","note":"松坂屋","ts":1,"tf":True}
        ctx=await q.mkctx(b,dsf=2); pg=await q.page(ctx,q.jst(11,24,7,40),init=q.seed(db)+'localStorage.setItem("ngy:notify","1");')
        await pg.clock.run_for(21000); await pg.wait_for_timeout(300)
        await pg.screenshot(path=S+"last_01_day.png")
        toast=await pg.evaluate('document.getElementById("toast")?.innerText.replace(/\\s+/g," ")')
        q.note("最後一天","07:40 開著 App 的提醒",toast)
        await pg.click('[data-go-tf]') if await pg.query_selector('[data-go-tf]') else None
        await pg.wait_for_timeout(400); await pg.screenshot(path=S+"last_02_tf.png")
        await ctx.close()
        # 回國後
        ctx=await q.mkctx(b,tz="Asia/Taipei",dsf=2); pg=await q.page(ctx,q.twt(11,25,20,0),init=q.seed(db)); await q.home(pg)
        await pg.evaluate('scrollTo(0,0)'); await pg.screenshot(path=S+"after_01_home.png")
        await pg.click('[data-story-open]'); await pg.wait_for_timeout(300); await pg.screenshot(path=S+"after_02_story.png")
        await ctx.close()
        # 回顧：完全沒有資料
        ctx=await q.mkctx(b,tz="Asia/Taipei",dsf=2); pg=await q.page(ctx,q.twt(11,25,20,0),init=q.seed({f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2}})); await q.home(pg)
        await pg.click('[data-story-open]'); await pg.wait_for_timeout(300)
        n=await pg.evaluate('document.querySelectorAll(".st-page").length')
        for i in range(n-1): await pg.click('.st-tap.next'); await pg.wait_for_timeout(100)
        await pg.screenshot(path=S+"after_03_story_empty_sum.png")
        txt=await pg.evaluate('document.querySelector(".st-page.on").innerText.replace(/\\s+/g," ").slice(0,300)')
        q.note("回顧","沒有任何資料時最後一頁",{"頁數":n,"內容":txt,"errs":pg.errs[:2]})
        await ctx.close()
        q.dump("ux")
        await b.close()
asyncio.run(main())
