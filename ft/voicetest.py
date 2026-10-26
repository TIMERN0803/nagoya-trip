# 求助：放大畫面的「播放日文」語音（用替身記錄唸了什麼）
import asyncio
import fulltest as ft
from playwright.async_api import async_playwright
STUB='''(()=>{window._said=[];window._cancel=0;const ss={getVoices:()=>window._voices||[{lang:"ja-JP",name:"Kyoko"},{lang:"en-US",name:"Sam"}],speak:u=>{window._said.push({t:u.text,lang:u.lang,rate:u.rate,voice:u.voice&&u.voice.name});setTimeout(()=>u.onend&&u.onend(),50)},cancel:()=>{window._cancel++}};Object.defineProperty(window,"speechSynthesis",{value:ss,configurable:true});window.SpeechSynthesisUtterance=function(t){this.text=t};})();'''
async def opensos(pg):
    if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
    await pg.click('[data-sos]');await pg.wait_for_timeout(300)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await ft.newpage(b,ft.twt(10,25,18,0),tz="Asia/Taipei");await pg.add_init_script(STUB);await pg.reload();await pg.wait_for_timeout(800)
        await opensos(pg)
        ft.rec("語音","列表提示可播放","可播放日文" in await pg.inner_text('.sos'))
        await pg.click('[data-sos-grp="stay"]');await pg.wait_for_timeout(200)
        await pg.click('.sos-ph button:nth-child(1)');await pg.wait_for_timeout(200)
        btn=await pg.query_selector('.sos-show [data-say]')
        ft.rec("語音","放大畫面有「播放日文」按鈕",btn and "播放日文" in await btn.inner_text())
        bb=await btn.bounding_box()
        ft.rec("語音","按鈕夠大（高 ≥ 48）",bb['height']>=48,bb)
        await btn.click();await pg.wait_for_timeout(20)
        st=await pg.evaluate('document.querySelector(".sos-show [data-say]").innerText')
        said=await pg.evaluate('window._said')
        ft.rec("語音","唸出日文句子，語言 ja-JP、用日文語音",said and said[-1]['t']=="荷物を預かってもらえますか？" and said[-1]['lang']=="ja-JP" and said[-1]['voice']=="Kyoko",said)
        ft.rec("語音","播放中顯示狀態","播放中" in st,st)
        await pg.wait_for_timeout(150)
        ft.rec("語音","播完變「再聽一次」","再聽一次" in await pg.evaluate('document.querySelector(".sos-show [data-say]").innerText'))
        ft.rec("語音","點播放不會關掉放大畫面",await pg.query_selector('.sos-show'))
        await pg.click('.sos-show [data-say]');await pg.wait_for_timeout(100)
        ft.rec("語音","可以重複播放",len(await pg.evaluate('window._said'))==2)
        c0=await pg.evaluate('window._cancel')
        await pg.click('.sos-show .sm-x');await pg.wait_for_timeout(150)  # 現在只有 × 才關閉
        ft.rec("語音","關閉放大畫面會停止播放",not await pg.query_selector('.sos-show') and await pg.evaluate('window._cancel')>c0)
        # 〇〇 唸成 ここ
        await pg.click('[data-sos-grp="go"]');await pg.wait_for_timeout(200)
        await pg.click('.sos-ph button:nth-child(2)');await pg.wait_for_timeout(200)
        big=await pg.inner_text('.sos-show .s-big')
        await pg.click('.sos-show [data-say]');await pg.wait_for_timeout(30)
        t=(await pg.evaluate('window._said'))[-1]['t']
        ft.rec("語音","〇〇 畫面照樣顯示、唸成「ここ」","〇〇" in big and "〇〇" not in t and t.startswith("ここへは"),[big,t])
        await pg.click('.sos-show .sm-x');await pg.wait_for_timeout(150)
        # 飯店地址
        await pg.click('[data-sos-tab="emg"]');await pg.wait_for_timeout(200)
        await pg.click('[data-sos-show="hotel"]');await pg.wait_for_timeout(200)
        await pg.click('.sos-show [data-say]');await pg.wait_for_timeout(30)
        t=(await pg.evaluate('window._said'))[-1]['t']
        ft.rec("語音","給司機看：唸住址（數字用讀音友善寫法）","この住所までお願いします" in t and "十三の十八" in t and "13-18" not in t,t)
        await pg.click('.sos-show .sm-x');await pg.wait_for_timeout(150)
        # 緊急句子
        await pg.click('.sos-ph button:nth-child(1)');await pg.wait_for_timeout(200)
        await pg.click('.sos-show [data-say]');await pg.wait_for_timeout(30)
        ft.rec("語音","緊急句子也能播放",(await pg.evaluate('window._said'))[-1]['t']=="救急車を呼んでください。")
        ft.rec("語音","沒有 JS 錯誤",not pg.errs,pg.errs[:2])
        await ft.close(pg)
        # 沒有日文語音的手機
        pg=await ft.newpage(b,ft.twt(10,25,18,0),tz="Asia/Taipei");await pg.add_init_script(STUB+'window._voices=[{lang:"en-US",name:"Sam"}];');await pg.reload();await pg.wait_for_timeout(800)
        await opensos(pg);await pg.click('.sos-ph button:nth-child(1)');await pg.wait_for_timeout(200)
        await pg.click('.sos-show [data-say]');await pg.wait_for_timeout(50)
        ft.rec("語音","沒有日文語音時提示下載、不亂唸","日文語音" in await pg.inner_text('.sos-show [data-say]') and await pg.evaluate('window._said.length')==0)
        await ft.close(pg)
        # 不支援語音的瀏覽器
        pg=await ft.newpage(b,ft.twt(10,25,18,0),tz="Asia/Taipei");await pg.add_init_script('Object.defineProperty(window,"speechSynthesis",{value:undefined,configurable:true});');await pg.reload();await pg.wait_for_timeout(800)
        await opensos(pg);await pg.click('.sos-ph button:nth-child(1)');await pg.wait_for_timeout(200)
        await pg.click('.sos-show [data-say]');await pg.wait_for_timeout(50)
        ft.rec("語音","瀏覽器不支援時顯示說明、不出錯","不支援" in await pg.inner_text('.sos-show [data-say]') and not pg.errs,pg.errs[:2])
        await ft.close(pg)
        await b.close()
asyncio.run(main())
