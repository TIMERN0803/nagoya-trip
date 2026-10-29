# 批 5｜Codex 二次審查 NEXT_PROMPT

建立：2026-10-29（lead）。給明彰 Mac 上的 Codex（codex-rescue，唯讀）。

## 明彰要做的（Mac）
1. 取得最新的兩個分支：`git fetch origin && git checkout main && git pull --ff-only`（應為 `a320dcc`）；tools 用 worktree：`git worktree add ../nagoya-tools origin/tools-qa-r2`（已有就 `git -C ../nagoya-tools pull --ff-only`）。
2. 在 repo 根目錄啟動 Codex，貼上下面「提示」整段。
3. Codex 只會寫 `EXEC_LOG.md`（repo 根目錄，不要 commit）。做完把整份 EXEC_LOG 內容貼到 Project 的新對話（見 Project `claude/QA_R2_批5_開工提示詞.md`）。

## lead 的修正時機判斷（10/29）
批 3 的 4 項真問題**不先修，批 5 後一起修**：
- Codex 審的是凍結版 `a320dcc`，現在改 main 會讓行號與前提對不上。
- UX-01／02 是「整筆寫入沒有 merge」，Codex 這次要掃同類寫入，一起修才不會修一半。
- 都是 P2／P3，沒有立即風險；修正期 11/4 起，出發前還有時間。
- 修正分兩組上線：**bug**（UX-01～04、CODE-03 等）一次上；**體驗優化**（C9a 回顧入口提前、C11 復原提示、REPORT_2 的對比與字級）累積後一起上。

---

## 提示（貼給 Codex）

你是名古屋旅遊 PWA QA R2 的二次審查員（唯讀）。只讀檔，不跑測試、不改任何檔案、不 commit；唯一可以寫的是 repo 根目錄的 `EXEC_LOG.md`。

【對象】
- 網站：目前目錄的 main `a320dcc`（ngy-v61）：`index.html`、`sw.js`、`manifest.webmanifest`、`nagoya-trip.ics`
- 報告（在 `../nagoya-tools/qa/R2/`）：`REPORT_2.md`（UI）、`REPORT_3.md`（UX／Break Test）、`REPORT_4.md`（程式碼）；原文 `*_raw.md` 需要時才對照
- 規則：`../nagoya-tools/qa/R2/DECISIONS.md`（10/29 更新：B8 維持現況、新增 C9a、C11、D12）、`SCOPE.md` 第 5 節
- 行號以 `a320dcc` 為準

【要做的】
1. **誤報**：三份報告每個 ❌／⚠️，對照程式判斷前提是否成立（行號、條件、觸發路徑）。前提不成立、或和 DECISIONS 一致的，判為誤報並寫原因。
2. **優先級**：覺得太高或太低的，寫建議優先與理由。特別看：UX-01 升 P2、CODE-02／03 降 P3、CODE-10 維持 P3。
3. **漏掉**：從程式找三份報告都沒列的問題，重點：
   - 其他整筆 `put(...)` 沒有 `{merge:true}` 的寫入（錢包、心情、清單勾選、行李、設定、匯率），兩人同時改會不會像 UX-01／02 一樣蓋掉對方
   - 其他 `location.reload()` 路徑（倒數歸零約 :2891、`reloadSoon` 約 :3032）會不會丟未存內容
   - 其他沒走 `modal()` 的全螢幕層或面板（CODE-07／UX-04 以外）
   - outbox 與旅程代碼的關係（CODE-10 以外的路徑）
4. **修法風險**：報告裡的建議修法會不會造成新問題，例如
   - UX-03 改用 `busyEditing()` 後，有草稿時會不會一直不換天、或換天後「今天」顯示錯
   - UX-01／02 改 merge 後，新增項目（第一次寫入）會不會變成只寫部分欄位
   - UX-04 回顧／導覽改走 `modal()` 後，回顧的點擊換頁、方向鍵、導覽的鏤空框會不會被影響

【規則】
- 和 DECISIONS 一致的不算問題（B8 淡入、D12 備註 Enter 送出、C9a／C11 是已決定待實作，不列）。
- 不確定列「待確認」，不要猜；不要為了湊數量而列；偏好不是缺陷。
- 每項附檔名＋行號＋程式片段（10 行內）。
- 不讀 `.sos-private.json`，不寫出任何旅程代碼。

【EXEC_LOG.md 格式】
1. 一句話結論
2. 誤報與優先：`| 原 ID | 判定（誤報／維持／改優先 Px） | 理由與程式證據 |`（每個 ❌／⚠️ 都要一列）
3. 漏掉：`| 新 ID（CX-01 起） | 狀態 | 優先 | 發現 | 程式證據 | 建議 |`
4. 修法風險：`| 原 ID | 風險 | 建議做法 |`
5. 待確認
回覆用繁體中文。
