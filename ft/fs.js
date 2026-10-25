// in-memory Firestore mock persisted in localStorage key "mockdb"
const load=()=>JSON.parse(localStorage.getItem("mockdb")||"{}");
const save=d=>localStorage.setItem("mockdb",JSON.stringify(d));
const subs=[];
const notify=()=>subs.forEach(f=>f());
export function initializeFirestore(){return {}}
export function getFirestore(){return {}}
export function persistentLocalCache(){return {}}
export function doc(a,b){if(b===undefined){const id=Math.random().toString(36).slice(2,10);return {path:a.path+"/"+id,id}}const path=typeof a==="object"&&a.path?a.path+"/"+b:b;return {path,id:path.split("/").pop()}}
export function collection(_,p){return {path:p,isCol:true}}
/* o.merge：只更新給的欄位（和 Firestore setDoc(...,{merge:true}) 一樣） */
export async function setDoc(r,d,o){const db=load();db[r.path]=o&&o.merge?{...(db[r.path]||{}),...d}:d;save(db);window.__writes=(window.__writes||0)+1;setTimeout(notify,0);if(window.__writeDelay)await new Promise(z=>setTimeout(z,window.__writeDelay))}
/* 一次寫入多筆：只通知一次（模擬 Firestore writeBatch） */
export function writeBatch(){const ops=[];return{set(r,d){ops.push([r,d]);return this},async commit(){const db=load();for(const[r,d]of ops)db[r.path]=d;save(db);window.__writes=(window.__writes||0)+ops.length;setTimeout(notify,0);if(window.__writeDelay)await new Promise(z=>setTimeout(z,window.__writeDelay))}}}
export async function deleteDoc(r){const db=load();delete db[r.path];save(db);setTimeout(notify,0)}
const snapDoc=p=>{const db=load();return {id:p.split("/").pop(),exists:()=>p in db,data:()=>db[p]}};
export async function getDoc(r){return snapDoc(r.path)}
export async function getDocFromServer(r){return snapDoc(r.path)}
export function onSnapshot(r,next){const f=()=>{if(r.isCol){const db=load();const docs=Object.keys(db).filter(k=>k.startsWith(r.path+"/")&&k.slice(r.path.length+1).indexOf("/")<0).map(k=>({id:k.split("/").pop(),data:()=>db[k]}));next({docs})}else next(snapDoc(r.path))};subs.push(f);setTimeout(f,30);return()=>{}}
addEventListener("storage",e=>{if(e.key==="mockdb")notify()});
