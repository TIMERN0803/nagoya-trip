#!/usr/bin/env bash
# 讓 qa/claude/scripts 的腳本可以照原路徑執行（腳本寫死 /home/claude/qa/...）
# 前提：網站在 /home/claude/nagoya-trip、tools 分支在 /home/claude/build（見 tools README）
set -e
Q=/home/claude/qa
if [ -e "$Q" ] && [ ! -L "$Q" ]; then echo "$Q 已存在且不是連結，請先移開"; exit 1; fi
ln -sfn /home/claude/build/qa/claude "$Q"
mkdir -p /home/claude/build/qa/claude/shots
# Service Worker 更新測試（t_sw.py、t_swlib.py）用的網站複本：v44＝目前網站、v45＝只改 sw 版本號
for v in v44 v45; do
  rm -rf "$Q/site_$v"; mkdir -p "$Q/site_$v"
  (cd /home/claude/nagoya-trip && git ls-files -z | xargs -0 -I{} cp --parents {} "$Q/site_$v/")
done
sed -i -E 's/ngy-v[0-9]+/ngy-v9045/' "$Q/site_v45/sw.js"
sed -i -E 's/ngy-v[0-9]+/ngy-v9044/' "$Q/site_v44/sw.js"
echo "完成。截圖會寫到 $Q/shots/（已列入 .gitignore，不要提交）。"
echo "本機伺服器：cd /home/claude/nagoya-trip && python3 -m http.server 8766（背景執行）"
