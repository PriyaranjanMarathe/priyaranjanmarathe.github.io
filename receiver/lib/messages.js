import { createHash, createHmac, timingSafeEqual } from 'node:crypto';

export const keyFor = id => createHash('sha256').update(id).digest('hex');
export function equal(a, b) {
  return typeof a === 'string' && typeof b === 'string' && a.length > 0 &&
    Buffer.byteLength(a) === Buffer.byteLength(b) && timingSafeEqual(Buffer.from(a), Buffer.from(b));
}
export function validSignature(raw, signature, secret) {
  return Boolean(secret) && equal(signature, 'sha256=' + createHmac('sha256', secret).update(raw).digest('hex'));
}
export function messagesFor(payload, env, now = Date.now()) {
  if (payload.object !== 'whatsapp_business_account') return [];
  const result = [];
  for (const entry of payload.entry || []) {
    if (entry.id !== env.META_WABA_ID) continue;
    for (const change of entry.changes || []) {
      const value = change.value;
      if (change.field !== 'messages' || value?.metadata?.phone_number_id !== env.META_PHONE_ID) continue;
      for (const message of value.messages || []) {
        if (message.from !== env.WHATSAPP_OWNER || typeof message.id !== 'string') continue;
        const timestamp = Number(message.timestamp);
        if (!Number.isFinite(timestamp) || timestamp * 1000 < Date.parse(env.CAPTURE_START) ||
            timestamp * 1000 > now + 300000 || timestamp * 1000 < now - 7 * 86400000) continue;
        const media = ['image', 'video', 'audio', 'document', 'sticker'].includes(message.type)
          ? message[message.type] : null;
        // Keep unsupported messages as barriers: a later save must never select an older item.
        result.push({id: message.id, timestamp, type: message.type,
          body: message.text?.body || media?.caption || '',
          media: media?.id ? {id: media.id, mime_type: media.mime_type, sha256: media.sha256} : null,
          context: message.context?.id || null});
      }
    }
  }
  return result;
}
