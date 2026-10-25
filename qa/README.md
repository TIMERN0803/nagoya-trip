# QA：v44 的獨立測試結果與修正計畫

| 檔案 | 內容 |
|---|---|
| `fix-plan.md` | **從這裡開始看**。兩份報告合併後的修正計畫，分三批，附每項的要點和驗收方式 |
| `test-brief.md` | 給測試者的委託書，正式旅程代碼已移除 |
| `claude/test-report.md` | 獨立測試代理的報告，27 項 |
| `claude/scripts/` | 獨立測試代理寫的重現腳本。共用設定在 `qa_common.py`，`fs_offline.js` 是能模擬離線的假資料庫，`out_*.json` 是當次的執行結果 |
| `claude/baseline/` | 當次跑既有測試的紀錄 |
| `codex/codex-test-report-v44.md` | Codex 的報告，4 項 |
| `codex/work/` | Codex 的腳本，原本是在 Windows 上跑的，路徑由 `prepare.py` 調整 |
| `codex/evidence/` | Codex 的 JSON 和 log 紀錄。截圖沒有收進 repo |
| `setup_qa.sh` | 讓 `claude/scripts` 能在沙箱照原路徑執行 |

## 在沙箱重跑 claude/scripts

```bash
# 先照 tools README 準備好 /home/claude/nagoya-trip、/home/claude/build，本機伺服器跑在 8766
bash /home/claude/build/qa/setup_qa.sh     # 建立 /home/claude/qa → qa/claude 的連結，並產生 SW 測試用的網站複本
cd /home/claude/qa/scripts && python3 t_offline.py   # 每支都可以單獨執行
```

- 腳本一律在本機假資料庫上執行，自建的 context 會攔截 Firebase，並另外擋掉 firestore.googleapis.com。
- `qa_common.py` 有防呆，不能使用正式旅程代碼：只存代碼的雜湊值，代碼本身不寫進 repo。
- 截圖寫到 `qa/claude/shots/`，網站複本寫到 `qa/claude/site_*`，這兩個都在 `.gitignore` 裡，不會被提交。
- 修完第一批後，`t_slowserver`、`t_slowlib`、`t_offline`、`t_coldcash`、`t_swlib` 原本 FAIL 的項目應該要變成 PASS。修好後請整理成正式回歸測試，放進 `ft/`。
- **第一批已修好（ngy-v45）**：上面五支和 Codex 的 mood_sync 全部 PASS，回歸測試是 `ft/synctest.py`。
  - 之後重跑 `t_sw.py` 會有 2 項顯示 FAIL：它要求快取清單「只有」新版本，但現在多了刻意保留的 `ngy-lib`（程式庫快取），屬於預期變化。
  - 腳本會覆寫 `claude/scripts/out_*.json`（當初的基準結果），跑完請用 `git checkout -- qa/claude/scripts/` 還原。
