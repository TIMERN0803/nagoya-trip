# 回歸基準（批 0）

- 執行：2026-10-28，lead，沙箱（Playwright Chromium，假資料庫）
- 對象：main `e3f5a5a`（ngy-v60）；測試工具：tools `add4c79`
- 腳本：`qa/R2/baseline/run.sh`（依 tools README 列的順序跑全部專項，最後 sweep、t5）；每支的完整輸出在 `qa/R2/baseline/<名稱>.log`

## 結果：全綠

**30 支專項測試，1,055 項全部通過，0 項失敗。** sweep 10 個時間點、t5 4 個情境都沒有錯誤。

| 測試 | 通過 | 失敗 | 秒 |
|---|---|---|---|
| fulltest | 177 | 0 | 94 |
| duetest | 10 | 0 | 8 |
| fabtest | 18 | 0 | 15 |
| packtest | 16 | 0 | 13 |
| gotest | 3 | 0 | 7 |
| buytest | 8 | 0 | 6 |
| cashtest | 25 | 0 | 20 |
| sostest | 32 | 0 | 15 |
| undotest | 34 | 0 | 27 |
| sorttest | 21 | 0 | 15 |
| janktest | 5 | 0 | 5 |
| setuptest | 20 | 0 | 25 |
| tourtest | 35 | 0 | 20 |
| tftest | 18 | 0 | 17 |
| placetest | 7 | 0 | 12 |
| reviewtest | 23 | 0 | 18 |
| fxtest | 14 | 0 | 91 |
| nexttest | 5 | 0 | 9 |
| hometest | 63 | 0 | 64 |
| sostabtest | 37 | 0 | 14 |
| voicetest | 15 | 0 | 14 |
| sheettest | 63 | 0 | 32 |
| synctest | 80 | 0 | 101 |
| fixtest | 64 | 0 | 76 |
| helptest | 71 | 0 | 58 |
| layouttest | 47 | 0 | 43 |
| smalltest | 13 | 0 | 16 |
| listtabtest | 27 | 0 | 25 |
| transtest | 82 | 0 | 50 |
| loadtest | 22 | 0 | 25 |

- **sweep**：台灣 10/24、出發前一晚、起飛前、起飛後、11/17 15:00、11/18 23:30、11/24 06:00、回國 11/24 20:00、11/25、12/20，開啟頁面與倒數都合理，`錯誤=[]`。
- **t5**：清單同步 4 個情境，新增後伺服器與畫面各 +1，使用者刪掉的項目沒有被加回，`[]`。

## 順手記下的工具問題（不是網站問題，批 1 一起處理）
- tools `README.md` 第 9 行寫「彈窗滑上 0.5 秒輕彈」，但 10/27 已改成不回彈（commit 8437626），`transtest.py` 也是驗證「不回彈」。README 過時。
- `ft/pulsetest.py` 在資料夾裡，但 README 的專項清單沒有列；本次沒有跑。需要確認是已淘汰還是漏列。
- 上一份交接說「v57 為止是綠的」；這次確認 **v60 也是綠的**。
