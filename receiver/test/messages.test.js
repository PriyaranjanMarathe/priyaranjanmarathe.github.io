import test from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { messagesFor, validSignature, equal } from '../lib/messages.js';
const now = Date.now();
const env = {META_WABA_ID: 'account', META_PHONE_ID: 'phone', WHATSAPP_OWNER: 'owner', CAPTURE_START: new Date(now - 60000).toISOString()};
const payload = (from = 'owner') => ({object: 'whatsapp_business_account', entry: [{id: 'account', changes: [{field: 'messages', value: {metadata: {phone_number_id: 'phone'}, contacts: [{secret: 'unused'}], messages: [{from, id: 'one', timestamp: String(Math.floor(now / 1000)), type: 'text', text: {body: 'Hello'}}]}}]}]});
test('signature checks exact raw bytes and fails closed without a secret', () => {
  const body = Buffer.from('{ "a":1 }');
  const signature = 'sha256=' + createHmac('sha256', 'test-only').update(body).digest('hex');
  assert(validSignature(body, signature, 'test-only'));
  assert(!validSignature(Buffer.from('{"a":1}'), signature, 'test-only'));
  assert(!validSignature(body, signature, ''));
  assert(!equal(undefined, undefined));
});
test('only exact owner, account and destination survive normalization', () => {
  assert.equal(messagesFor(payload(), env, now).length, 1);
  assert.deepEqual(messagesFor(payload('stranger'), env, now), []);
  assert.deepEqual(messagesFor(payload(), {...env, META_WABA_ID: 'other'}, now), []);
  assert.deepEqual(messagesFor(payload(), {...env, META_PHONE_ID: 'other'}, now), []);
  const serialized = JSON.stringify(messagesFor(payload(), env, now));
  assert(!serialized.includes('owner'));
  assert(!serialized.includes('unused'));
});
test('old events are ignored', () => {
  assert.deepEqual(messagesFor(payload(), {...env, CAPTURE_START: new Date(now + 60000).toISOString()}, now), []);
});
