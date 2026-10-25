import asyncio,inspect,json
from pathlib import Path
import fulltest as ft
from playwright.async_api import async_playwright
exec(inspect.getsource(ft.H_offline).replace('localhost:8766','localhost:8767'),ft.__dict__)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch();await ft.H_offline(b);await b.close()
 Path(__file__).resolve().parents[3].joinpath('outputs/baseline/offline-baseline.json').write_text(json.dumps(ft.R,ensure_ascii=False,indent=2),encoding='utf8')
asyncio.run(main())
