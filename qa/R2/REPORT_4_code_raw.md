# REPORT 批 4 原文 — qa-code（subagent 回傳，lead 原文存檔）

執行：2026-10-29，與批 2（qa-ui）同時跑。對象：main `e3f5a5a`（ngy-v60）。subagent：Sonnet，唯讀。
lead 的重現與判定見 `REPORT_4.md`；本檔不修改內容。

---

## qa-code 批 4 報告（main e3f5a5a／ngy-v60，純讀檔，未執行任何東西）

### 1. 結論
開場動畫舊殘留已清乾淨（`spout`、`sphop`、收圓圈皆 0 筆）。程式面最需要處理的是一個我在 R1 腳本裡沒看到有測的注入點：網址參數 `?scene=` 未過濾就寫進 HTML（CODE-01）。監聽器沒有洩漏。另外 `.sos-show` 與 `.story` 的淡入因 CSS 順序而實際生效，跟程式註解與 B4 的意圖不符，列待確認。

### 2. 問題表
| ID | 狀態 | 優先 | 範圍 | 發現 | 程式證據（行號／片段） | 觸發路徑 | 建議 | R1 |
|---|---|---|---|---|---|---|---|---|
| CODE-01 | ❌ | P1 | 注入 | 網址參數 `scene` 原樣進入 `data-period="${p}"`，可跳出屬性插入標籤 | index.html:1596 `heroPeriod` 回傳 query 值；:1623 `data-period="${p}"` | 打開 `/?scene=%22%3E%3Cimg%20src%3Dx%20onerror%3D…`（被傳來的連結）→ 首頁渲染即執行；腳本可讀 localStorage 的旅程代碼並寫入雲端 | 只接受五個時段名稱白名單，其餘忽略；或移除這個除錯入口 | 新（R1 t_xss 未涵蓋網址參數） |
| CODE-02 | ⚠️ | P2 | 注入 | 同步來的 `links` 經 `ext()` 無 scheme 檢查，可出現 `javascript:` href（理論風險，已降級） | :1810 `href="${esc(href)}"`；:2506 `r.links.map(l=>ext(...))` | 持有旅程代碼者直接寫 `items/<id>.links`；App 介面本身寫不出 | `ext()` 只放行 `https?:` | 新 |
| CODE-03 | ⚠️ | P2 | 同步資料 | 同步來的心情 `score` 不在 1–5 或非數字，`MOODS[v.score-1][1]` 會拋錯，首頁／當天頁心情區無法渲染 | :1848 `moodFace`；:1882、:1888、:1908 `MOODS[v.score-1][1]`；:2992 `moods=n` 無驗證 | 對方端（或直接寫入）出現 `score:0` 的文件 → onSnapshot 內 `rerenderMood()` 拋錯 | 快照進來時驗證並丟棄不合法文件 | 新 |
| CODE-04 | ⚠️ | P3 | 同步資料（理論風險） | 同步來的帳目缺 `day`，`localeCompare` 拋錯 | :2426 `b.localeCompare(a)`；:3195 `a.day.localeCompare(b.day)` | App 介面一定帶 `day`；需手寫壞資料 | 排序前 `String(e.day\|\|"")` | 新 |
| CODE-05 | 🔎 | P2 | 動效 | `.sos-show`（:1047 `fadein .15s`）與 `.story`（:1178 `fadein .2s`）寫在 :912 合併規則（sheetin）之後、同優先度，所以實際是 opacity 淡入，不是滑上；`.viewer` 的 :787 在 :912 之前，所以實際是滑上 | :906 註解寫全螢幕層滑上；:912 `.viewer,.sos-show,.story{animation:sheetin…}`；:1047、:1178 | 打開給司機看／旅程回顧 | 屬 B8（待明彰決定）；若決定要滑上，把兩處 `fadein` 刪掉 | 新 |
| CODE-06 | ⚠️ | P3 | 動效／B1 | 動畫用到非 transform 的屬性：`.days .ind` 的 width（:227）、`.coach-hole` 的 left/top/width/height 轉場（:1120）、`details.sched` 的 WAAPI height+opacity（:2747–2748）、`.st-page` 的 opacity 轉場（:1186） | 如左 | 切天、新手導覽、展開行程、故事換頁 | 是否改成 transform／是否算例外，列待確認 | 新 |
| CODE-07 | ⚠️ | P3 | 無障礙 | 旅程回顧（`openStory`）與新手導覽（`openTour`）沒走 `modal()`：沒有 Tab 限制、關閉後焦點不回原按鈕；Esc 只在焦點於面板內才有效 | :3182 `close`；`openStory` 自己綁 keydown | 鍵盤或讀屏使用 | 套用 `modal()`（對照 C5 說「所有面板」） | R1 C-P2-8 只修了求助／錢包／行事曆／出發前設定 |
| CODE-08 | 🔎 | P3 | 同步 | `send()` 比對 `"invalid_argument"`（底線），Firestore SDK 慣用 `invalid-argument`（連字號），該分支可能永遠不觸發。我無法確認假資料庫回什麼，所以不判 ❌ | :1761 vs :1763 `permission-denied` | 寫入被規則拒絕 | 兩種寫法都接受 | 新 |
| CODE-09 | ⚠️ | P3 | outbox | 被拒絕的寫入只在下次 `connect()`／重開才重送，沒有定期重試；`putMany` 吞掉錯誤 | `flushOutbox` 只在 `connect()` 呼叫；:1750 `.then(…,()=>{})` | 暫時性錯誤（非離線） | 在 `retrySync` 一併 flush | D7 範圍內的細節 |
| CODE-10 | ⚠️ | P3 | 同步（理論風險） | outbox 與本機快取不分旅程代碼；未送出時用 `#k=` 連結換代碼，舊寫入會送進新旅程 | :2904 `getCode()` 立即存新碼；`ngy:outbox` 無代碼前綴；:3047 註解承認 | 有未同步寫入時打開別的 `#k=` 連結 | 換碼時若 outbox 非空就先確認 | 新 |
| CODE-11 | ⚠️ | P3 | 同步 | 「隨身」切換用整筆 `set`，不是只寫改的欄位，可能蓋掉對方同時的修改 | :3207 `const {id:_i,...rec}=ex; put(…,rec)` | A 改金額、B 還沒收到快照就按隨身 | 改成只寫 `{carry}` 並 merge | 與 D8、R1 C-P1-5 精神不一致（C-P1-5 修的是編輯表單） |
| CODE-12 | ⚠️ | P3 | 資料殘留 | `deleteItem` 只刪 `checks/<id>`，不刪 `checks/<id>@人` | :2560 附近 `put("checks/"+id,null)` | 刪除已被個別勾選的打包項目 | 一併刪除 | 新 |
| CODE-13 | ⚠️ | P3 | 無障礙 | 日文區塊沒有 `lang="ja"`（全檔 0 筆），讀屏會用中文音念日文 | grep `lang="ja"` 0 筆 | 讀屏讀給司機看／日文常用語 | 日文節點加 `lang="ja"` | 新 |
| CODE-14 | ⚠️ | P3 | 無障礙 | 底部分頁按鈕有 `aria-selected` 卻沒有 `role="tab"`（:1453–1458）；`role="button"` 的帳目列內含真的 `<button class="del">`；`role=switch` 在 `<button>` 內（:2587） | 如左 | 讀屏 | 補 role 或改結構 | 新 |
| CODE-15 | ⚠️ | P3 | 死碼 | 見下方「死碼清單」 | 見下 | — | 清理 | 新 |
| CODE-16 | ⚠️ | P3 | 重複 id | `id="gDusk"` 定義兩次（:1411、:1415），後者永遠不會生效 | 如左 | 暮色插圖 | 刪掉一個或改名；哪個顏色才對請明彰／qa-ui 判斷 | 新 |
| CODE-17 | ⚠️ | P3 | 一致性 | 匯率邊界不同：手動 `>=0.1&&<=0.5`（:2812）、自動抓取 `>0.1&&<0.5`（:3355） | 如左 | 匯率剛好 0.1 或 0.5 | 統一 | D2 |
| CODE-18 | ⚠️ | P3 | SW | 帶 query 的網址各自存成獨立快取項目，沒用 `ignoreSearch`；`splash/*.png`、`icon-maskable-512.png` 不在 CORE；`ghibli-map-thumb.jpg` 預快取但 index.html 沒用到 | sw.js:6、:39 | 開 `/?utm=…` 之類的連結 | 視需要調整 | 新；E3、D10 本身符合 |
| CODE-19 | ⚠️ | P3 | 潛在 | `esc()` 不跳脫單引號；`sosEsc` 與 `esc` 重複（:1734、:1808）；`openViewer` 的 `src` 直接插入（呼叫端目前都是常數） | 如左 | 目前找不到可利用路徑 | 合併成一個並補 `'` | 新 |

### 3. 待確認（交給 lead／明彰）
1. **B8 全螢幕層與遮罩**，依你的要求全列待確認，不判缺陷：
   - 遮罩 `dimin`／`dimout`（:907–909、:914，只動背景色）。
   - `fadein` 實際生效於 `.sos-show`、`.story`（CODE-05）。
   - 其他小型 opacity 動畫：`fabin`（:581）、`toastin`（:759、:1062）、`coachin`（:1121）、`pop`（:848）、`hintout`（:795）、`vdim`（:905）。
2. B5 例外：`spfade`（:1380 附近）淡出 0.4 秒，符合 B5。
3. CODE-06 的非 transform 動畫是否算 B1 例外。
4. CODE-08 假資料庫實際回傳的錯誤碼，需要 lead 查 mock。
5. CODE-16 兩個 `gDusk` 該留哪一個。
6. R1 C-P3-6 觸控範圍（交給 qa-ui）。程式面 :186 的 `::before` 規則存在，我沒有量實際效果。

### 附錄｜已有決定（程式現況與 DECISIONS 一致，不列為問題）
- 開場動畫（B5）：只有 `spbob`／`spfade`，1.2 秒、減少動態移除、點擊跳過。
- 彈窗 `sheetin` 0.5 秒不回彈、退場 0.25 秒（B4）。
- 底部分頁不播動畫（B2）。
- 換頁 transform-only（B3）。
- 求助只在首頁與當天頁（A6），給司機看點大字不關（C4）。
- `modal()` 處理 Tab／Esc／焦點回復（C5）。
- 新代碼先確認、字元限制（C7）。
- `parseYen` 金額規則（D1），匯率 0.1–0.5（D2）。
- `tz` 欄位與 JX 320 台灣時間（D6）：`itemM`／`TZ_LAG` 正確，.ics 與 DAYS 逐筆比對時間與時區一致（JX 320 為 Taipei 07:05、Tokyo 10:40，JX 321 為 11:40）。
- outbox 序號保護（`obDone`）（D7）。
- 電話分機逗號（D9）。
- SW 1.5 秒 race（D10）、保留 `ngy-lib`（E3）。
- 心情以快照重建（D11）。
- 全域 `reduce` 動態處理完整。

### 明確回答三個重點
**(1) 舊開場殘留**：`spout`、`sphop`、收圓圈／clip-path 皆 0 筆。現有 splash CSS 在 :1375–1388、標記在 :1391–1399、JS 在 :1400–1406 與 :2700–2703，都在使用中。小殘留：splash SVG 內的 `.eyes`／`.pupil` 沒有對應樣式，是惰性的；splash 內自帶 `#sp-rough` 濾鏡與全域 `#rough` 重複，但是有意為之（splash 比 `#defs` 先出現）。

**(2) `fadein`／opacity 全螢幕層分類**
- `fadein` 在 :735、:787、:1047、:1178 共宣告 4 次（keyframes 在 :919）。
  - `.sheet-modal`（:735）被 :907 蓋過，無效。
  - `.viewer`（:787）被 :912 蓋過，無效。
  - `.sos-show`、`.story` 實際生效，歸 B8（CODE-05）。
- `dimin`／`dimout`：B8 待確認。
- `sheetup`（:737）被 :910 蓋過，是死碼。
- `spfade`：B5 例外。
- 沒有發現對整頁內容淡入而違反 B1 的 B1 違規；`.st-page` opacity（:1186）屬內容層淡入，列 CODE-06 待確認。

**(3) 注入與監聽器**
- 注入：
  - 帳目、項目、心情、`settings/sos` 的文字全部經 `esc()`／`sosEsc()`，沒有可利用點（和 R1 t_xss 結論一致）。
  - 新發現是 CODE-01（網址參數），其次 CODE-02／03／04。
  - `tel:` 經 `telHref` 只留數字與 `+`；`mapUrl` 用 `encodeURIComponent`。
- 監聽器：
  - 全域 click／keydown／visibilitychange 都只註冊一次。
  - 每次 render 會重建節點，`bindSched` 等綁在新節點上，舊的隨節點回收。
  - `openViewer`、`openTour` 的 `resize` 都會在 close 時移除。
  - 沒有洩漏。
  - 小瑕疵：`openTour` 的 `v._p` timer 關閉時沒清（:3182），只會對已移除節點寫樣式，無害。

### 死碼清單（CODE-15）
- `moodCtaHTML`（:1885）沒被呼叫。
- `@keyframes sheetup`（:737）無效。
- `fadein` 剩餘宣告 `.sheet-modal`（:735）與 `.viewer`（:787）被覆蓋。
- 未使用的 CSS 類別：`cats-bob`（:814，連同只被它用的 `@keyframes bob`）、`hp-day`（:43）、`mapcard`（:780–786）、`nl`（:637）、`pe-go`（:537–538）、`pk-hint`（:549）、`pk-prog`（:546–548）、`st-big`（:1190–1191）、`st-hint`（:1193）、`st-k`（:1189）、`su-me`（:1097–1098）、`w-acts`（:488）、`w-ask`（:473）、`w-head`（:471–478）。（`s-done`／`s-next`／`s-now`／`t1`／`t2` 是動態組字，不算。）
- :850 的註解「只動 opacity 和 transform」已過時。
- `ghibli-map-thumb.jpg` 預快取但沒被引用。

### 5. 沒讀到的範圍與原因
- 沒有執行任何程式、沒開瀏覽器，也沒碰 8766。CODE-05 的「實際是淡入」是依 CSS 順序推導，沒有實測。
- index.html 全檔 3,576 行都讀過，但 :1417–1445 的 SVG symbol／圖示定義只快速掃過。
- `splash/*.png`、`ghibli-map*.jpg`、各 icon 圖檔與 README 沒打開。
- `nagoya-trip.ics` 約 62–340 行只以 grep 對照 DTSTART／SUMMARY，沒有逐行讀。
- R1 腳本只讀了 `t_xss.py` 與 `test-report.md`，`t_leak.py` 等沒細讀。
- Firestore 安全規則不在範圍內；CODE-02／03／04／10 的前提「持有旅程代碼即可寫入」依 SCOPE 沒有驗證。
- 報告中沒有出現任何旅程代碼、訂位號或電話。
