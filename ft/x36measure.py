# QA R2 體驗優化批 B（X3–X6）量測：對比（getComputedStyle＋WCAG 公式）、全站最小可見文字
# 用法：BASE=http://localhost:8769/ TAG=after python3 x36measure.py  → 輸出 /tmp/x36_<TAG>.json
import os, json, asyncio
from phonelib import *
import reviewshot as rs
BASE = os.environ.get('BASE', 'http://localhost:8766/'); TAG = os.environ.get('TAG', 'x')
RVDB = json.loads(rs.DB.replace('trips/neko-test', B))
SHOT = os.environ.get('SHOTDIR', '')
JS = r'''
(()=>{
const P=s=>{const m=s.match(/rgba?\(([^)]+)\)/);if(!m)return null;const a=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);return [a[0],a[1],a[2],a.length>3?a[3]:1]};
const over=(t,b)=>{const a=t[3];return [t[0]*a+b[0]*(1-a),t[1]*a+b[1]*(1-a),t[2]*a+b[2]*(1-a),1]};
const L=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2])};
window.__bg=el=>{const st=[];let e=el,img=[];while(e&&e.nodeType===1){const s=getComputedStyle(e);if(s.backgroundImage!=="none")img.push(e.className||e.tagName);const c=P(s.backgroundColor);if(c&&c[3]>0){st.push(c);if(c[3]>=1)break}e=e.parentElement}
 let b=[255,255,255,1];for(let i=st.length-1;i>=0;i--)b=over(st[i],b);return {b,img}};
window.__cx=el=>{if(!el)return null;const s=getComputedStyle(el);const {b,img}=__bg(el);const f=over(P(s.color),b);const l1=L(f),l2=L(b);
 return {txt:el.innerText.trim().slice(0,24),fg:s.color,bg:"rgb("+b.slice(0,3).map(Math.round).join(",")+")",ratio:+((Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05)).toFixed(2),fs:s.fontSize,fw:s.fontWeight,img}};
window.__minfs=label=>{const out=[];const vis=e=>{for(let x=e;x&&x.nodeType===1;x=x.parentElement){const s=getComputedStyle(x);if(s.visibility==="hidden"||+s.opacity===0||s.display==="none")return false;if(x.inert)return false}return true};
 const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){if(!n.nodeValue.trim())continue;const e=n.parentElement;if(!e||e.closest("svg,script,style,template,noscript"))continue;
  const r=document.createRange();r.selectNodeContents(n);const rs=r.getClientRects();if(!rs.length||![...rs].some(q=>q.width>0&&q.height>0))continue;if(!vis(e))continue;
  const fs=parseFloat(getComputedStyle(e).fontSize);const dis=!!e.closest("[disabled],[aria-disabled=true]");
  const sel=(e.tagName.toLowerCase()+(e.className&&typeof e.className==="string"?"."+e.className.trim().split(/\s+/).join("."):""));const par=e.parentElement;const ps=par?(par.tagName.toLowerCase()+(typeof par.className==="string"&&par.className?"."+par.className.trim().split(/\s+/)[0]:"")):"";
  out.push({fs:+fs.toFixed(2),sel:ps+" > "+sel,txt:n.nodeValue.trim().slice(0,16),dis,where:label})}
 return out}
})()'''
R = {"contrast": {}, "fonts": []}
async def inj(pg): await pg.evaluate(JS)
async def cx(pg, key, sel):
    await inj(pg); R["contrast"][key] = await pg.evaluate(f'__cx(document.querySelector({json.dumps(sel)}))')
async def scan(pg, label):
    await inj(pg); R["fonts"] += await pg.evaluate(f'__minfs({json.dumps(label)})')
async def shot(pg, name, **kw):
    if SHOT: await pg.screenshot(path=SHOT + name, **kw)
async def tabgo(pg, t):
    await pg.evaluate(f'document.querySelector("nav.tabs button[data-tab={t}]").click()'); await pg.wait_for_timeout(700)
async def home(pg):
    await tabgo(pg, "plan")
    if await pg.query_selector('[data-home]'): await pg.click('[data-home]'); await pg.wait_for_timeout(700)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await newctx(b, tz="Asia/Taipei")
        # ---- 回顧（11/24 台灣 14:21）
        pg = await phone(ctx, twt(11, 24, 14, 21), "zhang", "rv", init=seed({**META, **RVDB}), url=BASE, wait=1200)
        await home(pg); await scan(pg, "首頁 11/24 14:21")
        await pg.click('#review[data-story-open]'); await pg.wait_for_timeout(900)
        n = await pg.evaluate('document.querySelectorAll(".story .st-page").length')
        for i in range(n):
            cls = await pg.evaluate(f'document.querySelectorAll(".story .st-page")[{i}].className')
            await scan(pg, f"回顧第 {i+1} 頁 {cls}")
            if "pg-open" in cls:
                await cx(pg, "X5 封面「點右邊看下一頁」", '.st-page.pg-open p.st-cap'); await shot(pg, 'x5_cover.png')
            if "pg-mood" in cls:
                await cx(pg, "X5（連帶）心情頁說明", '.st-page.pg-mood p.st-cap')
            if "pg-vs" in cls:
                await pg.clock.run_for(2500); await pg.wait_for_timeout(300)
                await cx(pg, "X3 角色卡 阿彰 標籤", '.pg-vs .vs-p:nth-child(1) .vh')
                await cx(pg, "X3 角色卡 星星 標籤", '.pg-vs .vs-p:nth-child(2) .vh')
                await shot(pg, 'x3_vs.png')
            if i < n - 1: await pg.click('.st-tap.next'); await pg.clock.run_for(1500); await pg.wait_for_timeout(300)
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
        await home(pg); await pg.click('.tile[data-day="7"]'); await pg.wait_for_timeout(800)
        await pg.evaluate('scrollTo(0,document.body.scrollHeight)'); await pg.wait_for_timeout(300)
        await scan(pg, "第 8 天行程頁（含回顧小卡）")
        await pg.close()
        # ---- 旅途中（11/19 日本 20:00）
        ctx2 = await newctx(b, tz="Asia/Tokyo")
        pg = await phone(ctx2, jst(11, 19, 20, 0), "zhang", "trip", init=seed({**META, **RVDB}), url=BASE, wait=1200)
        await home(pg); await scan(pg, "首頁 旅途中")
        await pg.click('[data-cal]'); await pg.wait_for_timeout(700)
        await cx(pg, "X4 iPhone 卡 說明（small）", '.sm-opt.main small')
        await cx(pg, "X4 iPhone 卡「重要：」（em）", '.sm-opt.main em')
        await cx(pg, "X4 iPhone 卡 標題（b，參考）", '.sm-opt.main b')
        await scan(pg, "行事曆面板"); await shot(pg, 'x4_cal.png')
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
        await pg.click('.tile[data-day="2"]'); await pg.wait_for_timeout(800); await scan(pg, "第 3 天行程頁")
        for t in ["wx", "move", "acct", "list"]:
            await tabgo(pg, t); await scan(pg, f"分頁 {t}")
        await tabgo(pg, "acct")
        if await pg.query_selector('[data-wallet-open]'):
            await pg.click('[data-wallet-open] >> nth=0'); await pg.wait_for_timeout(700); await scan(pg, "錢包面板"); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
        await pg.click('[data-exp-new]'); await pg.wait_for_timeout(700); await scan(pg, "記一筆面板"); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
        await home(pg)
        if await pg.query_selector('[data-sos]'):
            await pg.click('[data-sos] >> nth=0'); await pg.wait_for_timeout(700); await scan(pg, "求助面板"); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
        await pg.close()
        # ---- 出發前（台灣 11/10）＋行李，各寬度
        ctx3 = await newctx(b, tz="Asia/Taipei")
        for w in [320, 375, 390, 430]:
            pg = await phone(ctx3, twt(11, 10, 20, 0), "zhang", f"pre{w}", init=seed({}) if w == 320 else "", url=BASE, wait=2500)
            await pg.set_viewport_size({"width": w, "height": 844}); await pg.wait_for_timeout(300)
            await home(pg)
            if w == 390: await scan(pg, "首頁 出發前")
            await tabgo(pg, "list")
            await cx(pg, f"X6 清單頁行李卡 進度數字 {w}", '.pack-sum .pe-row small')
            hs = await pg.evaluate('document.documentElement.scrollWidth>innerWidth')
            rows = await pg.evaluate('[...document.querySelectorAll(".pack-sum .pe-row")].map(r=>Math.round(r.getBoundingClientRect().height))')
            R.setdefault("x6", {})[f"清單頁 {w}"] = {"hscroll": hs, "rowH": rows}
            await scan(pg, f"清單頁 {w}"); await shot(pg, f'x6_list_{w}.png')
            await pg.click('[data-pack-open]'); await pg.wait_for_timeout(700)
            hs = await pg.evaluate('document.documentElement.scrollWidth>innerWidth')
            rows = await pg.evaluate('[...document.querySelectorAll(".pack-sum .pe-row")].map(r=>Math.round(r.getBoundingClientRect().height))')
            R["x6"][f"行李頁 {w}"] = {"hscroll": hs, "rowH": rows}
            await cx(pg, f"X6 行李頁 進度數字 {w}", '.pack-sum .pe-row small')
            await scan(pg, f"行李頁 {w}"); await shot(pg, f'x6_pack_{w}.png')
            await pg.close()
        await b.close()
    json.dump(R, open(f'/tmp/x36_{TAG}.json', 'w'), ensure_ascii=False, indent=1)
    c = R["contrast"]
    for k, v in c.items(): print(k, v and (v["ratio"], v["fg"], v["bg"], v["fs"], v["fw"], v["img"]))
    small = {}
    for f in R["fonts"]:
        if f["fs"] < 12 and not f["dis"]: small.setdefault((f["fs"], f["sel"]), set()).add(f["where"].split(" ")[0] + "｜" + f["txt"])
    print("MIN visible font:", min(f["fs"] for f in R["fonts"] if not f["dis"]))
    for (fs, sel), w in sorted(small.items()): print(fs, sel, "｜", list(w)[:3])
    print("X6", R.get("x6"))
asyncio.run(main())
