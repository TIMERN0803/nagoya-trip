import asyncio,json
from pathlib import Path
import independent as ind
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch();await ind.layout(b);await b.close()
 (ind.OUT/'layout-complete.json').write_text(json.dumps({'results':ind.RESULT,'data':ind.DATA},ensure_ascii=False,indent=2),encoding='utf8')
asyncio.run(main())
