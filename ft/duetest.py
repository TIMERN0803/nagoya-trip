import asyncio,datetime as dt,json
import fulltest as ft
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,t,tz,exp in [("11/14 10:00 台灣",ft.twt(11,14,10),"Asia/Taipei","還有 21 小時 5 分 到期"),("11/15 07:20 台灣",ft.twt(11,15,7,20),"Asia/Taipei","已過期限 15 分"),("11/20 19:00 日本",ft.jst(11,20,19),"Asia/Tokyo","還有 1 小時 到期"),("11/10 台灣（還很久）",ft.twt(11,10,10),"Asia/Taipei","")]:
            pg=await ft.newpage(b,t,tz)
            if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
            await pg.evaluate('scrollTo(0,0)')
            a=await pg.evaluate('document.getElementById("due-alerts")?.innerText.replace(/\\s+/g," ")||""')
            chip=await pg.evaluate('document.querySelector(".hero .foot")?.innerText.replace(/\\s+/g," ")||""')
            ft.rec("待辦到期",name,(exp in a) if exp else a=="",a+" ｜ 首頁小標："+chip)
            if name.startswith("11/14"):
                await pg.screenshot(path='/home/claude/build/due_home.png')
                await pg.click('[data-done-id]');await pg.wait_for_timeout(500)
                a2=await pg.evaluate('document.getElementById("due-alerts")?.innerText||""')
                ck=await pg.evaluate('JSON.parse(localStorage.getItem("mockdb")||"{}")["trips/neko-test/checks/seat1"]')
                ft.rec("待辦到期","首頁按「完成」→ 提醒消失、清單打勾並同步",a2=="" and ck and ck.get("done"),f"{a2!r} {ck}")
                await pg.click('nav.tabs button[data-tab="list"]');await pg.wait_for_timeout(400)
                checked=await pg.evaluate('document.getElementById("c-seat1").checked')
                title=await pg.evaluate('document.querySelector(".group h3").innerText')
                ft.rec("待辦到期","清單也顯示已完成、標題改為待辦清單",checked and "待辦清單" in title,title)
                await pg.click('[data-item-edit="seat2"]');await pg.wait_for_timeout(300)
                v=await pg.evaluate('[document.querySelector("[name=dued]").value,document.querySelector("[name=duet]").value]')
                ft.rec("待辦到期","編輯時帶入原本的日期時間",v==["2026-11-22","11:40"],v)
                await pg.screenshot(path='/home/claude/build/due_form.png')
                await pg.fill('[name=duet]','12:15');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
                d=await pg.evaluate('JSON.parse(localStorage.getItem("mockdb")||"{}")["trips/neko-test/items/seat2"]?.due')
                ft.rec("待辦到期","改時間後存成 11/22 12:15",d=="11/22 12:15",d)
                await pg.click('[data-item-new="prep"]');await pg.fill('.chk-form input[name=title]','換日圓');await pg.fill('[name=dued]','2026-11-16');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
                d2=await pg.evaluate('Object.values(JSON.parse(localStorage.getItem("mockdb")||"{}")).find(x=>x&&x.title==="換日圓")?.due')
                ft.rec("待辦到期","只選日期也能存",d2=="11/16",d2)
                ft.rec("待辦到期","沒有錯誤",not pg.errs,pg.errs[:2])
            await ft.close(pg)
        await b.close()
asyncio.run(main())
