// 從 index.html 的 DAYS 產生行事曆檔：每個有時間的行程，前 30 分鐘提醒；航班另外提前 2 小時
const fs=require("fs");
const html=fs.readFileSync(process.argv[2],"utf8");
const a=html.indexOf("const DAYS=["),b=html.indexOf("];\n",a)+1;
const DAYS=eval(html.slice(a+"const DAYS=".length,b));
const YEAR=2026;
const pad=n=>String(n).padStart(2,"0");
const esc=s=>String(s||"").replace(/\\/g,"\\\\").replace(/;/g,"\;").replace(/,/g,"\\,").replace(/\n/g,"\\n");
const fold=l=>{const out=[];let cur="";for(const ch of l){if(Buffer.byteLength(cur+ch)>73){out.push(cur);cur=" "+ch}else cur+=ch}out.push(cur);return out.join("\r\n")};
const L=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//nagoya-trip//TW","CALSCALE:GREGORIAN","METHOD:PUBLISH","X-WR-CALNAME:名古屋看花花",
"BEGIN:VTIMEZONE","TZID:Asia/Tokyo","BEGIN:STANDARD","DTSTART:19700101T000000","TZOFFSETFROM:+0900","TZOFFSETTO:+0900","TZNAME:JST","END:STANDARD","END:VTIMEZONE",
"BEGIN:VTIMEZONE","TZID:Asia/Taipei","BEGIN:STANDARD","DTSTART:19700101T000000","TZOFFSETFROM:+0800","TZOFFSETTO:+0800","TZNAME:CST","END:STANDARD","END:VTIMEZONE"];
let n=0;
DAYS.forEach(x=>{const[m,d]=x.d.split("/").map(Number);
 x.items.forEach((it,i)=>{const mt=/(\d{1,2}):(\d{2})/.exec(it.t||"");if(!mt)return;
  let tz="Asia/Tokyo",dur=60,end=null;
  if(/^JX 320/.test(it.n)){tz="Asia/Taipei";end=["Asia/Tokyo",10,40]}
  if(/^JX 321/.test(it.n)){end=["Asia/Taipei",14,20]}
  const date=`${YEAR}${pad(m)}${pad(d)}`,st=`${date}T${pad(+mt[1])}${pad(+mt[2])}00`;
  const e=end?`DTEND;TZID=${end[0]}:${date}T${pad(end[1])}${pad(end[2])}00`:(()=>{const t=+mt[1]*60+ +mt[2]+dur;return `DTEND;TZID=${tz}:${date}T${pad(Math.floor(t/60)%24)}${pad(t%60)}00`})();
  const label=it.l||({fly:"航班",move:"交通",go:"景點",eat:"餐廳",stay:"住宿",do:"預約",remind:"提醒",buy:"外帶"})[it.k]||"";
  const desc=[label,it.jp,it.p,"名古屋看花花 https://timern0803.github.io/nagoya-trip/"].filter(Boolean).join("\n");
  L.push("BEGIN:VEVENT",`UID:ngy-${date}-${i}@nagoya-trip`,"DTSTAMP:20261024T000000Z",`DTSTART;TZID=${tz}:${st}`,e,fold("SUMMARY:"+esc(it.n)),fold("DESCRIPTION:"+esc(desc)));
  if(it.map)L.push(fold("LOCATION:"+esc(it.map)),fold("URL:https://www.google.com/maps/search/?api=1&query="+encodeURIComponent(it.map)));
  L.push("BEGIN:VALARM","ACTION:DISPLAY",fold("DESCRIPTION:30 分鐘後："+esc(it.n)),"TRIGGER:-PT30M","END:VALARM");
  if(it.k==="fly"&&/^JX/.test(it.n))L.push("BEGIN:VALARM","ACTION:DISPLAY",fold("DESCRIPTION:2 小時後起飛："+esc(it.n)),"TRIGGER:-PT2H","END:VALARM");
  L.push("END:VEVENT");n++});});
[["20261115T070500","Asia/Taipei","去程線上選位開放（JX 320）","seat1"],["20261120T200000","Asia/Tokyo","搶 KISO 號碼牌開放","kiso0"],["20261122T114000","Asia/Tokyo","回程線上選位開放（JX 321）","seat2"]].forEach(([st,tz,t,id])=>{if(id==="kiso0")return;
 const end=st.slice(0,9)+String(+st.slice(9,11)).padStart(2,"0")+String(+st.slice(11,13)+15).padStart(2,"0")+"00";
 L.push("BEGIN:VEVENT",`UID:ngy-${id}@nagoya-trip`,"DTSTAMP:20261024T000000Z",`DTSTART;TZID=${tz}:${st}`,`DTEND;TZID=${tz}:${end}`,fold("SUMMARY:"+esc(t)),fold("DESCRIPTION:"+esc("行前待辦\n名古屋看花花 https://timern0803.github.io/nagoya-trip/")),
 "BEGIN:VALARM","ACTION:DISPLAY",fold("DESCRIPTION:"+esc(t)),"TRIGGER:-PT30M","END:VALARM","BEGIN:VALARM","ACTION:DISPLAY",fold("DESCRIPTION:"+esc(t)),"TRIGGER:PT0M","END:VALARM","END:VEVENT");n++});
L.push("END:VCALENDAR");
fs.writeFileSync(process.argv[3],L.join("\r\n")+"\r\n");
console.log(n+" events");
