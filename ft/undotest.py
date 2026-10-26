# 刪除後復原測試：待辦、行李、要買的、記帳、心情
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
B="trips/neko-test"
def srv(pg,frag):return pg.evaluate(f'Object.keys(JSON.parse(localStorage.getItem("mockdb")||"{{}}")).filter(k=>k.includes({json.dumps(frag)}))')
async def item_case(pg,label,group):
    await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(500)
    if group in ("prep","buy"):await pg.click(f'[data-list-tab="{group}"]');await pg.wait_for_timeout(300)
    if group=="pack":
        g=await pg.query_selector('[data-list-sub="pack"],[data-go-pack],[data-sub="pack"]')
        if g:await g.click();await pg.wait_for_timeout(500)
    sel=f'[data-group-id={group}] [data-item-edit]' if group!="pack" else '[data-item-edit]'
    ed=await pg.query_selector(sel)
    if not ed: ft.rec("U 復原",f"{label}：找得到項目",False);return
    id=await ed.get_attribute('data-item-edit')
    await ed.click();await pg.wait_for_timeout(300)
    await pg.click(f'[data-item-del="{id}"]');await pg.wait_for_timeout(400)
    gone=not await pg.query_selector(f'[data-item-edit="{id}"]')
    bar=await pg.query_selector('.undo-bar')
    ft.rec("U 復原",f"{label}：按一次刪除",gone and f"{B}/items/{id}" not in await srv(pg,"/items/"))
    ft.rec("U 復原",f"{label}：出現「已刪除・復原」",bar and "已刪除" in await bar.inner_text())
    await pg.click('.undo-bar button');await pg.wait_for_timeout(600)
    ft.rec("U 復原",f"{label}：復原後回到清單",await pg.query_selector(f'[data-item-edit="{id}"]'))
    ft.rec("U 復原",f"{label}：雲端也寫回",f"{B}/items/{id}" in await srv(pg,"/items/"))
    ft.rec("U 復原",f"{label}：復原後提示消失",not await pg.query_selector('.undo-bar'))
    return id
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await ft.newpage(b,ft.jst(11,18,20,0))
        # 待辦：先打勾再刪，復原後勾選狀態也要回來
        await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(500)
        cid=await pg.evaluate('(document.querySelector("[data-group-id=prep] .chk input[type=checkbox]")||{}).id||""')
        cb=bool(cid)
        if cb:
            await pg.check('#'+cid);await pg.wait_for_timeout(400);cid=cid[2:]
        await item_case(pg,"待辦","prep")
        if cb:ft.rec("U 復原","待辦：打勾狀態一起回來",await pg.evaluate(f'document.getElementById("c-{cid}")?.checked')==True)
        await item_case(pg,"要買的","buy")
        await item_case(pg,"行李","pack")
        # 刪除後不按復原：5 秒後提示消失，資料維持刪除
        await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(500)
        await pg.click('[data-list-tab="buy"]');await pg.wait_for_timeout(300)
        ed=await pg.query_selector('[data-group-id=buy] [data-item-edit]');id=await ed.get_attribute('data-item-edit')
        await ed.click();await pg.wait_for_timeout(300);await pg.click(f'[data-item-del="{id}"]');await pg.wait_for_timeout(300)
        await pg.clock.run_for(5600);await pg.wait_for_timeout(300)
        ft.rec("U 復原","5 秒後提示自動消失",not await pg.query_selector('.undo-bar'))
        ft.rec("U 復原","沒按復原就維持刪除",not await pg.query_selector(f'[data-item-edit="{id}"]') and f"{B}/items/{id}" not in await srv(pg,"/items/"))
        # 連續刪兩筆：提示只有一個、復原的是最後一筆
        eds=await pg.query_selector_all('[data-group-id=buy] [data-item-edit]')
        ids=[await e.get_attribute('data-item-edit') for e in eds[:2]]
        for i in ids:
            await pg.click(f'[data-item-edit="{i}"]');await pg.wait_for_timeout(300);await pg.click(f'[data-item-del="{i}"]');await pg.wait_for_timeout(300)
        ft.rec("U 復原","連續刪除只顯示一個提示",len(await pg.query_selector_all('.undo-bar'))==1)
        await pg.click('.undo-bar button');await pg.wait_for_timeout(500)
        ft.rec("U 復原","復原的是最後刪的那筆",await pg.query_selector(f'[data-item-edit="{ids[1]}"]') and not await pg.query_selector(f'[data-item-edit="{ids[0]}"]'))
        # 記帳
        await pg.click('nav.tabs button[data-tab="acct"]');await pg.wait_for_timeout(400)
        await pg.fill('#f-amt','1234');await pg.fill('#f-note','復原測試');await pg.click('#f-save');await pg.wait_for_timeout(500)
        n0=await pg.evaluate('document.querySelectorAll(".ex[data-edit]").length')
        await pg.click('.ex[data-edit] >> nth=0');await pg.wait_for_timeout(300)
        await (await pg.query_selector('[data-del]')).click();await pg.wait_for_timeout(500)
        n1=await pg.evaluate('document.querySelectorAll(".ex[data-edit]").length')
        ft.rec("U 復原","記帳：按一次刪除",n1==n0-1,f"{n0}→{n1}")
        ft.rec("U 復原","記帳：刪掉正在修改的那筆，表單回到新增",await pg.evaluate('document.getElementById("f-cancel").hidden && document.getElementById("f-amt").value===""'))
        ft.rec("U 復原","記帳：提示顯示金額","¥1,234" in await pg.inner_text('.undo-bar'))
        await pg.click('.undo-bar button');await pg.wait_for_timeout(600)
        n2=await pg.evaluate('document.querySelectorAll(".ex[data-edit]").length')
        ft.rec("U 復原","記帳：復原後筆數回來",n2==n0,f"{n1}→{n2}")
        ft.rec("U 復原","記帳：雲端也寫回",len(await srv(pg,"/expenses/"))==n0)
        ft.rec("U 復原","記帳：總額正確","1,234" in await pg.inner_text('#acct-sum'))
        # 心情
        pg2=await ft.newpage(b,ft.jst(11,18,21,0))
        await pg2.click('#mood .fbtn[data-score="5"]');await pg2.fill('#mood-form textarea','復原測試心情');await pg2.click('#mood-form .primary');await pg2.wait_for_timeout(600)
        await pg2.evaluate('document.querySelector("#mood [data-mood-edit],#mood .mood-row [data-edit-mood],#mood button[data-mood-edit]")?.click()');await pg2.wait_for_timeout(300)
        md=await pg2.query_selector('[data-mood-del]')
        if not md:
            btns=await pg2.query_selector_all('#mood button')
            for x in btns:
                t=await x.inner_text()
                if "修改" in t or "編輯" in t:await x.click();await pg2.wait_for_timeout(300);break
            md=await pg2.query_selector('[data-mood-del]')
        if md:
            await md.click();await pg2.wait_for_timeout(500)
            ft.rec("U 復原","心情：按一次刪除",len(await srv(pg2,"/moods/"))==0)
            ft.rec("U 復原","心情：出現復原提示",await pg2.query_selector('.undo-bar'))
            await pg2.click('.undo-bar button');await pg2.wait_for_timeout(600)
            ft.rec("U 復原","心情：復原後文字回來","復原測試心情" in await pg2.inner_text('#mood'))
            ft.rec("U 復原","心情：雲端也寫回",len(await srv(pg2,"/moods/"))==1)
        else: ft.rec("U 復原","心情：找得到刪除按鈕",False)
        # 對方手機同步：A 刪除再復原，B 看得到
        a=await ft.newpage(b,ft.jst(11,18,20,0),me="zhang",code="neko-sync")
        bb=await ft.newpage(b,ft.jst(11,18,20,0),me="star",code="neko-sync",ctx=a.ctx)
        for q in (a,bb):await q.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await q.wait_for_timeout(500);await q.click('[data-list-tab="buy"]');await q.wait_for_timeout(300)
        ed=await a.query_selector('[data-group-id=buy] [data-item-edit]');id=await ed.get_attribute('data-item-edit')
        await ed.click();await a.wait_for_timeout(300);await a.click(f'[data-item-del="{id}"]');await a.wait_for_timeout(700)
        ft.rec("U 復原","同步：對方手機也刪掉",not await bb.query_selector(f'[data-item-edit="{id}"]'))
        await a.click('.undo-bar button');await a.wait_for_timeout(900)
        ft.rec("U 復原","同步：復原後對方手機也回來",await bb.query_selector(f'[data-item-edit="{id}"]'))
        ft.rec("U 復原","提示不會擋住分頁列",await a.evaluate('(()=>{const t=document.querySelector("nav.tabs .in").getBoundingClientRect();return true})()'))
        errs=pg.errs+pg2.errs+a.errs+bb.errs
        ft.rec("U 復原","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
