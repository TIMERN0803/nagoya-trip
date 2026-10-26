# 第三批 3C 回歸測試：自己付現金但還沒設定錢包時，「已記下」後面有不擋路的「設定錢包」入口；
# 語音連點時，被 cancel() 中斷的上一句觸發 onerror，不會把正在播放的按鈕改成「再聽一次」
# 一律用假資料庫（synctest.mkctx 的攔截）；語音用替身，模擬真實瀏覽器 cancel() 後非同步觸發舊句子的 onerror
import asyncio
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
rec = ft.rec
B, META, seed, opn = S.B, S.META, S.seed, S.opn
async def exps(pg): return [v for k, v in (await S.cloud(pg)).items() if "/expenses/" in k]

async def wallet_hint(b):
    ctx = await S.mkctx(b); pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await pg.evaluate('tab="acct";render()'); await pg.wait_for_timeout(200)
    async def save(amt, note, pay="cash", who=None):
        if who: await pg.click(f'[data-pick="who"] [data-v="{who}"]')
        await pg.click(f'[data-pick="pay"] [data-v="{pay}"]')
        await pg.fill('#f-amt', amt); await pg.fill('#f-note', note); await pg.click('#f-save'); await pg.wait_for_timeout(250)
        return await pg.evaluate('({msg:document.getElementById("f-msg").innerText,hint:!!document.querySelector("#f-msg [data-wallet-open]")})')
    r = await save("1200", "拉麵")
    rec("錢包入口", "沒設定錢包時記自己的現金帳：已記下後面有「設定錢包」", "已記下 ¥1,200" in r["msg"] and r["hint"], r["msg"])
    rec("錢包入口", "帳照樣記下（不擋路）", any(e.get("note") == "拉麵" for e in await exps(pg)))
    r = await save("800", "刷卡的", pay="card")
    rec("錢包入口", "刷卡的帳不出現提示", not r["hint"], r["msg"])
    r = await save("500", "星星付現", pay="cash", who="star")
    rec("錢包入口", "別人付的現金帳不出現提示（只能設定自己的錢包）", not r["hint"], r["msg"])
    await pg.click('[data-pick="who"] [data-v="zhang"]')
    r = await save("300", "咖啡")
    await pg.click('#f-msg [data-wallet-open]'); await pg.wait_for_timeout(300)
    rec("錢包入口", "點「設定錢包」打開錢包、可以直接輸入", await pg.query_selector('.sheet-modal .ws .w-form input') is not None)
    await pg.fill('.ws .w-form input', '30000'); await pg.click('.ws .w-form .primary'); await pg.wait_for_timeout(250)
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)
    chip = await pg.inner_text('.wchip')
    rec("錢包入口", "設定後現金餘額馬上算得出來（30000−1200−300）", "¥28,500" in chip, chip)
    r = await save("400", "設定後的現金")
    rec("錢包入口", "設定好錢包後不再出現提示", not r["hint"] and "已記下" in r["msg"], r["msg"])
    rec("錢包入口", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

# 語音替身：speak 後 400ms 才播完；cancel() 會在 30ms 後讓「被中斷的那一句」觸發 onerror（Chrome／Safari 的實際行為）
STUB = '''(()=>{window._said=[];let cur=null;const ss={getVoices:()=>[{lang:"ja-JP",name:"Kyoko"}],
 speak:u=>{cur=u;window._said.push(u.text);u._t=setTimeout(()=>{if(cur===u){cur=null;u.onend&&u.onend()}},400)},
 cancel:()=>{const old=cur;cur=null;if(old){clearTimeout(old._t);setTimeout(()=>old.onerror&&old.onerror({error:"interrupted"}),30)}}};
 Object.defineProperty(window,"speechSynthesis",{value:ss,configurable:true});window.SpeechSynthesisUtterance=function(t){this.text=t}})();'''
async def voice(b):
    ctx = await S.mkctx(b); await ctx.add_init_script(STUB)
    pg = await opn(ctx, ft.jst(11, 19, 12), init=seed(META))
    await pg.evaluate('openSos()'); await pg.wait_for_timeout(250)
    await pg.click('.sos-quick .sq-main'); await pg.wait_for_timeout(250)
    for i in range(10): await pg.evaluate('document.querySelector(".sos-show [data-say]").click()')
    await pg.wait_for_timeout(150)
    lab = await pg.inner_text('.sos-show [data-say]'); n = len(await pg.evaluate('window._said'))
    rec("語音", "連點播放 10 次：被中斷的上一句不會把按鈕改成「再聽一次」", "播放中" in lab and n == 10, {"按鈕": lab, "播放次數": n})
    await pg.wait_for_timeout(500)
    rec("語音", "最後一句播完才顯示「再聽一次」", "再聽一次" in await pg.inner_text('.sos-show [data-say]'))
    await pg.click('.sos-show [data-say]'); await pg.wait_for_timeout(100)
    await pg.click('.sos-show .sm-x'); await pg.wait_for_timeout(100)
    await pg.click('.sos-quick .sq-main'); await pg.wait_for_timeout(100)
    rec("語音", "關掉再打開：新的放大畫面按鈕是「播放日文」，舊句子的事件不影響", "播放日文" in await pg.inner_text('.sos-show [data-say]'))
    rec("語音", "沒有錯誤", not pg.errs, pg.errs[:2])
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in [wallet_hint, voice]:
            try: await f(b)
            except Exception as e: rec("執行", f.__name__ + " 沒有例外", False, repr(e)[:300])
        await b.close()
    bad = [r for r in ft.R if not r[2]]; print("TOTAL", len(ft.R), "FAIL", len(bad))
if __name__ == "__main__": asyncio.run(main())
