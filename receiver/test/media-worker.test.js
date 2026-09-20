import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../../media-worker/worker.mjs';
const url = 'https://media.example.com/media/' + 'a'.repeat(24) + '.mp4';
const env = {MEDIA:{
  head: async () => ({size:6, httpEtag:'"abc"', writeHttpMetadata:h=>h.set('Content-Type','video/mp4')}),
  get: async (key, options) => ({body: options?.range ? 'abcdef'.slice(options.range.offset,options.range.offset+options.range.length) : 'abcdef'})
}};
test('media Worker serves full files, HEAD, conditional requests and video ranges', async () => {
  let r = await worker.fetch(new Request(url), env); assert.equal(r.status,200); assert.equal(await r.text(),'abcdef');
  r = await worker.fetch(new Request(url,{method:'HEAD'}),env); assert.equal(r.headers.get('Content-Length'),'6'); assert.equal(await r.text(),'');
  r = await worker.fetch(new Request(url,{headers:{Range:'bytes=1-3'}}),env); assert.equal(r.status,206); assert.equal(r.headers.get('Content-Range'),'bytes 1-3/6'); assert.equal(await r.text(),'bcd');
  r = await worker.fetch(new Request(url,{headers:{Range:'bytes=-2'}}),env); assert.equal(await r.text(),'ef');
  r = await worker.fetch(new Request(url,{headers:{Range:'bytes=99-'}}),env); assert.equal(r.status,416);
  r = await worker.fetch(new Request(url,{headers:{'If-None-Match':'"abc"'}}),env); assert.equal(r.status,304);
});
test('media Worker never exposes arbitrary keys or write access', async () => {
  assert.equal((await worker.fetch(new Request(url,{method:'PUT',body:'bad'}),{})).status,405);
  assert.equal((await worker.fetch(new Request('https://media.example.com/inbox/private.json'),{})).status,404);
});
