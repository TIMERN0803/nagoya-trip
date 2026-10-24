import asyncio
import fulltest as ft
from playwright.async_api import async_playwright
CASES=[("11/21 10:20",ft.jst(11,21,10,20),"現在","熱田神宮"),("11/18 13:20",ft.jst(11,18,13,20),"現在","吉卜力公園"),("11/18 18:45",ft.jst(11,18,18,45),"接下來 19:30","伏見屋"),
("11/19 08:20",ft.jst(11,19,8,20),"現在","コンパル"),("11/17 21:00",ft.jst(11,17,21,0),"現在","すゞ家"),("11/17 23:30",ft.jst(11,17,23,30),None,None),("11/10 出發前",ft.jst(11,10,12),None,None),("11/25 結束",ft.jst(11,25,12),None,None)]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,t,lbl,n in CASES:
            pg=await ft.newpage(b,t)
            if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
            v=await pg.evaluate('(()=>{const f=document.querySelector(".fab");return f.hidden?null:f.innerText.replace(/\\s+/g," ")})()')
            ok=(v is None) if lbl is None else (v and lbl in v and n in v)
            ft.rec("首頁浮動按鈕",name,ok,v)
            if v and name=="11/21 10:20":
                await pg.screenshot(path='/home/claude/build/fab_home.png')
                await pg.click('.fab');await pg.wait_for_timeout(900)
                info=await pg.evaluate('(()=>{const el=document.getElementById("it-1");const r=el.getBoundingClientRect();return {when:document.querySelector(".banner .when")?.textContent,top:Math.round(r.top),fab:document.querySelector(".fab").hidden}})()')
                ft.rec("首頁浮動按鈕","點了跳到當天的熱田神宮，按鈕在行程頁隱藏","11/21" in info['when'] and 0<info['top']<400 and info['fab'],info)
                await pg.screenshot(path='/home/claude/build/fab_jump.png')
                await pg.click('[data-home]');await pg.wait_for_timeout(400)
                ft.rec("首頁浮動按鈕","回首頁按鈕再出現",not await pg.evaluate('document.querySelector(".fab").hidden'))
            ft.rec("首頁浮動按鈕",name+" 沒有錯誤",not pg.errs,pg.errs[:2])
            await ft.close(pg)
        await b.close()
asyncio.run(main())
