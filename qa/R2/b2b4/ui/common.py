import sys,asyncio,json
sys.path.insert(0,'/home/claude/build/ft')
import os
os.chdir('/home/claude/build/ft')
import fulltest as ft
import synctest as S
from synctest import mkctx,opn,seed
from playwright.async_api import async_playwright
OUT='/home/claude/qa-r2/work/ui/'
