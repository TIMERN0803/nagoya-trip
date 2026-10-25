# 測試工具（不影響網站）
放在 /home/claude/build（腳本內路徑寫死這個位置）。
- 本機伺服器：cd /home/claude/nagoya-trip && python3 -m http.server 8766
- 功能測試：cd /home/claude/build/ft && python3 fulltest.py（177 項）
- 專項測試（都在 ft/）：duetest fabtest packtest gotest buytest cashtest sostest undotest sorttest janktest setuptest tourtest tftest placetest reviewtest fxtest nexttest hometest sostabtest voicetest sheettest
- 日期掃描：cd /home/claude/build && python3 sweep.py；清單同步：python3 t5.py
- ft/fs.js、ft/app.js 是 Firebase 的假資料庫
- 行事曆檔：node mkics.js 產生 nagoya-trip.ics
- 測試前先 node mkdays.js 產生 /tmp/days.json；t5 需要 mock/（ft/app.js、ft/fs.js 的複本）
- 真實訂房資料只放 .sos-private.json（已列入 .gitignore，repo 是公開的，不要提交）
- 本機伺服器用背景方式啟動，2 小時後會自動停止，測試出現 ERR_CONNECTION_REFUSED 時重新啟動即可
