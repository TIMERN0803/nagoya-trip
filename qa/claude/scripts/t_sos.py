# 求助面板、全螢幕「給司機看」、語音邊界、鍵盤彈出
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
# 語音替身：cancel() 會「非同步」觸發上一句的 onerror（瀏覽器實際行為）；可設定一開始 getVoices() 為空、之後才載入
STUB='''(()=>{window._said=[];window._cancel=0;let cur=null;const ss={getVoices:()=>window._voices!==undefined?window._voices:[{lang:"ja-JP",name:"Kyoko"}],
 speak:u=>{cur=u;window._said.push({t:u.text,lang:u.lang,rate:u.rate,voice:u.voice&&u.voice.name});setTimeout(()=>{if(cur===u){cur=null;u.onend&&u.onend()}},window._dur||2000)},
 cancel:()=>{window._cancel++;const c=cur;cur=null;if(c)setTimeout(()=>c.onerror&&c.onerror({error:"interrupted"}),5)},speaking:false};
 Object.defineProperty(window,"speechSynthesis",{value:ss,configurable:true});window.SpeechSynthesisUtterance=function(t){this.text=t};})();'''
async def open_sos(pg):
    await q.home(pg); await pg.click('[data-sos]'); await pg.wait_for_timeout(250)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,19,21,0),init=STUB.replace("(()=>","(()=>").replace("})();","})();") if False else "")
        await pg.add_init_script(STUB); await pg.reload(); await pg.wait_for_timeout(900)
        await open_sos(pg)
        tab0=await pg.evaluate('document.querySelector(".sos-tabs [aria-selected=true]").innerText')
        q.note("求助","打開求助預設分頁",tab0)
        # 求助按鈕在各頁是否都找得到
        where={}
        for t in ["plan","wx","move","acct","list"]:
            await pg.evaluate('document.querySelector(".sheet-modal")?.remove();sosSheet=null;document.body.style.overflow=""')
            await q.tab(pg,t); where[t]=await pg.evaluate('!!document.querySelector("[data-sos]")')
        await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); where["day"]=await pg.evaluate('!!document.querySelector("[data-sos]")')
        q.rec("求助","「求助」按鈕在每個分頁都找得到（迷路時不用先回首頁）",all(where.values()),where)
        await open_sos(pg)
        # 鍵盤 Escape
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)
        q.rec("求助","外接鍵盤按 Esc 可關閉求助面板",not await pg.query_selector('.sheet-modal .sos'))
        await pg.evaluate('document.querySelector(".sheet-modal")?.remove();sosSheet=null;document.body.style.overflow=""')
        await open_sos(pg)
        # 撥號連結
        await pg.click('[data-sos-tab="emg"]'); await pg.wait_for_timeout(200)
        tels=await pg.evaluate('[...document.querySelectorAll(".sos a[href^=tel]")].map(a=>a.getAttribute("href"))')
        import re
        bad=[t for t in tels if not re.fullmatch(r"tel:\+?\d+",t)]
        q.rec("求助","所有 tel: 連結格式正確（只有 + 與數字）",not bad and len(tels)>=7,tels)
        # 旅平險：輸入帶分機/空白的電話
        await pg.click('.sos [data-sos-edit]'); await pg.wait_for_timeout(200)
        await pg.fill('.sos [data-sos-f="ins"]','國泰產險'); await pg.fill('.sos [data-sos-f="insTel"]','+886-2-2755-1299 #3')
        # 鍵盤彈出：把 viewport 縮成 844-336
        await pg.set_viewport_size({"width":390,"height":508}); await pg.wait_for_timeout(200)
        vis=await pg.evaluate('(()=>{const b=document.querySelector(".sos [data-sos-save]");const r=b.getBoundingClientRect();const c=document.querySelector(".sos");return {top:Math.round(r.top),bottom:Math.round(r.bottom),vh:innerHeight,scrollable:c.scrollHeight>c.clientHeight}})()')
        await pg.screenshot(path=q.SHOTS+"sos_ins_keyboard.png")
        q.note("求助","鍵盤彈出（可視高度 508）時旅平險「儲存」位置",vis)
        await pg.set_viewport_size({"width":390,"height":844})
        await pg.click('.sos [data-sos-save]'); await pg.wait_for_timeout(300)
        tel=await pg.evaluate('[...document.querySelectorAll(".sos a[href^=tel]")].map(a=>a.getAttribute("href")).pop()')
        q.rec("求助","旅平險電話「+886-2-2755-1299 #3」轉成 tel: 時分機不應黏在主號後面",tel!="tel:+886227551299 3".replace(" ","") ,tel)
        srv=(await q.mock(pg,"/settings/sos")).get(f"{B}/settings/sos")
        q.rec("求助","旅平險儲存到雲端（同步）",srv and srv.get("ins")=="國泰產險",srv)
        # 全螢幕給司機看
        await pg.click('.sos [data-sos-show="hotel"]'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=q.SHOTS+"sos_hotel_show_portrait.png")
        # 不小心點到大字 → 關掉了嗎？
        await pg.click('.sos-show .s-big'); await pg.wait_for_timeout(150)
        closed=not await pg.query_selector('.sos-show')
        q.rec("求助","「給司機看」全螢幕：點到畫面文字（司機想指著看）不應直接關閉",not closed,"點文字就關閉" if closed else "")
        # 橫向
        await pg.set_viewport_size({"width":844,"height":390}); await pg.wait_for_timeout(200)
        await pg.click('.sos [data-sos-show="hotel"]'); await pg.wait_for_timeout(250)
        lay=await pg.evaluate('(()=>{const v=document.querySelector(".sos-show");const els=[...v.children].map(e=>{const r=e.getBoundingClientRect();return [e.className,Math.round(r.top),Math.round(r.bottom)]});return {sh:v.scrollHeight,ch:v.clientHeight,els}})()')
        await pg.screenshot(path=q.SHOTS+"sos_hotel_show_landscape.png")
        hidden=[e for e in lay["els"] if e[1]<0 or e[2]>390]
        q.rec("求助","橫向（844×390）「給司機看」內容完整可見或可捲動",not hidden or lay["sh"]>lay["ch"],lay)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
        esc_closed=not await pg.query_selector('.sos-show')
        q.rec("求助","外接鍵盤 Esc 可關閉全螢幕",esc_closed)
        await pg.evaluate('document.querySelector(".sos-show")?.remove()')
        await pg.set_viewport_size({"width":320,"height":568}); await pg.wait_for_timeout(200)
        await pg.click('.sos [data-sos-show="hotel"]'); await pg.wait_for_timeout(250)
        lay2=await pg.evaluate('(()=>{const v=document.querySelector(".sos-show");return [...v.children].map(e=>{const r=e.getBoundingClientRect();return [e.className,Math.round(r.top),Math.round(r.bottom),Math.round(r.right)]})})()')
        await pg.screenshot(path=q.SHOTS+"sos_hotel_show_320.png")
        q.rec("求助","320×568（iPhone SE 1）「給司機看」內容不超出畫面",all(e[1]>=0 and e[2]<=568 and e[3]<=320 for e in lay2),lay2)
        await pg.evaluate('document.querySelector(".sos-show")?.remove()')
        await pg.set_viewport_size({"width":390,"height":844})
        # 語音邊界
        await pg.click('[data-sos-tab="talk"]'); await pg.wait_for_timeout(200)
        await pg.click('.sos-ph button >> nth=0'); await pg.wait_for_timeout(150)
        for i in range(10): await pg.evaluate('document.querySelector(".sos-show [data-say]").click()')
        await pg.wait_for_timeout(50)
        lab=await pg.inner_text('.sos-show [data-say]'); n=len(await pg.evaluate('window._said'))
        q.rec("語音","連點播放 10 次後按鈕應顯示「播放中…」（cancel 觸發的 onerror 不應蓋掉狀態）","播放中" in lab,{"按鈕文字":lab,"speak 次數":n})
        await pg.wait_for_timeout(2200)
        lab2=await pg.inner_text('.sos-show [data-say]')
        q.note("語音","最後一次播完的文字",lab2)
        await pg.evaluate('document.querySelector(".sos-show .sm-x").click()')
        # 播放中切到另一句
        await pg.click('.sos-ph button >> nth=1'); await pg.wait_for_timeout(100)
        await pg.click('.sos-show [data-say]'); c0=await pg.evaluate('window._cancel')
        await pg.click('.sos-show .sm-x'); await pg.wait_for_timeout(50)
        await pg.click('.sos-ph button >> nth=2'); await pg.wait_for_timeout(100)
        c1=await pg.evaluate('window._cancel')
        q.rec("語音","播放中關閉→點另一句：上一句被停止",c1>c0,[c0,c1])
        await pg.evaluate('document.querySelector(".sos-show")?.remove()')
        # getVoices 先空，按播放後才載入（iOS 常見）
        await pg.evaluate('window._voices=[]')
        await pg.click('.sos-ph button >> nth=3'); await pg.wait_for_timeout(100)
        await pg.click('.sos-show [data-say]'); await pg.wait_for_timeout(50)
        said=(await pg.evaluate('window._said'))[-1]
        q.rec("語音","getVoices() 空陣列時仍以 ja-JP 播放",said["lang"]=="ja-JP",said)
        await pg.evaluate('document.querySelector(".sos-show")?.remove()')
        await pg.evaluate('window._voices=[{lang:"en-US",name:"Samantha"},{lang:"zh-TW",name:"Meijia"}]')
        await pg.click('.sos-ph button >> nth=3'); await pg.wait_for_timeout(100)
        await pg.click('.sos-show [data-say]'); await pg.wait_for_timeout(50)
        lab3=await pg.inner_text('.sos-show [data-say]')
        q.rec("語音","沒有日文語音時按鈕改顯示說明","沒有日文語音" in lab3,lab3)
        await pg.screenshot(path=q.SHOTS+"voice_no_ja.png")
        await pg.evaluate('document.querySelector(".sos-show")?.remove()')
        # 'ja_JP' 格式（Android 某些版本）
        await pg.evaluate('window._voices=[{lang:"ja_JP",name:"Google 日本語"}]')
        await pg.click('.sos-ph button >> nth=3'); await pg.wait_for_timeout(100)
        await pg.click('.sos-show [data-say]'); await pg.wait_for_timeout(50)
        said=(await pg.evaluate('window._said'))[-1]
        q.rec("語音","Android 'ja_JP' 格式語音也能被選到",said.get("voice")=="Google 日本語",said)
        await pg.evaluate('document.querySelector(".sos-show")?.remove()')
        # 求助打開時關閉 → 預設停在日常日文
        await pg.click('.sos [data-sos-tab="emg"]'); await pg.click('.sos .sm-head .sm-x'); await pg.wait_for_timeout(100)
        await pg.click('[data-sos]'); await pg.wait_for_timeout(200)
        t=await pg.evaluate('document.querySelector(".sos-tabs [aria-selected=true]").innerText')
        q.note("求助","在「緊急求助」關掉後再打開，停在",t)
        # 情境篩選記憶
        await pg.click('[data-sos-grp="eat"]'); await pg.click('.sos .sm-head .sm-x'); await pg.click('[data-sos]'); await pg.wait_for_timeout(200)
        g=await pg.evaluate('document.querySelector(".sos-grps [aria-pressed=true]").innerText')
        q.note("求助","上次選「餐廳」關掉再打開，情境篩選停在",g)
        # a11y：tablist 鍵盤
        roles=await pg.evaluate('({sheet:document.querySelector(".sheet-modal").getAttribute("aria-modal"),focusIn:document.querySelector(".sheet-modal").contains(document.activeElement),active:document.activeElement.tagName+"."+document.activeElement.className})')
        q.rec("無障礙","求助面板打開後焦點移入面板（螢幕閱讀器／鍵盤）",roles["focusIn"],roles)
        q.dump("sos")
        await b.close()
asyncio.run(main())
