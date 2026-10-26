# 首頁「回家」浮動按鈕＋下午插圖
# 回家：當天行程都結束（最後有時間的行程已過 90 分，或 22:00 後沒有進行中／接下來的行程）→ 按鈕變「回家」，點了用 Google 地圖導航到飯店
# 最後一天（11/24 搭機回台灣）不顯示回家
import asyncio,urllib.parse as up
import fulltest as ft
from playwright.async_api import async_playwright
OUT='/home/claude/build/'
HOTEL_PID="ChIJ74aBvtd2A2AR8TRTA-QLXZM"
FAB='(()=>{const f=document.querySelector(".fab");return f.hidden?null:{t:f.innerText.replace(/\\s+/g," "),home:f.classList.contains("home"),mode:f.dataset.mode,aria:f.getAttribute("aria-label")}})()'
CASES=[
 # (名稱, 時間, 預期: None=隱藏 / "home" / 其他=一般按鈕要包含的字)
 ("11/17 21:00 晚餐進行中",ft.jst(11,17,21,0),"すゞ家"),
 ("11/17 22:30 最後的晚餐已過 90 分",ft.jst(11,17,22,30),"home"),
 ("11/17 23:50 深夜",ft.jst(11,17,23,50),"home"),
 ("11/18 00:30 隔天凌晨，回到下一天的第一項",ft.jst(11,18,0,30),"名古屋車站"),
 ("11/18 21:10 燒肉 19:30 已過 90 分",ft.jst(11,18,21,10),"home"),
 ("11/18 20:30 燒肉還在進行中",ft.jst(11,18,20,30),"伏見屋"),
 ("11/21 21:00 還有彈性行程，22 點前不算結束",ft.jst(11,21,21,0),"現在"),
 ("11/21 22:10 22 點後只剩彈性行程",ft.jst(11,21,22,10),"home"),
 ("11/20 21:00 20:00 提醒還在 90 分內",ft.jst(11,20,21,0),"現在"),
 ("11/20 21:40 20:00 提醒已過，但 22 點前還有彈性行程",ft.jst(11,20,21,40),"現在"),
 ("11/20 22:00 22 點後只剩彈性行程",ft.jst(11,20,22,0),"home"),
 ("11/24 15:00 最後一天搭機後不顯示回家",ft.jst(11,24,15,0),None),
 ("11/24 23:00 最後一天深夜也不顯示",ft.jst(11,24,23,0),None),
 ("11/10 出發前",ft.jst(11,10,22,30),None),
 ("11/25 結束後",ft.jst(11,25,22,30),None),
]
SCENES=[(5,"morning"),(10,"morning"),(11,"noon"),(13,"noon"),(14,"afternoon"),(16,"afternoon"),(17,"dinner"),(19,"dinner"),(20,"dinner"),(21,"night"),(23,"night"),(2,"night"),(4,"night")]
async def home(pg):
    if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,t,exp in CASES:
            pg=await ft.newpage(b,t);await pg.wait_for_timeout(300);await home(pg)
            v=await pg.evaluate(FAB)
            if exp is None:ok=v is None
            elif exp=="home":ok=bool(v) and v['home'] and v['mode']=="home" and "回家" in v['t'] and "今天行程結束" in v['t']
            else:ok=bool(v) and not v['home'] and exp in v['t']
            ft.rec("回家按鈕",name,ok,v);ft.rec("回家按鈕",name+"：沒有 JS 錯誤",not pg.errs,pg.errs[:2])
            await ft.close(pg)
        # 點擊：開 Google 地圖導航到飯店（大眾運輸），不切換頁面
        pg=await ft.newpage(b,ft.jst(11,17,22,30));await pg.wait_for_timeout(300);await home(pg)
        await pg.evaluate('(()=>{window._op=[];window.open=(u,n,f)=>{window._op.push([u,n,f]);return null}})()')
        await pg.screenshot(path=OUT+'home_fab.png')
        await pg.click('.fab');await pg.wait_for_timeout(400)
        op=await pg.evaluate('window._op');st=await pg.evaluate('({hash:location.hash,home:!!document.querySelector(".g-home,.hero"),fab:!document.querySelector(".fab").hidden})')
        u=op[0][0] if op else "";q=dict(up.parse_qsl(up.urlsplit(u).query))
        ft.rec("回家按鈕","點了只開一次地圖",len(op)==1,op)
        ft.rec("回家按鈕","目的地是飯店 Place ID",q.get("destination_place_id")==HOTEL_PID and "ランプライト" in q.get("destination",""),q)
        ft.rec("回家按鈕","大眾運輸模式、沒有寫死出發地（用目前位置）",q.get("travelmode")=="transit" and "origin" not in q,q)
        ft.rec("回家按鈕","以新分頁開啟（noopener）",op and op[0][1]=="_blank" and "noopener" in (op[0][2] or ""),op)
        ft.rec("回家按鈕","點完還在首頁、按鈕還在",st['home'] and st['fab'],st)
        # 外觀：焦糖棕字（不是綠色）、房子圖示、可讀名稱
        sty=await pg.evaluate('(()=>{const f=document.querySelector(".fab");return {c:getComputedStyle(f.querySelector("small")).color,hs:!!f.querySelector(".hs"),go:!!f.querySelector(".go"),w:f.getBoundingClientRect().width,r:f.getBoundingClientRect().right,a:f.getAttribute("aria-label")}})()')
        ft.rec("回家按鈕","小字是焦糖棕 #946645",sty['c']=="rgb(148, 102, 69)",sty)
        ft.rec("回家按鈕","有房子圖示和箭頭",sty['hs'] and sty['go'],sty)
        ft.rec("回家按鈕","按鈕在畫面內",sty['r']<=390 and sty['w']<=240,sty)
        ft.rec("回家按鈕","讀屏標籤說明會導航回飯店","飯店" in (sty['a'] or ""),sty)
        await ft.close(pg)
        # 時間往前走：22:00 前後按鈕會自動換（每 30 秒重畫）
        pg=await ft.newpage(b,ft.jst(11,17,21,58));await pg.wait_for_timeout(300);await home(pg)
        a=await pg.evaluate(FAB)
        await pg.clock.fast_forward("03:30");await pg.wait_for_timeout(600)
        c=await pg.evaluate(FAB)
        ft.rec("回家按鈕","21:58 是一般按鈕，過了 22:00 自動變回家",a and not a['home'] and c and c['home'],[a,c])
        # 回家後又切到一般按鈕（隔天）：點擊恢復跳行程
        await pg.clock.fast_forward("03:00:00");await pg.wait_for_timeout(600)
        await home(pg);await pg.evaluate('(()=>{window._op=[];window.open=(u)=>{window._op.push(u);return null}})()')
        d=await pg.evaluate(FAB)
        if d and not d['home']:
            await pg.click('.fab');await pg.wait_for_timeout(700)
            r=await pg.evaluate('({op:window._op.length,day:!!document.querySelector(".banner .when"),when:document.querySelector(".banner .when")?.textContent})')
        else:r=None
        ft.rec("回家按鈕","隔天變回一般按鈕，點了跳行程不開地圖",bool(r) and r['op']==0 and r['day'] and "11/18" in (r['when'] or ""),[d,r])
        await ft.close(pg)
        # 行程頁、其他分頁不顯示
        pg=await ft.newpage(b,ft.jst(11,17,22,30));await pg.wait_for_timeout(300);await home(pg)
        await pg.click('nav.tabs button[data-tab="list"]');await pg.wait_for_timeout(400)
        ft.rec("回家按鈕","切到清單分頁時隱藏",await pg.evaluate('document.querySelector(".fab").hidden'))
        await ft.close(pg)
        # 下午插圖：時段切換
        for h,exp in SCENES:
            pg=await ft.newpage(b,ft.jst(11,10,h,20));await pg.wait_for_timeout(200);await home(pg)
            v=await pg.evaluate('document.querySelector(".hero .scene")?.dataset.period')
            ft.rec("首頁插圖",f"{h}:20 是 {exp}",v==exp,v);await ft.close(pg)
        pg=await ft.newpage(b,ft.jst(11,19,15,0));await pg.wait_for_timeout(300);await home(pg)
        info=await pg.evaluate('''(()=>{const s=document.querySelector(".hero .scene");return {p:s.dataset.period,sky:!!s.querySelector('[fill="url(#gAft)"]'),grad:!!document.getElementById("gAft"),cats:s.querySelectorAll(".hero-cats .cat-a,.hero-cats .cat-b").length,hop:!!s.querySelector("[data-hop]")}})()''')
        ft.rec("首頁插圖","旅途中 15:00 也是下午，有午後天空與兩隻貓",info['p']=="afternoon" and info['sky'] and info['grad'] and info['cats']==2 and info['hop'],info)
        await pg.screenshot(path=OUT+'hero_pm.png')
        await pg.evaluate('scrollTo(0,0)');await pg.wait_for_timeout(100);await pg.click('.hero-cats .cat-b',force=True);await pg.wait_for_timeout(100)
        ft.rec("首頁插圖","下午的貓點一下會跳",await pg.evaluate('document.querySelector(".hero-cats").classList.contains("hop")'))
        ft.rec("首頁插圖","沒有 JS 錯誤",not pg.errs,pg.errs[:2])
        await ft.close(pg)
        # 16:59 → 17:00 自動從下午換到晚上
        pg=await ft.newpage(b,ft.jst(11,10,16,59));await pg.wait_for_timeout(300);await home(pg)
        a=await pg.evaluate('document.querySelector(".hero .scene").dataset.period')
        await pg.clock.fast_forward("01:30");await pg.wait_for_timeout(600)
        c=await pg.evaluate('document.querySelector(".hero .scene").dataset.period')
        ft.rec("首頁插圖","16:59 下午，過 17:00 自動換晚餐",a=="afternoon" and c=="dinner",[a,c])
        await ft.close(pg)
        # 晚餐插圖：外觀、會跳、20:00 換成睡覺
        pg=await ft.newpage(b,ft.jst(11,19,18,30));await pg.wait_for_timeout(300);await home(pg)
        info=await pg.evaluate('''(()=>{const s=document.querySelector(".hero .scene");return {p:s.dataset.period,sky:!!s.querySelector('[fill="url(#gDusk)"]'),grad:!!document.getElementById("gDusk"),cats:s.querySelectorAll(".hero-cats .cat-a,.hero-cats .cat-b").length,lantern:!!s.querySelector(".lantern"),sleep:!!s.querySelector(".sleeping")}})()''')
        ft.rec("首頁插圖","旅途中 18:30 是晚餐：暮色天空、燈籠、兩隻貓醒著",info['p']=="dinner" and info['sky'] and info['grad'] and info['cats']==2 and info['lantern'] and not info['sleep'],info)
        await pg.screenshot(path=OUT+'hero_dinner.png')
        await pg.click('.hero-cats .cat-b',force=True);await pg.wait_for_timeout(100)
        ft.rec("首頁插圖","晚餐的貓點一下會跳",await pg.evaluate('document.querySelector(".hero-cats").classList.contains("hop")'))
        ft.rec("首頁插圖","晚餐沒有 JS 錯誤",not pg.errs,pg.errs[:2])
        await ft.close(pg)
        pg=await ft.newpage(b,ft.jst(11,10,20,59));await pg.wait_for_timeout(300);await home(pg)
        a=await pg.evaluate('document.querySelector(".hero .scene").dataset.period')
        await pg.clock.fast_forward("01:30");await pg.wait_for_timeout(600)
        c=await pg.evaluate('document.querySelector(".hero .scene").dataset.period')
        ft.rec("首頁插圖","20:59 晚餐，過 21:00 自動換睡覺",a=="dinner" and c=="night",[a,c])
        await ft.close(pg)
        await b.close()
asyncio.run(main())
