import asyncio
import fulltest as ft
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Tokyo")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.jst(11,22,10),ctx=ctx)
        await pg.click('[data-home]');await pg.wait_for_timeout(500);await pg.evaluate('scrollTo(0,0)')
        await pg.click('.da-main[data-go-item="seat2"]');await pg.wait_for_timeout(1000)  # 過期的待辦也會留在首頁，所以指定回程選位那一則
        info=await pg.evaluate('(()=>{const r=document.getElementById("c-seat2").closest(".chk-row").getBoundingClientRect();return{tab:document.querySelector("nav.tabs button[aria-selected=true]").dataset.tab,top:Math.round(r.top),ping:document.getElementById("c-seat2").closest(".chk-row").classList.contains("ping")}})()')
        ft.rec("跳轉待辦","首頁到期提醒點了跳到清單並停在回程選位",info['tab']=="list" and 60<info['top']<500 and info['ping'],info)
        await pg.wait_for_timeout(200);await pg.screenshot(path='/home/claude/build/go_item.png')
        pg2=await ft.newpage(b,ft.jst(11,10,10),ctx=ctx)
        await pg2.click('.hero .chip.coral');await pg2.wait_for_timeout(200)
        await pg2.evaluate('render(true)');await pg2.wait_for_timeout(800)
        ok=await pg2.evaluate('document.getElementById("c-seat1").closest(".chk-row").classList.contains("ping")')
        ft.rec("跳轉待辦","倒數卡下的期限標籤也能點過去",ok)
        ft.rec("跳轉待辦","沒有錯誤",not pg.errs and not pg2.errs,(pg.errs+pg2.errs)[:2])
        await b.close()
if __name__=="__main__":asyncio.run(main())
