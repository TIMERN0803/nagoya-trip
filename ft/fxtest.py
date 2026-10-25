# 匯率自動更新測試
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
ER={"result":"success","rates":{"TWD":0.207301}}
CA={"date":"2026-10-24","jpy":{"twd":0.20776891}}
async def ctx_with(b,er=ER,ca=CA,er_fail=False,ca_fail=False,cnt=None):
    ctx=await b.new_context(viewport={'width':390,'height':844},timezone_id="Asia/Tokyo")
    await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
    async def h_er(r):
        if cnt is not None:cnt["er"]=cnt.get("er",0)+1
        await (r.abort() if er_fail else r.fulfill(body=json.dumps(er),content_type="application/json",headers={"access-control-allow-origin":"*"}))
    async def h_ca(r):
        if cnt is not None:cnt["ca"]=cnt.get("ca",0)+1
        await (r.abort() if ca_fail else r.fulfill(body=json.dumps(ca),content_type="application/json",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/open.er-api.com/**",h_er);await ctx.route("**/currency-api*/**",h_ca)
    return ctx
async def acct(pg):
    await pg.click('nav.tabs button[data-tab="acct"]');await pg.wait_for_timeout(300)
async def settle(pg):await pg.clock.run_for(3000);await pg.wait_for_timeout(700)
def cloud(pg,code):return pg.evaluate(f'JSON.parse(localStorage.getItem("mockdb")||"{{}}")["trips/{code}/settings/rate"]||null')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        cnt={}
        ctx=await ctx_with(b,cnt=cnt)
        a=await ft.newpage(b,ft.jst(11,20,20,0),code="neko-fx",ctx=ctx);await settle(a);await acct(a)
        ft.rec("F 匯率","打開後自動抓到匯率 0.2073",await a.input_value('#f-rate')=="0.2073")
        c=await cloud(a,"neko-fx")
        ft.rec("F 匯率","寫進雲端（含來源、自動）",c and c["jpyTwd"]==0.2073 and c["auto"] is True and c["src"]=="ExchangeRate-API",c)
        t=await a.inner_text('.rate-note')
        ft.rec("F 匯率","顯示「自動更新」和更新時間、資料來源","自動更新・11/20" in t and "ExchangeRate-API" in t,t)
        s=await ft.newpage(b,ft.jst(11,20,20,0),code="neko-fx",me="star",ctx=ctx);await s.wait_for_timeout(500);await acct(s)
        ft.rec("F 匯率","星星的手機也是同一個匯率",await s.input_value('#f-rate')=="0.2073")
        n0=cnt.get("er",0);await s.clock.run_for(3000);await s.wait_for_timeout(500)
        ft.rec("F 匯率","6 小時內不會重複抓",cnt.get("er",0)==n0,cnt)
        await a.fill('#f-rate','0.21');await a.press('#f-rate','Tab');await a.wait_for_timeout(500)
        c=await cloud(a,"neko-fx");t=await a.inner_text('.rate-note')
        ft.rec("F 匯率","手動改匯率：停止自動、顯示「改回自動」",c["jpyTwd"]==0.21 and c["auto"] is False and "手動設定" in t and await a.query_selector('[data-rate-auto]'),(c,t))
        await s.wait_for_timeout(500)
        ft.rec("F 匯率","手動設定同步到星星的手機","手動設定" in await s.inner_text('.rate-note') and await s.input_value('#f-rate')=="0.21")
        await a.clock.run_for(7*3600*1000);await a.wait_for_timeout(500)
        ft.rec("F 匯率","手動設定後過了 7 小時也不會被自動蓋掉",(await cloud(a,"neko-fx"))["jpyTwd"]==0.21)
        await acct(a);await a.click('[data-rate-auto]');await a.wait_for_timeout(800)
        c=await cloud(a,"neko-fx")
        ft.rec("F 匯率","按「改回自動」立刻重抓",c["jpyTwd"]==0.2073 and c["auto"] is True and await a.input_value('#f-rate')=="0.2073",c)
        ft.rec("F 匯率","台幣換算跟著新匯率",f"NT$" in await a.inner_text('#acct-sum'))
        errs=a.errs+s.errs;await ctx.close()
        # 主來源失敗 → 備用
        ctx=await ctx_with(b,er_fail=True)
        q=await ft.newpage(b,ft.jst(11,20,20,0),code="neko-fx2",ctx=ctx);await settle(q);await acct(q)
        ft.rec("F 匯率","主來源失敗時改用備用來源",await q.input_value('#f-rate')=="0.2078" and "currency-api" in await q.inner_text('.rate-note'))
        errs+=[e for e in q.errs if "Failed to fetch" not in e];await ctx.close()
        # 兩個都失敗 → 沿用
        ctx=await ctx_with(b,er_fail=True,ca_fail=True)
        q=await ft.newpage(b,ft.jst(11,20,20,0),code="neko-fx3",ctx=ctx);await settle(q);await acct(q)
        ft.rec("F 匯率","兩個來源都失敗時沿用原本的 0.2",await q.input_value('#f-rate')=="0.2" and "等待連線" in await q.inner_text('.rate-note'))
        errs+=[e for e in q.errs if "Failed to fetch" not in e];await ctx.close()
        # 異常值不採用
        ctx=await ctx_with(b,er={"result":"success","rates":{"TWD":21.5}},ca={"jpy":{"twd":0}})
        q=await ft.newpage(b,ft.jst(11,20,20,0),code="neko-fx4",ctx=ctx);await settle(q);await acct(q)
        ft.rec("F 匯率","API 回傳不合理的數字時不採用",await q.input_value('#f-rate')=="0.2")
        errs+=q.errs;await ctx.close()
        ft.rec("F 匯率","沒有錯誤",not errs,errs[:3])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
if __name__=="__main__":asyncio.run(main())
