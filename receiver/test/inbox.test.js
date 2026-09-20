import test from 'node:test';
import assert from 'node:assert/strict';
import {readInbox} from '../lib/inbox.js';
import {keyFor} from '../lib/messages.js';
const now=Date.now();
function fake(entries) {
 const reads=[];
 return {reads,
 list:async()=>({blobs:entries.map(([m,age])=>({pathname:'inbox/'+keyFor(m.id)+'.json',url:m.id,uploadedAt:new Date(now-age)})),hasMore:false}),
 get:async path=>{reads.push(path); const e=entries.find(([m])=>path==='inbox/'+keyFor(m.id)+'.json');return e?{statusCode:200,stream:new Response(JSON.stringify(e[0])).body}:null;},
 del:async()=>{}};
}
test('incremental reads skip old messages but fetch exact reply target',async()=>{
 const old={id:'old',timestamp:Math.floor(now/1000)-6000,body:'content'};
 const cmd={id:'cmd',timestamp:Math.floor(now/1000)-180,body:'save\nTitle: New',context:'old'};
 const store=fake([[old,6000000],[cmd,180000],[{id:'unrelated'},6000000]]);
 const result=await readInbox(store,{after:now-3600000,now});
 assert.equal(store.reads.length,2); assert.equal(result.messages.length,2);
});
test('settling-window messages stay unread until next cursor',async()=>{
 const store=fake([[{id:'new'},10000]]);
 const result=await readInbox(store,{now});assert.equal(store.reads.length,0);assert(result.cursor<now-120000);
});
test('failed command is fetched again despite old cursor',async()=>{
 const store=fake([[{id:'retry'},3600000]]);
 await readInbox(store,{after:now-600000,retry:[keyFor('retry')],now});assert.equal(store.reads.length,1);
});
test('pagination handles more than 1000 entries',async()=>{
 let calls=0; const store=fake([]);store.list=async args=>{calls++;return calls===1?{blobs:[],hasMore:true,cursor:'next'}:{blobs:[],hasMore:false};};
 await readInbox(store,{now});assert.equal(calls,2);
});
test('read failure does not return a checkpoint',async()=>{
 const store=fake([[{id:'x'},180000]]);store.get=async()=>{throw Error('transient');};
 await assert.rejects(readInbox(store,{now}));
});
