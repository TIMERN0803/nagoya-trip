# 測試工具（不影響網站）
放在 /home/claude/build（腳本內路徑寫死這個位置）。
- 本機伺服器：cd /home/claude/nagoya-trip && python3 -m http.server 8766
- 功能測試：cd /home/claude/build/ft && python3 fulltest.py（177 項）
- 專項測試（都在 ft/）：duetest fabtest packtest gotest buytest cashtest sostest undotest sorttest janktest setuptest tourtest tftest placetest reviewtest fxtest nexttest hometest sostabtest voicetest sheettest synctest fixtest helptest layouttest smalltest
- smalltest：v44 第三批 3C（沒設定錢包時記現金帳的「設定錢包」入口、語音連點狀態）
- layouttest：v44 第三批 3B（320px／200% 縮放無水平捲動、可點範圍 44、首頁「今天」對比、排序鍵盤）
- helptest：v44 第三批 3A（首頁和當天行程頁的求助、飯店捷徑、給司機看只按 × 關閉與橫向捲動、面板 Esc／焦點、窄螢幕標題列）
- fixtest：v44 第二批修正的回歸測試（金額輸入、兩人同時改帳、航班時區、過期待辦、匯率、分機、旅程代碼、沒選身分、超支、連點）
- synctest：同步與離線回歸測試（v44 第一批）。用 ft/fs_offline.js 模擬 Firestore 離線、慢伺服器、權限錯誤；SW 項目會在 8767 埠開暫存網站複本
- 日期掃描：cd /home/claude/build && python3 sweep.py；清單同步：python3 t5.py
- ft/fs.js、ft/app.js 是 Firebase 的假資料庫；ft/fs_offline.js 是會模擬離線的版本（synctest、fixtest 用）；兩個假資料庫都支援 setDoc(...,{merge:true})
- 行事曆檔：node mkics.js 產生 nagoya-trip.ics
- 測試前先 node mkdays.js 產生 /tmp/days.json；t5 需要 mock/（ft/app.js、ft/fs.js 的複本）
- 真實訂房資料只放 .sos-private.json（已列入 .gitignore，repo 是公開的，不要提交）
- 本機伺服器用背景方式啟動，2 小時後會自動停止，測試出現 ERR_CONNECTION_REFUSED 時重新啟動即可

- **v44 獨立測試結果與修正計畫**：見 `qa/README.md` 和 `qa/fix-plan.md`（兩份測試報告、重現腳本、離線模擬 `qa/claude/scripts/fs_offline.js`）
