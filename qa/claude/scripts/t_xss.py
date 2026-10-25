# XSS／跳脫：雲端資料與輸入欄位含 HTML、script、引號
import asyncio, json, qa_common as q
from playwright.async_api import async_playwright
B="trips/"+q.CODE
X='<img src=x onerror="window.__xss=(window.__xss||0)+1">"\'&<script>window.__xss=99</script>'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        db={f"{B}/expenses/x1":{"amt":6000,"cat":"food","who":"star","split":"both","pay":"cash","day":"11/19","note":X,"ts":1,"tf":True},
            f"{B}/items/x2":{"group":"buy","title":X,"place":X,"what":X,"note":"","due":"","order":1},
            f"{B}/items/x3":{"group":"prep","title":X,"note":X,"due":"11/19 13:00","order":1},
            f"{B}/items/x4":{"group":"pack","title":X,"note":X,"cat":"etc","order":1},
            f"{B}/moods/11-19_star":{"score":4,"note":X,"who":"star","day":"11/19","ts":1},
            f"{B}/settings/sos":{"ins":X,"insTel":X+"0800","order":X,"guest":X,"payNote":X},
            f"{B}/settings/meta":{"itemsSeeded":True,"itemsRestore":2}}
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,19,12,0),init=q.seed(db)); await pg.wait_for_timeout(800)
        visited=[]
        async def step(name,js):
            try: await pg.evaluate(js); await pg.wait_for_timeout(300); visited.append(name)
            except Exception as e: visited.append(name+" ERR "+str(e)[:60])
        await step("home",'document.querySelector("nav.tabs button[data-tab=plan]").click()')
        await step("acct",'document.querySelector("nav.tabs button[data-tab=acct]").click()')
        await step("list",'document.querySelector("nav.tabs button[data-tab=list]").click()')
        await step("pack",'document.querySelector("[data-pack-open]").click()')
        await step("day3",'tab="plan";view="day";dayIdx=2;render()')
        await step("day1 stay",'tab="plan";view="day";dayIdx=0;render()')
        await step("sos emg",'openSos();document.querySelector("[data-sos-tab=emg]").click()')
        await step("sos edit",'document.querySelector(".sos [data-sos-edit]")?.click()')
        await step("story",'document.querySelector(".sheet-modal")?.remove();openStory()')
        x1=await pg.evaluate('window.__xss||0')
        q.rec("XSS","雲端資料含 HTML／script：所有頁面都跳脫、沒有執行",x1==0,{"__xss":x1,"visited":visited,"errs":pg.errs[:3]})
        tel=await pg.evaluate('[...document.querySelectorAll("a[href^=tel]")].map(a=>a.getAttribute("href")).slice(-2)')
        q.note("XSS","旅平險電話含奇怪字元時的 tel: 連結",tel)
        await ctx.close()
        # 輸入欄位
        ctx=await q.mkctx(b); pg=await q.page(ctx,q.jst(11,19,12,0)); 
        await q.tab(pg,"acct"); await pg.fill('#f-amt','100'); await pg.fill('#f-note',X[:40]); await pg.click('#f-save'); await pg.wait_for_timeout(300)
        await q.tab(pg,"list"); await pg.click('[data-item-new="prep"]'); await pg.fill('.chk-form input[name=title]',X[:40]); await pg.fill('.chk-form input[name=note]',X[:60]); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(300)
        await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(300)
        await pg.click('#mood .fbtn[data-score="3"]'); await pg.fill('#mood-note',X); await pg.click('#mood-form .primary'); await pg.wait_for_timeout(300)
        await q.home(pg); await q.tab(pg,"acct"); await q.tab(pg,"list")
        x2=await pg.evaluate('window.__xss||0'); shown=await pg.evaluate('document.querySelector("[data-group-id=prep]").innerText.includes("<img")')
        q.rec("XSS","輸入欄位輸入 HTML 後原樣顯示文字、不執行",x2==0 and shown,{"__xss":x2,"顯示原文":shown})
        # 超長文字、emoji、只有空白
        await pg.click('[data-item-new="prep"]'); await pg.fill('.chk-form input[name=title]','   '); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(200)
        still=await pg.evaluate('!!document.querySelector(".chk-form")')
        q.rec("輸入邊界","待辦名稱只有空白：不新增、停在表單",still)
        await pg.click('[data-item-cancel]')
        L="很長"*300
        await pg.click('[data-item-new="buy"]'); await pg.fill('.chk-form input[name=title]',L); v=await pg.input_value('.chk-form input[name=title]')
        q.note("輸入邊界","名稱欄位上限（maxlength）",len(v))
        await pg.fill('.chk-form input[name=title]','🍙🦐🍡 天むす 👩‍👩‍👧‍👦'); await pg.fill('.chk-form input[name=place]','名古屋駅 エスカ'); await pg.click('.chk-form .primary'); await pg.wait_for_timeout(300)
        ok=await pg.evaluate('document.querySelector("[data-group-id=buy]").innerText.includes("👩‍👩‍👧‍👦")')
        q.rec("輸入邊界","emoji（含 ZWJ 家庭）與日文正常存取顯示",ok)
        await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(300)
        await pg.click('#mood [data-mood-edit]'); await pg.fill('#mood-note',"長"*600); v=await pg.input_value('#mood-note')
        q.note("輸入邊界","心情 600 字輸入後實際長度（maxlength）",len(v))
        await ctx.close()
        q.dump("xss")
        await b.close()
asyncio.run(main())
