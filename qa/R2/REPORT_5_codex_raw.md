# REPORT 批 5 — Codex 二次審查原文（EXEC_LOG.md）

執行：2026-10-29 約 14:00–14:11，明彰 Mac 上 Claude Code → Codex rescue（唯讀）。對象 main `a320dcc`。lead 由 Mac 讀取原檔存入，**未改任何字**。

---

# QA R2 二次審查（唯讀）

## 1. 一句話結論

a320dcc 的主要覆寫與草稿遺失前提成立，UX-01 維持 P2、UX-02 建議升 P2，另補 7 項靜態可追溯的缺口；CODE-01 已修好，已決定的動效、純偏好與無觸發路徑的防禦建議不應繼續算現存缺陷。

審查日期：2026-10-29；HEAD：`a320dcc`，`sw.js:2`：`const VERSION = "ngy-v61";`。讀取 REPORT_2／3／4、DECISIONS（10/29 更新）、SCOPE §5 與四個指定網站檔案；只在核對死碼及建議範圍時對照 REPORT_4_code_raw.md。沒有跑測試、啟動網站、連線正式資料庫、讀取 `.sos-private.json` 或取得旅程代碼。下文「成立」表示靜態路徑成立，不表示本次重現過；報告中的量測數字仍屬前次審查證據。

片段均為 a320dcc 原始碼的局部摘錄（單段不超過 10 行）；表格內省略號是摘錄省略。優先依 SCOPE §5 判斷，修法短不作為升級理由。相同 ID 在指定項目與問題表重複出現者合併一列。

## 2. 誤報與優先

| 原 ID | 判定（誤報／維持／改優先 Px） | 理由與程式證據 |
|---|---|---|
| UI-01 | 維持 P3 | 星星標籤確為白字／珊瑚底，17px 粗體的前提成立。`index.html:1280`：`.vs-p .vh{background:var(--pc);color:#fff;…font-weight:900;font-size:17px;…}`；`:3214`：`const RV_PEOPLE_COLOR={zhang:"#3F3127",star:"#E07A5F"};`。前報對比 2.95:1 可由這組色值支持；固定「第 5 頁」不是穩定定位，無資料頁會跳過，應用角色卡定位。 |
| UI-02 | 維持 P3 | 非 Android 的行事曆訂閱卡確套用低對比顏色；它是主要選項，不是操作後才被選中。`index.html:2599`：`<a class="sm-opt main" …>`；`:750–752`：`.sm-opt.main{background:var(--accent);…color:#fff}`、`.sm-opt.main small{color:rgba(255,255,255,.9)}`、`.sm-opt.main em{color:#FFE29A}`。樣式支持前報問題，但本次沒有重做像素量測。 |
| UI-03 | 維持 P3 | 提示確在封面黃底，且因 `.st-page p` specificity 較高，實際仍為 15px，非後面的 `.st-cap` 13.5px。`index.html:1192`：`.st-page p{…font-size:15px;…color:var(--muted)}`；`:1203`：`.pg-open{background:#F6D58A;background-image:radial-gradient(…)}`；`:3248`：`<p class="st-cap">點右邊看下一頁</p>`。前報 4.37:1 的低對比前提成立。 |
| UI-04 | 誤報（作為缺陷；保留實機觀察） | 小字前提成立，但「至少 12px」不是既有決定，不能只憑大小判缺陷。`index.html:531`：`.pe-row{…font-size:13px}`；`:536`：`.pe-row small{font-family:var(--f-display);font-weight:700;…}` 未覆寫 small 的縮小規則。10.83px 與前報相容；是否難讀依 E5 留實機確認，不直接排修。 |
| UX-01 | 維持 P2 | 確實把舊金額／備註帶入「隨身」寫入，可能悄悄改錯結算。`index.html:3208–3209`：`ex.carry=!ex.carry;`、`const {id:_i,...rec}=ex;put("expenses/"+id,rec);`；`:1762`：`e.m?r.set(e.d,{merge:true}):r.set(e.d)`。對方更新尚未抵達時成立。與 CODE-11 同一問題，不重複計數。 |
| UX-02 | 改優先 P2 | 同為使用者正常操作可造成不同欄位靜默遺失，還可能把期限、購買內容改回；不只是外觀細節。`index.html:2835`：`const it={...(old\|\|{}),…title,…note:…,…due:…}`；`:2551`：`const {id,...rec}=it;put("items/"+id,rec);`。且表單舊值也會覆蓋已收到的新值，詳修法風險。 |
| UX-03 | 維持 P3 | 日本跨日且非有值輸入框獲焦時確實直接 reload；記帳／心情等草稿未持久化。`index.html:1820`：`if(a&&/^(INPUT\|TEXTAREA\|SELECT)$/.test(a.tagName)&&a.value)return false;location.reload();`；`:1821`：`setInterval(dayCheck,30000)` 及 visible 時呼叫。跨日窄情境維持 P3，但修正要涵蓋 CX-03／04。 |
| UX-04 | 維持 P3 | 兩層僅局部 keydown，未加入共用焦點堆疊。`index.html:3187`：`v.addEventListener("keydown",e=>{if(e.key==="Escape")close()});`；`:3287`：`…if(e.key==="Escape")close();if(e.key==="ArrowRight")go(cur+1)…`；`:2378`：`const m=modals[modals.length-1];if(!m)return;`。焦點跑到層外後 Esc 無局部接收者；與 CODE-07 合併。 |
| UX-05（指定項目 ⚠️） | 誤報（已決定待實作，不列問題） | C11 已決定新增同名提示，不再列未決疑問或新缺陷。現況可追溯：`index.html:2875–2878`：`if(ex)undoSnack(…,async()=>{…if(!expenses.some(e=>e.id===id))expenses.push({...ex});put("expenses/"+id,rec);…});` 只比原 ID；清單同類在 `:2555–2557`。依 C11 執行即可。 |
| CODE-01 | 誤報（目標版本已修好） | 原報 v60 的漏洞曾成立，但 v61 不再接受任意 scene。`index.html:1597–1598`：`const SCENE_KEYS=["morning","noon","afternoon","dinner","night"];`、`if(SCENE_KEYS.includes(q))return q;`。不得把已修的 P1 算進現存問題。 |
| CODE-02 | 維持 P3 | `links` 的 URL scheme 未過濾，屬壞資料防禦；介面沒有編輯 links 的入口，無證據升成一般使用者可觸發的注入。`index.html:1812`：`const ext=(label,href)=>…href="${esc(href)}" target="_blank" rel="noopener"…`；`:2508`：`r.links.map(l=>ext(l[0],l[1]))`；`:2835`：`links:old?old.links\|\|null:null`。實際執行 javascript URL 的能力仍依瀏覽器與外部寫入權限待確認。 |
| CODE-03 | 維持 P3 | 壞 score 確能索引 undefined；一般 UI 只產生 1–5。`index.html:1850`：`const m=MOODS[n-1]`；`:1859`：`fill="${m[2]}"`；`:1907`：`MOODS.map(m=>…data-score="${m[0]}"…)`；`:2994`：`n[d.id]=d.data()` 沒驗證。P3 防禦合理，不回升 P2。 |
| CODE-04 | 維持 P3 | 缺 day 且排序 comparator 被呼叫才拋錯，單一筆不一定；原報應補條件。`index.html:2428`：`const days=[...new Set(expenses.map(e=>e.day))].sort((a,b)=>b.localeCompare(a));`；`:2996`：`day:v.day` 沒預設；`:3197`：`a.day.localeCompare(b.day)` 也是入口。介面會選有效日期，因此仍屬壞資料防禦。 |
| CODE-05（B8） | 誤報（符合決定） | 這項原列 🔎，特列結案以免繼續誤算。`index.html:907`：`.sheet-modal{animation:dimin .3s ease}`；`:1047`：`.sos-show{…animation:fadein .15s ease;…}`；`:1178`：`.story{…animation:fadein .2s ease;…}`。DECISIONS B8 已明確保留；不用刪除這些動畫。 |
| CODE-06（原列 🔎） | 維持待確認，未定優先 | 其餘動效尚無明確例外決定。`index.html:1120`：`.coach-hole{…transition:left .3s …,top .3s …,width .3s,height .3s;…}`；`:1186`：`.st-page{…transition:opacity .25s}`；`:2749`：`body.animate([{height:"0px",opacity:0},{height:h+"px",opacity:1}],…)`。B8 只解決指定遮罩／層的進場，不等於所有內容轉場獲准。 |
| CODE-07 | 維持 P3（併 UX-04） | 前提成立，證據見 UX-04 及 `index.html:2365`：`modals.push(m);`；`openTour`（:3156–3190）、`openStory`（:3276–3294）都未呼叫 modal。不可重複計為兩件。 |
| CODE-08 | 維持 P3（錯誤碼待確認） | 底線比較和失敗保留的路徑可見，但本 repo 未提供 SDK 錯誤碼定義，不能把外部 enum 當本次已驗證。`index.html:1763`：`if(c==="invalid_argument"){canWrite=false;obDone(path,s);render(true)}`；`:1765`：`else if(c==="permission-denied")…`；其他錯誤不 obDone。請 lead 以本版 SDK 文件／假 SDK 精確錯誤碼確認，勿刪除所有未知錯誤的待同步資料。 |
| CODE-09 | 維持 P3 | 非權限失敗沒有自身 backoff；原報「只在連線／重開」略窄，還有 visible、30 秒探測，但 srv 已 ok 的失敗不一定觸發。`index.html:1762–1766`：`…then(()=>{obDone(path,s);srvOk()},err=>{…});`；`:3036`：`if(live){if(srv!=="ok")checkServer();return}`；`:3055`：`((!live&&libFailed)\|\|(live&&srv==="down"))`。重試機制不足成立，不能說完全沒有定時恢復。 |
| CODE-10 | 維持 P3 | outbox 路徑不含旅程，hash 解析沒有 pending 檢查，連線後直接送。`index.html:1741`：`const OB_KEY="ngy:outbox";`；`:2906–2907`：`const m=location.hash.match(/k=([\w-]+)/);if(m){…localStorage.setItem(TRIP_KEY,m[1])…}`；`:2985`：`flushOutbox();`。需另開旅程連結才觸發，兩人單旅程情境維持 P3。沒有 hashchange handler；不是每次變 hash 都立即切 db，而是 getCode 被呼叫／重開後生效。 |
| CODE-11 | 改優先 P2（併 UX-01） | 靜態覆寫已獲前報行為證據支持。`index.html:3209`：`const {id:_i,...rec}=ex;put("expenses/"+id,rec);`。以 UX-01 為唯一修正與驗收項，不保留另一個 P3。 |
| CODE-12 | 維持 P3 | 刪除時確只刪裸 ID，雖已算出含人名的 key。`index.html:2554`：`dk=Object.keys(done).filter(k=>k===id\|\|k.startsWith(id+"@"))`；`:2561–2562`：`delete done[id];…put("items/"+id,null);put("checks/"+id,null);`。殘留同時在本機與雲端；一般列表先由 items 決定，因此不應宣稱目前畫面一定錯。 |
| CODE-13 | 維持 P3 | HTML 只有全頁中文 lang，日文 DOM 未加局部語言；語音合成的設定不等於讀屏標記。`index.html:2`：`<html lang="zh-Hant">`；`:3494`：`<div class="s-lead">この住所までお願いします。</div>`；`:3482`：`u.lang="ja-JP"` 僅供播放功能。朗讀結果依裝置待實機確認，標記缺口成立。 |
| CODE-14 | 維持 P3 | 不適用的 selected 與巢狀互動語意成立。`index.html:1454`：`<button data-tab="plan" aria-selected="true">`；`:2431`：`<div class="ex…" …role="button" tabindex="0">…<button …data-del=…>`；`:2589`：`<button class="rm-row" …><span class="switch…" role="switch" aria-checked=…>`。修正應把 switch role 放在可操作 button 上，而非只刪狀態；底導覽也可採 aria-current，無須硬套 tabs。 |
| CODE-15 | 維持 P3（清理，非功能缺陷） | 抽查死碼前提成立，raw 的 14 類別清單有提供；不需要因此動未使用的所有樣式。`index.html:1887`：`function moodCtaHTML(x,i){` 全檔只有定義；`:780`：`.mapcard{…}` 只有 CSS 引用；`:735` 舊 `.sheet-modal{…animation:fadein .18s ease}` 被 `:907` 的 `animation:dimin .3s ease` 覆蓋。清理可留到同區改動，沒有升級理由。 |
| CODE-16 | 維持 P3（顏色待確認） | 重複 ID 本身成立，選哪組顏色仍是設計判斷。`index.html:1411`：`<linearGradient id="gDusk" …><stop offset="0" stop-color="#4A5488"/>…`；`:1415`：`<linearGradient id="gDusk" …><stop offset="0" stop-color="#C9C3E6"/>…`；`:1601`：`fill="url(#gDusk)"`。本次不保證每個 SVG 消費者都選第一組，應保留已核准外觀並消除重名。 |
| CODE-17 | 誤報（作為使用缺陷） | 邊界不一致成立，但沒有可追溯的實際錯誤匯率或自動邊界必須包含的決定，不能只因運算子不同列 bug。`index.html:2814`：`v>=0.1&&v<=0.5`；`:3357`：`if(!(v>0.1&&v<0.5))continue;`。D2 規範手動範圍，現況符合；可作日後一致性清理。 |
| CODE-18 | 維持 P3（僅快取整理部分） | 多存無用縮圖與 query 副本成立；未預快取 splash 不能單憑此推論 iOS 啟動畫面失效。`sw.js:6`：`CORE=[…"./ghibli-map-thumb.jpg",…]`；`:35`：`c.put(req, copy)`；`:39`：`caches.match(req)`；`index.html:2763` 實際開啟 `openViewer("ghibli-map.jpg",…)`。保留 E3 的 LIB；不得直接對所有資源 ignoreSearch（可能混用不同 query 內容）。 |
| CODE-19 | 誤報（作為漏洞） | 沒有單引號屬性 sink；現有 esc 已處理雙引號，函式重複是清理，不是缺陷。`index.html:1736`：`String(s).replace(/[&<>\"]/g,…)`；`:1812`：`href="${esc(href)}"`；`:1939`：`src="${src}"` 的實際呼叫 `:2763` 是常數圖檔。沒有證據支持可利用路徑；不要把將來可能改成單引號當現存漏洞。 |

## 3. 漏掉

以下均由原始碼推導，未執行重現。狀態 ❌ 代表明確寫入／丟棄路徑；仍需 lead 在假資料庫驗收。

| 新 ID（CX-01 起） | 狀態 | 優先 | 發現 | 程式證據 | 建議 |
|---|---|---|---|---|---|
| CX-01 | ❌ 靜態成立 | P2 | 排序不只是改 order，而是批次重送多筆完整清單。A 修改內容，B 未收更新就排序，B 可一次把多筆標題、備註、期限蓋回；UX-02 只列編輯表單，未列這個入口。 | `index.html:3532`：`it.order=i+1;changed.push(it)`；`:3537`：`putMany(changed.map(it=>{const{id,...rec}=it;return["items/"+id,rec]}));`；`:2973`：`for(const[p,d]of list)b.set(ref(p),d)`；`:1753`：`outbox[p]={d,s}`。 | 排序只送 order patch；批次 API、outbox 的 merge 旗標及快照疊加一起支援，保留批次原子性。不要僅把所有 b.set 改 merge，卻繼續傳完整舊資料。 |
| CX-02 | ❌ 靜態成立 | P2 | 訂房與旅平險共用 settings/sos；不同人離線改不同區塊也會整筆蓋掉另一區。即使已收到最新快照，同一區表單仍可能含開啟時的舊欄位。 | `index.html:3383`：`BOOK_FIELDS=[…],INS_FIELDS=[…]`；`:3385`：`const n={...sosInfo};…n[i.dataset.sosF]=i.value.trim();…put("settings/sos",sosInfo)`；`:2998`：`sosInfo=x.data()\|\|{};…if(!sosEditing)paintSos()`。 | 表單開啟時保存 baseline，只送使用者改動欄位並 merge；空字串清除要保留。訂房與保險可分文件，但非必要。 |
| CX-03 | ❌ 靜態成立 | P3 | 倒數歸零的 reload 沒有任何草稿判斷，可繞過 UX-03 將來加的 busyEditing。條件較窄：App 前一天載入，跨日被有值輸入框擋住後，留著首頁倒數到起飛時；例如首頁上方錢包層正在填。 | `index.html:1993–1995`：`if(cdParts().ms>0){…id="cd-s"…}`；`:2891`：`if(c.ms<=0){if(todayIdx<0&&jpDay()>=start){location.reload();return}render(true);return}`；`:1820` 跨日可因有值輸入而暫緩。 | 所有自動 reload 共用同一安全入口；不要只修 dayCheck。倒數歸零先更新非破壞性 UI，等草稿處理完才重載。 |
| CX-04 | ❌ 靜態成立 | P3 | reloadSoon 已用 busyEditing，但第一次設定錢包不會設 walletEdit；金額只在 DOM，焦點離開輸入框後便可能在程式庫恢復時被 reload 丟掉。 | `index.html:2390`：`walletEdit=null`；`:2333`：`const editing=walletEdit===me\|\|!set`；`:2337`：`<input name="amt" …>`；`:3024–3025`：只判 activeElement 與 `…\|\|walletEdit`；`:3029–3032`：不忙就 `location.reload()`。 | 用獨立錢包草稿與 dirty 判斷，涵蓋初次設定和補錢；不要用是否開啟編輯模式當是否有未存內容。重載前可保存草稿與所屬旅程。 |
| CX-05 | ❌ 靜態成立 | P3 | 錢包輸入還有更常見的丟失入口：任一記帳或錢包快照直接重畫面板，未保存 DOM 金額；對方記一筆也能清空你正在填的補錢。不同於 CX-04 的 reload。 | `index.html:2344`：`c.innerHTML=walletSheetHTML()`；`:2337`：金額 input 沒有草稿 value；`:2996` expenses 回呼：`paintWalletSheet();`；`:2997` wallet 回呼：`paintWalletSheet();`。 | 資料更新只重畫餘額區，或先保存並還原錢包草稿、模式、身分與焦點；使用者按取消或儲存才清除。 |
| CX-06 | ❌ 靜態成立 | P3 | 不用 hash 也能把 pending 寫入送往另一旅程：權限拒絕觸發 badCode 清除目前代碼、保留 outbox，重新輸入不同有效代碼沒有 pending 擋阻，就會 flush 舊資料。這是 CODE-10 未列的正常表單／錯誤恢復路徑。 | `index.html:3017–3018`：`db=null;live=false;…localStorage.removeItem(TRIP_KEY)`；`:2838–2841`：表單驗格式後 `localStorage.setItem(TRIP_KEY,v);…connect()`；`:2985`：`flushOutbox()`；`:3047` 的 `if(pendingCount())return` 僅存在「換一個代碼」按鈕。 | 每筆佇列綁定建立時旅程；錯誤恢復與 hash／手動輸入共用切換程序。原旅程不明的舊佇列要隔離並讓使用者決定，不自動歸給新代碼；和 CODE-10 一起修，不重複計算同一底層缺陷。 |
| CX-07 | ❌ 靜態成立 | P3 | 自動匯率請求只在開始前檢查 auto。請求尚未返回時手動改匯率，舊回應仍會把模式寫回 auto 並整筆上傳，蓋掉剛做的手動選擇；兩支手機一支慢請求、一支改手動也有同路徑。 | `index.html:3352`：`if(rateBusy\|\|!rateMeta.auto)return`；`:3356`：`await fetch(…)`、`await r.json()`；`:3358–3360`：`rateMeta={auto:true,…};…put("settings/rate",{jpyTwd:rate,auto:true,…})`；`:2815` 手動會 `rateMeta={auto:false,…}`。 | 開始請求時記設定世代；每次 await 後／寫入前確認仍是同一自動世代，否則忽略。收到手動快照或本機改手動要使舊請求失效；單用 merge 不會解決同欄位覆蓋。 |

其餘指定方向的核對結果：

| 方向 | 結果與程式證據 |
|---|---|
| 錢包整筆 put | 不同人使用 `wallet/<who>`，正常各改自己不會互蓋；同一身分兩裝置的「補錢」為讀改寫，可能少算一次補入，但不是 merge 能解決的不同欄位問題。`index.html:2405`：`mode==="add"?cashIn(me)+py.v:py.v`；`:2412`：`put("wallet/"+w,wallet[w])`。同身分併發是否要支援列待確認；CX-05 是不同身分也可觸發的確定缺口。 |
| 心情整筆 put | key 含日期與人，正常兩人各寫自己的 key，不能直接類比 UX-01。`index.html:1847`：`const mk=(d,who)=>d.replace("/","-")+"_"+who`；`:1928–1929`：`key=mk(d,me),rec={score,note,ts:Date.now(),who:me,day:d};…put("moods/"+key,rec)`。同身分多裝置改同一天有最後寫入行為；不另造正常兩人互蓋缺陷。 |
| 勾選／行李／設定勾選 | 每個文件只含 done；行李與手機設定 key 另分人。`index.html:2788`：`put("checks/"+k,{done:v})`；`:2819`：`put("checks/"+id,{done:t.checked})`；`:3101`：`put("checks/"+id,{done:v})`。不同項目不共文件，同一項目最後操作覆蓋是同欄位行為，不能用 merge 解決；行李項目內容編輯則已包含 UX-02。 |
| settings/meta | `index.html:2535`：`const meta=await db.doc("settings/meta").get(),m=…`；`:2542`：`put("settings/meta",{...m,itemsSeeded:true,itemsRestore:2})`。目前介面沒有其他可獨立編輯的 meta 欄位；沒有證據支持另一件使用者欄位被覆蓋，不列。初始化批次同時把本機預設項目寫回的競態另留待確認。 |
| 匯率整筆 put | jpyTwd／auto／ts／src 是同一次設定，直接拆成互不相關 patch 反而可能留下不相容來源；手動寫入沒 src 但 auto=false 時本來不顯示來源。`index.html:2815`：`put("settings/rate",{jpyTwd:v,auto:false,ts:rateMeta.ts})`；`:3347`：`if(!rateMeta.auto)return …手動設定…`。真正缺口是 CX-07 的過期非同步回應。 |
| 其他全螢幕層／面板 | 沒找到第三個應接 modal 而未接的常駐 dialog。`index.html:1961` 地圖 `const close=modal(v,…)`、`:2303` 記一筆 `v._close=modal(v,…)`、`:2393` 錢包、`:2604` 行事曆、`:3126` 設定、`:3499` 給司機看、`:3505` 求助皆已接。`:2290` 的 `.exp-confirm` 是內嵌記帳確認區，`:2305` 有 Esc 攔截，非另一個獨立全螢幕層。開場（`:2703–2705`）是 B5 的短暫動畫，toast（`:2614–2619`）、復原條（`:3522–3526`）是非模態通知，不應硬接 modal。 |

## 4. 修法風險

| 原 ID | 風險 | 建議做法 |
|---|---|---|
| UX-03 | 直接改用 busyEditing 會延長「今天」凍結，且可能永久延後。`index.html:3025`：`…\|\|moodDraft\|\|editItem\|\|editingId\|\|stayEditing\|\|sosEditing\|\|walletEdit` 是模式／物件判斷；`:2771` 只點分數也建 moodDraft，空白新清單也設 editItem（:2777）。切其他分頁未必清空旗標。`today`／`todayIdx` 在 `:1818–1828` 都是載入時 const，`:1919` 的「今天」與 `:1966` 的預設記帳日期仍依舊值。 | 區分有內容的 dirty 與開著的編輯模式，定義送出、取消、離頁時的清除；確認 dirty 是否仍對應可恢復草稿。延後期間要保住草稿並更新目前日期的衍生資訊，或顯示換日待處理狀態；完成後再重載。不要只把 LOADED_DAY 更新為新日期卻留下舊 todayIdx，那會使之後 dayCheck 永遠認為已處理。所有自動重載統一入口，並涵蓋 CX-03／04。 |
| UX-01／02 | 全面把 put 改成 patch，可能讓第一次寫入只剩一個欄位；刪除與 patch 競態也可能重新建立殘缺文件。`index.html:1747–1749`：`if(opt&&opt.merge&&data!=null){if(o&&o.d)e={d:{...o.d,...data},s,...(o.m?{m:1}:{})};else e={d:data,s,m:1};}`；`:2861` 新帳目前整筆，`:2551` saveItem 同時服務新增、編輯、復原。 | UX-01 已有新帳在 outbox 的情況，現有 put 合併邏輯會保留完整新增，應保留它。UX-02 明確區分新增／補預設／復原的完整資料與既存編輯 patch；不要用一個一律 patch 的 saveItem。遠端已刪除則提示衝突，避免單欄位 merge 使文件復活；安全規則或交易的實作可另討論。 |
| UX-02 | 「只送和目前 items 不同的欄位」仍可能寫回使用者沒動的表單舊值。`index.html:2834–2835`：送出時才 `old=items.find(…)`，但 title／note 等直接取表單；`:2755`：`if(editItem)return` 只停止畫面重畫，`:2991–2992` 仍更新 items。 | 開啟編輯時保存 baseline；比較表單與 baseline，只傳使用者真正改的欄位。若對方也改同欄位，提示衝突或採已決定規則；不要拿最新快照當表單基準。排序採 CX-01 的專用 order patch。 |
| UX-04／CODE-07 | modal 只處理焦點／Tab／Esc，不會破壞現有點擊及方向鍵；但若改 DOM 包裝或刪局部 listener，可能破壞操作。`index.html:2379–2380`：capture handler 只特別處理 Escape／Tab；`:3285–3288` 回顧另綁點擊、方向鍵與觸控；`:3167` 導覽鏤空位置用實際畫面的 getBoundingClientRect。 | 保持原容器、點擊區、方向鍵及手勢 handler；讓所有關閉入口呼叫 modal 回傳的同一 close，移除舊 Esc 的重複關閉。modal 不要求新遮罩，不要新增會遮住鏤空或攔事件的 wrapper；保留導覽的 place／scroll／resize 與轉場完成定位。 |
| UX-04／CODE-07 | 只接 modal 還不夠：回顧非當頁仍是 opacity:0，不是 hidden，末頁按鈕仍會被共用 FOCUSABLE 收到；換頁後原本 focused 的 next 也可能被 hidden。`index.html:1186–1187`：`.st-page{…opacity:0;pointer-events:none}`／`.st-page.on{opacity:1;pointer-events:auto}`；`:2381` 只用 `getClientRects().length` 篩選；`:3282`：`…next.hidden=last;…prev.style.width=last?"0":""`。 | 每頁非作用時設 inert／適當 aria-hidden，並管理其可聚焦狀態；換頁後若目前焦點被隱藏，把焦點移至可見且合適的控制。保留淡入決定；不要為焦點管理擅自更改 B8。 |
| UX-04／CODE-07 | 導覽會換頁，入口可能不存在；從設定開導覽還會直接 remove 設定層，未經其 close，留下 modal 記錄。`index.html:3184`：`…goHome();scrollTo(0,0)`；`:3192`：`setupSheet.remove();setupSheet=null;…openTour()`；`:2351–2362` 的返回焦點需要可連接的 back 或 backSel。 | 導覽開始前經原設定層的 close 正常退棧，先記錄合理的返回入口／畫面；自動首開沒有按鈕時定義首頁焦點備援。最後「開始設定」先關導覽再開設定，避免返回焦點被新層搶回背景。不要宣稱套 modal 後一定能回到已被導覽移除的原按鈕。 |
| CODE-02／03／04 | 過度清洗可能把原資料誤刪，或為了救一筆壞資料讓整份畫面不顯示。`index.html:2994`：心情快照逐筆 `n[d.id]=d.data()`；`:2996`：帳目 `day:v.day`。 | 在讀取邊界逐筆驗證並保留原雲端資料，不自動寫回刪除；可跳過／隔離壞筆並提供診斷。URL scheme 篩選不可誤傷合法 https 連結，仍保留輸出 escaping。 |
| CODE-08／09／10、CX-06 | 「拒絕就刪 outbox」會遺失合法暫存；僅分 localStorage key 也未必足夠。`index.html:1762`：成功回呼使用 `obDone(path,s)`；`:1768` 只比 path／序號，沒有旅程；`:2972–2976` 的快照 overlay 同樣使用共用 outbox。 | db 連線、待送資料、快照 overlay、成功回呼與持久化都綁同一旅程／連線世代；避免舊連線回呼清掉新旅程資料。先分類永久／暫時錯誤，暫時錯誤 backoff 並顯示待同步；既有無旅程 outbox 遷移要保守隔離。 |
| CODE-12 | 只補刪雲端 @人 文件卻不刪本機 key，或復原沒恢復原勾選，會產生不同步。`index.html:2554–2558` 已保存 `dk`／`dv` 並復原每個 key；`:2561` 目前只 `delete done[id]`。 | 用同一份 dk 刪本機和雲端；復原仍按 dv 還原全部 key。驗收含預設行李刪除、補回與 5 秒內復原，避免破壞已決定的復原提示 C11。 |
| CODE-16／18／19 | 清理時誤改既有視覺或資源語意。`index.html:1411/1415` 重複 gDusk；`sw.js:35/39` 以完整 request 為 key；`index.html:1809–1812` 的 sosEsc 對 null 與 esc 不同（null 轉空字串）。 | gDusk 去重先確認保留外觀；query 正規化限確定等價的首頁追蹤參數；合併 esc/sosEsc 時保留 null 行為。這些不是為了修 CODE-01 必須一併做的變動。 |

## 5. 待確認

1. **保留原報的設計待確認，不自行認定缺陷。** CODE-06 的小型淡入、導覽框尺寸及行程展開動效，見 `index.html:1120`：`transition:left…top…width…height…`、`:2749`：`body.animate([{height:"0px",opacity:0},…])`。CODE-16 的暮色兩組顏色見 `:1411/1415`。B8 指定進場已結案，C9a 回顧入口、C11 重複復原提示、D12 備註 Enter 都不再列待確認。
2. **UI 原報的規則文字與實機現象。** 選項黃底／類別色是否需澄清 A2；小字、缺字及浮動鈕遮擋留實機。`index.html:1454`：底導覽 `aria-selected`；`:3248` 的登機證及其他回顧小字也是不同字級，不能由 UI-04 推論全站違反最小字級規範。`index.html:851`：`.acct-fab{position:fixed;…bottom:calc(104px + env(safe-area-inset-bottom,0px));…}`，實際遮擋／捲到底可達性須以 viewport 和裝置確認。空清單是否要增加說明是文案偏好（`:2509` 仍有「新增一項」），不直接排 bug。
3. **CODE-08 的外部 SDK 錯誤碼與永久錯誤處理。** `index.html:2949`：`const FB_V="10.12.2"`；`:1763` 比對 `invalid_argument`。本次遵守只讀檔，未查外網或執行 SDK；由 lead 對該版 enum／既有本機 SDK 定義確認。CODE-02 的外部寫入權限及瀏覽器行為同樣未驗，安全規則不在範圍。
4. **同身分多裝置的並行語意。** `index.html:2405`：補錢以 `cashIn(me)+py.v` 算總額；`:1928` 心情以 `mk(d,me)` 定址。正常兩人不同身分不互蓋；若需支援同身分多裝置離線同時補錢，應使用增量事件／交易，而非 merge 假裝解決。同欄位心情編輯的衝突政策也需先定義，不另列確定缺陷。
5. **首次種資料競態。** `index.html:2537`：`await Promise.race([itemsLoaded,new Promise(r=>setTimeout(r,4000))])`；`:2540–2541`：缺 serverIds 即組整筆 `putMany(list)`。若首次連線快照超過 4 秒、meta 仍舊，本機舊預設值可能被當缺項回送；需要假資料庫精準安排 get(meta)、快照與寫入時序才能確認，不猜測為已重現覆蓋。

執行限制：本次只做檔案與 Git 狀態讀取，唯一寫入為本檔；未修改網站、未 commit、未跑任何測試。後續由 lead 以假資料庫重現 CX-01～07 與修法風險，不把本次靜態審查描述成新一輪實測全綠。
