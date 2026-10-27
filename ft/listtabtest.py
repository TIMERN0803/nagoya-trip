# 清單頁籤：待辦／要買的兩個頁籤，行李維持上方卡片；只有頁籤固定在最上方
# 首頁入口：待辦小圓角 → 待辦、要買的小圓角和「要買的」格子 → 要買的、到期提醒 → 待辦並標出那一項
import asyncio
import fulltest as ft
from playwright.async_api import async_playwright
OUT='/home/claude/build/'
SEL='document.querySelector(".ltab[aria-selected=true]")?.dataset.listTab'
async def to_list(pg):
    await pg.click('nav.tabs button[data-tab="list"]');await pg.wait_for_timeout(400)
async def to_home(pg):
    await pg.click('nav.tabs button[data-tab="plan"]');await pg.wait_for_timeout(300)
    if not await pg.query_selector('.hero'):await pg.click('[data-home]');await pg.wait_for_timeout(300)
    await pg.evaluate('scrollTo(0,0)')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # 版面與切換
        pg=await ft.newpage(b,ft.jst(10,26,20,50));await pg.wait_for_timeout(600)
        await to_list(pg)
        lay=await pg.evaluate('''(()=>{const st=document.querySelector(".stack.lt-top .pack-entry"),t=document.querySelector(".ltab-strip"),p=document.getElementById("lt-panel");return {pack:!!st,order:st&&t?!!(st.compareDocumentPosition(t)&Node.DOCUMENT_POSITION_FOLLOWING):false,tabs:[...document.querySelectorAll(".ltab")].map(x=>x.dataset.listTab),role:document.querySelector(".ltabs").getAttribute("role"),groups:[...p.querySelectorAll("[data-group-id]")].map(x=>x.dataset.groupId)}})()''')
        ft.rec("清單頁籤","行李卡片在最上方、頁籤在它下面",lay['pack'] and lay['order'],lay)
        ft.rec("清單頁籤","只有待辦、要買的兩個頁籤",lay['tabs']==["prep","buy"] and lay['role']=="tablist",lay)
        ft.rec("清單頁籤","預設是待辦，只顯示待辦清單",await pg.evaluate(SEL)=="prep" and lay['groups']==["prep"],lay)
        await pg.click('[data-list-tab="buy"]');await pg.wait_for_timeout(300)
        g=await pg.evaluate('[...document.querySelectorAll("#lt-panel [data-group-id]")].map(x=>x.dataset.groupId)')
        ft.rec("清單頁籤","點要買的：只顯示要買的、免稅提醒還在",await pg.evaluate(SEL)=="buy" and g==["buy"] and await pg.query_selector('#lt-panel .tf-tip'),g)
        sty=await pg.evaluate('(()=>{const on=getComputedStyle(document.querySelector(".ltab[aria-selected=true]")),off=getComputedStyle(document.querySelector(".ltab[aria-selected=false]"));return {bg:on.backgroundColor,c:on.color,offbg:off.backgroundColor,h:document.querySelector(".ltab").getBoundingClientRect().height,icon:document.querySelectorAll(".ltab svg").length}})()')
        ft.rec("清單頁籤","樣式和緊急資訊頁籤一致：選中焦糖棕底白字、未選透明",sty['bg']=="rgb(148, 102, 69)" and sty['c']=="rgb(255, 255, 255)" and sty['offbg'] in ("rgba(0, 0, 0, 0)","transparent"),sty)
        ft.rec("清單頁籤","頁籤有圖示、高度至少 44",sty['icon']==2 and sty['h']>=44,sty)
        # 頁籤上的數字會跟著勾選更新
        await pg.click('[data-list-tab="prep"]');await pg.wait_for_timeout(300)
        c0=await pg.inner_text('#lt-prep small')
        cid=await pg.evaluate('document.querySelector("#lt-panel .chk input:not(:checked)").id')
        await pg.check('#'+cid);await pg.wait_for_timeout(400)
        c1=await pg.inner_text('#lt-prep small')
        ft.rec("清單頁籤","勾一項後待辦頁籤的數字加一",int(c1.split("/")[0])==int(c0.split("/")[0])+1 and c1.split("/")[1]==c0.split("/")[1],[c0,c1])
        # 記住上次的頁籤：切到別的分頁再回來、重新整理
        await pg.click('[data-list-tab="buy"]');await pg.wait_for_timeout(300)
        await pg.click('nav.tabs button[data-tab="acct"]');await pg.wait_for_timeout(300);await to_list(pg)
        ft.rec("清單頁籤","切到記帳再回清單，停在要買的",await pg.evaluate(SEL)=="buy")
        await pg.reload();await pg.wait_for_timeout(900);await to_list(pg)
        ft.rec("清單頁籤","重新打開 App 也記得要買的",await pg.evaluate(SEL)=="buy")
        # 鍵盤
        await pg.focus('#lt-buy');await pg.keyboard.press('ArrowLeft');await pg.wait_for_timeout(300)
        k=await pg.evaluate('[document.querySelector(".ltab[aria-selected=true]").dataset.listTab,document.activeElement.id]')
        ft.rec("清單頁籤","鍵盤左右鍵切換、焦點跟著到新頁籤",k==["prep","lt-prep"],k)
        await pg.keyboard.press('End');await pg.wait_for_timeout(300)
        ft.rec("清單頁籤","End 到最後一個頁籤",await pg.evaluate(SEL)=="buy")
        # 行李卡片：點進行李頁、返回後頁籤不變
        await pg.click('[data-pack-open]');await pg.wait_for_timeout(700)
        ft.rec("清單頁籤","點行李卡片進入原本的行李頁",await pg.query_selector('.pk-bar [data-pack-close]') and not await pg.query_selector('.ltab-strip'))
        await pg.click('[data-pack-close]');await pg.wait_for_timeout(400)
        ft.rec("清單頁籤","從行李頁返回，還是要買的頁籤",await pg.evaluate(SEL)=="buy" and await pg.query_selector('.pack-entry'))
        # 只有頁籤固定：要買的加到很多項後往下捲
        for i in range(8):
            await pg.click('[data-item-new="buy"]');await pg.wait_for_timeout(150)
            await pg.fill('.chk-form input[name=title]',f'伴手禮 {i+1}');await pg.keyboard.press('Enter');await pg.wait_for_timeout(200)
        await pg.evaluate('scrollTo(0,0)');await pg.wait_for_timeout(100)
        await pg.mouse.move(195,500);await pg.mouse.wheel(0,900);await pg.wait_for_timeout(500)
        st=await pg.evaluate('(()=>{const t=document.querySelector(".ltab-strip");return {tab:Math.round(t.getBoundingClientRect().top),bar:Math.round(document.querySelector("header.bar").getBoundingClientRect().top),pack:Math.round(document.querySelector(".pack-entry").getBoundingClientRect().bottom),shade:t.classList.contains("shade"),y:scrollY}})()')
        ft.rec("清單頁籤","往下捲：頁籤固定在最上方、有陰影",st['tab']==0 and st['shade'],st)
        ft.rec("清單頁籤","往下捲：標題和行李卡片會捲走，不固定",st['bar']<0 and st['pack']<=0,st)
        hit=await pg.evaluate('(()=>{const r=document.querySelector("#lt-prep").getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest(".ltab")?.id})()')
        ft.rec("清單頁籤","固定時頁籤沒有被內容蓋住、點得到",hit=="lt-prep",hit)
        await pg.click('#lt-prep');await pg.wait_for_timeout(400)
        ft.rec("清單頁籤","固定時切換頁籤，換成待辦",await pg.evaluate(SEL)=="prep")
        await pg.mouse.wheel(0,-3000);await pg.wait_for_timeout(400)
        ft.rec("清單頁籤","捲回最上面陰影消失",not await pg.evaluate('document.querySelector(".ltab-strip").classList.contains("shade")'))
        await pg.screenshot(path=OUT+'list_tabs.png')
        ft.rec("清單頁籤","沒有 JS 錯誤",not pg.errs,pg.errs[:2])
        await ft.close(pg)
        # 首頁入口 → 對應頁籤
        pg=await ft.newpage(b,ft.jst(10,26,20,50));await pg.wait_for_timeout(600)
        await to_list(pg);await pg.click('[data-list-tab="buy"]');await pg.wait_for_timeout(200)
        await to_home(pg);await pg.click('.hp-todo');await pg.wait_for_timeout(400)
        t=await pg.evaluate('document.querySelector("nav.tabs button[aria-selected=true]").dataset.tab')
        ft.rec("首頁入口","待辦小圓角 → 清單的待辦頁籤（上次停在要買的也一樣）",t=="list" and await pg.evaluate(SEL)=="prep" and await pg.evaluate('scrollY')==0,t)
        await to_home(pg);await pg.click('.hp-buy');await pg.wait_for_timeout(400)
        ft.rec("首頁入口","要買的小圓角 → 要買的頁籤",await pg.evaluate(SEL)=="buy" and await pg.evaluate('scrollY')==0)
        await to_list(pg);await pg.click('[data-list-tab="prep"]');await pg.wait_for_timeout(200)
        await to_home(pg)
        tile=await pg.query_selector('.grid .tile[data-go-group="buy"]')
        ft.rec("首頁入口","地點格子最後的「要買的」改成帶到要買的頁籤",bool(tile))
        if tile:
            await tile.scroll_into_view_if_needed();await tile.click();await pg.wait_for_timeout(400)
            ft.rec("首頁入口","點「要買的」格子 → 要買的頁籤、從頂端開始",await pg.evaluate(SEL)=="buy" and await pg.evaluate('scrollY')==0)
        ft.rec("首頁入口","沒有 JS 錯誤",not pg.errs,pg.errs[:2])
        await ft.close(pg)
        # 到期提醒 → 待辦頁籤並標出那一項（就算上次停在要買的）
        pg=await ft.newpage(b,ft.jst(11,22,10));await pg.wait_for_timeout(600)
        await to_list(pg);await pg.click('[data-list-tab="buy"]');await pg.wait_for_timeout(200)
        await to_home(pg)
        await pg.click('.da-main[data-go-item="seat2"]');await pg.wait_for_timeout(900)
        info=await pg.evaluate('(()=>{const r=document.getElementById("c-seat2")?.closest(".chk-row");return r?{sel:document.querySelector(".ltab[aria-selected=true]").dataset.listTab,ping:r.classList.contains("ping"),top:Math.round(r.getBoundingClientRect().top),strip:Math.round(document.querySelector(".ltab-strip").getBoundingClientRect().bottom)}:null})()')
        ft.rec("首頁入口","到期提醒 → 待辦頁籤，那一項有標示、沒被頁籤擋住",bool(info) and info['sel']=="prep" and info['ping'] and info['top']>=info['strip'] and info['top']<700,info)
        ft.rec("首頁入口","到期提醒：沒有 JS 錯誤",not pg.errs,pg.errs[:2])
        await ft.close(pg)
        # 320 寬度
        ctx=await b.new_context(viewport={'width':320,'height':568},timezone_id="Asia/Tokyo")
        await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
        for u in ["**/api.open-meteo.com/**","**/open.er-api.com/**","**/currency-api*/**","**/fonts.googleapis.com/**"]: await ctx.route(u,lambda r:r.abort())
        pg=await ft.newpage(b,ft.jst(10,26,20,50),ctx=ctx);await pg.wait_for_timeout(600)
        await to_list(pg)
        w=await pg.evaluate('(()=>{const t=[...document.querySelectorAll(".ltab")];return {sw:document.documentElement.scrollWidth,iw:innerWidth,clip:t.some(x=>x.scrollWidth>x.clientWidth+1)}})()')
        ft.rec("清單頁籤","320 寬度：沒有水平捲動、頁籤文字沒被裁掉",w['sw']<=w['iw'] and not w['clip'],w)
        await ctx.close()
        await b.close()
asyncio.run(main())
