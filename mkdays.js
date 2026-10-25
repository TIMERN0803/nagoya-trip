// 從 index.html 取出 DAYS 給測試用：node mkdays.js → /tmp/days.json
const fs=require('fs');const s=fs.readFileSync('/home/claude/nagoya-trip/index.html','utf8');
const i=s.indexOf('const DAYS=[');const j=s.indexOf('\n];',i)>0?s.indexOf('\n];',i)+3:s.indexOf('];',i)+2;
const DAYS=eval(s.slice(i+11,j).replace(/;\s*$/,''));fs.writeFileSync('/tmp/days.json',JSON.stringify(DAYS));console.log(DAYS.length,'days');
