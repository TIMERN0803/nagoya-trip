# 批 3 指定 5：換頁轉場（B1–B4）連點、換頁中途點別的；面板開關連點。只看行為（殘影／狀態一致／錯誤），不重做轉場時間對比
import random
from uxlib import *
STATE = '''(()=>({tab,view,dayIdx,views:app.querySelectorAll(":scope>.view").length,vtOld:document.querySelectorAll(".vt-old").length,vt:!!app.parentElement.classList.contains("vt"),ghost:document.querySelectorAll(".day-ghost").length,
 sel:document.querySelector("nav.tabs button[aria-selected=true]")?.dataset.tab,chip:[...document.querySelectorAll(".day-btn")].findIndex(c=>c.getAttribute("aria-selected")==="true"),
 dc:document.getElementById("dayCount")?.innerText||"",inert:!!app.querySelector(":scope>.view")?.inert,ox:document.querySelector("#dayBody")?.parentElement?.style.overflowX||"",sheets:document.querySelectorAll(".sheet-modal:not(.leaving),.exp-sheet:not(.leaving)").length,bodyOv:document.body.style.overflow}))()'''
async def sc(pg, sel, **kw):
    try: await pg.click(sel, force=True, timeout=800, **kw)
    except Exception as e: pass
async def main():
    random.seed(7)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for rnd in range(3):
            ctx = await S.mkctx(b)
            pg = await S.opn(ctx, jst(11, 19, 13), init=seed(META), wait=1200)
            # --- S1 首頁↔當天 中途點別的
            await pg.evaluate('tab="plan";view="home";render()'); await pg.wait_for_timeout(700)
            seqs = [('.tile[data-day="3"]', 150), ('[data-home]', 150), ('.tile[data-day="5"]', 100), ('nav.tabs button[data-tab=list]', 100), ('nav.tabs button[data-tab=plan]', 60), ('.tile[data-day="1"]', 200), ('[data-home]', 0)]
            for sel, d in seqs:
                try: await pg.click(sel, timeout=1500, force=True)
                except Exception as e: print("  click fail", sel, str(e)[:60])
                await pg.wait_for_timeout(d)
            await pg.wait_for_timeout(900)
            s = await pg.evaluate(STATE); print(f"[{rnd}] S1 結束:", s)
            rec("轉場連點", f"[{rnd}] 首頁↔當天中途連點：只剩 1 個 view、沒有殘影層、tab 選取一致", s["views"] == 1 and s["vtOld"] == 0 and not s["vt"] and s["sel"] == s["tab"] and not s["inert"], s)
            # --- S2 當天頁連點換天
            await pg.evaluate('tab="plan";view="day";dayIdx=0;render()'); await pg.wait_for_timeout(800)
            for i in range(25):
                k = random.randint(0, 7)
                try: await pg.click(f'.day-btn >> nth={k}', timeout=1500, force=True)
                except Exception as e: print("  chip fail", k, str(e)[:60])
                await pg.wait_for_timeout(random.choice([20, 40, 80, 150]))
            await pg.wait_for_timeout(900)
            s = await pg.evaluate(STATE); print(f"[{rnd}] S2 結束:", s)
            rec("轉場連點", f"[{rnd}] 連點換天 25 次：無殘影、chip 與內容同一天、overflow 還原", s["ghost"] == 0 and s["chip"] == s["dayIdx"] and f"第 {s['dayIdx']+1} 天" in s["dc"] and s["ox"] == "", s)
            body_day = await pg.evaluate('document.querySelector(".banner .when, #dayBody")?.innerText.slice(0,40)')
            await pg.screenshot(path=SHOTS + f'u06_after_chips_{rnd}.png')
            # --- S3 底部分頁連點
            for i in range(30):
                t = random.choice(["plan", "wx", "move", "acct", "list"])
                await pg.click(f'nav.tabs button[data-tab={t}]', force=True, timeout=1500); await pg.wait_for_timeout(random.choice([20, 50, 120]))
            await pg.wait_for_timeout(900)
            s = await pg.evaluate(STATE); print(f"[{rnd}] S3 結束:", s)
            rec("轉場連點", f"[{rnd}] 底部分頁連點 30 次：1 個 view、選取一致", s["views"] == 1 and s["sel"] == s["tab"] and s["vtOld"] == 0 and not s["vt"], s)
            # --- S4 面板開關連點
            await pg.evaluate('tab="acct";view="home";render()'); await pg.wait_for_timeout(700)
            for i in range(12):
                await sc(pg,'.wchip'); await pg.wait_for_timeout(random.choice([30, 90, 200]))
                if await pg.query_selector('.ws .sm-x'): await sc(pg,'.ws .sm-x')
                await pg.wait_for_timeout(random.choice([30, 90, 200]))
            for i in range(10):
                await sc(pg,'[data-exp-new]'); await pg.wait_for_timeout(random.choice([40, 120, 300]))
                if await pg.query_selector('.exp-sheet:not(.leaving) [data-exp-x]'): await sc(pg,'.exp-sheet:not(.leaving) [data-exp-x]')
                await pg.wait_for_timeout(random.choice([40, 120, 300]))
            await pg.wait_for_timeout(900)
            s = await pg.evaluate(STATE)
            allsheets = await pg.evaluate('document.querySelectorAll(".sheet-modal,.exp-sheet").length')
            print(f"[{rnd}] S4 結束:", s, "殘留面板節點:", allsheets)
            rec("轉場連點", f"[{rnd}] 面板開關連點：最後沒有殘留面板、body 可捲動", allsheets <= s["sheets"] and s["bodyOv"] == "", {**s, "nodes": allsheets})
            rec("轉場連點", f"[{rnd}] 沒有 JS 錯誤", not pg.errs, pg.errs[:3])
            await ctx.close()
        await b.close()
    summary()
asyncio.run(main())
