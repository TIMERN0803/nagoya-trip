import asyncio,datetime as dt,json,re,sys
from playwright.async_api import async_playwright
U=dt.timezone.utc
APP=open('app.js').read();FS=open('fs.js').read()
SRC=open('/home/claude/nagoya-trip/index.html',encoding='utf8').read()
R=[]
def rec(area,case,ok,detail=""):R.append((area,case,bool(ok),detail));print(("PASS " if ok else "FAIL ")+area+" | "+case+(" | "+str(detail) if detail else ""),flush=True)
def jst(m,d,h,mi=0):return dt.datetime(2026,m,d,h,mi,tzinfo=dt.timezone(dt.timedelta(hours=9)))
def twt(m,d,h,mi=0):return dt.datetime(2026,m,d,h,mi,tzinfo=dt.timezone(dt.timedelta(hours=8)))
async def newpage(b,t,tz="Asia/Tokyo",me="zhang",code="neko-test",init="",perm=None,ctx=None):
    own=ctx is None
    if own:
        ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id=tz,permissions=perm or [])
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
        await ctx.route("**/fonts.googleapis.com/**",lambda r:r.abort())
        await ctx.route("**/open.er-api.com/**",lambda r:r.abort())
        await ctx.route("**/currency-api*/**",lambda r:r.abort())
    pg=await ctx.new_page();pg.errs=[];pg.on('pageerror',lambda e:pg.errs.append(str(e)))
    pg.on('console',lambda m:pg.errs.append("console:"+m.text) if m.type=="error" and "net::" not in m.text and "Failed to load" not in m.text else None)
    await pg.clock.install(time=t)
    await pg.add_init_script('try{sessionStorage.setItem("ngy:launched","1")}catch(e){}')  # 開啟動畫只在重新開啟 App 時播；一般測試當作已經開過
    s='try{if(!sessionStorage.getItem("s")){localStorage.setItem("ngy:tour","1");'+(f'localStorage.setItem("ngy:me",{json.dumps(me)});' if me else '')+(f'localStorage.setItem("ngy:code",{json.dumps(code)});' if code else '')+init+'sessionStorage.setItem("s",1)}}catch(e){}'
    await pg.add_init_script(s)
    await pg.goto('http://localhost:8766/'); await pg.wait_for_timeout(900)
    pg.ctx=ctx;pg.own=own
    return pg
async def close(pg):
    if pg.own:await pg.ctx.close()
    else:await pg.close()
DAYS=json.loads(open('/tmp/days.json').read())
def tmin(t):
    if not t:return None
    h,m=t.split(":");return int(h)*60+int(m)

async def A_timeline(b):
    times=[(8,0),(13,0),(21,0)]
    for di,d in enumerate(DAYS):
        m,dd=map(int,d['d'].split('/'))
        for h,mi in times:
            if (d["d"],h)==("11/17",8):h,mi=9,0
            pg=await newpage(b,jst(m,dd,h,mi))
            nowM=h*60+mi
            info=await pg.evaluate('''()=>({when:document.querySelector(".banner .when")?.textContent||"",flags:[...document.querySelectorAll("ol.tl li.item")].map(li=>li.id+":"+(li.className.match(/s-(\\w+)/)||[,""])[1]),now:document.querySelector(".nowcard")?.innerText.replace(/\\s+/g," ")||"",legs:document.querySelectorAll(".leg").length,mood:document.getElementById("mood")?.classList.contains("locked")})''')
            lab=f"{d['d']} {h:02d}:{mi:02d}"
            rec("A 當天行程",f"{lab} 自動開到當天",d['d'] in info['when'] and "今天" in info['when'],info['when'])
            exp={}
            nxt=None
            # 行程時間換算成日本時間：去程航班（tz Asia/Taipei）寫的是台灣時間，比日本慢 1 小時
            tmj=lambda it:None if tmin(it.get('t')) is None else tmin(it.get('t'))+(60 if it.get('tz')=="Asia/Taipei" else 0)
            for i,it in enumerate(d['items']):
                tm=tmj(it)
                if tm is None:continue
                if tm>nowM:
                    if nxt is None:nxt=i
                else:exp[i]="now" if nowM-tm<90 else "done"
            if nxt is not None:exp[nxt]="next"
            got={int(x.split(':')[0][3:]):x.split(':')[1] for x in info['flags']}
            bad=[(i,exp.get(i,""),got.get(i,"")) for i in range(len(d['items'])) if exp.get(i,"")!=got.get(i,"")]
            rec("A 當天行程",f"{lab} 已過／進行中／接下來標示",not bad,bad)
            if nxt is not None:
                it=d['items'][nxt];left=tmj(it)-nowM
                ok=it['n'][:6] in info['now'] and (f"{left%60} 分後" in info['now'])
                rec("A 當天行程",f"{lab} 接下來列",ok,info['now'])
            else:
                cur=[i for i,v in exp.items() if v=="now"]
                if cur:rec("A 當天行程",f"{lab} 最後一個行程進行中的提示","進行中" in info['now'] and d['items'][max(cur)]['n'][:6] in info['now'],info['now'])
                else:rec("A 當天行程",f"{lab} 行程走完時的提示","心情" in info['now'] or "走完" in info['now'],info['now'])
            rec("A 當天行程",f"{lab} 當天心情可填",info['mood'] is False)
            rec("A 當天行程",f"{lab} 沒有錯誤",not pg.errs,pg.errs[:2])
            if h==8:
                await pg.click('[data-home]');await pg.wait_for_timeout(300)
                hero=await pg.evaluate('document.querySelector(".today-main")?.innerText.replace(/\\s+/g," ")||document.querySelector(".hero")?.innerText.slice(0,40)')
                rec("A 首頁",f"{d['d']} 首頁顯示 D{di+1}",f"D{di+1}" in (hero or "") and d['title'][:3] in hero,hero)
                tiles=await pg.evaluate('[...document.querySelectorAll(".tile.today")].map(t=>t.dataset.day)')
                rec("A 首頁",f"{d['d']} 地點格標示今天",tiles==[str(di)],tiles)
                nxtday=di+1
                if nxtday<len(DAYS):
                    await pg.click(f'.tile[data-day="{nxtday}"]');await pg.wait_for_timeout(300)
                    lk=await pg.evaluate('document.getElementById("mood")?.classList.contains("locked")')
                    rec("A 首頁",f"{d['d']} 明天的心情還鎖著",lk is True)
            await close(pg)

async def A2_tz(b):
    for name,t,tz,exp in [("台灣時區 11/17 06:30 起飛前",twt(11,17,6,30),"Asia/Taipei","cd"),("台灣時區 11/17 07:06 起飛後",twt(11,17,7,6),"Asia/Taipei","D1"),
                          ("手機沒切日本時區 11/18 23:30 台灣（日本已 11/19）",twt(11,18,23,30),"Asia/Taipei","?"),("日本 11/24 23:50 最後一天",jst(11,24,23,50),"Asia/Tokyo","D8"),("日本 11/25 00:10 結束",jst(11,25,0,10),"Asia/Tokyo","完")]:
        pg=await newpage(b,t,tz)
        if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
        h=await pg.evaluate('document.querySelector(".hero").innerText.replace(/\\s+/g," ").slice(0,80)')
        if exp=="cd":ok="時" in h and "秒" in h
        elif exp=="?":ok=True
        else:ok=exp in h
        rec("A 時區與日期邊界",name,ok and not pg.errs,h)
        await close(pg)

async def B_overnight(b):
    for name,t,tz,adv,exp in [("前一晚 11/16 23:50 開著，放到 11/17 07:10（起飛後）",twt(11,16,23,50),"Asia/Taipei",7*3600e3+20*60e3,"D1"),
                              ("11/17 22:00 開著，放到隔天 11/18 08:00",jst(11,17,22),"Asia/Tokyo",10*3600e3,"D2"),
                              ("11/24 21:00 開著，放到 11/25 09:00",jst(11,24,21),"Asia/Tokyo",12*3600e3,"完")]:
        pg=await newpage(b,t,tz)
        await pg.clock.fast_forward(int(adv));await pg.wait_for_timeout(500)
        await pg.evaluate('document.dispatchEvent(new Event("visibilitychange"))');await pg.wait_for_timeout(1500)
        try:
            if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
            h=await pg.evaluate('document.querySelector(".hero").innerText.replace(/\\s+/g," ").slice(0,80)')
        except Exception as e:h="ERR "+str(e)[:80]
        rec("B App 開著跨日",name,exp in h,h)
        await close(pg)

async def C_remind(b):
    for name,t,tz,exp in [("11/18 19:00 伏見屋 19:30",jst(11,18,19,0),"Asia/Tokyo","伏見屋"),("11/17 06:35 台灣 JX 320 07:05",twt(11,17,6,35),"Asia/Taipei","JX 320"),("11/20 07:35 KISO? 11/21 07:30 KISO 08:00",jst(11,21,7,30),"Asia/Tokyo","KISO")]:
        pg=await newpage(b,t,tz,init='localStorage.setItem("ngy:notify","1");')
        await pg.clock.run_for(21000);await pg.wait_for_timeout(500)
        tx=await pg.evaluate('document.getElementById("toast")?.innerText.replace(/\\s+/g," ")||""')
        rec("C 行程提醒",name,exp in tx and "30 分鐘後" in tx,tx)
        await close(pg)
    pg=await newpage(b,jst(11,18,12,0))
    await pg.click('[data-home]');await pg.wait_for_timeout(300)
    await pg.click('[data-notify]');await pg.wait_for_timeout(500)
    on=await pg.evaluate('localStorage.getItem("ngy:notify")')
    rec("C 行程提醒","首頁開關可以打開並記住",on=="1")
    await pg.click('[data-cal]');await pg.wait_for_timeout(300)
    links=await pg.evaluate('[...document.querySelectorAll(".sm-opt")].map(a=>a.getAttribute("href")||a.textContent.trim().slice(0,6))')
    rec("C 行程提醒","加到行事曆選單（訂閱／下載／複製）",any(str(l).startswith("webcal:") for l in links) and any(str(l).endswith(".ics") for l in links),links)
    await close(pg)

async def D_mood_sync(b):
    ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id="Asia/Tokyo")
    await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
    a=await newpage(b,jst(11,18,21,0),ctx=ctx,me="zhang")
    # A writes mood
    await a.click('#mood .fbtn[data-score="5"]');await a.fill('#mood-form textarea','龍貓好可愛');await a.click('#mood-form .primary');await a.wait_for_timeout(600)
    saved=await a.evaluate('Object.entries(JSON.parse(localStorage.getItem("mockdb")||"{}")).filter(([k])=>k.includes("/moods/")).map(([k,v])=>k+":"+v.score)')
    rec("D 心情與同步","阿彰寫 11/18 心情並送出",any("11-18_zhang:5" in s for s in saved),saved)
    await a.click('[data-home]');await a.wait_for_timeout(300)
    ml=await a.evaluate('document.querySelector(".mood-line")?.innerText.replace(/\\s+/g," ")')
    rec("D 心情與同步","首頁心情列變成已填",ml and "超開心" in ml,ml)
    # B (cindy) on another page — simulate other phone: separate me in same storage is shared... use sessionStorage-less override
    bpg=await ctx.new_page();bpg.errs=[];bpg.on('pageerror',lambda e:bpg.errs.append(str(e)))
    await bpg.clock.install(time=jst(11,18,21,5))
    await bpg.add_init_script('try{localStorage.setItem("ngy:me","star")}catch(e){}')
    await bpg.goto('http://localhost:8766/');await bpg.wait_for_timeout(1200)
    txt=await bpg.evaluate('document.getElementById("mood")?.innerText.replace(/\\s+/g," ")||""')
    rec("D 心情與同步","星星的手機看得到阿彰寫的心情","龍貓好可愛" in txt,txt[:80])
    await bpg.click('#mood .fbtn[data-score="4"]');await bpg.fill('#mood-form textarea','鰻魚飯讚');await bpg.click('#mood-form .primary');await bpg.wait_for_timeout(800)
    await a.wait_for_timeout(800)
    await a.click('.tile[data-day="1"]');await a.wait_for_timeout(500)
    txa=await a.evaluate('document.getElementById("mood")?.innerText.replace(/\\s+/g," ")||""')
    rec("D 心情與同步","阿彰這邊即時看到星星寫的","鰻魚飯讚" in txa,txa[:100])
    rec("D 心情與同步","沒有錯誤",not a.errs and not bpg.errs,(a.errs+bpg.errs)[:2])
    await ctx.close()

async def openexp(pg):
    # 記帳分成清單頁和「記一筆」填寫面板：面板沒開就按「記一筆」
    if not await pg.query_selector('.exp-sheet:not(.leaving) #f-amt'):
        await pg.click('[data-exp-new]');await pg.wait_for_timeout(600)

async def E_acct(b):
    pg=await newpage(b,jst(11,18,20,0))
    await pg.click('nav.tabs button[data-tab="acct"]');await pg.wait_for_timeout(400)
    async def add(amt,cat,who,split,note):
        await openexp(pg);await pg.fill('#f-amt',str(amt));await pg.click(f'[data-pick="cat"] [data-v="{cat}"]');await pg.click(f'[data-pick="who"] [data-v="{who}"]');await pg.click(f'[data-pick="split"] [data-v="{split}"]');await pg.fill('#f-note',note);await pg.click('#f-save');await pg.wait_for_timeout(500)
    await openexp(pg);cats=await pg.evaluate('[...document.querySelectorAll("[data-pick=cat] [data-v]")].map(x=>x.dataset.v)')
    await add(3000,cats[0],"zhang","both","燒肉");await add(1000,cats[1],"star","both","車票");await add(500,cats[2],"star","self","扭蛋")
    s=await pg.evaluate('document.getElementById("acct-sum").innerText.replace(/\\s+/g," ")')
    rec("E 記帳","新增三筆後總額 ¥4,500","4,500" in s,s[:60])
    rec("E 記帳","分帳：星星要給阿彰 ¥1,000","星星要給阿彰 ¥1,000" in s,re.search(r'.{0,6}要給.{0,12}',s).group(0) if '要給' in s else s[-40:])
    rec("E 記帳","台幣換算 0.2 → NT$ 900","NT$ 900" in s)
    await pg.fill('#f-rate','0.21');await pg.press('#f-rate','Tab');await pg.wait_for_timeout(400)
    s=await pg.evaluate('document.getElementById("acct-sum").innerText.replace(/\\s+/g," ")')
    rec("E 記帳","改匯率 0.21 → NT$ 945","NT$ 945" in s,re.search(r'NT\$ [\d,]+',s).group(0) if 'NT$' in s else s)
    await pg.click('.ex[data-edit] >> nth=0');await pg.wait_for_timeout(600)
    await pg.fill('#f-amt','600');await pg.click('#f-save');await pg.wait_for_timeout(500)
    s=await pg.evaluate('document.getElementById("acct-sum").innerText.replace(/\\s+/g," ")')
    rec("E 記帳","修改一筆金額","4,600" in s or "4,100" in s or "3,600" in s or "1,6" in s,s[:40])
    n0=await pg.evaluate('document.querySelectorAll(".ex[data-edit]").length')
    await pg.click('.ex[data-edit] >> nth=0');await pg.wait_for_timeout(600)
    await pg.click('[data-exp-del]');await pg.wait_for_timeout(500)
    n1=await pg.evaluate('document.querySelectorAll(".ex[data-edit]").length')
    rec("E 記帳","刪除一筆（按一次＋可復原）",n1==n0-1 and await pg.query_selector('.undo-bar'),f"{n0}→{n1}")
    srv=await pg.evaluate('Object.keys(JSON.parse(localStorage.getItem("mockdb")||"{}")).filter(k=>k.includes("/expenses/")).length')
    rec("E 記帳","有寫到雲端（共用）",srv==n1,f"雲端 {srv} 筆")
    rec("E 記帳","沒有錯誤",not pg.errs,pg.errs[:2])
    await close(pg)

async def F_list(b):
    pg=await newpage(b,jst(11,18,20,0))
    await pg.click('nav.tabs button[data-tab="list"]');await pg.wait_for_timeout(500)
    p0=await pg.evaluate('document.querySelectorAll("[data-group-id=prep] .chk-row").length')
    await pg.click('[data-list-tab="buy"]');await pg.wait_for_timeout(300)
    n0=await pg.evaluate('document.querySelectorAll(".chk-row").length')
    rec("F 清單","預設項目都在（待辦＋要買的）",p0+n0>=10,[p0,n0])
    await pg.click('[data-item-new="buy"]');await pg.fill('.chk-form input[name=title]','白色戀人');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
    n1=await pg.evaluate('document.querySelectorAll(".chk-row").length')
    rec("F 清單","新增一項",n1==n0+1,f"{n0}→{n1}")
    cb=await pg.query_selector('.chk-row input[type=checkbox]');await cb.click();await pg.wait_for_timeout(400)
    ck=await pg.evaluate('Object.keys(JSON.parse(localStorage.getItem("mockdb")||"{}")).filter(k=>k.includes("/checks/")).length')
    rec("F 清單","打勾並同步到雲端",ck>=1,ck)
    rec("F 清單","沒有錯誤",not pg.errs,pg.errs[:2])
    await close(pg)

async def G_weather(b):
    days=[]
    for k in range(16):days.append((dt.date(2026,11,9)+dt.timedelta(days=k)).isoformat())
    def mk(code):return {"daily":{"time":days,"weather_code":[code]*16,"temperature_2m_max":[14.6]*16,"temperature_2m_min":[5.2]*16,"precipitation_probability_max":[40]*16}}
    body=json.dumps([mk(61),mk(3),mk(0),mk(2)])
    ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id="Asia/Tokyo")
    await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/api.open-meteo.com/**",lambda r:r.fulfill(body=body,content_type="application/json",headers={"access-control-allow-origin":"*"}))
    pg=await newpage(b,jst(11,9,9,0),ctx=ctx)
    await pg.wait_for_timeout(800)
    await pg.click('nav.tabs button[data-tab="wx"]');await pg.wait_for_timeout(400)
    w=await pg.evaluate('document.querySelector(".app, #app").innerText.replace(/\\s+/g," ")')
    rec("G 天氣","出發前 8 天抓到預報並顯示","實際預報" in w and "15°" in w and "有雨" in w,w[w.find("實際"):w.find("實際")+40] if "實際" in w else w[:80])
    await ctx.close()

async def H_offline(b):
    ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id="Asia/Tokyo")
    await ctx.route("**/firebasejs/**",lambda r:r.abort())
    pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.add_init_script('try{localStorage.setItem("ngy:tour","1")}catch(e){}')
    await pg.goto('http://localhost:8766/');await pg.wait_for_timeout(2500)
    await pg.reload();await pg.wait_for_timeout(1500)
    ready=await pg.evaluate('navigator.serviceWorker.controller?1:0')
    await ctx.set_offline(True)
    await pg.reload();await pg.wait_for_timeout(1500)
    t=await pg.evaluate('document.body.innerText.slice(0,40)')
    await pg.click('.tile[data-day="1"]');await pg.wait_for_timeout(400)
    img=await pg.evaluate('(()=>{const i=document.querySelector(".inmap img");return i?i.complete&&i.naturalWidth>0:null})()')
    rec("H 離線","沒網路也能打開 App",ready==1 and "名古屋" in t,t)
    rec("H 離線","沒網路也看得到吉卜力地圖",img is True,img)
    await ctx.set_offline(False);await ctx.close()

def I_ics():
    s=open('/home/claude/nagoya-trip/nagoya-trip.ics',encoding='utf8').read().replace("\r\n ","")
    ev=s.split("BEGIN:VEVENT")[1:]
    rec("I 行事曆檔","25 個行程（含 11/24 07:45 先辦退稅）",len(ev)==25,len(ev))
    al=all("BEGIN:VALARM" in e and "TRIGGER:-PT30M" in e for e in ev)
    rec("I 行事曆檔","每個行程都有 30 分鐘前提醒",al)
    bad=[]
    for d in DAYS:
        m,dd=map(int,d['d'].split('/'))
        for it in d['items']:
            if not it.get('t'):continue
            hh,mm=it['t'].split(':')
            hit=[e for e in ev if f"2026{m:02d}{dd:02d}T{hh}{mm}00" in e]
            if not hit:bad.append(d['d']+" "+it['t']+" "+it['n'][:10])
    rec("I 行事曆檔","有時間的行程都在、日期時間正確",not bad,bad[:4])
    tz=[x for e in ev for x in re.findall(r'DTSTART[^:\n]*',e)]
    rec("I 行事曆檔","時區標註",all("TZID" in x or x.endswith("Z") for x in tz),sorted(set(tz))[:3])

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for f in [A_timeline,A2_tz,B_overnight,C_remind,D_mood_sync,E_acct,F_list,G_weather,H_offline]:
            try:await f(b)
            except Exception as e:rec(f.__name__,"執行失敗",False,str(e)[:200])
        I_ics()
        await b.close()
    json.dump(R,open('results.json','w'),ensure_ascii=False)
    print("TOTAL",len(R),"FAIL",sum(1 for r in R if not r[2]))
if __name__=='__main__':asyncio.run(main())
