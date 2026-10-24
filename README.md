# 測試工具（不影響網站）
放在 /home/claude/build（腳本內路徑寫死這個位置）。
- 本機伺服器：cd /home/claude/nagoya-trip && python3 -m http.server 8766
- 功能測試：cd /home/claude/build/ft && python3 fulltest.py（177 項），另有 duetest / fabtest / packtest / gotest / buytest / cashtest
- 日期掃描：cd /home/claude/build && python3 sweep.py；清單同步：python3 t5.py
- ft/fs.js、ft/app.js 是 Firebase 的假資料庫
- 行事曆檔：node mkics.js 產生 nagoya-trip.ics
