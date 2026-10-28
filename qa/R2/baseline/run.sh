#!/bin/bash
# 全套回歸基準：v60 main
cd /home/claude/nagoya-trip && (python3 -m http.server 8766 >/dev/null 2>&1 &) ; sleep 1
OUT=/home/claude/baseline/logs; mkdir -p $OUT
cd /home/claude/build/ft
for t in fulltest duetest fabtest packtest gotest buytest cashtest sostest undotest sorttest janktest setuptest tourtest tftest placetest reviewtest fxtest nexttest hometest sostabtest voicetest sheettest synctest fixtest helptest layouttest smalltest listtabtest transtest loadtest; do
  s=$(date +%s); timeout 1500 python3 $t.py > $OUT/$t.log 2>&1; rc=$?
  p=$(grep -c '^PASS' $OUT/$t.log); f=$(grep -c '^FAIL' $OUT/$t.log)
  echo "$t rc=$rc pass=$p fail=$f $(( $(date +%s)-s ))s" >> $OUT/summary.txt
done
cd /home/claude/build
s=$(date +%s); timeout 1500 python3 sweep.py > $OUT/sweep.log 2>&1; echo "sweep rc=$? $(( $(date +%s)-s ))s" >> $OUT/summary.txt
s=$(date +%s); timeout 1500 python3 t5.py > $OUT/t5.log 2>&1; echo "t5 rc=$? $(( $(date +%s)-s ))s" >> $OUT/summary.txt
echo DONE >> $OUT/summary.txt
