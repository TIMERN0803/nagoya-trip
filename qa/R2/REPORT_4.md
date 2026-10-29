# REPORT 批 4 — 程式碼（qa-code）

執行：2026-10-29（與批 2 同時跑）。對象：main `e3f5a5a`（ngy-v60）`index.html`、`sw.js`、`manifest.webmanifest`、`nagoya-trip.ics`。
原文：`REPORT_4_code_raw.md`（qa-code 只讀檔，沒有執行）。lead 重現腳本：`b2b4/lead/p4_code.py`、`p4_code01.py`、`p4_code03.py`，一律假資料庫。

## 結論

**有 1 個要立即修的注入（CODE-01，已重現）；其餘都是 P3 等級的防呆、無障礙與清理，誤報 0。** 舊開場動畫的 `spout`、`sphop`、圓圈收合已經沒有殘留；監聽器沒有洩漏；同步來的文字都有跳脫（和 R1 t_xss 一致）。

## 指定項目

| 項目 | 判定 |
|---|---|
| 舊開場動畫殘留（`spout`、`sphop`、圓圈收合） | ✅ 0 筆。現在只有 `spbob`／`spfade`，都在用。splash SVG 裡 `.eyes`／`.pupil` 沒有樣式，無作用但無害 |
| 全螢幕層的 `fadein`（opacity） | 🔎 歸 B8。lead 用 computed style 實測：`.sos-show`（給司機看）**fadein 0.15s**、`.story`（旅程回顧）**fadein 0.2s**、`.viewer` sheetin 0.5s、`.sheet-modal` 遮罩 dimin 0.3s。註解寫「全螢幕層滑上」，但前兩個因為 CSS 先後順序實際是淡入（CODE-05） |

## 問題表（lead 重現或對照程式後）

**修正狀態（10/29）**：明彰同意提前修。分支 `fix-scene-param`（`a320dcc`，sw.js → ngy-v61）；新測試 `ft/scenetest.py` 24 項（v60 失敗 12 項、修正版全過）；完整回歸 32 支 1,086 項全綠、sweep／t5 沒有錯誤。**已上線**：明彰 12:02 說「可以上線」→ main `a320dcc`（ngy-v61），12:03 GitHub Pages 部署成功；SCOPE 凍結版本改為 v61，批 3 以 v61 為對象。上線後回歸結果見 SCOPE 第 9 節。

### bug 立即修

| ID | 狀態 | 優先 | 發現 | lead 重現 | 建議 |
|---|---|---|---|---|---|
| CODE-01 | ❌ | P1 | 網址參數 `?scene=` 原樣寫進首頁插圖的 `data-period="${p}"`，可以跳出屬性插入標籤並執行程式 | `heroPeriod`（:1596）`if(q)return q`。打開 `/?scene=` 加上一段 `"><img src=x onerror=…>`：**出發前（10/30）與旅途中切回首頁（11/18）都執行了**，`window.__xss` 讀到頁面標題；`.scene-wrap` 多了 1 個 `<img>`；`?scene=dinner` 對照組正常。網站是公開的 GitHub Pages，只要有人傳一個連結給你們點開就會中；能讀到 localStorage 的旅程代碼並寫入雲端 | `scene` 只接受 `morning／noon／afternoon／dinner／night`，其他忽略（一行）。這是開發時切換插圖的除錯入口，也可以直接拿掉 |

### 防呆（同步來的壞資料）

| ID | 狀態 | 優先 | 發現 | lead 判定 |
|---|---|---|---|---|
| CODE-03 | ❌ | P3 | 雲端心情 `score` 不是 1–5（0、文字、null）時，首頁和那一天的頁面**畫不出來** | 已重現：`render()` 拋 `TypeError: Cannot read properties of undefined (reading '2')`，切首頁或 11/17 都停在原頁；score=3 對照組正常。App 介面送不出這種值（沒選分數時「送出」停用），要手寫壞資料才會發生，所以 qa 的 P2 降成 P3。但一發生兩支手機都會壞，修法很小：快照進來時丟掉不合法的 |
| CODE-02 | ⚠️ | P3 | 同步來的項目 `links` 沒檢查網址開頭，可能出現 `javascript:` 連結 | 理論風險：App 介面寫不出來，要直接寫 Firestore。能直接寫的人本來就能改所有資料。`ext()` 只放行 `https?:` 即可（qa 原 P2，降一級） |
| CODE-04 | ⚠️ | P3 | 同步來的帳目沒有 `day` 時排序拋錯 | 理論風險，同上 |

### 同步與資料

| ID | 狀態 | 優先 | 發現 | lead 判定 |
|---|---|---|---|---|
| CODE-08 | ⚠️ | P3 | `send()` 比對的是 `"invalid_argument"`（底線，:1761），Firestore 錯誤碼是 `invalid-argument`（連字號），這個分支不會觸發，被拒絕的寫入會留在 outbox、每次連線重送 | 程式片段已核對；假資料庫只會回 `permission-denied`／`unavailable`，無法在沙箱重現。實際要真 Firestore 拒絕一筆格式錯誤的寫入才會發生，機率很低 |
| CODE-09 | ⚠️ | P3 | 非離線的暫時性寫入失敗，只在下次連線／重開才重送 | 屬 D7 的細節，影響小 |
| CODE-10 | ⚠️ | P3 | outbox 不分旅程代碼：有未同步的寫入時開別的 `#k=` 連結換代碼，舊的寫入會送進新旅程 | 理論風險（兩人只用一個代碼） |
| CODE-11 | ⚠️ | P3 | 帳目「隨身」切換整筆覆寫（:3207），不是只寫改的欄位 | 程式已核對。和 D8「只寫有改的欄位」不一致；兩人同時改同一筆才會發生 |
| CODE-12 | ⚠️ | P3 | 刪除打包項目只刪 `checks/<id>`，沒刪 `checks/<id>@人` | 程式已核對（:2560）；只留下沒用的雲端資料，畫面不受影響 |
| CODE-17 | ⚠️ | P3 | 匯率範圍：手動 `>=0.1 && <=0.5`、自動抓取 `>0.1 && <0.5` | 只差剛好 0.1／0.5 這兩個值，實際碰不到 |

### 無障礙

| ID | 狀態 | 優先 | 發現 | lead 判定 |
|---|---|---|---|---|
| CODE-07 | ⚠️ | P3 | 旅程回顧（`openStory`）與新手導覽（`openTour`）沒有走 `modal()`：沒有 Tab 限制、關閉後焦點不回原按鈕 | 已核對：其他 7 個面板都呼叫 `modal()`，這兩個沒有。和 C5「所有面板」不一致（R1 C-P2-8 修的是求助／錢包／行事曆／設定） |
| CODE-13 | ⚠️ | P3 | 全檔沒有 `lang="ja"`，讀屏會用中文念日文 | grep 0 筆已核對。給司機看與日文常用語用得到 |
| CODE-14 | ⚠️ | P3 | 底部分頁有 `aria-selected` 但沒有 `role="tab"`；帳目列 `role="button"` 裡面有真的按鈕；`role=switch` 包在 `<button>` 裡 | 讀屏才會碰到 |

### 清理（不影響使用）

| ID | 狀態 | 優先 | 發現 | lead 判定 |
|---|---|---|---|---|
| CODE-15 | ⚠️ | P3 | 死碼：`moodCtaHTML` 沒被呼叫；`@keyframes sheetup` 與兩處 `fadein` 被覆蓋；14 個 CSS 類別沒有 HTML 用到（`mapcard`、`w-head`、`pk-prog`…）；:850 註解過時 | 抽查 6 個類別：都只出現在自己的 CSS 規則，確認沒用 |
| CODE-16 | ⚠️ | P3 | `id="gDusk"` 定義兩次（:1411 深藍→紫→橘、:1415 淡紫→粉→杏），瀏覽器只用第一個 | 已核對。**要留哪一個是設計判斷**，列待確認 |
| CODE-18 | ⚠️ | P3 | SW 預快取 `ghibli-map-thumb.jpg` 但 index.html 沒用到；`splash/*.png` 不在預快取；帶 query 的網址各存一份 | 已核對 `ghibli-map-thumb` 在 index.html 0 筆。E3、D10 本身符合 |
| CODE-19 | ⚠️ | P3 | `esc()` 不跳脫單引號；`sosEsc` 和 `esc` 重複 | 目前所有屬性都用雙引號，找不到可利用路徑 |

## 待確認（批 5 討論）

1. 🔎 **B8**：遮罩 `dimin`／`dimout`；給司機看、旅程回顧實際是淡入（CODE-05，實測）；其他小型 opacity 動畫 `fabin`、`toastin`、`coachin`、`pop`、`hintout`、`vdim`。如果決定全螢幕層也要滑上，只要刪掉 :1047、:1178 兩處 `fadein`。
2. 🔎 **B1 例外**（CODE-06）：切天的指示條動 `width`、新手導覽的鏤空框動 `left/top/width/height`、行程展開動 `height＋opacity`、旅程回顧換頁動 `opacity`。算不算「頁面與內容不淡入淡出」的例外？
3. 🔎 **CODE-16**：暮色漸層要用哪一組顏色？（目前畫面用的是第一組深藍→紫→橘）

## 附錄｜已有決定（和 DECISIONS 一致）
B2 底部分頁不播動畫；B3 換頁只動 transform；B4 sheetin 0.5 秒不回彈、退場 0.25 秒；B5 開場只有 `spbob`／`spfade`、1.2 秒、淡出 0.4 秒、減少動態移除；A6、C4、C5（`modal()` 那 7 個面板）、C7；D1 `parseYen`、D2、D6（`.ics` 與 DAYS 時間時區逐筆一致，JX 320 台北 07:05）、D7 `obDone` 序號保護、D9、D10 1.5 秒退快取、D11；E3 保留 `ngy-lib`。

## 沒讀到
- 沒執行網站（qa-code 唯讀）；lead 只重現了 CODE-01、03、05。
- SVG symbol（:1417–1445）只快速掃過；圖檔沒打開；`.ics` 用 grep 對照 DTSTART／SUMMARY。
- Firestore 安全規則不在範圍；CODE-02／04／10 的「持有代碼就能直接寫」沒有驗證。
