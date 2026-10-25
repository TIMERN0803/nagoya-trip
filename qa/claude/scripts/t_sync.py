# 雙機同步（同一個 browser context 裡兩個 page，共用假資料庫；身分 ngy:me 也共用，見報告說明）
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
META={f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2}}
async def two(b,t,db):
    ctx=await q.mkctx(b)
    a=await q.page(ctx,t,init=q.seed(db)); s=await q.page(ctx,t)
    await a.wait_for_timeout(600); return ctx,a,s
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # 1. 兩人同時改同一筆帳
        db={**META,f"{B}/expenses/e1":{"amt":3000,"cat":"food","who":"zhang","split":"both","pay":"cash","day":"11/19","note":"午餐","ts":1}}
        ctx,a,s=await two(b,q.jst(11,19,20,0),db)
        for x in (a,s): await q.tab(x,"acct")
        await a.click('.ex[data-edit="e1"]'); await s.click('.ex[data-edit="e1"]'); await a.wait_for_timeout(200)
        await a.fill('#f-amt','3200'); await a.click('#f-save'); await a.wait_for_timeout(500)
        sv=await s.input_value('#f-amt')
        await s.fill('#f-note','午餐（含飲料）'); await s.click('#f-save'); await s.wait_for_timeout(500)
        e=(await q.mock(a,"/expenses/e1"))[f"{B}/expenses/e1"]
        q.rec("同步衝突","A 改金額 3000→3200、B（表單開著）只改備註 → 雲端金額應保留 3200",e["amt"]==3200,{"B 表單裡的金額":sv,"雲端":{k:e[k] for k in ("amt","note")}})
        await ctx.close()
        # 2. A 刪除帳 → B 正在修改同一筆 → B 按更新
        ctx,a,s=await two(b,q.jst(11,19,20,0),db)
        for x in (a,s): await q.tab(x,"acct")
        await s.click('.ex[data-edit="e1"]'); await s.wait_for_timeout(200)
        await a.click('[data-del="e1"]'); await a.wait_for_timeout(5800)
        st=await s.evaluate('({editing:editingId,rows:document.querySelectorAll(".ex[data-edit]").length,btn:document.getElementById("f-save").innerText})')
        await s.fill('#f-amt','3100'); await s.click('#f-save'); await s.wait_for_timeout(500)
        alive=f"{B}/expenses/e1" in await q.mock(a,"/expenses/")
        q.note("同步衝突","A 刪除一筆帳（5 秒後確定），B 正在修改同一筆 → B 按「更新這筆」",{"B 當時畫面":st,"雲端是否又出現 e1":alive})
        await ctx.close()
        # 3. 復原時對方已修改／已刪除
        db2={**META,f"{B}/items/i1":{"group":"buy","title":"小倉山莊","note":"","due":"","order":1}}
        ctx,a,s=await two(b,q.jst(11,19,20,0),db2)
        for x in (a,s): await q.tab(x,"list")
        await a.click('[data-item-edit="i1"]'); await a.wait_for_timeout(200); await a.click('[data-item-del="i1"]'); await a.wait_for_timeout(400)
        # 對方在 5 秒內新增一筆同名（以為被刪了）
        await s.click('[data-item-new="buy"]'); await s.fill('.chk-form input[name=title]','小倉山莊'); await s.click('.chk-form .primary'); await s.wait_for_timeout(300)
        await a.click('.undo-bar button'); await a.wait_for_timeout(600)
        n=len([v for v in (await q.mock(a,"/items/")).values() if v.get("title")=="小倉山莊"])
        q.note("同步衝突","A 刪除→B 以為不見又新增同名→A 按復原：雲端同名項目數",n)
        await ctx.close()
        # 4. 排序中另一支手機新增／改名
        P=[(f"p{i}",f"待辦{i}") for i in range(1,6)]
        db3={**META,**{f"{B}/items/{i}":{"group":"prep","title":t,"note":"","due":"","order":k+1} for k,(i,t) in enumerate(P)}}
        ctx,a,s=await two(b,q.jst(11,10,20,0),db3)
        for x in (a,s): await q.tab(x,"list")
        await a.click('[data-sort-toggle=prep]'); await a.wait_for_timeout(300)
        await s.click('[data-item-new="prep"]'); await s.fill('.chk-form input[name=title]','星星新增'); await s.click('.chk-form .primary'); await s.wait_for_timeout(500)
        rows_a=await a.evaluate('[...document.querySelectorAll("[data-sort-id]")].map(x=>x.dataset.sortId)')
        await s.click('[data-item-edit="p5"]'); await s.fill('.chk-form input[name=title]','待辦5（改名）'); await s.click('.chk-form .primary'); await s.wait_for_timeout(500)
        # A 把 p5 拖到最上
        await a.evaluate('applyOrder("prep",["p5","p1","p2","p3","p4",...itemsOf("prep").map(x=>x.id).filter(i=>!/^p[1-5]$/.test(i))],true)'); await a.wait_for_timeout(600)
        srv=await q.mock(a,"/items/")
        t5=srv.get(f"{B}/items/p5",{}).get("title"); new=[v for v in srv.values() if v.get("title")=="星星新增"]
        q.rec("同步衝突","排序模式中對方新增：新項目出現在排序清單",any(r not in [i for i,_ in P] for r in rows_a),rows_a)
        q.rec("同步衝突","排序寫入不覆蓋對方剛改的名稱",t5=="待辦5（改名）",t5)
        q.rec("同步衝突","排序後對方新增的項目還在",len(new)==1,len(new))
        await ctx.close()
        # 5. 勾選同步、心情同一天兩人
        ctx,a,s=await two(b,q.jst(11,19,21,0),{**META,f"{B}/items/i1":{"group":"buy","title":"ういろう","note":"","due":"","order":1}})
        for x in (a,s): await q.tab(x,"list")
        await a.check('#c-i1'); await s.wait_for_timeout(500)
        q.rec("同步","A 勾選，B 畫面跟著勾",await s.evaluate('document.getElementById("c-i1").checked'))
        await ctx.close()
        # 6. 首頁「完成」到期提醒 vs 對方取消勾選
        q.dump("sync")
        await b.close()
asyncio.run(main())
