import { keyFor } from './messages.js';

export async function readInbox(storage, {after = 0, retry = [], now = Date.now()} = {}) {
  const cutoff = now - 120000;
  const messages = new Map();
  const requested = new Set(retry.map(key => 'inbox/' + key + '.json'));
  let cursor;
  let pages = 0;
  do {
    const page = await storage.list({prefix: 'inbox/', limit: 1000, ...(cursor ? {cursor} : {})});
    if (++pages > 100) throw new Error('Inbox pagination limit');
    for (let offset = 0; offset < page.blobs.length; offset += 5) {
      await Promise.all(page.blobs.slice(offset, offset + 5).map(async blob => {
        const uploaded = new Date(blob.uploadedAt).getTime();
        if (uploaded < now - 7 * 86400000) { await storage.del(blob.url); return; }
        if (uploaded > cutoff || (uploaded < after && !requested.has(blob.pathname))) return;
        const result = await storage.get(blob.pathname, {access: 'private', useCache: false});
        if (result?.statusCode !== 200) throw new Error('Inbox read failed');
        const message = await new Response(result.stream).json();
        messages.set(message.id, message);
      }));
    }
    cursor = page.hasMore ? page.cursor : undefined;
    if (page.hasMore && !cursor) throw new Error('Missing cursor');
  } while (cursor);
  // Fetch exact reply targets even when they were received in an earlier import.
  const contextIds = new Set([...messages.values()].filter(m => /^save(?:\s|$)/i.test(m.body || '') && m.context).map(m => m.context));
  for (const id of contextIds) {
    if (messages.has(id)) continue;
    const result = await storage.get('inbox/' + keyFor(id) + '.json', {access: 'private', useCache: false});
    if (!result) continue;
    if (result.statusCode !== 200) throw new Error('Reply target unavailable');
    const message = await new Response(result.stream).json();
    if (message.timestamp * 1000 >= now - 7 * 86400000) messages.set(message.id, message);
  }
  return {messages: [...messages.values()], cursor: Math.max(after, cutoff - 2000)};
}
