# 產生 iOS 啟動圖：用 App 裡同一份開啟畫面（豆花和芝麻），各種 iPhone 尺寸各一張
import asyncio, re, os, sys
from playwright.async_api import async_playwright
ROOT="/home/claude/nagoya-trip"; OUT=os.path.join(ROOT,"splash")
DEV=[(440,956,3),(420,912,3),(402,874,3),(430,932,3),(393,852,3),(428,926,3),(390,844,3),(375,812,3),(414,896,3),(414,896,2),(375,667,2)]
s=open(os.path.join(ROOT,"index.html"),encoding="utf-8").read()
css=re.search(r"<style>\s*/\* ===== 開啟動畫.*?</style>",s,re.S).group(0)
div=re.search(r'<div id="splash".*?</svg>\s*</div></div>',s,re.S).group(0)
html=f'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">{css}<style>html,body{{margin:0;background:#F8F3EC}}#splash .sp-a,#splash .sp-b{{animation:none!important}}</style></head><body>{div}</body></html>'
async def main():
    os.makedirs(OUT,exist_ok=True)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for w,h,d in DEV:
            pg=await b.new_page(viewport={"width":w,"height":h},device_scale_factor=d)
            await pg.set_content(html); await pg.wait_for_timeout(100)
            await pg.screenshot(path=os.path.join(OUT,f"{w}x{h}@{d}.png")); await pg.close()
        await b.close()
    tags="\n".join(f'<link rel="apple-touch-startup-image" media="(device-width: {w}px) and (device-height: {h}px) and (-webkit-device-pixel-ratio: {d}) and (orientation: portrait)" href="splash/{w}x{h}@{d}.png">' for w,h,d in DEV)
    print(tags)
asyncio.run(main())
