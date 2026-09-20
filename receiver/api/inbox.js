import { list, get, del } from '@vercel/blob';
import { equal } from '../lib/messages.js';

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (!process.env.INBOX_READ_TOKEN || !equal(req.headers.authorization, 'Bearer ' + process.env.INBOX_READ_TOKEN))
    return res.status(401).end();
  if (req.method !== 'GET') return res.status(405).end();
  try {
    const page = await list({prefix: 'inbox/', limit: 1000});
    if (page.hasMore) return res.status(503).json({error: 'Inbox capacity exceeded'});
    const messages = [];
    for (const blob of page.blobs) {
      // Cleanup occurs when the authorized hourly importer runs. Paused imports pause cleanup.
      if (Date.now() - new Date(blob.uploadedAt).getTime() > 86400000) {
        await del(blob.url); continue;
      }
      const result = await get(blob.pathname, {access: 'private', useCache: false});
      if (result?.statusCode !== 200) throw new Error('Unavailable');
      const message = await new Response(result.stream).json();
      messages.push(message);
    }
    return res.status(200).json({messages});
  } catch { return res.status(503).json({error: 'Inbox unavailable'}); }
}
