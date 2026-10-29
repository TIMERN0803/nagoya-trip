#!/bin/bash
# 跑全部專項測試＋fulltest＋sweep＋t5，彙整到 /tmp/runall/summary.txt
# 用法：EXTRA="conflicttest reloadtest focustest" ./runall.sh   （P=並行數，預設 4）
cd /home/claude/build/ft || exit 1
BASE="duetest fabtest pulsetest packtest gotest buytest cashtest sostest undotest sorttest janktest setuptest tourtest tftest placetest reviewtest fxtest nexttest hometest sostabtest voicetest sheettest synctest fixtest helptest layouttest smalltest listtabtest transtest loadtest scenetest"
LIST="fulltest $BASE $EXTRA ${ONLY_EXTRA:-}"
[ -n "$ONLY" ] && LIST="$ONLY"
OUT=/tmp/runall; rm -rf $OUT; mkdir -p $OUT
echo $LIST | tr ' ' '\n' | grep . | xargs -P ${P:-4} -I{} sh -c 'timeout 1500 python3 {}.py > '$OUT'/{}.log 2>&1; echo $? > '$OUT'/{}.rc'
[ -z "$ONLY" ] && { (cd /home/claude/build && timeout 1200 python3 sweep.py > $OUT/sweep.log 2>&1; echo $? > $OUT/sweep.rc; timeout 900 python3 t5.py > $OUT/t5.log 2>&1; echo $? > $OUT/t5.rc); }
: > $OUT/summary.txt
for f in $OUT/*.log; do n=$(basename $f .log); p=$(grep -c '^PASS' $f); x=$(grep -c '^FAIL' $f); rc=$(cat $OUT/$n.rc 2>/dev/null); echo "$n PASS $p FAIL $x rc $rc" >> $OUT/summary.txt; done
cat $OUT/summary.txt | awk '{s+=$3;f+=$5} END{print "SUM PASS",s,"FAIL",f}' >> $OUT/summary.txt
