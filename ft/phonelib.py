# 「兩支手機」測試共用 helper（QA R2 修正階段：conflicttest／reloadtest／focustest 用）。一律假資料庫；旅程代碼 qa-r2-test。
# 同一個 context 兩個頁面像兩支手機：ngy:* 的 localStorage 依 window.__ns 分開（outbox、me、快取各自一份），mockdb／mocknet 共用。
import sys, asyncio, json
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import fulltest as ft
import synctest as S
from playwright.async_api import async_playwright
S.CODE = "qa-r2-test"; S.B = "trips/qa-r2-test"
S.META = {f"{S.B}/settings/meta": {"itemsSeeded": True, "itemsRestore": 2}}
B, META, FSO, seed, cloud, tab = S.B, S.META, S.FSO, S.seed, S.cloud, S.tab
rec, jst, twt = ft.rec, ft.jst, ft.twt
SHOTS = os.environ.get('SHOTS', '/home/claude/build/shots/')
os.makedirs(SHOTS, exist_ok=True)
# 讓一個 context 內的兩個頁面像兩支手機：ngy:* 的 localStorage 依 window.__ns 分開（outbox、me、快取各自一份），mockdb／mocknet 共用
NS = '''(()=>{const ns=%s;const g=Storage.prototype.getItem,s=Storage.prototype.setItem,r=Storage.prototype.removeItem;
const k=(o,x)=>(o===localStorage&&typeof x==="string"&&x.startsWith("ngy:"))?ns+"|"+x:x;
Storage.prototype.getItem=function(x){return g.call(this,k(this,x))};Storage.prototype.setItem=function(x,v){return s.call(this,k(this,x),v)};Storage.prototype.removeItem=function(x){return r.call(this,k(this,x))}})();'''
async def phone(ctx, t, me, ns, init="", pre="", wait=900, **kw):
    """另一支手機：me＝zhang／star；ns＝這支手機的名字"""
    init2 = init + (f'localStorage.setItem("ngy:me",{json.dumps(me)});' if me else '')
    return await S.opn(ctx, t, init=init2, pre=NS % json.dumps(ns) + pre, wait=wait, **kw)
async def exps(pg): return {k.split("/")[-1]: v for k, v in (await cloud(pg)).items() if "/expenses/" in k}
async def items_cloud(pg): return {k.split("/")[-1]: v for k, v in (await cloud(pg)).items() if "/items/" in k}
async def newctx(b, fs=FSO, **kw):
    return await S.mkctx(b, fs=fs, **kw)
def summary():
    bad = [r for r in ft.R if not r[2]]
    print("TOTAL", len(ft.R), "FAIL", len(bad))
