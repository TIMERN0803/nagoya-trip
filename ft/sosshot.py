import asyncio,json,sys
import fulltest as ft
from playwright.async_api import async_playwright
import os
# 真實訂房資料只放本機 .sos-private.json（不進 git，repo 是公開的）；沒有就用假資料
_P='/home/claude/build/.sos-private.json'
SOS=json.load(open(_P,encoding='utf8')) if os.path.exists(_P) else {"order":"TEST-0000","via":"測試平台","guest":"TEST","room":"測試房型","pay":"測試付款","payNote":"測試提醒"}
DB=json.dumps({"trips/neko-test/settings/sos":SOS})
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(10,25,11,0),tz="Asia/Taipei",ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        if not await pg.query_selector('.g-home'):await pg.click('[data-home]');await pg.wait_for_timeout(400)
        await pg.screenshot(path='/home/claude/build/sos_0.png',clip={'x':0,'y':0,'width':390,'height':260})
        await pg.click('[data-sos]');await pg.wait_for_timeout(500)
        await pg.screenshot(path='/home/claude/build/sos_1.png')
        card=await pg.query_selector('.sos')
        for i,y in enumerate([620,1250]):
            await card.evaluate(f'e=>e.scrollTop={y}');await pg.wait_for_timeout(200)
            await pg.screenshot(path=f'/home/claude/build/sos_{i+2}.png')
        await card.evaluate('e=>e.scrollTop=0')
        await pg.click('[data-sos-show="hotel"]');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/sos_show.png')
        print(pg.errs);await b.close()
asyncio.run(main())
async def day1():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        pg=await ft.newpage(b,ft.twt(10,25,11,0),tz="Asia/Taipei",ctx=ctx,init=f'localStorage.setItem("mockdb",{json.dumps(DB)});')
        if not await pg.query_selector('.g-home'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
        await pg.click('[data-day="0"]') if await pg.query_selector('[data-day="0"]') else None
        await pg.wait_for_timeout(500)
        el=await pg.query_selector('.stay-ord')
        await el.scroll_into_view_if_needed();await pg.evaluate('scrollBy(0,-260)');await pg.wait_for_timeout(300)
        await pg.screenshot(path='/home/claude/build/stay_day1.png')
        print('day1',pg.errs);await b.close()
asyncio.run(day1())
