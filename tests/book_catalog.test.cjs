const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const vm=require('node:vm');
const catalogHtml=fs.readFileSync(path.join(__dirname,'../docs/finds/stories/my-library.html'),'utf8');
const engine=catalogHtml.match(/<script id="catalog-engine">([\s\S]*?)<\/script>/)[1];
const context={module:{exports:{}}};vm.runInNewContext(engine,context);const api=context.module.exports;
const books=JSON.parse(catalogHtml.match(/<script id="catalog-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const text=b=>Object.values(b).filter(v=>v!==null).map(v=>Array.isArray(v)?v.join(' '):String(v)).join(' ');
function fakeCatalog(){
 const nodes=books.map((b,i)=>({dataset:{bookSearch:text(b),bookTags:JSON.stringify(b.tags||[]),bookLanguage:b.language,bookTitle:b.title,bookAuthor:b.authors[0]||'',bookYear:b.year||0,bookAdded:b.addedAt||'',bookIndex:String(i)},hidden:false}));
 const elements={'.book-topic':{value:''},'.book-language':{value:''},'.book-sort':{value:'added-desc'},'.catalog-status':{textContent:''},'.book-empty':{hidden:true},'.book-results':{children:[],scrollTop:0,appendChild(n){this.children=this.children.filter(x=>x!==n);this.children.push(n);}}};
 return {nodes,elements,querySelector:s=>elements[s],querySelectorAll:s=>s==='.owned-book'?nodes:[]};
}
test('all 158 titles match their complete records',()=>{assert.equal(books.length,158);books.forEach(b=>assert.ok(api.matches(text(b),b.title),b.title));});
test('authors, tags, accents and mixed terms search inline',()=>{assert.ok(api.matches('Dalí Max Gérard surrealism','dali gerard'));assert.ok(api.matches('Design Patterns Erich Gamma computing','gamma patterns'));assert.ok(!api.matches('Design Patterns','missing title'));});
test('every ISBN supports hyphenated or spaced lookup',()=>{books.forEach(b=>{for(const k of ['isbn13','isbn10'])if(b[k]){assert.ok(api.matches(text(b),b[k].slice(0,3)+'-'+b[k].slice(3)));assert.ok(api.matches(text(b),b[k].split('').join(' ')));}});});
test('empty query shows all, unknown query shows no-match, repeated clearing restores all',()=>{const c=fakeCatalog();assert.equal(api.filter(c,''),158);assert.equal(api.filter(c,'zzzznotownedzzzz'),0);assert.equal(c.elements['.book-empty'].hidden,false);assert.equal(api.filter(c,''),158);assert.equal(c.elements['.book-empty'].hidden,true);assert.equal(c.elements['.book-results'].children.length,159);});
test('topic, language and global tags compose without hidden-book counts',()=>{const c=fakeCatalog();c.elements['.book-topic'].value='science';c.elements['.book-language'].value='English';const expected=books.filter(b=>b.tags.includes('science')&&b.language==='English').length;assert.equal(api.filter(c,''),expected);assert.equal(api.filter(c,'','science'),expected);assert.equal(api.filter(c,'','zzzznotatag'),0);});
test('all sort modes preserve all rows and correct ordering',()=>{for(const mode of ['title','author','year-desc','year-asc','added-desc','added-asc']){const c=fakeCatalog();c.elements['.book-sort'].value=mode;assert.equal(api.filter(c,''),158);const rows=c.elements['.book-results'].children.filter(x=>x.dataset);for(let i=1;i<rows.length;i++)assert.ok(api.compare(rows[i-1].dataset,rows[i].dataset,mode)<=0,mode);}});
test('show all resets every catalog control',()=>{const c=fakeCatalog();c.elements['.book-topic'].value='science';c.elements['.book-language'].value='English';c.elements['.book-sort'].value='title';api.reset({querySelectorAll:()=>[c]});assert.equal(c.elements['.book-topic'].value,'');assert.equal(c.elements['.book-language'].value,'');assert.equal(c.elements['.book-sort'].value,'added-desc');});
test('search punctuation is literal and does not become executable HTML',()=>{assert.ok(api.matches('C++ [notes]','c++ [notes]'));assert.ok(!api.matches('Normal book','<script>alert(1)</script>'));});
