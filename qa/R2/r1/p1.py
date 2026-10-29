import asyncio,json,sys
sys.path.insert(0,'/home/claude/build/ft');import os;os.chdir('/home/claude/build/ft')
import fulltest as ft
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    g=await ft.newpage(b,ft.twt(10,25,18),tz='Asia/Taipei')
    for fn in ['openSos','openWallet','openCalSheet','openSetup']:
      await g.evaluate(fn+'()');await g.wait_for_timeout(600)
      await g.keyboard.press('Escape');n0=await g.locator('.sheet-modal').count();lv=await g.locator('.sheet-modal.leaving, .sheet-modal .leaving').count()
      await g.wait_for_timeout(400);n1=await g.locator('.sheet-modal').count()
      print(fn,'right after Esc:',n0,'leaving:',lv,'after 400ms:',n1)
    await ft.close(g)
    mock={'trips/neko-test/settings/meta':{'itemsSeeded':True,'itemsRestore':2}}
    for group in ['prep','pack','buy']:
      for i in range(200):mock[f'trips/neko-test/items/{group}{i}']={'group':group,'title':f'{group}-{i}','note':'','cat':'etc','order':i,'due':''}
    g=await ft.newpage(b,ft.jst(11,18,20),init='localStorage.setItem("mockdb",'+json.dumps(json.dumps(mock))+');')
    await g.click('[data-tab="list"]');await g.wait_for_timeout(700)
    a=await g.locator('#lt-panel .chk-row').count();await g.click('[data-list-tab="buy"]');await g.wait_for_timeout(400);bb=await g.locator('#lt-panel .chk-row').count()
    await g.click('[data-pack-open]');n0=await g.locator('.chk-row').count();await g.wait_for_timeout(800);n1=await g.locator('.chk-row').count()
    print('prep tab',a,'buy tab',bb,'| pack right after click',n0,'after 800ms',n1)
    await b.close()
asyncio.run(main())
