# 壓力測試（只在本機假資料庫）：資料量、快速切換、長時間執行、低階裝置
import asyncio, json, time, random, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
META={f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2}}
DAYS=["11/17","11/18","11/19","11/20","11/21","11/22","11/23","11/24"]
def gen_exp(n,seed=1):
    r=random.Random(seed);d={};tot=0;cash={"zhang":0,"star":0};bal=0
    for i in range(n):
        a=r.randint(100,30000);who=r.choice(["zhang","star"]);pay=r.choice(["cash","card"]);split=r.choice(["both","self"])
        d[f"{B}/expenses/e{i:05d}"]={"amt":a,"cat":r.choice(["food","move","shop","ticket","stay","etc"]),"who":who,"split":split,"pay":pay,"day":r.choice(DAYS),"note":f"測試{i}","ts":1000+i,**({"tf":True} if a>=5000 and i%5==0 else {})}
        tot+=a
        if pay=="cash":cash[who]+=a
        if split=="both":bal+=a/2 if who=="zhang" else -a/2
    return d,tot,cash,bal
async def timed(pg,js):
    return await pg.evaluate('(async()=>{const t=performance.now();'+js+';await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return Math.round(performance.now()-t)})()')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        rows=[]
        # ---------- 記帳筆數 ----------
        for n in [50,300,1000]:
            db,tot,cash,bal=gen_exp(n); db.update(META); db[f"{B}/wallet/zhang"]={"cashIn":10**8,"ts":1}
            ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,20,20,0),init=q.seed(db)); await pg.wait_for_timeout(1500)
            await q.home(pg)
            th=await timed(pg,'render(true)')
            ta=await timed(pg,'tab="acct";render()')
            # 新增一筆（含 snapshot 回來後重畫）的時間
            await pg.fill('#f-amt','123')
            tadd=await pg.evaluate('(async()=>{const t=performance.now();document.getElementById("f-save").click();await new Promise(r=>setTimeout(r,0));while(!document.getElementById("f-msg").innerText.includes("已記下"))await new Promise(r=>setTimeout(r,5));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return Math.round(performance.now()-t)})()')
            # 一次 snapshot 觸發的重畫成本（模擬對方新增一筆）
            tsnap=await timed(pg,'renderAcct()')
            sm=await pg.inner_text('#acct-sum')
            ok=f"¥{tot+123:,}" in sm
            st=await pg.inner_text('#acct-sum .settle')
            expbal=bal+61.5
            m=await q.metrics(pg)
            # 捲動：每 16ms 捲動 200px，統計長 frame
            jank=await pg.evaluate('(async()=>{const fr=[];let last=performance.now();let run=true;(function f(t){fr.push(t-last);last=t;if(run)requestAnimationFrame(f)})(last);for(let y=0;y<document.body.scrollHeight;y+=200){scrollTo(0,y);await new Promise(r=>setTimeout(r,16))}run=false;fr.shift();return {frames:fr.length,over50:fr.filter(x=>x>50).length,max:Math.round(Math.max(...fr))}})()')
            rows.append({"項目":f"記帳 {n} 筆","首頁重畫ms":th,"記帳頁渲染ms":ta,"新增一筆到畫面更新ms":tadd,"renderAcct ms":tsnap,"合計正確":ok,"結算":st,"預期結算差額":expbal,"heapMB":m["heapMB"],"DOM nodes":m["nodes"],"捲動":jank})
            q.rec("壓力 記帳",f"{n} 筆合計正確（含新增一筆）",ok,sm.split("\n")[1] if "\n" in sm else sm)
            if n==1000: await pg.screenshot(path=q.SHOTS+"stress_acct_1000.png")
            await ctx.close()
        # 時間掛鐘下的 CPU throttle 4x / 6x：1000 筆 記帳頁
        for rate in [4,6]:
            db,tot,cash,bal=gen_exp(1000); db.update(META)
            ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,20,20,0),init=q.seed(db)); await pg.wait_for_timeout(1500)
            c=await ctx.new_cdp_session(pg); await c.send("Emulation.setCPUThrottlingRate",{"rate":rate})
            ta=await timed(pg,'tab="acct";render()')
            await pg.fill('#f-amt','55')
            tadd=await timed(pg,'document.getElementById("f-save").click();await new Promise(r=>setTimeout(r,50))')
            tl=await timed(pg,'tab="list";render()')
            rows.append({"項目":f"記帳 1000 筆＋CPU {rate}× 降速","記帳頁渲染ms":ta,"按記下到重畫ms":tadd,"切到清單ms":tl})
            await ctx.close()
        # ---------- 清單 各 200 筆 ----------
        db=dict(META)
        for g,base in [("prep",0),("buy",1000),("pack",2000)]:
            for i in range(200): db[f"{B}/items/{g}{i:03d}"]={"group":g,"title":f"{g} 項目 {i}","note":"備註","due":"11/20 10:00" if g=="prep" and i%7==0 else "","order":base+i,**({"cat":"etc"} if g=="pack" else {})}
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,19,12,0),init=q.seed(db)); await pg.wait_for_timeout(1500)
        tl=await timed(pg,'tab="list";render()')
        tchk=await pg.evaluate('(async()=>{const c=document.querySelector("#c-buy100");const t=performance.now();c.click();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return Math.round(performance.now()-t)})()')
        tsort=await timed(pg,'document.querySelector("[data-sort-toggle=prep]").click()')
        w0=await pg.evaluate('window.__writes||0')
        ids=await pg.evaluate('[...document.querySelectorAll("[data-sort-id]")].map(x=>x.dataset.sortId)')
        tord=await pg.evaluate('(async()=>{const ids=[...document.querySelectorAll("[data-sort-id]")].map(x=>x.dataset.sortId);ids.unshift(ids.pop());const t=performance.now();await applyOrder("prep",ids,true);return Math.round(performance.now()-t)})()')
        w1=await pg.evaluate('window.__writes||0')
        # 實際拖曳 199 → 0
        await pg.evaluate('document.querySelector("[data-sort-toggle=prep]").click()'); await pg.wait_for_timeout(200)
        await pg.click('[data-pack-open]'); tp=await timed(pg,'render(true)')
        tpk=await pg.evaluate('(async()=>{const c=document.querySelector("[data-pack]");const t=performance.now();c.click();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return Math.round(performance.now()-t)})()')
        await pg.screenshot(path=q.SHOTS+"stress_pack_200.png")
        m=await q.metrics(pg)
        await q.home(pg); th=await timed(pg,'render(true)')
        rows.append({"項目":"清單 待辦/要買/行李 各 200 筆","清單頁渲染ms":tl,"勾選一項ms":tchk,"進入排序ms":tsort,"最後一項移到最上（批次寫入）ms":tord,"批次寫入筆數":w1-w0,"行李頁渲染ms":tp,"行李勾選ms":tpk,"首頁ms":th,"heapMB":m["heapMB"],"nodes":m["nodes"]})
        await ctx.close()
        # ---------- 心情 8 天 × 2 人 × 多次編輯 + 回顧 ----------
        db=dict(META)
        for d in DAYS:
            for w in ["zhang","star"]:
                db[f"{B}/moods/{d.replace('/','-')}_{w}"]={"score":random.randint(1,5),"note":"很長的心情"*40,"who":w,"day":d,"ts":1}
        e,_,_,_=gen_exp(300); db.update(e)
        ctx=await q.mkctx(b,tz="Asia/Taipei",accept_downloads=True); pg=await q.page(ctx,q.twt(11,25,20,0),init=q.seed(db)); await pg.wait_for_timeout(1500); await q.home(pg)
        # 一個人連續編輯同一天心情 20 次
        await pg.evaluate('tab="plan";view="day";dayIdx=3;render()'); await pg.wait_for_timeout(200)
        te=[]
        for i in range(20):
            t0=time.time()
            await pg.click('#mood [data-mood-edit]'); await pg.click(f'#mood .fbtn[data-score="{i%5+1}"]'); await pg.fill('#mood-note',f"第{i}次"); await pg.click('#mood-form .primary')
            te.append(round((time.time()-t0)*1000))
        mv=(await q.mock(pg,"/moods/11-20_zhang")).get(f"{B}/moods/11-20_zhang",{})
        q.rec("壓力 心情","連續編輯 20 次後雲端為最後一次",mv.get("note")=="第19次",mv.get("note"))
        await q.home(pg)
        tst=await timed(pg,'openStory()')
        await pg.evaluate('document.querySelectorAll(".st-tap.next").forEach(()=>{});')
        n=await pg.evaluate('document.querySelectorAll(".st-page").length')
        for i in range(n-1): await pg.click('.st-tap.next'); await pg.wait_for_timeout(80)
        await pg.screenshot(path=q.SHOTS+"stress_review_sum_long.png")
        await pg.evaluate('navigator.canShare=undefined')
        t0=time.time()
        async with pg.expect_download(timeout=20000) as dl:
            await pg.click('[data-story-save]')
        d=await dl.value; tsave=round((time.time()-t0)*1000)
        path=q.SHOTS+"stress_review_saved.png"; await d.save_as(path)
        rows.append({"項目":"心情 16 則（各 200 字）＋記帳 300 筆，回顧","編輯心情一次（含點擊）ms":f"中位數 {sorted(te)[10]}","開啟故事ms":tst,"頁數":n,"存成圖片ms":tsave})
        await ctx.close()
        # ---------- 頻繁切換 100 次：記憶體、listener ----------
        db,_,_,_=gen_exp(300); db.update(META)
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,20,12,0),init=q.seed(db)); await pg.wait_for_timeout(1500)
        await q.home(pg); await pg.evaluate('gc&&gc()') if False else None
        m0=await q.metrics(pg)
        t0=time.time()
        for i in range(100):
            await pg.evaluate('document.querySelector("nav.tabs button[data-tab=%s]").click()'%["plan","wx","move","acct","list"][i%5])
        for i in range(100):
            await pg.evaluate('tab="plan";view="day";render();switchDay(%d)'%(i%8))
        await pg.wait_for_timeout(500)
        el=round((time.time()-t0)*1000)
        c=await ctx.new_cdp_session(pg); await c.send("HeapProfiler.collectGarbage"); await c.detach()
        await q.home(pg); m1=await q.metrics(pg)
        # 開關面板 50 次（錢包、求助、行事曆、地圖檢視器）
        for i in range(50):
            await pg.evaluate('openSos();document.querySelector(".sheet-modal .sm-x").click();openWallet();document.querySelector(".sheet-modal .sm-x").click();openCalSheet();document.querySelector(".sheet-modal .sm-x").click()')
        for i in range(30):
            await pg.evaluate('openViewer("ghibli-map.jpg","x");document.querySelector(".viewer .vclose").click()')
        await pg.wait_for_timeout(500)
        c=await ctx.new_cdp_session(pg); await c.send("HeapProfiler.collectGarbage"); await c.detach()
        m2=await q.metrics(pg)
        lst=await pg.evaluate('(()=>{let n=0;const o=EventTarget.prototype.addEventListener;return getEventListeners?0:0})()') if False else None
        rows.append({"項目":"分頁 100 次＋日期 100 次切換","耗時ms":el,"heap 前MB":m0["heapMB"],"heap 後MB":m1["heapMB"],"listeners 前":m0["listeners"],"listeners 後":m1["listeners"],"nodes 前/後":f'{m0["nodes"]}/{m1["nodes"]}'})
        rows.append({"項目":"求助/錢包/行事曆面板各開關 50 次＋地圖檢視器 30 次","heapMB":m2["heapMB"],"listeners":m2["listeners"],"nodes":m2["nodes"]})
        q.rec("壓力 切換","切換 200 次後 listener 數沒有持續增加（±30）",abs(m1["listeners"]-m0["listeners"])<=30,[m0["listeners"],m1["listeners"]])
        q.rec("壓力 面板","開關面板 180 次後 listener 數沒有持續增加（±30）",abs(m2["listeners"]-m1["listeners"])<=30,[m1["listeners"],m2["listeners"]])
        await ctx.close()
        # ---------- 長時間執行：12 小時 ----------
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,20,8,0),init=q.seed(META)); await pg.wait_for_timeout(1000)
        await pg.evaluate('tab="plan";view="day";dayIdx=todayIdx;render()')
        m0=await q.metrics(pg); snaps=[]
        for h in range(12):
            await pg.clock.run_for(3600*1000); await pg.wait_for_timeout(100)
            if h in (0,5,11):
                c=await ctx.new_cdp_session(pg); await c.send("HeapProfiler.collectGarbage"); await c.detach()
                snaps.append((h+1,await q.metrics(pg)))
        rows.append({"項目":"當天行程頁開著 12 小時（run_for，30 秒計時器都會跑）","起始":m0,"1/6/12 小時":snaps,"JS 錯誤":pg.errs[:2]})
        await ctx.close()
        # ---------- 低階裝置：Slow 3G + CPU 6x 首次載入 ----------
        for label,lat,down,rate in [("Fast 3G + CPU 4×",150,1.6*1024*1024/8,4),("Slow 3G + CPU 6×",400,500*1024/8,6)]:
            ctx=await q.mkctx(b); pg=await ctx.new_page()
            c=await ctx.new_cdp_session(pg)
            await c.send("Network.enable"); await c.send("Network.emulateNetworkConditions",{"offline":False,"latency":lat,"downloadThroughput":down,"uploadThroughput":down})
            await c.send("Emulation.setCPUThrottlingRate",{"rate":rate})
            await pg.add_init_script('try{localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang")}catch(e){}')
            t0=time.time(); await pg.goto('http://localhost:8766/',wait_until="load"); tl=round((time.time()-t0)*1000)
            nav=await pg.evaluate('(()=>{const n=performance.getEntriesByType("navigation")[0];const p=performance.getEntriesByType("paint");return {dcl:Math.round(n.domContentLoadedEventEnd),load:Math.round(n.loadEventEnd),fcp:Math.round((p.find(x=>x.name==="first-contentful-paint")||{}).startTime||0),size:n.transferSize}})()')
            ti=await timed(pg,'document.querySelector("nav.tabs button[data-tab=acct]").click()')
            rows.append({"項目":f"首次載入 {label}","load 事件ms":tl,"FCP ms":nav["fcp"],"DCL ms":nav["dcl"],"index.html 傳輸位元組":nav["size"],"切到記帳ms":ti})
            await ctx.close()
        json.dump(rows,open("/home/claude/qa/scripts/out_stress_rows.json","w"),ensure_ascii=False,indent=1,default=str)
        for r in rows: print("ROW",json.dumps(r,ensure_ascii=False,default=str))
        q.dump("stress")
        await b.close()
asyncio.run(main())
