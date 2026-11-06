const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../docs/finds/stories/colorado-election-results.html'),'utf8');
const code=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
function load(){
 const node=()=>({dataset:{},hidden:false,attrs:{},events:{},classList:{toggle(){}},setAttribute(k,v){this.attrs[k]=v},addEventListener(k,f){this.events[k]=f}});
 const chips=['all','pass','fail','amendment','proposition','close'].map(f=>Object.assign(node(),{dataset:{filter:f}}));
 const list={children:[node()],replaceChildren(){this.children=[]},appendChild(n){this.children.push(n)}};
 const search=Object.assign(node(),{value:''}),count=node(),empty=node();
 const context={document:{getElementById:id=>({'measure-list':list,'measure-search':search,'measure-count':count,'measure-empty':empty})[id],querySelectorAll:()=>chips,createElement:node}};
 vm.runInNewContext(code,context);
 return {context,list,search,count,chips,shown:()=>list.children.filter(c=>!c.hidden).length,filter(f){chips.find(c=>c.dataset.filter===f).events.click()},query(q){search.value=q;search.events.input()}};
}
test('14 measures replace static fallback without duplicate cards',()=>{assert.equal(load().list.children.length,14)});
test('passing, failing, amendment and proposition filters show seven each',()=>{const x=load();for(const f of ['pass','fail','amendment','proposition']){x.filter(f);assert.equal(x.shown(),7,f)}x.filter('close');assert.equal(x.shown(),6)});
test('search composes with filters and clearing restores the current filter',()=>{const x=load();x.query('Amendment 85');assert.equal(x.shown(),1);x.filter('pass');assert.equal(x.shown(),0);x.query('');assert.equal(x.shown(),7);x.filter('all');assert.equal(x.shown(),14)});
test('no-match and repeated show-all controls are stable',()=>{const x=load();x.query('<script>');assert.equal(x.shown(),0);for(let i=0;i<4;i++){x.query('');x.filter('all');assert.equal(x.shown(),14)}assert.equal(x.count.textContent,'Showing 14 of 14 measures')});
test('all constitutional thresholds and provisional labels are retained',()=>{const {context}=load();assert.equal(context.MEASURES.length,14);for(const m of context.MEASURES){assert.equal(m.threshold,['81','82','83','84','85','86'].includes(m.id)?55:50)}assert.match(context.MEASURES.find(m=>m.id==='85').badge,/uncalled/)});
test('repaired statewide-office table contains four complete rows',()=>{const section=html.match(/<section id="offices">([\s\S]*?)<\/section>/)[1];assert.equal((section.match(/<td /g)||[]).length,20);assert.equal((section.match(/<tr>/g)||[]).length,5);assert.ok(!section.includes('td<td'))});
test('publication notes distinguish dated totals, new AP call and verification limits',()=>{assert.match(html,/AP called CD-3 for Jeff Hurd on Nov. 6/);assert.match(html,/not a live results feed/);assert.match(html,/could not be independently reverified directly/);assert.ok(!/precisely two-thirds|exactly two-thirds|fails regardless|cannot reach 55%/.test(html))});
test('inline story has responsive grids, bounded parent support and safe links',()=>{assert.match(html,/minmax\(min\(100%,300px\),1fr\)/);assert.match(html,/linked-blog-story-resize/);assert.match(html,/linked-blog-story-scroll/);for(const a of html.matchAll(/<a href="https?:[^>]+>/g))assert.match(a[0],/rel="noopener noreferrer"/)});
