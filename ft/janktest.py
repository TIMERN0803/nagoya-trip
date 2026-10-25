# 排序放開後不應抽動：放開後 0~400ms 內，被拖的那一列位置要穩定、其他列不能跑回原位再跳
import asyncio,json
import fulltest as ft
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await ft.newpage(b,ft.jst(11,10,20,0),tz="Asia/Taipei",code="neko-jank")
        await pg.evaluate('window.__writeDelay=180');
        await pg.evaluate('document.querySelector(".tabs [data-tab=list]").click()');await pg.wait_for_timeout(500)
        await pg.click('[data-sort-toggle=prep]');await pg.wait_for_timeout(300)
        await pg.evaluate('(()=>{const g=document.querySelector("[data-group-id=prep]");scrollTo(0,g.getBoundingClientRect().top+scrollY-70)})()');await pg.wait_for_timeout(200)
        ids=await pg.evaluate('[...document.querySelectorAll("[data-sort-id]")].map(x=>x.dataset.sortId)')
        mv=ids[-1]
        h=await pg.query_selector(f'[data-sort-id="{mv}"] .drag-h');bb=await h.bounding_box();x,y=bb['x']+22,bb['y']+22
        t0=(await (await pg.query_selector(f'[data-sort-id="{ids[0]}"]')).bounding_box())['y']
        me=(await (await pg.query_selector(f'[data-sort-id="{mv}"]')).bounding_box())['y']
        dy=t0+6-me
        await pg.mouse.move(x,y);await pg.mouse.down()
        for k in range(1,11):await pg.mouse.move(x,y+dy*k/10)
        await pg.wait_for_timeout(250)
        await pg.evaluate('''window._samples=[];const t=performance.now();(function f(){const r=[...document.querySelectorAll("[data-sort-id]")].map(e=>[e.dataset.sortId,Math.round(e.getBoundingClientRect().top)]);window._samples.push(r);if(performance.now()-t<1400)requestAnimationFrame(f)})()''')
        await pg.mouse.up();await pg.wait_for_timeout(1600)
        S=await pg.evaluate('window._samples')
        final={i:t for i,t in S[-1]}
        # 每個元素在每一格畫面裡的位置，和最後位置相差的最大值
        maxdev=0;worst=None;back=0
        prev=None
        for fr in S[1:]:
            pos=dict(fr)
            for i,t in fr:
                d=abs(t-final[i])
                if i!=mv and d>maxdev:maxdev,worst=d,i
            if prev is not None and abs(pos[mv]-final[mv])>abs(prev-final[mv])+1:back+=1
            prev=pos[mv]
        order=[i for i,_ in sorted(S[-1],key=lambda z:z[1])]
        orders=[]
        for fr in S[1:]:
            o=[i for i,_ in sorted(fr,key=lambda z:z[1])]
            if not orders or orders[-1]!=o:orders.append(o)
        ft.rec("J 排序抽動","放開後不會出現一半新一半舊的中間順序",len(orders)==1,orders)
        ft.rec("J 排序抽動","放開後順序正確",order==[mv]+ids[:-1],order)
        ft.rec("J 排序抽動","放開後其他列完全不動（偏移 ≤ 3px）",maxdev<=3,f"最大偏移 {maxdev}px（{worst}），共 {len(S)} 格畫面")
        ft.rec("J 排序抽動","被拖的那一列只朝新位置滑進去、不會來回",back==0,f"反向 {back} 次")
        ft.rec("J 排序抽動","沒有錯誤",not pg.errs,pg.errs[:2])
        await b.close()
    bad=[r for r in ft.R if not r[2]];print("TOTAL",len(ft.R),"FAIL",len(bad))
asyncio.run(main())
