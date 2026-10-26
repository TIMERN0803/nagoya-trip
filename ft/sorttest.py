# 待辦自訂排序測試
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-sort"
async def order(pg):return await pg.evaluate('[...document.querySelectorAll("[data-group-id=prep] [data-item-edit],[data-group-id=prep] [data-sort-id]")].map(x=>x.dataset.itemEdit||x.dataset.sortId)')
async def drag(pg,id,steps,to_id=None):
    await pg.evaluate(f'(()=>{{const r=document.querySelector(\'[data-sort-id="{id}"]\').closest(".group");scrollTo(0,r.getBoundingClientRect().top+scrollY-70)}})()');await pg.wait_for_timeout(200)
    h=await pg.query_selector(f'[data-sort-id="{id}"] .drag-h');bb=await h.bounding_box()
    rh=(await (await pg.query_selector(f'[data-sort-id="{id}"]')).bounding_box())['height']
    x,y=bb['x']+bb['width']/2,bb['y']+bb['height']/2
    dy=rh*steps
    if to_id:
        t=await (await pg.query_selector(f'[data-sort-id="{to_id}"]')).bounding_box();me=await (await pg.query_selector(f'[data-sort-id="{id}"]')).bounding_box()
        dy=(t['y']+8-me['y']) if t['y']<me['y'] else (t['y']+t['height']-8-(me['y']+me['height']))
    await pg.mouse.move(x,y);await pg.mouse.down()
    for k in range(1,11):await pg.mouse.move(x,y+dy*k/10)
    await pg.mouse.up();await pg.wait_for_timeout(500)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        a=await ft.newpage(b,ft.jst(11,10,20,0),tz="Asia/Taipei",me="zhang",code="neko-sort")
        s=await ft.newpage(b,ft.jst(11,10,20,0),tz="Asia/Taipei",me="star",code="neko-sort",ctx=a.ctx)
        for q in (a,s):await q.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await q.wait_for_timeout(500)
        o0=await order(a)
        ft.rec("O 排序","待辦有排序按鈕",await a.query_selector('[data-group-id=prep] [data-sort-toggle]'))
        ft.rec("O 排序","待辦頁籤不顯示要買的",not await a.query_selector('[data-group-id=buy]'))
        await a.click('[data-sort-toggle=prep]');await a.wait_for_timeout(300)
        ft.rec("O 排序","進入排序模式：每列左側有把手，沒有數字和箭頭",len(await a.query_selector_all('[data-group-id=prep] .drag-h'))==len(o0) and not await a.query_selector('.sort-n,[data-sort-up]') and await a.evaluate('(()=>{const r=document.querySelector(".sort-row");return r.querySelector(".drag-h").getBoundingClientRect().left<r.querySelector(".txt").getBoundingClientRect().left})()'))
        ft.rec("O 排序","排序模式沒有勾選框、不會誤觸打勾",not await a.query_selector('[data-group-id=prep] input[type=checkbox]'))
        # 把最後一項拖到第一個
        await drag(a,o0[-1],0,to_id=o0[0])
        o1=await order(a)
        ft.rec("O 排序","拖曳：最後一項拖到最上面",o1==[o0[-1]]+o0[:-1],o1)
        db=json.loads(await a.evaluate('localStorage.getItem("mockdb")'))
        ords=[db.get(f"{B}/items/{i}",{}).get("order") for i in o1]
        ft.rec("O 排序","新順序存進雲端",ords==list(range(1,len(o1)+1)),ords)
        await s.wait_for_timeout(500)
        ft.rec("O 排序","星星的手機也是新順序",await order(s)==o1,await order(s))
        # 往下拖一格
        await drag(a,o1[0],0,to_id=o1[1])
        o2=await order(a)
        ft.rec("O 排序","往下拖一格",o2==[o1[1],o1[0]]+o1[2:],o2)
        await drag(a,o1[0],0,to_id=o1[1])
        ft.rec("O 排序","再拖回第一個",await order(a)==o1,await order(a))
        # 拖一下但沒移動位置：不改順序
        await drag(a,o1[1],0.2)
        ft.rec("O 排序","拖一點點沒越過一半，順序不變",await order(a)==o1)
        # 完成
        await a.click('[data-sort-toggle=prep]');await a.wait_for_timeout(300)
        ft.rec("O 排序","按完成回到一般清單、可以打勾",await a.query_selector('[data-group-id=prep] input[type=checkbox]') and await order(a)==o1)
        # 重新整理後仍是新順序
        await a.reload();await a.wait_for_timeout(900);await a.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await a.wait_for_timeout(500)
        ft.rec("O 排序","重新整理後順序還在",await order(a)==o1,await order(a))
        # 新增一項會排在最後
        await a.click('[data-item-new="prep"]');await a.fill('.chk-form input[name=title]','排序測試');await a.click('.chk-form .primary');await a.wait_for_timeout(500)
        o3=await order(a)
        ft.rec("O 排序","新增的項目排在最後",len(o3)==len(o1)+1 and o3[:-1]==o1,o3)
        # 要買的排序
        for q in (a,s):await q.click('[data-list-tab="buy"]');await q.wait_for_timeout(300)
        ft.rec("O 排序","要買的也有排序按鈕",await a.query_selector('[data-group-id=buy] [data-sort-toggle]'))
        async def border():return await a.evaluate('[...document.querySelectorAll("[data-group-id=buy] [data-item-edit],[data-group-id=buy] [data-sort-id]")].map(x=>x.dataset.itemEdit||x.dataset.sortId)')
        b0=await border()
        await a.click('[data-sort-toggle=buy]');await a.wait_for_timeout(300)
        ft.rec("O 排序","要買的：排序模式顯示地點和品項","名鐵 Sun Road" in await a.inner_text('[data-group-id=buy]'))
        ft.rec("O 排序","同一時間只有一個清單在排序",not await a.query_selector('[data-group-id=prep].sorting'))
        await drag(a,b0[-1],0,to_id=b0[0])
        b1=await border()
        ft.rec("O 排序","要買的：最後一項拖到最上面",b1==[b0[-1]]+b0[:-1],b1)
        db=json.loads(await a.evaluate('localStorage.getItem("mockdb")'))
        ft.rec("O 排序","要買的：新順序存進雲端",[db.get(f"{B}/items/{i}",{}).get("order") for i in b1]==list(range(1,len(b1)+1)))
        await s.wait_for_timeout(500)
        ft.rec("O 排序","要買的：星星的手機也是新順序",await s.evaluate('[...document.querySelectorAll("[data-group-id=buy] [data-item-edit]")].map(x=>x.dataset.itemEdit)')==b1)
        await a.click('[data-sort-toggle=buy]');await a.wait_for_timeout(300)
        ft.rec("O 排序","要買的：按完成回到一般清單",await a.query_selector('[data-group-id=buy] input[type=checkbox]'))
        # 首頁待辦提醒照常
        errs=a.errs+s.errs
        ft.rec("O 排序","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
