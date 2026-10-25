# 名古屋 PWA 測試附件（Windows）

先讀 codex-test-report-v44.md，原始數據在 evidence，重現腳本在 work。
所有結果來自假資料庫；不要開正式 App 或輸入任何正式旅程代碼。

## 準備

1. 將此 ZIP 解壓到新工作資料夾；具備 Python 3.12、Node.js、Git、Chrome。
2. 把可用 Python 執行環境放在 work/python/python.exe（本次用 embeddable Python 3.12.10＋pip）；也可自行將以下命令的 Python 路徑改成你的環境。
3. 安裝依賴：work/python/python.exe -m pip install playwright==1.64.1
4. 下載測試來源，僅本機使用，不要提交測試調整：

```powershell
git clone --branch main https://github.com/TIMERN0803/nagoya-trip.git app-source
git -C app-source checkout bdc133039c0a360d11ea0733b10a715c58b2d9f8
git clone --branch tools https://github.com/TIMERN0803/nagoya-trip.git test-tools
git -C test-tools checkout ced748894bef30f1fd053127e4d846ab9724cab6
$env:PYTHONUTF8='1'
New-Item -ItemType Directory work/tmp -Force
$env:TEMP=(Resolve-Path work/tmp).Path
$env:TMP=$env:TEMP
work/python/python.exe -X utf8 work/prepare.py
node work/run-tools/mkdays.js
```

runner 使用 Chrome 路徑 C:\Program Files\Google\Chrome\Application\chrome.exe；若不同請只修改自己的 runner 副本。不要直接執行原始測試，應經過 run_test.py 套用安全隔離。

## 啟動伺服器

在另一個 PowerShell 保持開啟（只服務本機）：

```powershell
work/python/python.exe -m http.server 8766 --bind 127.0.0.1 --directory app-source
```

一般測試：

```powershell
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/fulltest.py
work/python/python.exe -X utf8 work/baseline_batch.py
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/independent.py
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/layout_complete.py
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/followup.py
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/journey.py
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/advanced.py
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/final_probe.py
```

回顧原基準若使用下載分支，先設 $env:FORCE_DOWNLOAD='1' 再執行 reviewtest.py；完成後 Remove-Item Env:FORCE_DOWNLOAD。原生分享是否成功需另驗，不能只等 download。

獨立腳本使用 rec() 記錄布林檢查，退出碼不代表所有檢查成功；請讀 results.json 和 PASS／FAIL。預期會重現報告的缺陷。

## 安全離線測試

在另一個視窗執行 work/python/python.exe -X utf8 work/isolated_server.py，提供 8767 的同源假 SDK＋CSP fixture。這個 fixture 是唯一允許 SW 的測試入口。

```powershell
$env:SAFE_SW='1'
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/offline_probe.py
work/python/python.exe -X utf8 work/run_test.py work/run-tools/ft/offline_baseline.py
Remove-Item Env:SAFE_SW
```

不要將 SAFE_SW 套用在正式網站或原版未改來源的 server 上。外部請求攔截不保證涵蓋 Service Worker 自己發出的請求，所以此處必須用 8767 fixture。

## 資料與限制

- evidence/baseline/fulltest-original-results.json 是首輪 SW 封鎖造成離線中斷的原始紀錄；offline-baseline.json 是兩個原離線檢查的安全補測。
- reviewtest.log 是原生分享平台差異的首輪紀錄；reviewtest-confirmed.log 是關閉分享、驗下載分支的 23 項通過紀錄。
- evidence/independent/results.json 是確認輪的 94 個檢查；其中 13 個失敗檢查去重成 3 類缺陷，另外量測到 44px 問題。layout-complete.json 是五分頁六尺寸 42 項通過。
- report 所稱「無 Firestore 正式寫入」建立在只載入本地 fake SDK、外部封鎖以及隔離 SW fixture；安全紀錄的外部封鎖次數不能單獨證明所有真實網路請求。
- 部分 PowerShell 轉存日誌有中文字元編碼問題；直接由 Python 寫出的 UTF-8 JSON 為主要依據。fulltest-readable.log 是從原始 JSON 重建的可讀版，不是另跑一次。
- 截圖為本次模擬資料；沒有任何正式訂房、保險或真實旅程內容。PNG 使用本機 Chrome 字型與渲染，不能取代 iPhone 實機。
