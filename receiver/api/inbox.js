import { list, get, del } from '@vercel/blob';
import { equal } from '../lib/messages.js';
import { readInbox } from '../lib/inbox.js';

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (!process.env.INBOX_READ_TOKEN || !equal(req.headers.authorization, 'Bearer ' + process.env.INBOX_READ_TOKEN)) return res.status(401).end();
  if (req.method !== 'GET') return res.status(405).end();
  const query = new URL(req.url, 'https://receiver.invalid').searchParams;
  const after = Number(query.get('after') || 0);
  const retry = (query.get('retry') || '').split(',').filter(Boolean);
  if (!Number.isFinite(after) || after < 0 || after > Date.now() || retry.length > 100 || retry.some(k => !/^[a-f0-9]{64}$/.test(k))) return res.status(400).end();
  try { return res.status(200).json(await readInbox({list,get,del}, {after,retry})); }
  catch { return res.status(503).json({error: 'Inbox unavailable'}); }
}
