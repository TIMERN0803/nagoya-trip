// 回歸測試用的假 Firestore（複製自 qa/claude/scripts/fs_offline.js，以 ft/fs.js 為基礎；synctest.py 使用），加上「真實 Firestore SDK 開了 persistentLocalCache、離線時」的行為：
//  - 離線時 setDoc / deleteDoc / batch.commit 立刻套用在本機並通知 onSnapshot（latency compensation），
//    但回傳的 Promise 要等恢復連線、伺服器確認後才 resolve（Firestore 官方行為）。
//  - 離線寫入的佇列存在 localStorage["mockpending"]（模擬 IndexedDB 持久化：App 關掉重開後仍會在連線時送出）。
//  - 離線期間收不到其他手機的變更；getDocFromServer 會 reject {code:"unavailable"}。
//  - 網路狀態存在 localStorage["mocknet"]（"0"＝離線），重新整理後維持；window.__forceOnline=1 的頁面不受影響（當作另一支手機）。
//  - window.__reject="代碼"：寫入以該 error.code 拒收（invalid-argument＝伺服器認定資料不合法；unavailable＝暫時性失敗）
//  - window.__deny=1：模擬「旅程代碼沒有權限」，getDocFromServer 與寫入都 reject {code:"permission-denied"}
//  - window.__goOffline() / window.__goOnline()：切換；上線時把佇列依序寫進共用的 mockdb（後到的蓋掉先到的），resolve 所有 Promise，再通知。
const load=()=>JSON.parse(localStorage.getItem("mockdb")||"{}");
const save=d=>localStorage.setItem("mockdb",JSON.stringify(d));
const lp=()=>JSON.parse(localStorage.getItem("mockpending")||"[]");
const sp=p=>localStorage.setItem("mockpending",JSON.stringify(p));
const subs=[];let waiters=[],frozen=null;
if(localStorage.getItem("mocknet")==="0"&&!window.__forceOnline){window.__net=false;frozen=load()}
const online=()=>window.__net!==false;
const ap=(v,p,d,m)=>{if(d===null)delete v[p];else v[p]=m?{...(v[p]||{}),...d}:d};
const view=()=>{if(online())return load();const v={...(frozen||load())};for(const[p,d,m]of lp())ap(v,p,d,m);return v};
const notify=()=>subs.forEach(f=>f());
window.__goOffline=()=>{frozen=load();window.__net=false;localStorage.setItem("mocknet","0")};
window.__goOnline=()=>{const db=load();for(const[p,d,m]of lp())ap(db,p,d,m);save(db);sp([]);window.__net=true;localStorage.removeItem("mocknet");const w=waiters;waiters=[];w.forEach(f=>f());setTimeout(notify,0)};
window.__pending=()=>lp().length;
const wait=()=>online()?Promise.resolve():new Promise(r=>waiters.push(r));
function write(path,d,m){if(online()){const db=load();ap(db,path,d,m);save(db)}else{const p=lp();p.push([path,d,!!m]);sp(p)}window.__writes=(window.__writes||0)+1;setTimeout(notify,0)}
export function initializeFirestore(){return {}}
export function getFirestore(){return {}}
export function persistentLocalCache(){return {}}
export function doc(a,b){if(b===undefined){const id=Math.random().toString(36).slice(2,10);return {path:a.path+"/"+id,id}}const path=typeof a==="object"&&a.path?a.path+"/"+b:b;return {path,id:path.split("/").pop()}}
export function collection(_,p){return {path:p,isCol:true}}
const deny=()=>Object.assign(new Error("Missing or insufficient permissions."),{code:"permission-denied"});
export async function setDoc(r,d,o){if(window.__deny)throw deny();if(window.__reject)throw Object.assign(new Error("rejected"),{code:window.__reject});write(r.path,d,o&&o.merge);if(window.__writeDelay)await new Promise(z=>setTimeout(z,window.__writeDelay));await wait()}
export function writeBatch(){const ops=[];return{set(r,d,o){ops.push([r,d,o]);return this},async commit(){if(window.__deny)throw deny();if(window.__reject)throw Object.assign(new Error("rejected"),{code:window.__reject});for(const[r,d,o]of ops)write(r.path,d,o&&o.merge);await wait()}}}
export async function deleteDoc(r){if(window.__deny)throw deny();if(window.__reject)throw Object.assign(new Error("rejected"),{code:window.__reject});write(r.path,null);await wait()}
const snapDoc=p=>{const db=view();return {id:p.split("/").pop(),exists:()=>p in db,data:()=>db[p]}};
export async function getDoc(r){return snapDoc(r.path)}
export async function getDocFromServer(r){if(window.__deny)throw deny();if(window.__serverDelay)await new Promise(z=>setTimeout(z,window.__serverDelay));if(!online())throw Object.assign(new Error("Failed to get document because the client is offline."),{code:"unavailable"});return snapDoc(r.path)}
export function onSnapshot(r,next){const f=()=>{if(r.isCol){const db=view();const docs=Object.keys(db).filter(k=>k.startsWith(r.path+"/")&&k.slice(r.path.length+1).indexOf("/")<0).map(k=>({id:k.split("/").pop(),data:()=>db[k]}));next({docs})}else next(snapDoc(r.path))};subs.push(f);setTimeout(f,30);return()=>{}}
addEventListener("storage",e=>{if(e.key==="mockdb"&&online())notify()});
export function initializeApp(c){return {c}}
