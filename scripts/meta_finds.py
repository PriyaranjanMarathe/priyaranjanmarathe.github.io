"""Read the authenticated private inbox; publish only explicit WhatsApp replies."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from urllib.parse import urlsplit

import requests
from saved_finds import ROOT, TYPES, render, tags_for


def selections(messages, start, now):
    unique = {m['id']: m for m in messages}
    for command in sorted(unique.values(), key=lambda m: (m['timestamp'], m['id'])):
        text = command.get('body', '').strip()
        if not re.fullmatch(r'save(?:\s+#[\w-]+)*', text, re.I):
            continue
        # Reply context names the exact forward; arrival ordering cannot select another item.
        item = unique.get(command.get('context'))
        if (not item or item['type'] not in {'text', 'image', 'video', 'audio', 'document', 'sticker'}
                or item['timestamp'] < start or command['timestamp'] < start
                or not 0 <= command['timestamp'] - item['timestamp'] <= 86400
                or command['timestamp'] > now - 120):
            continue
        yield item, re.findall(r'#([\w-]+)', text)


def media_attachment(item, directory, key):
    media = item.get('media')
    if not media:
        if item['type'] != 'text':
            raise ValueError('Missing attachment')
        return []
    if not re.fullmatch(r'\d+', media['id']):
        raise ValueError('Invalid media ID')
    version = os.environ['META_GRAPH_VERSION']
    if not re.fullmatch(r'v\d+\.0', version):
        raise ValueError('Invalid API version')
    headers = {'Authorization': 'Bearer ' + os.environ['META_ACCESS_TOKEN']}
    with requests.get(f'https://graph.facebook.com/{version}/{media["id"]}', headers=headers, timeout=30) as response:
        if response.status_code != 200:
            raise RuntimeError('Meta media metadata unavailable')
        metadata = response.json()
    parsed = urlsplit(metadata['url'])
    if parsed.scheme != 'https' or parsed.hostname != 'lookaside.fbsbx.com' or parsed.username or parsed.password:
        raise ValueError('Unexpected media host')
    mime = metadata['mime_type'].split(';')[0]
    if mime not in TYPES or int(metadata.get('file_size', 0)) > 20 * 1024 * 1024:
        raise ValueError('Unsupported or oversized attachment')
    directory.mkdir(parents=True, exist_ok=True)
    filename = key + TYPES[mime]
    temporary = directory / (filename + '.part')
    digest = hashlib.sha256()
    try:
        with requests.get(metadata['url'], headers=headers, timeout=45, stream=True, allow_redirects=False) as response:
            if response.status_code != 200:
                raise RuntimeError('Meta media unavailable')
            with temporary.open('wb') as output:
                size = 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 20 * 1024 * 1024:
                        raise ValueError('Attachment exceeds 20 MB')
                    digest.update(chunk)
                    output.write(chunk)
        if metadata.get('sha256') and digest.hexdigest().lower() != metadata['sha256'].lower():
            raise ValueError('Attachment checksum mismatch')
        temporary.replace(directory / filename)
    finally:
        temporary.unlink(missing_ok=True)
    return [{'url': '/finds/media/' + filename, 'type': mime}]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    endpoint = os.environ['WHATSAPP_INBOX_URL']
    parsed = urlsplit(endpoint)
    if parsed.scheme != 'https' or parsed.hostname != 'saved-finds-receiver.vercel.app' or parsed.path != '/api/inbox':
        raise ValueError('Unexpected inbox URL')
    with requests.get(endpoint, headers={'Authorization': 'Bearer ' + os.environ['INBOX_READ_TOKEN']},
                      timeout=90, allow_redirects=False) as response:
        if response.status_code != 200:
            raise RuntimeError('Private inbox unavailable')
        messages = response.json()['messages']
    start = datetime.fromisoformat(os.environ['CAPTURE_START'].replace('Z', '+00:00')).timestamp()
    directory = ROOT / 'docs/finds'
    database = directory / 'finds.json'
    records = json.loads(database.read_text()) if database.exists() else []
    existing = {r['id'] for r in records}
    added = 0
    for item, explicit in selections(messages, start, datetime.now(timezone.utc).timestamp()):
        key = hashlib.sha256(item['id'].encode()).hexdigest()[:24]
        if key in existing:
            continue
        existing.add(key)
        added += 1
        if not args.publish:
            continue
        body = item['body']
        tags, method = tags_for(body, explicit)
        records.append({'id': key, 'title': body.strip().split('\n')[0][:120] or 'Saved attachment',
                        'body': body, 'saved_at': datetime.fromtimestamp(item['timestamp'], timezone.utc).isoformat(),
                        'tags': tags, 'tag_method': method,
                        'attachments': media_attachment(item, directory / 'media', key)})
    if args.publish:
        render(records, directory)
        database.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{added} new selected item(s); mode={"publish" if args.publish else "preview"}.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Import failed ({type(error).__name__}); no content committed. Check receiver or Meta credentials.')
        raise SystemExit(1)
