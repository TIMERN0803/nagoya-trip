# 天氣改以氣象廳為主（ngy-v72）：7 天內用氣象廳愛知縣預報（3 天內用愛知西部＋名古屋氣溫），更遠用 Open-Meteo 長期參考；
# 長期參考的「有雨」要看降雨機率；每列標可信度或長期參考；tenki.jp 各地點 10 天預報連結；氣象廳抓不到時退回長期參考
import asyncio, json, datetime as dt
from fulltest import newpage, jst, close, rec, R, APP, FS
from playwright.async_api import async_playwright
A = "天氣來源"
def om_body(codes, pops):
    days = [(dt.date(2026, 11, 8) + dt.timedelta(days=k)).isoformat() for k in range(17)]
    # 11/17 起依序帶入 codes／pops（index 9 起）
    wc = [3] * 17; pp = [20] * 17
    for i, (c, p) in enumerate(zip(codes, pops)): wc[9 + i] = c; pp[9 + i] = p
    one = {"daily": {"time": days, "weather_code": wc, "temperature_2m_max": [15.4] * 17, "temperature_2m_min": [5.2] * 17, "precipitation_probability_max": pp}}
    return json.dumps([one, one, one, one])
def T(m, d, h): return f"2026-{m:02d}-{d:02d}T{h:02d}:00:00+09:00"
def jma(rep, near_days, week_start, wcodes, wpops, wrels, tmax, tmin, near_codes, near_pops, near_temps):
    w0 = [T(11, week_start + k, 0) for k in range(7)]
    near = {"publishingOffice": "名古屋地方気象台", "reportDatetime": rep, "timeSeries": [
        {"timeDefines": [T(11, d, 5 if i == 0 else 0) for i, d in enumerate(near_days)], "areas": [
            {"area": {"name": "西部", "code": "230010"}, "weatherCodes": near_codes},
            {"area": {"name": "東部", "code": "230020"}, "weatherCodes": ["400"] * len(near_codes)}]},
        {"timeDefines": [t for t, _ in near_pops], "areas": [
            {"area": {"name": "西部", "code": "230010"}, "pops": [p for _, p in near_pops]},
            {"area": {"name": "東部", "code": "230020"}, "pops": ["100"] * len(near_pops)}]},
        {"timeDefines": [t for t, _ in near_temps], "areas": [
            {"area": {"name": "名古屋", "code": "51106"}, "temps": [v for _, v in near_temps]},
            {"area": {"name": "豊橋", "code": "51331"}, "temps": ["30"] * len(near_temps)}]}]}
    week = {"publishingOffice": "名古屋地方気象台", "reportDatetime": rep, "timeSeries": [
        {"timeDefines": w0, "areas": [{"area": {"name": "愛知県", "code": "230000"}, "weatherCodes": wcodes, "pops": wpops, "reliabilities": wrels}]},
        {"timeDefines": w0, "areas": [{"area": {"name": "名古屋", "code": "51106"}, "tempsMin": tmin, "tempsMax": tmax}]}]}
    return json.dumps([near, week])
async def mkctx(b, w, omb, jmb):
    ctx = await b.new_context(viewport={'width': w, 'height': 844}, timezone_id="Asia/Tokyo")
    h = {"access-control-allow-origin": "*"}
    await ctx.route("**/firebasejs/**/firebase-app.js", lambda r: r.fulfill(body=APP, content_type="text/javascript", headers=h))
    await ctx.route("**/firebasejs/**/firebase-firestore.js", lambda r: r.fulfill(body=FS, content_type="text/javascript", headers=h))
    await ctx.route("**/api.open-meteo.com/**", lambda r: r.fulfill(body=omb, content_type="application/json", headers=h))
    if jmb is None: await ctx.route("**/www.jma.go.jp/**", lambda r: r.abort())
    else: await ctx.route("**/www.jma.go.jp/**", lambda r: r.fulfill(body=jmb, content_type="application/json", headers=h))
    for u in ("**/fonts.googleapis.com/**", "**/open.er-api.com/**", "**/currency-api*/**"): await ctx.route(u, lambda r: r.abort())
    return ctx
ROWS = """[...document.querySelectorAll('.wxrow')].map(r=>({d:r.querySelector('.d').firstChild.textContent.trim(),p:r.querySelector('.p').textContent,t:r.querySelector('.t').textContent.replace(/\\s+/g,''),icon:r.querySelector('use').getAttribute('href')}))"""
async def wxtab(pg):
    await pg.click('nav.tabs button[data-tab="wx"]'); await pg.wait_for_timeout(500)
    rows = {r["d"]: r for r in await pg.evaluate(ROWS)}
    chip = await pg.evaluate('document.querySelector(".src").textContent')
    return rows, chip
# 出發前 11/14：週間涵蓋 11/14–11/20，3 天內 11/14–11/15
PRE = jma(T(11, 14, 5), [14, 15], 14,
          ["101", "200", "100", "203", "101", "214", "200"], ["", "40", "20", "60", "20", "40", "30"], ["", "", "A", "A", "B", "C", ""],
          ["", "18", "19", "18", "17", "16", "16"], ["", "10", "11", "12", "9", "8", "7"],
          ["101", "200"], [(T(11, 14, 6), "0"), (T(11, 14, 12), "10"), (T(11, 15, 0), "20"), (T(11, 15, 6), "40")],
          [(T(11, 14, 9), "20"), (T(11, 14, 0), "20"), (T(11, 15, 0), "11"), (T(11, 15, 9), "18")])
PRE_OM = om_body([3, 3, 3, 3, 61, 61, 61, 0], [49, 29, 22, 12, 12, 70, 35, 10])
# 旅途中 11/18 早上：3 天內 11/18–11/19（今天的最低不採用），週間 11/18–11/24
TRIP = jma(T(11, 18, 5), [18, 19], 18,
           ["200", "200", "101", "100", "101", "200", "111"], ["", "30", "20", "10", "20", "30", "20"], ["", "", "A", "A", "B", "B", "C"],
           ["", "15", "17", "18", "18", "17", "16"], ["", "8", "7", "8", "9", "9", "8"],
           ["300", "201"], [(T(11, 18, 6), "50"), (T(11, 18, 12), "80"), (T(11, 18, 18), "60"), (T(11, 19, 0), "10")],
           [(T(11, 18, 9), "14"), (T(11, 18, 0), "14"), (T(11, 19, 0), "6"), (T(11, 19, 9), "13")])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. 出發前：11/17–11/20 氣象廳、11/21 起長期參考
        for w in (320, 390):
            ctx = await mkctx(b, w, PRE_OM, PRE)
            pg = await newpage(b, jst(11, 14, 9), ctx=ctx)
            rows, chip = await wxtab(pg)
            r17, r18, r19, r20 = rows["11/17"], rows["11/18"], rows["11/19"], rows["11/20"]
            rec(A, f"{w} 寬：頂部寫氣象廳預報", chip.startswith("氣象廳預報，") and "更新" in chip, chip)
            rec(A, f"{w} 寬：11/17 用氣象廳（陰時有雨 60%、18°/12°、可信度 A、雨傘圖示）", "陰時有雨" in r17["p"] and "降雨 60%" in r17["p"] and r17["t"] == "18°/12°" and "可信度 A" in r17["p"] and r17["icon"] == "#w-rain", r17)
            rec(A, f"{w} 寬：11/18 晴時多雲 20%、17°/9°、可信度 B", "晴時多雲" in r18["p"] and "降雨 20%" in r18["p"] and r18["t"] == "17°/9°" and "可信度 B" in r18["p"], r18)
            rec(A, f"{w} 寬：11/19 陰後轉雨但降雨 40% → 雲的圖示、可信度 C", "陰後轉雨" in r19["p"] and r19["icon"] == "#w-cloud" and "可信度 C" in r19["p"], r19)
            rec(A, f"{w} 寬：11/20 可信度空白時不顯示「可信度」", "陰天" in r20["p"] and "可信度" not in r20["p"] and "長期參考" not in r20["p"], r20)
            r21, r22, r23, r24 = rows["11/21"], rows["11/22"], rows["11/23"], rows["11/24"]
            rec(A, f"{w} 寬：11/21 長期參考：代碼是雨但降雨 12% → 陰天，不再寫「有雨」", "陰天" in r21["p"] and "有雨" not in r21["p"] and "長期參考" in r21["p"] and r21["icon"] == "#w-cloud", r21)
            rec(A, f"{w} 寬：11/22 降雨 70% → 有雨（雨傘圖示）", "有雨" in r22["p"] and r22["icon"] == "#w-rain" and "長期參考" in r22["p"], r22)
            rec(A, f"{w} 寬：11/23 降雨 35% → 陰偶有雨", "陰偶有雨" in r23["p"], r23)
            rec(A, f"{w} 寬：11/24 晴、長期參考、Open-Meteo 氣溫四捨五入", "晴" in r24["p"] and r24["t"] == "15°/5°" and "長期參考" in r24["p"], r24)
            ln = await pg.evaluate("[...document.querySelectorAll('.wx-src a')].map(a=>[a.textContent.trim(),a.href,a.target,a.rel])")
            exp = {"名古屋": "23100", "長久手": "23238", "犬山": "23215", "常滑": "23216"}
            ok = len(ln) == 4 and all(any(x[0] == f"tenki.jp {n}" and x[1] == f"https://tenki.jp/lite/forecast/5/26/5110/{c}/10days.html" and x[2] == "_blank" and "noopener" in x[3] for x in ln) for n, c in exp.items())
            rec(A, f"{w} 寬：資料來源卡有 4 個 tenki.jp 連結（名古屋、長久手、犬山、常滑 10 天預報，另開分頁）", ok, ln)
            src = await pg.evaluate("document.querySelector('.wx-src').textContent")
            rec(A, f"{w} 寬：資料來源說明氣象廳與長期參考", "日本氣象廳" in src and "長期參考" in src, src)
            sw = await pg.evaluate("document.documentElement.scrollWidth")
            rec(A, f"{w} 寬：沒有水平捲動、沒有錯誤", sw == w and not pg.errs, (sw, pg.errs[:2]))
            if w == 390:
                await pg.screenshot(path="/tmp/wx_pre_390.png", full_page=True)
                await pg.click('nav.tabs button[data-tab="plan"]'); await pg.wait_for_timeout(400)
                await pg.click('.tile[data-day="0"]'); await pg.wait_for_timeout(700)
                m = await pg.evaluate("(document.querySelector('.wx .w-meta')||{}).textContent||''")
                rec(A, "11/17 當天頁天氣用氣象廳、標可信度", "陰時有雨" in m and "降雨 60%" in m and "可信度 A" in m, m)
            st = await pg.evaluate("JSON.parse(localStorage.getItem('ngy:wx'))")
            rec(A, f"{w} 寬：快取記版本 2 與來源", st.get("v") == 2 and st["days"]["11/17"]["src"] == "jma" and st["days"]["11/21"]["src"] == "om", {k: st["days"][k].get("src") for k in ("11/17", "11/21")})
            await ctx.close()
        # 2. 旅途中 11/18 早上：今天用 3 天內預報（雨、降雨取最高 80%、最高 14°，最低用 Open-Meteo），11/19 用 3 天內的 13°/6°
        # 昨天 11/17 的氣象廳資料在快取裡（4 小時前抓的），今天的氣象廳 JSON 已經不含 11/17：要保留
        prev = json.dumps({"v": 2, "updated": "2026-11-18T04:00:00+09:00", "fetched": int(jst(11, 18, 4).timestamp() * 1000), "days": {"11/17": {"hi": 18, "lo": 12, "icon": "rain", "desc": "陰時有雨", "pop": 60, "src": "jma", "rel": ""}}})
        ctx = await mkctx(b, 390, PRE_OM, TRIP)
        pg = await newpage(b, jst(11, 18, 8), ctx=ctx, init=f'localStorage.setItem("ngy:wx",{json.dumps(prev)});')
        rows, chip = await wxtab(pg)
        r18, r19, r24 = rows["11/18"], rows["11/19"], rows["11/24"]
        rec(A, "旅途中：今天 11/18 用愛知西部 3 天內預報（有雨、降雨 80%、14°/5°）", "有雨" in r18["p"] and "降雨 80%" in r18["p"] and r18["t"] == "14°/5°" and r18["icon"] == "#w-rain", r18)
        rec(A, "旅途中：明天 11/19 用 3 天內的天氣與氣溫（多雲時晴、13°/6°、降雨 10%）", "多雲時晴" in r19["p"] and r19["t"] == "13°/6°" and "降雨 10%" in r19["p"], r19)
        rec(A, "旅途中：11/24 也是氣象廳（晴時多雲、可信度 C）；昨天保留快取裡的氣象廳資料，整頁沒有長期參考", "晴時多雲" in r24["p"] and "可信度 C" in r24["p"] and not any("長期參考" in r["p"] for r in rows.values()), r24)
        src = await pg.evaluate("document.querySelector('.wx-src').textContent")
        rec(A, "旅途中：資料來源只說氣象廳（不提長期參考、不說出發前會換）", "長期參考" not in src and "出發前" not in src and "日本氣象廳" in src, src)
        rec(A, "旅途中：昨天 11/17 保留快取的氣象廳資料", "陰時有雨" in rows["11/17"]["p"] and rows["11/17"]["t"] == "18°/12°", rows["11/17"])
        rec(A, "旅途中：沒有錯誤", not pg.errs, pg.errs[:2])
        await pg.screenshot(path="/tmp/wx_trip_390.png", full_page=True)
        await ctx.close()
        # 3. 氣象廳抓不到：退回長期參考，不出錯
        ctx = await mkctx(b, 390, PRE_OM, None)
        pg = await newpage(b, jst(11, 14, 9), ctx=ctx)
        rows, chip = await wxtab(pg)
        rec(A, "氣象廳抓不到：頂部寫長期參考預報、每天都有數字", chip.startswith("長期參考預報，") and len(rows) == 8 and all("長期參考" in r["p"] for r in rows.values()), chip)
        src = await pg.evaluate("document.querySelector('.wx-src').textContent")
        rec(A, "氣象廳抓不到：資料來源寫目前是長期參考、出發前一週左右換成氣象廳", "目前是長期參考" in src and "更遠的日子" not in src, src)
        await pg.screenshot(path="/tmp/wx_om_390.png", full_page=True)
        rec(A, "氣象廳抓不到：沒有錯誤", not pg.errs, pg.errs[:2])
        await ctx.close()
        # 3b. 氣象廳暫時抓不到、快取裡有 4 小時前的氣象廳資料：保留，不用長期參考蓋掉
        prev = json.dumps({"v": 2, "updated": "2026-11-14T05:00:00+09:00", "fetched": int(jst(11, 14, 5).timestamp() * 1000), "days": {"11/17": {"hi": 18, "lo": 12, "icon": "rain", "desc": "陰時有雨", "pop": 60, "src": "jma", "rel": "A"}}})
        ctx = await mkctx(b, 390, PRE_OM, None)
        pg = await newpage(b, jst(11, 14, 9), ctx=ctx, init=f'localStorage.setItem("ngy:wx",{json.dumps(prev)});')
        rows, chip = await wxtab(pg)
        rec(A, "氣象廳暫時抓不到：11/17 保留快取的氣象廳資料、其他天用長期參考", "陰時有雨" in rows["11/17"]["p"] and "可信度 A" in rows["11/17"]["p"] and "長期參考" in rows["11/21"]["p"], (rows["11/17"], rows["11/21"]))
        await ctx.close()
        # 4. 舊版快取（沒有 v:2、1 小時前抓的）會重新抓，改用氣象廳
        old = json.dumps({"updated": "2026-11-14T08:00:00+09:00", "fetched": int(jst(11, 14, 8).timestamp() * 1000), "days": {"11/17": {"hi": 19, "lo": 12, "icon": "cloud", "desc": "陰天", "pop": 49}}})
        ctx = await mkctx(b, 390, PRE_OM, PRE)
        pg = await newpage(b, jst(11, 14, 9), ctx=ctx, init=f'localStorage.setItem("ngy:wx",{json.dumps(old)});')
        rows, chip = await wxtab(pg)
        rec(A, "舊版快取：重新抓、11/17 換成氣象廳", "陰時有雨" in rows["11/17"]["p"] and "可信度 A" in rows["11/17"]["p"], rows["11/17"])
        await ctx.close()
        # 5. 3 小時內的新版快取不重抓（氣象廳不會被打太多次）
        n = {"c": 0}
        ctx = await mkctx(b, 390, PRE_OM, PRE)
        ctx.on("request", lambda r: n.__setitem__("c", n["c"] + 1) if "jma.go.jp" in r.url else None)
        pg = await newpage(b, jst(11, 14, 9), ctx=ctx)
        await pg.wait_for_timeout(500); c1 = n["c"]
        await pg.reload(); await pg.wait_for_timeout(900)
        rec(A, "3 小時內重新開啟不再抓氣象廳", c1 == 1 and n["c"] == 1, (c1, n["c"]))
        await ctx.close()
        await b.close()
    print(f"\n{sum(1 for x in R if x[2])}/{len(R)} PASS")
asyncio.run(main())
