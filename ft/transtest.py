# 換頁與彈窗轉場（溫柔版：換頁 0.5 秒、換天 0.45 秒、彈窗滑上 0.5 秒（不回彈）、滑下 0.25 秒）：往深一層整頁從右推入（舊頁往左退）、返回舊頁往右滑走、底部分頁切換不播、記帳分成清單頁和「記一筆」填寫面板、換天左右翻頁、全部不淡入淡出；同步重畫不播；彈窗關閉有退場動畫且一定會移除；
# 退場中的面板點不到、不擋下一個面板；減少動態時直接移除；轉場只動 opacity／transform；滑入時沒有橫向捲軸
# 一律用假資料庫（synctest.mkctx 的攔截）
import asyncio
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
rec = ft.rec
B, META, seed, opn, tab = S.B, S.META, S.seed, S.opn, S.tab
cls = 'document.querySelector("#app .view").className'
props = '''(()=>{const a=document.querySelector("#app .view").getAnimations()[0];if(!a)return [];return [...new Set(a.effect.getKeyframes().flatMap(k=>Object.keys(k).filter(x=>!["offset","easing","composite","computedOffset"].includes(x))))]})()'''

async def pages(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('.g-home .grid .tile[data-day="2"]'); c = await pg.evaluate(cls)
    rec("換頁", "首頁點某一天：從右邊滑進（go-fwd）", "go-fwd" in c, c)
    rec("換頁", "轉場只動 transform（不淡入淡出）", await pg.evaluate(props) == ["transform"], await pg.evaluate(props))
    sw = await pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
    rec("換頁", "滑入過程中沒有橫向捲軸", sw)
    o = await pg.evaluate('(()=>{const L=document.querySelector(".vt-old");return L?{n:document.querySelectorAll(".vt-old").length,hid:L.getAttribute("aria-hidden"),inert:L.querySelector(".view").inert,pe:getComputedStyle(L).pointerEvents,anim:getComputedStyle(L.querySelector(".view")).animationName,inApp:!!document.querySelector("#app .vt-old")}:null})()')
    rec("換頁", "推入時舊頁暫留在下層往左退（不能點、對輔助技術隱藏、不在 #app 裡）", o and o["n"] == 1 and o["hid"] == "true" and o["inert"] and o["pe"] == "none" and o["anim"] == "vpushOut" and not o["inApp"], o)
    rec("換頁", "推入時新頁不透明、蓋住舊頁", await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).backgroundColor!=="rgba(0, 0, 0, 0)"'))
    await pg.wait_for_timeout(700)
    rec("換頁", "轉場結束舊頁移除、新頁恢復一般版面", await pg.evaluate('!document.querySelector(".vt-old")&&!document.querySelector(".view.vt-in")&&!document.querySelector(".shell.vt")'))
    await pg.click('[data-home]'); c = await pg.evaluate(cls)
    rec("換頁", "當天行程按返回：從左邊滑進（go-back）", "go-back" in c, c)
    rec("換頁", "返回時舊頁在上層往右滑走", await pg.evaluate('getComputedStyle(document.querySelector(".vt-old.go-back>.view")).animationName') == "vbackOut")
    await pg.wait_for_timeout(700)
    await pg.click('nav.tabs button[data-tab="wx"]'); c = await pg.evaluate(cls)
    rec("換頁", "切底部分頁：不播動畫、不留舊頁", await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).animationName') == "none" and not await pg.evaluate('!!document.querySelector(".vt-old")'), c)
    await pg.wait_for_timeout(400)
    await pg.click('nav.tabs button[data-tab="list"]'); await pg.wait_for_timeout(300)
    await pg.evaluate('listSub="pack";render()'); c = await pg.evaluate(cls)
    rec("換頁", "清單進行李頁：從右邊滑進", "go-fwd" in c, c)
    await pg.wait_for_timeout(700)
    await pg.evaluate('render(true)'); c = await pg.evaluate(cls)
    rec("換頁", "同步資料進來重畫（keep）：不播轉場", "go-" not in c and await pg.evaluate('document.querySelector("#app .view").style.animationName==="none"||document.querySelector("#app .view").style.animation.includes("none")'), c)
    await pg.evaluate('render()'); c = await pg.evaluate(cls)
    rec("換頁", "同一頁重畫：不播動畫", "go-" not in c and await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).animationName') == "none", c)
    # 從當天行程按底部「行程」回首頁：是切分頁，不播
    await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(700)
    await pg.click('nav.tabs button[data-tab="plan"]')
    rec("換頁", "當天行程按底部「行程」回首頁：直接換、不滑動", not await pg.evaluate('!!document.querySelector(".vt-old")') and await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).animationName') == "none")
    # 點「行程」後再點一天：照樣推入（切分頁的旗標不會殘留）
    await pg.click('nav.tabs button[data-tab="plan"]'); await pg.wait_for_timeout(200)
    await pg.click('.g-home .grid .tile[data-day="3"]')
    rec("換頁", "同一分頁再點一下後點某天：照樣推入", "go-fwd" in await pg.evaluate(cls))
    await pg.wait_for_timeout(700)
    # 連續快速換頁：最多只暫留一頁，結束後全部清掉
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(700)
    for i in range(4):
        await pg.evaluate(f'view="day";dayIdx={i};render();view="home";render()')
    n = await pg.evaluate('document.querySelectorAll(".vt-old").length')
    await pg.wait_for_timeout(750)
    rec("換頁", "連續快速換頁：畫面上最多兩頁、結束後清乾淨", n <= 1 and await pg.evaluate('!document.querySelector(".vt-old")&&document.querySelectorAll("#app .view").length===1'), n)
    # 推入中同步資料進來重畫：新頁仍不透明，舊頁照樣收掉
    await pg.evaluate('view="day";dayIdx=1;render();render(true)')
    rec("換頁", "推入中同步重畫：新頁仍蓋住舊頁", await pg.evaluate('!!document.querySelector("#app .view.vt-in")'))
    await pg.wait_for_timeout(750)
    rec("換頁", "之後舊頁和暫時樣式都移除", await pg.evaluate('!document.querySelector(".vt-old")&&!document.querySelector(".view.vt-in")'))
    # 轉場結束後 .view 沒有殘留位移（sticky、固定元素位置正常）
    await pg.wait_for_timeout(100)
    rec("換頁", "轉場結束後沒有殘留 transform", await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).transform') == "none")
    rec("換頁", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def sheets(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    for nm, op, x, sel in [("求助", 'openSos()', '.sheet-modal .sm-x', '.sheet-modal'), ("錢包", 'openWallet()', '.sheet-modal .sm-x', '.sheet-modal'),
                           ("地圖", 'openViewer("ghibli-map.jpg","x")', '.viewer .vclose', '.viewer'), ("給司機看", 'sosShow("hotel")', '.sos-show .sm-x', '.sos-show')]:
        await pg.evaluate(op); await pg.wait_for_timeout(300)
        await pg.click(x)
        st = await pg.evaluate(f'(()=>{{const v=document.querySelector("{sel}");return v?{{leaving:v.classList.contains("leaving"),role:v.getAttribute("role"),pe:getComputedStyle(v).pointerEvents,anim:getComputedStyle(v).animationName}}:null}})()')
        rec("彈窗關閉", f"{nm}：按關閉後往下滑走（背景遮罩漸淡、內容不淡出）", st and st["leaving"] and st["anim"] in ("dimout", "sheetdown"), st)
        rec("彈窗關閉", f"{nm}：退場中不再是對話框、點不到", st and st["role"] is None and st["pe"] == "none", st)
        await pg.clock.run_for(300); await pg.wait_for_timeout(100)
        rec("彈窗關閉", f"{nm}：退場後一定移除", await pg.evaluate(f'document.querySelectorAll("{sel}").length') == 0)
    # 底部面板：卡片整片從下方滑上來
    await pg.evaluate('openSos()')
    rec("彈窗打開", "底部面板從下方滑上來（不回彈）、背景遮罩漸暗", await pg.evaluate('getComputedStyle(document.querySelector(".sheet-modal .sm-card")).animationName') == "sheetin" and await pg.evaluate('getComputedStyle(document.querySelector(".sheet-modal")).animationName') == "dimin")
    await pg.keyboard.press("Escape"); await pg.clock.run_for(300); await pg.wait_for_timeout(350)
    await pg.evaluate('openViewer("ghibli-map.jpg","x")')
    rec("彈窗打開", "全螢幕的也從下方滑上來（不淡入）", await pg.evaluate('getComputedStyle(document.querySelector(".viewer")).animationName') == "sheetin")
    await pg.keyboard.press("Escape"); await pg.clock.run_for(300); await pg.wait_for_timeout(350)
    # 底部面板：卡片往下滑
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(350); await pg.click('.sheet-modal .sm-x')
    rec("彈窗關閉", "底部面板的卡片往下滑", await pg.evaluate('getComputedStyle(document.querySelector(".sheet-modal.leaving .sm-card")).animationName') == "sheetdown")
    # 退場中立刻再開：新的面板正常可用，舊的不會被點到
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(50)
    n = await pg.evaluate('document.querySelectorAll(".sheet-modal:not(.leaving)").length')
    await pg.evaluate('document.querySelector(".sheet-modal.leaving .sm-x").click()')
    rec("彈窗關閉", "退場中馬上再打開：新面板正常、點退場中的舊面板沒反應", n == 1 and await pg.evaluate('modals.length') == 1 and await pg.evaluate('!!document.querySelector(".sheet-modal:not(.leaving)")'))
    await pg.keyboard.press("Escape"); await pg.clock.run_for(300); await pg.wait_for_timeout(350)
    rec("彈窗關閉", "Esc 關閉後全部移除、捲動恢復", await pg.evaluate('document.querySelectorAll(".sheet-modal").length===0&&document.body.style.overflow===""'))
    # 焦點回到打開它的按鈕（退場不影響）
    await pg.click('.hud-sos'); await pg.wait_for_timeout(350); await pg.keyboard.press("Escape"); await pg.wait_for_timeout(350)
    rec("彈窗關閉", "關閉時焦點馬上回到原本的按鈕", await pg.evaluate('!!document.activeElement?.closest(".hud-sos")'))
    rec("彈窗關閉", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def acct(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('nav.tabs button[data-tab="acct"]'); await pg.wait_for_timeout(400)
    st = await pg.evaluate('({form:!!document.getElementById("f-amt"),fab:!!document.querySelector(".acct-fab:not([disabled])"),y:scrollY,list:!!document.getElementById("acct-list")})')
    rec("記帳", "點記帳分頁：只顯示清單（沒有填寫表單）、有「記一筆」按鈕、停在頂端", not st["form"] and st["fab"] and st["list"] and st["y"] == 0, st)
    # 打開「記一筆」：從下方滑上來、輕輕彈一下，金額有焦點（跳出數字鍵盤）
    await pg.click('[data-exp-new]')
    an = await pg.evaluate('getComputedStyle(document.querySelector(".exp-sheet .sm-card")).animationName')
    await pg.wait_for_timeout(650)
    st = await pg.evaluate('({t:document.getElementById("exp-title").innerText,f:document.activeElement?.id,role:document.querySelector(".exp-sheet").getAttribute("role"),again:!!document.querySelector("[data-again]")})')
    rec("記帳", "「記一筆」面板從下方滑上來（不回彈）", an == "sheetin", an)
    rec("記帳", "面板標題「記一筆」、金額有焦點、有「再記一筆」", st["t"] == "記一筆" and st["f"] == "f-amt" and st["role"] == "dialog" and st["again"], st)
    # 再記一筆：面板不關、金額清空、付款方式留著
    await pg.click('[data-pick="pay"] [data-v="card"]'); await pg.fill('#f-amt', '1200'); await pg.fill('#f-note', '鰻魚飯')
    await pg.click('[data-again]'); await pg.wait_for_timeout(300)
    st = await pg.evaluate('({open:!!document.querySelector(".exp-sheet:not(.leaving)"),amt:document.getElementById("f-amt").value,note:document.getElementById("f-note").value,pay:draft.pay,msg:document.getElementById("f-msg").innerText,f:document.activeElement?.id})')
    rec("記帳", "再記一筆：面板不關、清空金額和備註、付款方式留著、焦點回到金額", st["open"] and st["amt"] == "" and st["note"] == "" and st["pay"] == "card" and "已記下 ¥1,200" in st["msg"] and st["f"] == "f-amt", st)
    # 記下這筆：面板滑下關閉，記帳頁顯示已記下、新的那筆亮一下
    await pg.fill('#f-amt', '800'); await pg.click('#f-save')
    lv = await pg.evaluate('(()=>{const v=document.querySelector(".exp-sheet.leaving");return v?getComputedStyle(v.querySelector(".sm-card")).animationName:null})()')
    await pg.wait_for_timeout(500)
    st = await pg.evaluate('({open:!!document.querySelector(".exp-sheet"),note:document.getElementById("acct-note").innerText,ping:!!document.querySelector(".ex.ping"),n:document.querySelectorAll(".ex[data-edit]").length})')
    rec("記帳", "記下這筆：面板滑下去關閉", lv == "sheetdown" and not st["open"], [lv, st])
    rec("記帳", "記帳頁顯示「已記下」、新的那筆亮一下", "已記下 ¥800" in st["note"] and st["ping"] and st["n"] == 2, st)
    # 沒填東西：按 × 直接關，不問
    await pg.click('[data-exp-new]'); await pg.wait_for_timeout(650); await pg.click('[data-exp-x]'); await pg.wait_for_timeout(80)  # 退場 0.25 秒中檢查
    rec("記帳", "沒填東西按 ×：直接關，不問", not await pg.is_visible('.exp-confirm') and await pg.query_selector('.exp-sheet.leaving'))
    await pg.wait_for_timeout(400)
    # 修改：點一筆打開「修改這筆」，有刪除；改了金額按 × 會問；Esc 也會問
    await pg.click('.ex[data-edit] >> nth=0'); await pg.wait_for_timeout(650)
    st = await pg.evaluate('({t:document.getElementById("exp-title").innerText,del:!!document.querySelector("[data-exp-del]"),again:!!document.querySelector("[data-again]"),save:document.getElementById("f-save").innerText})')
    rec("記帳", "點一筆：打開「修改這筆」，底部是刪除＋更新（沒有再記一筆）", st["t"] == "修改這筆" and st["del"] and not st["again"] and "更新" in st["save"], st)
    before = {k: v for k, v in (await S.cloud(pg)).items() if "/expenses/" in k}
    await pg.fill('#f-amt', '999'); await pg.click('[data-exp-x]'); await pg.wait_for_timeout(350)
    st = await pg.evaluate('({cf:!document.querySelector(".exp-confirm").hidden,txt:document.querySelector(".exp-confirm").innerText,f:document.activeElement?.hasAttribute("data-exp-keep")})')
    rec("記帳", "改了沒存按 ×：問「要放棄嗎？」，焦點在「繼續填寫」", st["cf"] and "放棄" in st["txt"] and st["f"], st)
    await pg.click('[data-exp-keep]'); await pg.wait_for_timeout(150)
    rec("記帳", "按「繼續填寫」：回到面板、內容還在", await pg.evaluate('document.querySelector(".exp-confirm").hidden&&document.getElementById("f-amt").value==="999"'))
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(350)
    rec("記帳", "改了沒存按 Esc：也先問，不直接關", await pg.evaluate('!document.querySelector(".exp-confirm").hidden&&!!document.querySelector(".exp-sheet:not(.leaving)")'))
    await pg.click('[data-exp-discard]'); await pg.wait_for_timeout(500)
    after = {k: v for k, v in (await S.cloud(pg)).items() if "/expenses/" in k}
    rec("記帳", "放棄修改：面板關閉、雲端不變", not await pg.query_selector('.exp-sheet') and before == after and await pg.evaluate('editingId===null'))
    # 點背景：沒填東西直接關
    await pg.click('[data-exp-new]'); await pg.wait_for_timeout(650); await pg.mouse.click(200, 20); await pg.wait_for_timeout(400)
    rec("記帳", "沒填東西點背景：直接關", not await pg.query_selector('.exp-sheet'))
    # 面板開著時同步重畫：面板不會被換掉
    await pg.click('[data-exp-new]'); await pg.wait_for_timeout(650); await pg.fill('#f-amt', '321')
    await pg.evaluate('window.__sh=document.querySelector(".exp-sheet");render(true)')
    rec("記帳", "面板開著時頁面重畫：面板和輸入都還在", await pg.evaluate('window.__sh===document.querySelector(".exp-sheet")&&document.getElementById("f-amt").value==="321"'))
    await S.expclose(pg)
    # 沒有記帳權限：「記一筆」停用並寫出原因
    await pg.evaluate('canWrite=false;render(true)')
    st = await pg.evaluate('({dis:document.querySelector(".acct-fab").disabled,note:document.getElementById("acct-note").innerText,hid:document.getElementById("acct-note").hidden})')
    rec("記帳", "沒有記帳權限：「記一筆」停用並寫出原因", st["dis"] and "沒有記帳權限" in st["note"] and not st["hid"], st)
    await pg.evaluate('canWrite=true;render(true)')
    # 換到別的分頁再回來：已記下的提示清掉
    await pg.click('nav.tabs button[data-tab="wx"]'); await pg.click('nav.tabs button[data-tab="acct"]'); await pg.wait_for_timeout(200)
    rec("記帳", "換分頁回來：已記下的提示清掉", await pg.evaluate('document.getElementById("acct-note").hidden'))
    rec("記帳", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def days(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await pg.evaluate('tab="plan";view="day";dayIdx=2;render()'); await pg.wait_for_timeout(700)
    await pg.click('.day-btn[data-day="3"]')
    g = await pg.evaluate('(()=>{const g=document.querySelector(".day-ghost");if(!g)return null;const ka=document.getElementById("dayBody").getAnimations().flatMap(a=>a.effect.getKeyframes().flatMap(k=>Object.keys(k))).filter(x=>!["offset","easing","composite","computedOffset"].includes(x));return {inert:g.inert,hid:g.getAttribute("aria-hidden"),ids:g.querySelectorAll("[id]").length+(g.id?1:0),props:[...new Set(ka)],one:document.querySelectorAll("#dayBody").length}})()')
    rec("換天", "舊內容往旁邊滑走、新內容同時滑進（只動 transform、不淡入淡出）", g and g["props"] == ["transform"], g)
    gap = await pg.evaluate('document.getElementById("dayBody").getAnimations().map(a=>JSON.stringify(a.effect.getKeyframes())).join("")')
    rec("換天", "新舊兩頁中間留 24px 空隙（不會黏在一起）", "24px" in gap, gap[:120])
    rec("換天", "滑動只在內容寬度裡（不滑進左右留白，iOS 才不會留殘影）", await pg.evaluate('getComputedStyle(document.getElementById("dayBody").parentElement).overflowX') == "clip")
    rec("換天", "滑走的舊內容不能點、沒有重複 id", g and g["inert"] and g["hid"] == "true" and g["ids"] == 0 and g["one"] == 1, g)
    for d in (4, 5, 6): await pg.click(f'.day-btn[data-day="{d}"]')
    n = await pg.evaluate('document.querySelectorAll(".day-ghost").length')
    await pg.wait_for_timeout(750)
    rec("換天", "連點換天：最多一個舊內容、結束後清乾淨", n <= 1 and await pg.evaluate('document.querySelectorAll(".day-ghost").length') == 0, n)
    rec("換天", "結束後拿掉裁切（sticky 和陰影照常）", await pg.evaluate('document.getElementById("dayBody").parentElement.style.overflowX') == "")
    # iOS Safari 的 animation.finished 有時不觸發：模擬動畫卡住（暫停、finished 永遠不 resolve），舊內容也要在時間到後移除，不留殘影
    await pg.click('.day-btn[data-day="2"]')
    await pg.evaluate('document.querySelectorAll(".day-ghost").forEach(g=>g.getAnimations().forEach(a=>a.pause()))')
    stuck = await pg.evaluate('document.querySelectorAll(".day-ghost").length')
    await pg.wait_for_timeout(700)
    rec("換天", "動畫卡住（finished 不觸發）時，舊內容仍在 0.53 秒後移除、不留殘影", stuck == 1 and await pg.evaluate('document.querySelectorAll(".day-ghost").length') == 0, stuck)
    await pg.click('.day-btn[data-day="6"]'); await pg.wait_for_timeout(750)
    rec("換天", "最後顯示的是點的那一天", "11/23" in await pg.evaluate('document.getElementById("dayBody").innerText') or await pg.evaluate('dayIdx') == 6, await pg.evaluate('dayIdx'))
    rec("換天", "沒有橫向捲軸", await pg.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    rec("換天", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def micro(b):
    """彈一下只留給剛完成一件事的小東西：打勾、裝好行李、記好一筆、行李全部裝好"""
    pg = await ft.newpage(b, ft.jst(11, 10, 12)); ctx = pg.ctx  # 有預設清單和行李項目
    await pg.click('nav.tabs button[data-tab="list"]'); await pg.wait_for_timeout(300)
    cid = await pg.evaluate('document.querySelector(".chk input[type=checkbox]:not(:checked)")?.id')
    await pg.check('#' + cid); await pg.wait_for_timeout(60)
    st = await pg.evaluate(f'({{me:document.getElementById("{cid}").classList.contains("pop"),an:getComputedStyle(document.getElementById("{cid}")).animationName,others:[...document.querySelectorAll(".chk input.pop")].length}})')
    rec("小回饋", "清單打勾：剛勾的框「啵」一下，其他框不動", st["me"] and st["an"] == "tickpop" and st["others"] == 1, st)
    await pg.uncheck('#' + cid); await pg.wait_for_timeout(60)
    rec("小回饋", "取消打勾不彈", not await pg.evaluate(f'document.getElementById("{cid}").classList.contains("pop")'))
    # 行李：剩最後一項
    await pg.click('[data-pack-open]'); await pg.wait_for_timeout(750)
    # 先把自己的行李除了第一項都裝好（照 App 的方式寫進資料庫，同步重畫後也一樣）
    last = await pg.evaluate('(()=>{const rows=itemsOf("pack");rows.forEach((r,i)=>{const k=packKey(r.id,me);done[k]=i>0;put("checks/"+k,{done:i>0})});render(true);return rows[0].id})()')
    await pg.wait_for_timeout(300); other = await pg.evaluate('itemsOf("pack")[1].id')
    await pg.click(f'[data-pack="{other}"][data-who="zhang"]'); await pg.wait_for_timeout(60)
    await pg.click(f'[data-pack="{other}"][data-who="zhang"]'); await pg.wait_for_timeout(60)
    rec("小回饋", "還沒全部裝好：行李箱不跳", not await pg.evaluate('!!document.querySelector(".pack-sum .pe-art.yay")'))
    await pg.click(f'[data-pack="{last}"][data-who="zhang"]'); await pg.wait_for_timeout(60)
    st = await pg.evaluate(f'({{btn:getComputedStyle(document.querySelector(\'[data-pack="{last}"][data-who="zhang"]\')).animationName,art:document.querySelector(".pack-sum .pe-art.yay")?getComputedStyle(document.querySelector(".pack-sum .pe-art")).animationName:null}})')
    rec("小回饋", "裝好行李：按鈕「啵」一下", st["btn"] == "tickpop", st)
    rec("小回饋", "最後一項裝好：行李箱和貓咪跳一下", st["art"] == "hop", st)
    await pg.wait_for_timeout(1400)
    rec("小回饋", "跳完拿掉 class（之後重畫不會再跳）", not await pg.evaluate('!!document.querySelector(".pop,.yay")'))
    await pg.evaluate('render(true)'); await pg.wait_for_timeout(60)
    rec("小回饋", "已經都裝好、同步重畫：不會再跳", not await pg.evaluate('!!document.querySelector(".yay")'))
    # 自己都裝好時，每次進到清單或行李頁都跳一下
    await pg.click('.pk-bar [data-pack-close]'); await pg.wait_for_timeout(100)
    rec("小回饋", "都裝好後回到清單：行李卡片上的行李箱和貓咪跳一下", await pg.evaluate('(()=>{const a=document.querySelector("#app .pack-entry .pe-art");return a&&a.classList.contains("yay")?getComputedStyle(a).animationName:null})()') == "hop")
    await pg.wait_for_timeout(1500)
    await pg.click('#app [data-pack-open]'); await pg.wait_for_timeout(200)
    early = await pg.evaluate('!!document.querySelector("#app .pack-sum .pe-art.yay")')
    await pg.wait_for_timeout(400)
    rec("小回饋", "都裝好後進行李頁：等頁面滑進來再跳", not early and await pg.evaluate('!!document.querySelector("#app .pack-sum .pe-art.yay")'), early)
    await pg.wait_for_timeout(1500)
    # 別人還沒裝完不影響：條件是「自己」都裝好
    await pg.evaluate('(()=>{const r=itemsOf("pack")[0];const k=packKey(r.id,"star");done[k]=false;put("checks/"+k,{done:false})})()'); await pg.wait_for_timeout(300)
    await pg.click('.pk-bar [data-pack-close]'); await pg.wait_for_timeout(100)
    rec("小回饋", "只看自己：星星還沒裝完，阿彰都裝好也會跳", await pg.evaluate('!!document.querySelector("#app .pack-entry .pe-art.yay")'))
    await pg.wait_for_timeout(1500)
    # 自己還沒裝完：進來不跳
    await pg.evaluate('(()=>{const r=itemsOf("pack")[0];const k=packKey(r.id,me);done[k]=false;put("checks/"+k,{done:false})})()'); await pg.wait_for_timeout(300)
    await pg.click('nav.tabs button[data-tab="plan"]'); await pg.wait_for_timeout(200); await pg.click('nav.tabs button[data-tab="list"]'); await pg.wait_for_timeout(100)
    rec("小回饋", "自己還沒裝完：進清單不跳", not await pg.evaluate('!!document.querySelector(".yay")'))
    rec("小回饋", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()
    # 記帳：新的那筆從上方落下
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await pg.click('nav.tabs button[data-tab="acct"]'); await pg.wait_for_timeout(300)
    await S.expopen(pg); await pg.fill('#f-amt', '500'); await pg.click('#f-save'); await pg.wait_for_timeout(150)
    an = await pg.evaluate('(()=>{const r=document.querySelector(".ex.ping");return r?getComputedStyle(r).animationName:null})()')
    rec("小回饋", "記下這筆：新的那筆從上方輕輕落下、彈一下就定位（加上亮一下）", an and "exdrop" in an and "rowping" in an, an)
    await ctx.close()

async def reduced(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.emulate_media(reduced_motion="reduce")
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('.g-home .grid .tile[data-day="2"]')
    rec("減少動態", "換頁不暫留舊頁", not await pg.evaluate('!!document.querySelector(".vt-old")'))
    rec("減少動態", "換頁不播動畫", await pg.evaluate('getComputedStyle(document.querySelector("#app .view")).animationName') == "none")
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(350); await pg.click('.sheet-modal .sm-x')
    rec("減少動態", "彈窗關閉直接移除", await pg.evaluate('document.querySelectorAll(".sheet-modal").length') == 0)
    await ctx.close()

async def narrow(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 10, 12), init=seed(META))
    await pg.set_viewport_size({"width": 320, "height": 640})
    await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(300)
    await pg.click('.g-home .grid .tile[data-day="1"]')
    w = []
    for i in range(6):
        w.append(await pg.evaluate('document.documentElement.scrollWidth-innerWidth')); await pg.wait_for_timeout(40)
    rec("換頁", "320 寬：滑入的每一刻都沒有橫向捲軸", max(w) <= 0, w)
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in [pages, sheets, acct, days, micro, reduced, narrow]:
            try: await f(b)
            except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
        await b.close()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
