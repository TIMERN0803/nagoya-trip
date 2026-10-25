import asyncio,json,time
from pathlib import Path
import fulltest as ft
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parents[3]/'outputs'/'advanced';OUT.mkdir(parents=True,exist_ok=True)
R=[]
def rec(n,c,d=None):R.append({'name':n,'pass':bool(c),'details':d});print(json.dumps(R[-1],ensure_ascii=False),flush=True)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch();a=await ft.newpage(b,ft.jst(11,18,20));c=await ft.newpage(b,ft.jst(11,18,20),ctx=a.ctx)
  await a.click('[data-tab="list"]');await c.click('[data-tab="list"]')
  before=await a.evaluate('itemsOf("buy").length');ids=await a.evaluate('itemsOf("buy").map(x=>x.id).reverse()')
  await c.click('[data-item-new="buy"]');await c.fill('.chk-form input[name=title]','concurrent-added')
  await asyncio.gather(a.evaluate('ids=>applyOrder("buy",ids,true)',ids),c.click('.chk-form .primary'));await a.wait_for_timeout(200)
  rows=await a.evaluate('itemsOf("buy").map(x=>({id:x.id,title:x.title,order:x.order}))');rec('sort_during_remote_add_no_loss',len(rows)==before+1 and any(x['title']=='concurrent-added' for x in rows),rows)
  # Switch tabs during the undo window and restore the most recently deleted item.
  id=await a.locator('[data-group-id="buy"] [data-item-edit]').first.get_attribute('data-item-edit');await a.locator('[data-item-edit="'+id+'"]').click();await a.click('[data-item-del="'+id+'"]');await a.click('[data-tab="acct"]');await a.locator('.undo-bar button').click();await a.wait_for_timeout(100)
  rec('undo_after_tab_switch',await a.evaluate('(id)=>!!JSON.parse(localStorage.mockdb)["trips/neko-test/items/"+id]',id))
  await a.ctx.close()
  # Many mood edits: same mock context, identities intentionally changed in-process.
  g=await ft.newpage(b,ft.jst(11,26,12));t=time.perf_counter()
  await g.evaluate('''async()=>{for(let round=0;round<3;round++)for(let d=17;d<=24;d++)for(let who of ['zhang','star']){me=who;await saveMood('11/'+d,1+(d+round)%5,'edit-'+round+'-'+who)}}''')
  docs=await g.evaluate('Object.entries(JSON.parse(localStorage.mockdb)).filter(([k])=>k.includes("/moods/")).map(([k,v])=>v)')
  rec('mood_48_edits_16_final_documents',len(docs)==16 and all(x['note'].startswith('edit-2-') for x in docs),{'documents':len(docs),'ms':round((time.perf_counter()-t)*1000,2)})
  await g.evaluate('document.querySelector("[data-tab=plan]").click()')
  if await g.locator('[data-home]').count():await g.click('[data-home]')
  t=time.perf_counter();await g.click('[data-story-open]');await g.wait_for_timeout(100);rec('many_moods_review_opens',await g.locator('.story').count()==1,{'ms':round((time.perf_counter()-t)*1000,2),'pages':await g.locator('.st-page').count()});await ft.close(g)
  await b.close()
 (OUT/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2),encoding='utf8')
asyncio.run(main())
