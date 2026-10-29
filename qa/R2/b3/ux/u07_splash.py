# B5 開場動畫行為：點擊穿透、跳過、同一次使用重整不再播、減少動態；重跑 3 次看時間
from uxlib import *
SPL = '(()=>{const s=document.getElementById("splash");return s?{out:s.classList.contains("out"),op:+getComputedStyle(s).opacity,pe:getComputedStyle(s).pointerEvents}:null})()'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for rnd in range(3):
            ctx = await S.mkctx(b)
            pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.add_init_script('try{localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code","qa-r2-test")}catch(e){}')
            t0 = None
            await pg.goto("http://localhost:8766/", wait_until="commit")
            # 取樣 splash 存在時間
            gone = None
            for i in range(40):
                s = await pg.evaluate(SPL)
                if s is None and gone is None and i > 2: gone = i * 50; break
                await pg.wait_for_timeout(50)
            print(f"[{rnd}] 開場動畫約 {gone} ms 後移除（含載入時間）")
            await ctx.close()
        # 點擊穿透：動畫還在時點背後的求助
        ctx = await S.mkctx(b)
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script('try{localStorage.setItem("ngy:tour","1");localStorage.setItem("ngy:me","zhang");localStorage.setItem("ngy:code","qa-r2-test")}catch(e){}')
        await pg.goto("http://localhost:8766/"); await pg.wait_for_timeout(250)
        s = await pg.evaluate(SPL); print("250ms splash:", s)
        await pg.mouse.click(195, 60); await pg.wait_for_timeout(120)
        opened = await pg.query_selector('.sheet-modal') is not None
        print("點動畫上方（背後是求助／標題列區域）後有沒有開面板:", opened, "| splash:", await pg.evaluate(SPL))
        await pg.wait_for_timeout(500)
        rec("B5 開場", "點一下跳過時不會穿透點到背後", not opened, opened)
        await pg.reload(); await pg.wait_for_timeout(300)
        rec("B5 開場", "同一次使用中重新整理不再播", await pg.evaluate(SPL) is None, await pg.evaluate(SPL))
        rec("B5 開場", "沒有錯誤", not errs, errs[:2])
        await ctx.close()
        # 減少動態
        ctx = await b.new_context(viewport={'width':390,'height':844}, reduced_motion='reduce', service_workers='block')
        for pat in ["**/*.googleapis.com/**","**/firebasejs/**","**/api.open-meteo.com/**","**/open.er-api.com/**"]: await ctx.route(pat, lambda r: r.abort())
        pg = await ctx.new_page(); await pg.goto("http://localhost:8766/"); await pg.wait_for_timeout(200)
        print("減少動態 200ms splash:", await pg.evaluate(SPL))
        await pg.wait_for_timeout(1800); print("減少動態 2s splash:", await pg.evaluate(SPL))
        await ctx.close()
        await b.close()
    summary()
asyncio.run(main())
