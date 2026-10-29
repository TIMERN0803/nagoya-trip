()=>{
function parse(c){const m=c.match(/rgba?\(([^)]+)\)/);if(!m)return null;const p=m[1].split(/[ ,\/]+/).map(Number);return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}}
function bgOf(el){let layers=[];for(let e=el;e;e=e.parentElement){const cs=getComputedStyle(e);const c=parse(cs.backgroundColor);if(cs.backgroundImage&&cs.backgroundImage!=="none"&&!/^url/.test(cs.backgroundImage)&&!/gradient/.test(cs.backgroundImage)){}
 if(c&&c.a>0){layers.push(c);if(c.a>=1)break}}
 let base={r:255,g:255,b:255};for(let i=layers.length-1;i>=0;i--){const c=layers[i];base={r:base.r*(1-c.a)+c.r*c.a,g:base.g*(1-c.a)+c.g*c.a,b:base.b*(1-c.a)+c.b*c.a}}return base}
function lum(c){const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b)}
function cr(a,b){const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
const out={sw:document.documentElement.scrollWidth,iw:innerWidth,low:[],small:[],trunc:[],hscroll:[]};
const seen=new Set();
for(const el of document.body.querySelectorAll("*")){
 if(!el.childNodes.length)continue;const hasText=[...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());if(!hasText)continue;
 const r=el.getBoundingClientRect();if(!r.width||!r.height)continue;if(r.bottom<0||r.top>innerHeight)continue;
 const cs=getComputedStyle(el);if(cs.visibility==="hidden"||cs.display==="none"||+cs.opacity===0)continue;
 let op=1;for(let e=el;e;e=e.parentElement){op*=+getComputedStyle(e).opacity}if(op<0.05)continue;
 const fg=parse(cs.color);if(!fg)continue;const bg=bgOf(el);
 const fgm={r:fg.r*fg.a+bg.r*(1-fg.a),g:fg.g*fg.a+bg.g*(1-fg.a),b:fg.b*fg.a+bg.b*(1-fg.a)};
 const ratio=cr(fgm,bg);const fs=parseFloat(cs.fontSize);const bold=+cs.fontWeight>=700;const large=fs>=24||(fs>=18.66&&bold);
 const need=large?3:4.5;const t=el.textContent.trim().slice(0,14);
 if(ratio<need&&op>=0.95)out.low.push([el.className.toString().slice(0,20)||el.tagName,t,+ratio.toFixed(2),fs]);
 if(fs<11)out.small.push([el.className.toString().slice(0,20)||el.tagName,t,fs]);
 if(el.scrollWidth>el.clientWidth+1&&["hidden","clip"].includes(cs.overflowX)&&cs.textOverflow==="ellipsis")out.trunc.push([el.className.toString().slice(0,20)||el.tagName,t,el.scrollWidth,el.clientWidth]);
 if(r.right>innerWidth+1&&cs.position!=="fixed")out.hscroll.push([el.className.toString().slice(0,20)||el.tagName,t,Math.round(r.right)]);
}
return out}