# 所有彈出面板（錢包、行事曆、出發前設定、求助）與行李頁：標題固定、面板不超出畫面
import asyncio
import fulltest as ft
from playwright.async_api import async_playwright
SHEETS=[("錢包","openWallet()"),("行事曆","openCalSheet()"),("出發前設定","openSetup()"),("求助","openSos()")]
SIZES=[("直向 390×844",390,844),("小螢幕 375×667",375,667),("橫向 844×390",844,390)]
M='''(()=>{const c=document.querySelector(".sheet-modal .sm-card");const h=c.querySelector(":scope>.sm-head,:scope>.sos-top");const x=c.querySelector(".sm-x").getBoundingClientRect();const hit=document.elementFromPoint(x.x+x.width/2,x.y+x.height/2);const r=c.getBoundingClientRect();return {top:Math.round(r.top),bot:Math.round(r.bottom),sh:c.scrollHeight,ch:c.clientHeight,st:c.scrollTop,head:Math.round(h.getBoundingClientRect().top),shade:h.classList.contains("shade"),xhit:!!(hit&&hit.closest(".sm-x")),vh:innerHeight}})()'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for sz,w,h in SIZES:
            for nm,fn in SHEETS:
                pg=await ft.newpage(b,ft.twt(10,25,18,0),tz="Asia/Taipei");await pg.set_viewport_size({'width':w,'height':h})
                if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
                await pg.evaluate(fn);await pg.wait_for_timeout(650)  # 面板滑上 0.5 秒（最後輕輕彈一下），停穩再量
                a=await pg.evaluate(M)
                ft.rec("面板",f"{sz} {nm}：面板完整在畫面內",a['top']>=0 and a['bot']<=a['vh']+1,a)
                await pg.evaluate('(()=>{const c=document.querySelector(".sheet-modal .sm-card");c.scrollTop=99999;c.dispatchEvent(new Event("scroll"))})()');await pg.wait_for_timeout(250)
                z=await pg.evaluate(M)
                ft.rec("面板",f"{sz} {nm}：內容放不下時可以捲到底",a['sh']<=a['ch']+1 or z['st']+z['ch']>=z['sh']-2,[a['sh'],a['ch'],z['st']])
                ft.rec("面板",f"{sz} {nm}：捲動後標題不動、關閉鈕點得到",z['head']==a['head'] and z['xhit'],[a['head'],z['head'],z['xhit']])
                if a['sh']>a['ch']+20:ft.rec("面板",f"{sz} {nm}：捲動後標題下緣有陰影",z['shade'] and not a['shade'])
                ft.rec("面板",f"{sz} {nm}：沒有 JS 錯誤",not pg.errs,pg.errs[:2])
                await ft.close(pg)
        # 出發前設定：直向捲到底，標題仍在
        pg=await ft.newpage(b,ft.twt(10,25,18,0),tz="Asia/Taipei")
        if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
        await pg.click('[data-setup-open]');await pg.wait_for_timeout(400)
        await pg.evaluate('document.querySelector(".su-sheet").scrollTop=99999');await pg.wait_for_timeout(250)
        t=await pg.evaluate('(()=>{const h=document.querySelector(".su-sheet>.sm-head");const r=h.getBoundingClientRect();return {txt:h.innerText,top:Math.round(r.top),vis:r.bottom>0}})()')
        ft.rec("面板","出發前設定捲到底仍看得到標題",t['vis'] and "出發前手機設定" in t['txt'],t)
        await pg.screenshot(path='/home/claude/build/setup_sticky.png')
        await pg.click('.su-sheet .sm-x');await pg.wait_for_timeout(350)
        ft.rec("面板","捲動後點關閉可以關掉",not await pg.query_selector('.sheet-modal'))
        await ft.close(pg)
        # 行李頁標題列
        pg=await ft.newpage(b,ft.twt(10,25,18,0),tz="Asia/Taipei")
        await pg.click('nav.tabs button[data-tab="list"]');await pg.wait_for_timeout(300)
        await pg.click('[data-pack-open]');await pg.wait_for_timeout(400)
        a=await pg.evaluate('(()=>{const b=document.querySelector(".pk-bar");return {top:Math.round(b.getBoundingClientRect().top),shade:b.classList.contains("shade"),pos:getComputedStyle(b).position}})()')
        await pg.evaluate('scrollTo(0,1500)');await pg.wait_for_timeout(250)
        z=await pg.evaluate('(()=>{const b=document.querySelector(".pk-bar"),k=b.querySelector(".back").getBoundingClientRect(),e=document.elementFromPoint(k.x+k.width/2,k.y+k.height/2);return {top:Math.round(b.getBoundingClientRect().top),shade:b.classList.contains("shade"),hit:!!(e&&e.closest("[data-pack-close]")),y:scrollY,bg:getComputedStyle(b).backgroundColor}})()')
        ft.rec("行李頁","往下捲時標題列固定在最上方",a['pos']=="sticky" and z['y']>1000 and z['top']<=1,[a,z])
        ft.rec("行李頁","返回鈕點得到、有不透明底色",z['hit'] and z['bg']!="rgba(0, 0, 0, 0)",z)
        ft.rec("行李頁","捲動後出現陰影",z['shade'] and not a['shade'])
        await pg.screenshot(path='/home/claude/build/pack_sticky.png')
        await pg.click('.pk-bar [data-pack-close]');await pg.wait_for_timeout(700)  # 返回轉場 0.54 秒後舊頁才移除
        ft.rec("行李頁","捲動中點返回回到清單",not await pg.query_selector('.pk-bar') and await pg.query_selector('[data-pack-open]'))
        ft.rec("行李頁","沒有 JS 錯誤",not pg.errs,pg.errs[:2])
        await ft.close(pg)
        await b.close()
asyncio.run(main())
