"""要買的：依地點分區＋誰要買的名字標籤（v77）
- 地點自動分區：PARCO、LACHIC、中日大樓、榮其他、高島屋／Gate Tower、名鐵 Sun Road、其他地點、地點還沒填
- 舊項目沒有 who 欄位 → 顯示星星；新增時預設是自己；可選星星／阿彰／一起；改誰只送 who
- 排序模式維持一整串，副標題帶名字；320 寬度不橫向捲動
截圖：/home/claude/build/bz_*.png
"""
import asyncio,json,sys
import fulltest as ft
from playwright.async_api import async_playwright
base="trips/neko-test"
# (id, 標題, 地點, 品項, who)
BUY=[("p1","jouetie","Nagoya PARCO 4F","黑色褲褲",None),
     ("l1","OVERRIDE","LACHIC ラシック 3F","毛毛耳罩",None),
     ("l2","Beams","LACHIH BEAMS 名古屋","",None),
     ("c1","Mont bell","中日大樓 2F","羽絨外套",None),
     ("t1","資生堂","ジェイアール名古屋タカシマヤ 3F","",None),
     ("t2","香氛類","JR 名古屋高島屋 gate tower 6F","Aíam、baum",None),
     ("o1","I18pro 手機殼","Big camera 名古屋","",None),
     ("n1","Dior","","打亮006",None),
     ("z1","RAGEBLUE","名古屋 PARCO","灰色或黑色寬褲","zhang"),
     ("w1","伴手禮","","","both")]
srv={}
for i,(k,t,pl,w,who) in enumerate(BUY):
    d={"group":"buy","title":t,"place":pl,"what":w,"note":"","order":1+i}
    if who:d["who"]=who
    srv[f"{base}/items/{k}"]=d
# 舊格式：備註裡的 📍 地點
srv[f"{base}/items/s1"]={"group":"buy","title":"大國藥妝","note":"📍榮","order":20}
srv[f"{base}/items/m1"]={"group":"buy","title":"妙香園","note":"📍名鐵 Sun Road 🍵常磐の昔","order":21}
srv[f"{base}/settings/meta"]={"itemsSeeded":True,"itemsRestore":2}
ZONES_JS='[...document.querySelectorAll("[data-group-id=buy] .zone")].map(z=>[z.dataset.zone,[...z.querySelectorAll(".chk input")].map(i=>i.id.slice(2))])'
async def ctxof(b,w=390):
    ctx=await b.new_context(viewport={'width':w,'height':844},device_scale_factor=2,timezone_id="Asia/Taipei")
    await ctx.route("**/firebasejs/**/firebase-app.js",lambda r:r.fulfill(body=ft.APP,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/firebasejs/**/firebase-firestore.js",lambda r:r.fulfill(body=ft.FS,content_type="text/javascript",headers={"access-control-allow-origin":"*"}))
    await ctx.route("**/api.open-meteo.com/**",lambda r:r.abort())
    return ctx
async def openbuy(b,me="zhang",w=390):
    ctx=await ctxof(b,w)
    pg=await ft.newpage(b,ft.twt(11,16,1),ctx=ctx,me=me,init=f'localStorage.setItem("mockdb",{json.dumps(json.dumps(srv))});localStorage.setItem("ngy:listTab","buy");')
    await pg.wait_for_timeout(800)
    await pg.click('.hp-buy');await pg.wait_for_timeout(800)
    return pg
db=lambda pg,k:pg.evaluate(f'JSON.parse(localStorage.getItem("mockdb"))["{base}/items/{k}"]')
async def main():
    shots="--shots" in sys.argv
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await openbuy(b)
        z=await pg.evaluate(ZONES_JS)
        want=[["parco",["p1","z1"]],["lachic",["l1","l2"]],["chunichi",["c1"]],["sakae",["s1"]],["taka",["t1","t2"]],["meitetsu",["m1"]],["other",["o1"]],["none",["n1","w1"]]]
        ft.rec("分區","依地點分區、照固定順序、區內照原本排序",z==want,z)
        hs=await pg.evaluate('[...document.querySelectorAll(".zone-h")].map(h=>h.innerText.replace(/\\s+/g," ").trim())')
        ft.rec("分區","區名帶商圈、各區已買數",hs[0]=="名古屋 PARCO 榮 0 / 2" and hs[4]=="JR 高島屋・Gate Tower 名古屋車站 0 / 2" and hs[-1]=="地點還沒填 0 / 2",hs)
        tot=await pg.evaluate('document.querySelector("[data-group-id=buy] h3 .prog").innerText')
        ft.rec("分區","整份清單總數不變",tot=="0 / 12",tot)
        tags=await pg.evaluate('Object.fromEntries([...document.querySelectorAll("[data-group-id=buy] .chk-row")].map(r=>[r.querySelector("input").id.slice(2),r.querySelector(".who-tag").innerText.trim()]))')
        ft.rec("名字","舊項目沒填誰 → 星星；有填照填",tags["p1"]=="星星" and tags["s1"]=="星星" and tags["z1"]=="阿彰" and tags["w1"]=="一起",tags)
        # 勾已買：區的數字跟著變
        await pg.click('label[for="c-t1"]');await pg.wait_for_timeout(300)
        h=await pg.evaluate('document.querySelector("[data-zone=taka] .zone-c").innerText')
        d=await db(pg,"t1")
        ft.rec("分區","勾已買後該區數字更新、項目資料不動",h=="1 / 2" and "who" not in d,[h,d])
        if shots:
            await pg.evaluate('scrollTo(0,document.querySelector("[data-group-id=buy]").offsetTop-60)');await pg.wait_for_timeout(200)
            await pg.screenshot(path='/home/claude/build/bz_list.png',full_page=False)
            await pg.screenshot(path='/home/claude/build/bz_full.png',full_page=True)
        # 新增：預設自己（阿彰）
        await pg.click('[data-item-new="buy"]');await pg.wait_for_timeout(300)
        sel=await pg.evaluate('document.querySelector(".chk-form input[name=who]:checked").value')
        ft.rec("名字","新增時預設是自己",sel=="zhang",sel)
        if shots:
            await pg.evaluate('document.querySelector(".chk.editing").scrollIntoView({block:"center"})');await pg.wait_for_timeout(200)
            await pg.screenshot(path='/home/claude/build/bz_form.png')
        await pg.fill('.chk-form input[name=title]','code:graphy');await pg.fill('[name=place]','名古屋PARCO 東館');await pg.fill('[name=what]','上衣');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
        alld=await pg.evaluate('JSON.parse(localStorage.getItem("mockdb"))')
        nk=[k for k,v in alld.items() if isinstance(v,dict) and v.get("title")=="code:graphy"]
        nd=alld[nk[0]] if nk else {}
        z=await pg.evaluate(ZONES_JS)
        ft.rec("名字","新增存 who＝阿彰，自動進 PARCO 區",nd.get("who")=="zhang" and any(k=="parco" and len(ids)==3 for k,ids in z),[nd,z[0]])
        # 編輯舊項目改成一起：只送 who
        await pg.click('[data-item-edit="s1"]');await pg.wait_for_timeout(300)
        sel=await pg.evaluate('document.querySelector(".chk-form input[name=who]:checked").value')
        ft.rec("名字","編輯舊項目時選的是星星",sel=="star",sel)
        await pg.click('.chk-form .who-pick label:has(input[value=both])');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
        d=await db(pg,"s1")
        tag=await pg.evaluate('document.querySelector("#c-s1").closest(".chk-row").querySelector(".who-tag").innerText.trim()')
        ft.rec("名字","改成一起只多存 who，舊備註格式照常拆",d.get("who")=="both" and tag=="一起",[d,tag])
        # 編輯沒改東西：不送 who
        await pg.click('[data-item-edit="p1"]');await pg.wait_for_timeout(300);await pg.click('.chk-form .primary');await pg.wait_for_timeout(400)
        d=await db(pg,"p1")
        ft.rec("名字","沒改東西就儲存不會寫入 who","who" not in d,d)
        # 鍵盤：方向鍵切換
        await pg.click('[data-item-edit="c1"]');await pg.wait_for_timeout(300)
        await pg.focus('.chk-form input[name=who]:checked');await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(100)
        sel=await pg.evaluate('document.querySelector(".chk-form input[name=who]:checked").value')
        hgt=await pg.evaluate('Math.round(document.querySelector(".who-pick .pick").getBoundingClientRect().height)')
        ft.rec("名字","選項可用方向鍵切換、高度至少 44",sel=="zhang" and hgt>=44,[sel,hgt])
        await pg.click('[data-item-cancel]');await pg.wait_for_timeout(300)
        # 手選分區
        await pg.click('[data-item-new="buy"]');await pg.wait_for_timeout(300)
        t0=await pg.evaluate('document.querySelector(".chk-form [name=zone] option[value=\'\']").textContent')
        await pg.fill('.chk-form input[name=title]','LAKOLE');await pg.fill('[name=place]','LACHIC 4F')
        t1=await pg.evaluate('document.querySelector(".chk-form [name=zone] option[value=\'\']").textContent')
        ft.rec("分區選單","預設自動，打地點時顯示會分到哪",t0=="自動：地點還沒填" and t1=="自動：LACHIC ラシック",[t0,t1])
        if shots:
            await pg.evaluate('document.querySelector(".chk.editing").scrollIntoView({block:"center"})');await pg.wait_for_timeout(200)
            await pg.screenshot(path='/home/claude/build/bz_zone.png')
        await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
        alld=await pg.evaluate('JSON.parse(localStorage.getItem("mockdb"))')
        lk=[k for k,v in alld.items() if isinstance(v,dict) and v.get("title")=="LAKOLE"][0].split("/")[-1]
        d=await db(pg,lk);z=dict(await pg.evaluate(ZONES_JS))
        ft.rec("分區選單","不選就存空白、照地點自動分",d.get("zone")=="" and lk in z["lachic"],[d.get("zone"),z["lachic"]])
        # 把 Big camera 手動改到高島屋
        await pg.click('[data-item-edit="o1"]');await pg.wait_for_timeout(300)
        await pg.select_option('.chk-form [name=zone]','taka');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
        d=await db(pg,"o1");z=dict(await pg.evaluate(ZONES_JS))
        ft.rec("分區選單","手選的分區優先、只送 zone，其他地點區沒了就不顯示",d.get("zone")=="taka" and "o1" in z["taka"] and "other" not in z and d.get("place")=="Big camera 名古屋",[d,list(z)])
        await pg.wait_for_timeout(800)  # 同一項 1 秒內連存會被當成連點
        await pg.click('[data-item-edit="o1"]');await pg.wait_for_timeout(300)
        v=await pg.evaluate('document.querySelector(".chk-form [name=zone]").value')
        await pg.select_option('.chk-form [name=zone]','');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
        d=await db(pg,"o1");z=dict(await pg.evaluate(ZONES_JS))
        ft.rec("分區選單","編輯時帶入手選的分區；改回自動就照地點",v=="taka" and d.get("zone")=="" and "o1" in z["other"],[v,d.get("zone"),z.get("other")])
        # 手選但地點沒填：照手選
        await pg.click('[data-item-edit="n1"]');await pg.wait_for_timeout(300)
        await pg.select_option('.chk-form [name=zone]','taka');await pg.click('.chk-form .primary');await pg.wait_for_timeout(500)
        z=dict(await pg.evaluate(ZONES_JS))
        ft.rec("分區選單","地點沒填也能手選分區","n1" in z["taka"] and "n1" not in z.get("none",[]),z)
        # 排序模式：一整串，副標題帶名字
        await pg.click('[data-sort-toggle="buy"]');await pg.wait_for_timeout(400)
        n=await pg.evaluate('[document.querySelectorAll(".sort-row").length,document.querySelectorAll(".zone").length,document.querySelector("[data-sort-id=z1] small").innerText]')
        ft.rec("排序","排序時是一整串、副標題帶名字",n[0]==14 and n[1]==0 and n[2].startswith("阿彰・"),n)
        await pg.click('[data-sort-toggle="buy"]');await pg.wait_for_timeout(300)
        ft.rec("分區","沒有錯誤",not pg.errs,pg.errs[:2])
        # 星星的手機：新增預設星星
        pg2=await openbuy(b,me="star")
        await pg2.click('[data-item-new="buy"]');await pg2.wait_for_timeout(300)
        sel=await pg2.evaluate('document.querySelector(".chk-form input[name=who]:checked").value')
        ft.rec("名字","星星的手機新增預設星星",sel=="star",sel)
        # 320 寬
        pg3=await openbuy(b,w=320)
        ov=await pg3.evaluate('document.documentElement.scrollWidth-innerWidth')
        await pg3.click('[data-item-new="buy"]');await pg3.wait_for_timeout(300)
        ov2=await pg3.evaluate('document.documentElement.scrollWidth-innerWidth')
        ft.rec("版面","320 寬度清單和表單都不橫向捲動",ov<=0 and ov2<=0,[ov,ov2])
        if shots:
            await pg3.evaluate('document.querySelector(".chk.editing").scrollIntoView({block:"center"})');await pg3.wait_for_timeout(200)
            await pg3.screenshot(path='/home/claude/build/bz_320.png')
        ft.rec("版面","沒有錯誤",not pg2.errs and not pg3.errs,(pg2.errs+pg3.errs)[:2])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print(f"\n{len(ft.R)-len(bad)}/{len(ft.R)} 通過")
if __name__=="__main__":asyncio.run(main())
