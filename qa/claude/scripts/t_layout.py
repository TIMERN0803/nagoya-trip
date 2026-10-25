# 版面、無障礙：寬度、橫向、安全區域、觸控目標、對比、reduced motion、200% 縮放、鍵盤、讀屏標籤
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
CONTRAST_JS=r'''(()=>{
const parse=c=>{const m=c.match(/rgba?\(([^)]+)\)/);if(!m)return null;const a=m[1].split(",").map(s=>parseFloat(s));return {r:a[0],g:a[1],b:a[2],a:a.length>3?a[3]:1}};
const lum=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b)};
const bgOf=el=>{let e=el;let layers=[];while(e&&e.nodeType===1){const s=getComputedStyle(e);if(s.backgroundImage&&s.backgroundImage!=="none")return {img:true};const c=parse(s.backgroundColor);if(c&&c.a>0){layers.push(c);if(c.a>=1)break}e=e.parentElement}
 let base={r:255,g:255,b:255};for(const l of layers.reverse()){base={r:l.r*l.a+base.r*(1-l.a),g:l.g*l.a+base.g*(1-l.a),b:l.b*l.a+base.b*(1-l.a)}}return base};
const out=[];const seen=new Set();
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
while(n=walker.nextNode()){const t=n.textContent.trim();if(!t)continue;const el=n.parentElement;if(!el||seen.has(el))continue;seen.add(el);
 const r=el.getBoundingClientRect();if(!r.width||!r.height)continue;if(el.closest("svg,[aria-hidden=true]"))continue;
 const s=getComputedStyle(el);if(s.visibility==="hidden"||+s.opacity===0)continue;
 const fg=parse(s.color);const bg=bgOf(el);if(!fg||bg.img)continue;
 const L1=lum(fg),L2=lum(bg);const ratio=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
 const fs=parseFloat(s.fontSize),fw=+s.fontWeight||400;const large=fs>=24||(fs>=18.66&&fw>=700);
 const need=large?3:4.5;if(ratio<need)out.push({t:t.slice(0,24),cls:(el.className&&el.className.baseVal===undefined?el.className:"")+"",fs,fw,color:s.color,ratio:Math.round(ratio*100)/100,need})}
return out})()'''
TARGETS_JS=r'''(()=>{const out=[];document.querySelectorAll("button,a[href],input[type=checkbox],[role=button],select,summary").forEach(e=>{const r=e.getBoundingClientRect();if(!r.width||!r.height)return;if(getComputedStyle(e).visibility==="hidden")return;
 let w=r.width,h=r.height;if(e.tagName==="INPUT"){const l=e.closest("label");if(l){const lr=l.getBoundingClientRect();w=lr.width;h=lr.height}}
 if(w<44||h<44)out.push({el:e.tagName.toLowerCase()+(e.className?"."+String(e.className).split(" ")[0]:""),txt:(e.getAttribute("aria-label")||e.innerText||"").trim().slice(0,16),w:Math.round(w),h:Math.round(h)})});return out})()'''
LABELS_JS=r'''(()=>{const out=[];document.querySelectorAll("button,a[href],[role=button],input,select,textarea").forEach(e=>{const r=e.getBoundingClientRect();if(!r.width)return;
 let name=(e.getAttribute("aria-label")||"").trim()||(e.getAttribute("aria-labelledby")?"lb":"")||(e.innerText||"").trim()||(e.getAttribute("title")||"")||(e.labels&&e.labels[0]&&e.labels[0].innerText.trim())||(e.getAttribute("placeholder")||"");
 if(!name)out.push(e.tagName.toLowerCase()+"."+String(e.className).split(" ")[0]+" "+e.outerHTML.slice(0,80))});return out})()'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # ---------- 寬度與 FAB / 底部分頁 ----------
        res=[]
        for w,h in [(320,568),(375,667),(390,844),(430,932),(844,390),(667,375)]:
            ctx=await q.mkctx(b,vw=w,vh=h); pg=await q.page(ctx,q.jst(11,21,10,20)); await q.home(pg)
            info=await pg.evaluate('''(()=>{const f=document.querySelector(".fab"),t=document.querySelector("nav.tabs");const fr=f.hidden?null:f.getBoundingClientRect(),tr=t.getBoundingClientRect();
              return {sw:document.documentElement.scrollWidth,fab:fr&&[Math.round(fr.left),Math.round(fr.top),Math.round(fr.right),Math.round(fr.bottom)],tabs:[Math.round(tr.top),Math.round(tr.bottom)],overlap:fr?fr.bottom>tr.top:false,
              tabH:Math.round(tr.height),tabsVisibleH:Math.round(Math.min(innerHeight,tr.bottom)-tr.top)}})()''')
            await pg.screenshot(path=q.SHOTS+f"layout_home_{w}x{h}.png")
            # 每個分頁有沒有水平捲動
            hs={}
            for t in ["wx","move","acct","list"]:
                await q.tab(pg,t); hs[t]=await pg.evaluate('document.documentElement.scrollWidth')
            await pg.evaluate('tab="plan";view="day";dayIdx=4;render()'); hs["day"]=await pg.evaluate('document.documentElement.scrollWidth')
            if w in (320,844): await pg.screenshot(path=q.SHOTS+f"layout_day_{w}x{h}.png")
            over={k:v for k,v in hs.items() if v>w}
            q.rec("版面",f"{w}×{h} 各頁沒有水平捲動",info["sw"]<=w and not over,{"home":info["sw"],**hs})
            q.rec("版面",f"{w}×{h} 浮動按鈕不壓到底部分頁",not info["overlap"],info)
            await ctx.close()
        # 橫向時面板
        ctx=await q.mkctx(b,vw=844,vh=390); pg=await q.page(ctx,q.jst(11,21,10,20)); await q.home(pg)
        await pg.click('[data-sos]'); await pg.wait_for_timeout(200)
        sh=await pg.evaluate('(()=>{const c=document.querySelector(".sheet-modal .sm-card");const r=c.getBoundingClientRect();const t=document.querySelector(".sos-top").getBoundingClientRect();return {top:Math.round(r.top),h:Math.round(r.height),vh:innerHeight,contentVisible:Math.round(r.bottom-t.bottom)}})()')
        await pg.screenshot(path=q.SHOTS+"layout_sos_landscape.png")
        q.note("版面","橫向 844×390 求助面板：固定標題後剩下可捲動內容高度",sh)
        await ctx.close()
        # ---------- 安全區域（模擬 iPhone 瀏海 47px／Home Indicator 34px）----------
        ctx=await q.mkctx(b,vw=390,vh=844); pg=await q.page(ctx,q.jst(11,21,10,20)); await q.home(pg)
        await pg.add_style_tag(content=":root{}")
        sa=await pg.evaluate('''(()=>{const s=getComputedStyle(document.querySelector("nav.tabs"));return {pb:s.paddingBottom,bottom:s.bottom}})()''')
        q.note("版面","底部分頁 padding-bottom（未模擬 inset 時）",sa)
        await ctx.close()
        # ---------- 對比 ----------
        allbad={}
        ctx=await q.mkctx(b); 
        for lab,t,act in [("首頁出發前",q.twt(10,25,18,0),None),("首頁旅途中",q.jst(11,19,12,0),"home"),("當天行程",q.jst(11,19,12,0),None),("記帳",q.jst(11,19,12,0),"acct"),("清單",q.jst(11,19,12,0),"list"),("交通",q.jst(11,19,12,0),"move"),("天氣",q.jst(11,19,12,0),"wx"),("求助",q.jst(11,19,12,0),"sos")]:
            pg=await q.page(ctx,t,init=q.seed({f"{B}/wallet/zhang":{"cashIn":6000},f"{B}/expenses/e":{"amt":3000,"cat":"food","who":"zhang","split":"both","pay":"cash","day":"11/19","note":"x","ts":1}}))
            if act=="home": await q.home(pg)
            elif act=="sos": await q.home(pg); await pg.click('[data-sos]'); await pg.wait_for_timeout(200); await pg.click('[data-sos-tab=emg]')
            elif act: await q.tab(pg,act)
            await pg.wait_for_timeout(300)
            bad=await pg.evaluate(CONTRAST_JS)
            allbad[lab]=bad
            await pg.close()
        await ctx.close()
        flat=[(k,x) for k,v in allbad.items() for x in v]
        uniq={}
        for k,x in flat:
            key=(x["color"],x["fs"],x["t"][:10])
            if key not in uniq: uniq[key]=(k,x)
        lst=sorted(uniq.values(),key=lambda z:z[1]["ratio"])
        q.note("對比","WCAG AA 不足的文字（去重，依對比由低到高，前 40）",[f'{k}｜{x["t"]}｜{x["fs"]}px/{x["fw"]}｜{x["color"]}｜{x["ratio"]}:1（需 {x["need"]}）' for k,x in lst[:40]])
        q.rec("對比",f"所有頁面文字對比 ≥ AA（共 {len(lst)} 種不足）",len(lst)==0)
        # ---------- 觸控目標 ----------
        ctx=await q.mkctx(b); res={}
        for lab,t,act in [("首頁旅途中",q.jst(11,19,12,0),"home"),("當天行程",q.jst(11,19,12,0),None),("記帳",q.jst(11,19,12,0),"acct"),("清單",q.jst(11,19,12,0),"list"),("行李",q.jst(11,19,12,0),"pack"),("求助",q.jst(11,19,12,0),"sos")]:
            pg=await q.page(ctx,t)
            if act=="home": await q.home(pg)
            elif act=="pack": await q.tab(pg,"list"); await pg.click('[data-pack-open]')
            elif act=="sos": await q.home(pg); await pg.click('[data-sos]'); await pg.wait_for_timeout(200)
            elif act: await q.tab(pg,act)
            await pg.wait_for_timeout(300)
            res[lab]=await pg.evaluate(TARGETS_JS)
            await pg.close()
        await ctx.close()
        summ={k:[f'{x["el"]}「{x["txt"]}」{x["w"]}×{x["h"]}' for x in v] for k,v in res.items()}
        uniq=sorted({s for v in summ.values() for s in v})
        q.note("觸控目標","小於 44×44 的可點元素（去重）",uniq[:60])
        # ---------- 讀屏標籤 ----------
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,19,12,0)); labs={}
        for act in ["day","home","acct","list","pack"]:
            if act=="home": await q.home(pg)
            elif act=="pack": await q.tab(pg,"list"); await pg.click('[data-pack-open]')
            elif act!="day": await q.tab(pg,act)
            await pg.wait_for_timeout(200); labs[act]=await pg.evaluate(LABELS_JS)
        await q.home(pg); await pg.click('[data-sos]'); await pg.wait_for_timeout(200); await pg.click('.sos-ph button >> nth=0')
        labs["sos-show"]=await pg.evaluate(LABELS_JS)
        roles=await pg.evaluate('({show:document.querySelector(".sos-show").getAttribute("role"),modal:document.querySelector(".sos-show").getAttribute("aria-modal"),focus:document.activeElement.className})')
        q.note("無障礙","沒有可讀名稱的互動元素",{k:v[:8] for k,v in labs.items() if v})
        q.rec("無障礙","全螢幕放大畫面打開後焦點移到畫面內（讀屏會讀到大字）",roles["focus"]!="" and "sos" in roles["focus"],roles)
        await ctx.close()
        # ---------- reduced motion ----------
        ctx=await q.mkctx(b,reduced_motion="reduce"); pg=await q.page(ctx,q.jst(11,19,9,0)); await q.home(pg); await pg.wait_for_timeout(500)
        anim=await pg.evaluate('(()=>{const out=[];document.querySelectorAll("*").forEach(e=>{const s=getComputedStyle(e);if(s.animationName&&s.animationName!=="none"&&s.animationPlayState==="running"&&parseFloat(s.animationDuration)>0&&s.animationIterationCount==="infinite")out.push((e.getAttribute("class")||e.tagName)+":"+s.animationName)});return [...new Set(out)]})()')
        q.rec("無障礙","prefers-reduced-motion 時沒有無限循環動畫",not anim,anim[:15])
        await ctx.close()
        # ---------- 200% 縮放（以 device 寬 195 CSS px 模擬）與大字 ----------
        ctx=await q.mkctx(b,vw=195,vh=422,dsf=2); pg=await q.page(ctx,q.jst(11,19,12,0)); await q.home(pg)
        z=await pg.evaluate('({sw:document.documentElement.scrollWidth,iw:innerWidth})')
        await pg.screenshot(path=q.SHOTS+"layout_zoom200_home.png")
        await q.tab(pg,"acct"); z2=await pg.evaluate('document.documentElement.scrollWidth'); await pg.screenshot(path=q.SHOTS+"layout_zoom200_acct.png")
        await q.home(pg); await pg.click('[data-sos]'); await pg.wait_for_timeout(200); await pg.screenshot(path=q.SHOTS+"layout_zoom200_sos.png")
        q.rec("版面","200% 縮放（195 CSS px 寬）沒有水平捲動",z["sw"]<=195 and z2<=195,{"home":z,"acct":z2})
        await ctx.close()
        # ---------- 鍵盤操作 ----------
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,19,12,0)); await q.home(pg)
        seq=[]
        for i in range(25):
            await pg.keyboard.press("Tab")
            seq.append(await pg.evaluate('(()=>{const e=document.activeElement;const s=getComputedStyle(e);return (e.getAttribute("aria-label")||e.innerText||e.tagName).trim().slice(0,12)+(s.outlineStyle!=="none"&&s.outlineWidth!=="0px"||s.boxShadow!=="none"?"":"〔無焦點框〕")})()'))
        q.note("鍵盤","首頁按 Tab 25 次的焦點順序",seq)
        # 記帳流程只用鍵盤
        await q.tab(pg,"acct"); await pg.focus('#f-amt'); await pg.keyboard.type("1500")
        for i in range(30):
            await pg.keyboard.press("Tab")
            if await pg.evaluate('document.activeElement.id==="f-save"'): break
        await pg.keyboard.press("Enter"); await pg.wait_for_timeout(300)
        ok=len(await q.mock(pg,"/expenses/"))==1
        q.rec("鍵盤","只用鍵盤可完成記一筆帳",ok)
        # 排序可否用鍵盤
        await q.tab(pg,"list"); await pg.click('[data-sort-toggle=prep]'); await pg.focus('.drag-h'); o0=await pg.evaluate('[...document.querySelectorAll("[data-sort-id]")].map(x=>x.dataset.sortId)')
        await pg.keyboard.press("ArrowDown"); await pg.keyboard.press("Space"); await pg.keyboard.press("ArrowDown"); await pg.wait_for_timeout(200)
        o1=await pg.evaluate('[...document.querySelectorAll("[data-sort-id]")].map(x=>x.dataset.sortId)')
        q.rec("鍵盤","排序把手（role=button, tabindex=0）可用鍵盤移動",o0!=o1,"順序沒變" if o0==o1 else "")
        await ctx.close()
        q.dump("layout")
        await b.close()
asyncio.run(main())
