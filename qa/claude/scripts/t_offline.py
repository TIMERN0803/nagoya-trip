# 離線與同步（只用假資料庫）
#  A. Firebase 程式庫載入失敗／500／逾時：App 是否可用、狀態文字
#  B. 「程式庫已快取、但手機離線」（真實 Firestore SDK 的行為用 fs_offline.js 模擬：寫入在本機生效，Promise 等上線才 resolve）
#  C. 程式庫載入失敗時在本機記的資料，恢復連線後有沒有上傳
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
FSO=open("/home/claude/qa/scripts/fs_offline.js").read()
SYNC='(()=>{const s=document.querySelector(".sync, #code-form");return s?s.innerText.replace(/\\s+/g," "):"(無)"})()'
async def exps(pg): return {k:v for k,v in (await q.mock(pg,"/expenses/")).items()}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # ---------- A. 程式庫失敗 ----------
        for mode in ["abort","500","hang"]:
            ctx=await q.mkctx(b,firebase=mode); pg=await q.page(ctx,q.jst(11,19,12,0)); await pg.wait_for_timeout(1500)
            await q.tab(pg,"list"); s1=await pg.evaluate(SYNC)
            await pg.screenshot(path=q.SHOTS+f"sync_lib_{mode}.png")
            await q.tab(pg,"acct"); await pg.fill('#f-amt','500'); await pg.click('#f-save'); await pg.wait_for_timeout(300)
            m=await pg.inner_text('#f-msg'); s2=await pg.evaluate(SYNC)
            usable=("已記下" in m)
            q.rec("程式庫失敗",f"Firebase 程式庫 {mode}：仍可記帳",usable,{"清單頁狀態":s1,"記帳訊息":m,"記帳頁狀態":s2,"errs":pg.errs[:2]})
            if mode=="hang":
                q.rec("程式庫失敗","程式庫一直沒回應（慢網路）時，不應顯示「輸入旅行代碼」表單（代碼其實已存好）","輸入旅行代碼" not in s1,s1)
                # 使用者看到表單，重新輸入代碼
                await q.tab(pg,"list")
                if await pg.query_selector('#f-code'):
                    await pg.fill('#f-code',q.CODE); await pg.click('#code-form .primary'); await pg.wait_for_timeout(5000)
                    s3=await pg.evaluate(SYNC)
                    q.note("程式庫失敗","慢網路下重新輸入代碼後 5 秒的狀態",s3)
                    await pg.screenshot(path=q.SHOTS+"sync_lib_hang_reenter.png")
            await ctx.close()
        # ---------- C. 程式庫載入失敗（離線開啟）→ 本機記資料 → 恢復連線 ----------
        st={"mode":"abort"}
        seedb={f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2},f"{B}/items/srv1":{"group":"buy","title":"星星之前加的","note":"","due":"","order":150},f"{B}/items/p1":{"group":"prep","title":"換日圓","note":"","due":"","order":1},
               f"{B}/wallet/zhang":{"cashIn":20000,"ts":1}}
        ctx=await q.mkctx(b,firebase=st)
        # 先用連線狀態開一次，讓本機有清單快取（模擬平常有用過）
        st["mode"]="mock"; pg=await q.page(ctx,q.jst(11,19,12,0),init=q.seed(seedb)); await pg.wait_for_timeout(1200); await pg.close()
        st["mode"]="abort"
        pg=await ctx.new_page(); pg.errs=[]; pg.on('pageerror',lambda e:pg.errs.append(str(e)))
        await pg.clock.install(time=q.jst(11,19,20,0)); await pg.goto('http://localhost:8766/'); await pg.wait_for_timeout(1500)
        await q.tab(pg,"list"); s0=await pg.evaluate(SYNC)
        await pg.click('[data-item-new="buy"]'); await pg.fill('.chk-form input[name=title]','離線時新增的要買'); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(300)
        cid=await pg.evaluate('document.querySelector("[data-group-id=prep] .chk input:not(:checked)").id'); await pg.check('#'+cid); await pg.wait_for_timeout(200)
        await q.tab(pg,"acct"); await pg.fill('#f-amt','1200'); await pg.fill('#f-note','離線記帳'); await pg.click('#f-save'); await pg.wait_for_timeout(300)
        await pg.click('.wchip'); await pg.wait_for_timeout(200)
        if await pg.locator('.ws [data-wallet-edit][data-mode="add"]').count(): await pg.click('.ws [data-wallet-edit][data-mode="add"]')
        await pg.fill('.ws .w-form input','5000'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(300); await pg.click('.ws .sm-x')
        await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(300)
        await pg.click('#mood .fbtn[data-score="5"]'); await pg.fill('#mood-note','離線寫的心情'); await pg.click('#mood-form .primary'); await pg.wait_for_timeout(300)
        loc=await pg.evaluate('({items:items.length,exp:expenses.length,done:Object.keys(done).length,wallet:cashIn("zhang"),mood:!!moods["11-19_zhang"]})')
        # 恢復連線
        st["mode"]="mock"; await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(2500)
        srv=await q.mock(pg,"")
        up={"要買":any(v.get("title")=="離線時新增的要買" for k,v in srv.items() if "/items/" in k),
            "勾選":(srv.get(f"{B}/checks/{cid[2:]}") or {}).get("done")==True,
            "記帳":any(v.get("note")=="離線記帳" for k,v in srv.items() if "/expenses/" in k),
            "錢包":(srv.get(f"{B}/wallet/zhang") or {}).get("cashIn"),
            "心情":f"{B}/moods/11-19_zhang" in srv}
        after=await pg.evaluate('({sync:document.querySelector(".sync")?.innerText,items:items.some(x=>x.title==="離線時新增的要買"),done:done[%s]===true,wallet:cashIn("zhang"),mood:!!moods["11-19_zhang"]})'%json.dumps(cid[2:]))
        q.note("離線補傳","開啟時程式庫失敗的狀態文字",s0)
        q.rec("離線補傳","離線新增的「要買」恢復連線後上傳雲端",up["要買"],{"雲端":up,"本機畫面":after})
        q.rec("離線補傳","離線勾選恢復連線後上傳雲端",up["勾選"],{"本機畫面勾選還在":after["done"]})
        q.rec("離線補傳","離線記帳恢復連線後上傳雲端",up["記帳"])
        q.rec("離線補傳","離線補錢（錢包 20000→25000）恢復連線後上傳雲端",up["錢包"]==25000,{"雲端":up["錢包"],"本機":after["wallet"]})
        q.rec("離線補傳","離線寫的心情恢復連線後上傳雲端（對方看得到）",up["心情"],{"本機還在":after["mood"]})
        conn=await pg.evaluate('({live,syncMsg,sync:document.querySelector(".sync")?.innerText||""})')
        q.rec("離線補傳","收到 online 事件後應重新連上同步（不用關掉 App）",conn["live"],conn)
        # 使用者把 App 關掉重開（有網路）
        await pg.reload(); await pg.wait_for_timeout(2500)
        srv=await q.mock(pg,"")
        up2={"要買":any(v.get("title")=="離線時新增的要買" for k,v in srv.items() if "/items/" in k),
            "勾選":(srv.get(f"{B}/checks/{cid[2:]}") or {}).get("done")==True,
            "記帳":any(v.get("note")=="離線記帳" for k,v in srv.items() if "/expenses/" in k),
            "錢包":(srv.get(f"{B}/wallet/zhang") or {}).get("cashIn"),
            "心情":f"{B}/moods/11-19_zhang" in srv}
        after2=await pg.evaluate('({live,items:items.some(x=>x.title==="離線時新增的要買"),done:done[%s]===true,wallet:cashIn("zhang"),mood:!!moods["11-19_zhang"],exp:expenses.some(e=>e.note==="離線記帳")})'%json.dumps(cid[2:]))
        q.rec("離線補傳","重開 App 後：離線記帳有上傳",up2["記帳"],{"雲端":up2,"本機":after2})
        q.rec("離線補傳","重開 App 後：離線新增的「要買」有上傳、畫面還在",up2["要買"] and after2["items"],{"雲端":up2["要買"],"本機":after2["items"]})
        q.rec("離線補傳","重開 App 後：離線勾選有上傳、畫面還勾著",up2["勾選"] and after2["done"],{"雲端":up2["勾選"],"本機":after2["done"]})
        q.rec("離線補傳","重開 App 後：離線補錢有上傳（應為 25000）",up2["錢包"]==25000 and after2["wallet"]==25000,{"雲端":up2["錢包"],"本機":after2["wallet"]})
        q.rec("離線補傳","重開 App 後：離線心情有上傳（對方看得到）",up2["心情"],{"雲端":up2["心情"],"本機":after2["mood"]})
        await q.tab(pg,"list"); await pg.screenshot(path=q.SHOTS+"offline_reopen_list.png")
        await ctx.close()

        # ---------- B. 程式庫已快取、手機離線（真實 SDK 行為） ----------
        ctx=await q.mkctx(b,fs=FSO)
        pg=await q.page(ctx,q.jst(11,19,12,0),init=q.seed({f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2},f"{B}/wallet/zhang":{"cashIn":20000,"ts":1}})); await pg.wait_for_timeout(1200)
        await pg.evaluate('__goOffline()'); await ctx.set_offline(True); await pg.evaluate('dispatchEvent(new Event("offline"))')
        await q.tab(pg,"acct"); s=await pg.evaluate(SYNC)
        q.rec("離線（已快取）","手機離線時狀態不應仍顯示綠色「同步中」","同步中" not in s,s)
        await pg.fill('#f-amt','3000'); await pg.fill('#f-note','拉麵'); await pg.click('#f-save'); await pg.wait_for_timeout(1500)
        r=await pg.evaluate('({msg:document.getElementById("f-msg").innerText,amt:document.getElementById("f-amt").value,dis:document.getElementById("f-save").disabled,rows:document.querySelectorAll(".ex[data-edit]").length,chip:document.querySelector(".wchip").innerText.replace(/\\s+/g," ")})')
        await pg.screenshot(path=q.SHOTS+"offline_acct_after_save.png")
        q.rec("離線（已快取）","離線按「記下這筆」後：出現「已記下」、金額欄清空、按鈕可再用",("已記下" in r["msg"]) and r["amt"]=="" and not r["dis"],r)
        # 使用者以為沒存到 → 切分頁再回來 → 再按一次
        await q.tab(pg,"plan"); await q.tab(pg,"acct")
        r2=await pg.evaluate('({amt:document.getElementById("f-amt").value,dis:document.getElementById("f-save").disabled})')
        if r2["amt"] and not r2["dis"]:
            await pg.click('#f-save'); await pg.wait_for_timeout(800)
        n_local=await pg.evaluate('expenses.filter(e=>e.note==="拉麵").length')
        await pg.evaluate('__goOnline()'); await ctx.set_offline(False); await pg.evaluate('dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(1500)
        n_srv=len([v for v in (await exps(pg)).values() if v.get("note")=="拉麵"])
        q.rec("離線（已快取）","→ 切分頁回來表單還留著同一筆，再按一次會重複記帳",n_srv==1,{"切回來時":r2,"本機筆數":n_local,"恢復連線後雲端筆數":n_srv})
        # 錢包：離線補錢
        await pg.evaluate('__goOffline()')
        await pg.click('.wchip'); await pg.wait_for_timeout(200)
        await pg.click('.ws [data-wallet-edit][data-mode="add"]'); await pg.fill('.ws .w-form input','10000'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(800)
        ws=await pg.evaluate('({form:!!document.querySelector(".ws .w-form"),hero:document.querySelector(".ws-hero").innerText.replace(/\\s+/g," ")})')
        await pg.screenshot(path=q.SHOTS+"offline_wallet_after_add.png")
        q.rec("離線（已快取）","離線「加進錢包」後表單應關閉（不然會再按一次 → 重複加錢）",not ws["form"],ws)
        if ws["form"]:
            await pg.fill('.ws .w-form input','10000'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(500)
        await pg.evaluate('__goOnline()'); await pg.wait_for_timeout(1000)
        cw=(await q.mock(pg,"/wallet/zhang")).get(f"{B}/wallet/zhang",{}).get("cashIn")
        q.note("離線（已快取）","使用者以為沒加成功又按一次後，雲端錢包總額（原 20000，只想 +10000）",cw)
        await pg.click('.ws .sm-x') if await pg.query_selector('.ws .sm-x') else None
        # 心情：離線送出
        await pg.evaluate('__goOffline()')
        await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(300)
        await pg.click('#mood .fbtn[data-score="4"]'); await pg.fill('#mood-note','犬山好好玩'); await pg.click('#mood-form .primary'); await pg.wait_for_timeout(800)
        mf=await pg.evaluate('({form:!!document.querySelector("#mood-form"),btn:document.querySelector("#mood-form [type=submit]")?.innerText})')
        await pg.screenshot(path=q.SHOTS+"offline_mood_after_submit.png")
        q.rec("離線（已快取）","離線送出心情後畫面應切到已送出（不是停在表單）",not mf["form"],mf)
        # 入住卡訂房資料：離線儲存
        await pg.evaluate('tab="plan";view="day";dayIdx=0;render()'); await pg.wait_for_timeout(300)
        if await pg.query_selector('[data-stay-edit]'):
            await pg.click('[data-stay-edit]'); await pg.wait_for_timeout(200)
            await pg.fill('[data-stay-form] input[data-sos-f="room"]','雙人房'); await pg.click('[data-stay-save]'); await pg.wait_for_timeout(800)
            se=await pg.evaluate('!!document.querySelector("[data-stay-form]")')
            q.rec("離線（已快取）","離線儲存訂房資料後表單應關閉",not se,"表單還開著" if se else "")
        await pg.evaluate('__goOnline()'); await pg.wait_for_timeout(800)
        await ctx.close()
        # 重開 App 時已離線（冷啟動，程式庫在快取）
        ctx=await q.mkctx(b,fs=FSO)
        pg=await q.page(ctx,q.jst(11,19,12,0),init=q.seed({f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2}})+'localStorage.setItem("mocknet","0");'); await pg.wait_for_timeout(1500)
        await q.tab(pg,"list"); s=await pg.evaluate(SYNC)
        await pg.screenshot(path=q.SHOTS+"offline_coldstart_list.png")
        q.rec("離線（已快取）","離線冷啟動：應顯示「目前離線，先記在這支手機上」",("離線" in s),s)
        await ctx.close()
        q.dump("offline")
        await b.close()
asyncio.run(main())
