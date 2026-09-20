import { put } from '@vercel/blob';
import { equal, keyFor, validSignature, messagesFor } from '../lib/messages.js';

export const config = {api: {bodyParser: false}};
export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  const env = process.env;
  if (req.method === 'GET') {
    const query = new URL(req.url, 'https://receiver.invalid').searchParams;
    if (query.get('hub.mode') === 'subscribe' && equal(query.get('hub.verify_token'), env.META_VERIFY_TOKEN))
      return res.status(200).send(query.get('hub.challenge'));
    return res.status(403).end();
  }
  if (req.method !== 'POST') return res.status(405).end();
  if (!env.META_APP_SECRET || !env.WHATSAPP_OWNER || !env.META_PHONE_ID ||
      !env.META_WABA_ID || !Number.isFinite(Date.parse(env.CAPTURE_START))) return res.status(503).end();
  try {
    const chunks = []; let size = 0;
    for await (const chunk of req) {
      size += chunk.length;
      if (size > 262144) return res.status(413).end();
      chunks.push(chunk);
    }
    const raw = Buffer.concat(chunks);
    if (!validSignature(raw, req.headers['x-hub-signature-256'], env.META_APP_SECRET)) return res.status(401).end();
    let payload;
    try { payload = JSON.parse(raw.toString('utf8')); } catch { return res.status(400).end(); }
    for (const message of messagesFor(payload, env)) {
      // Stable names make Meta retries idempotent. Only normalized owner data is persisted.
      await put('inbox/' + keyFor(message.id) + '.json', JSON.stringify(message), {
        access: 'private', addRandomSuffix: false, allowOverwrite: true,
        contentType: 'application/json', cacheControlMaxAge: 60,
      });
    }
    return res.status(200).end();
  } catch {
    // Ask Meta to retry on storage failures; never log webhook bodies or credentials.
    return res.status(503).end();
  }
}
