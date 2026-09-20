"""Read the authenticated private inbox; publish only explicit WhatsApp replies."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import requests
from saved_finds import ROOT, TYPES, render, tags_for
import media_storage


def parse_command(body):
    lines = body.strip().splitlines()
    if not lines or not re.fullmatch(r'save(?:\s+#[\w-]+)*', lines[0], re.I):
        return None
    result = {'tags': re.findall(r'#([\w-]+)', lines[0]), 'title': None, 'note': None}
    field = None
    for line in lines[1:]:
        match = re.match(r'^(Title|Note):\s*(.*)$', line, re.I)
        if match:
            field = match[1].lower()
            if result[field] is not None: return None
            result[field] = match[2]
        elif field == 'note': result['note'] += '\n' + line
        elif line.strip(): return None
    if result['title'] is not None and not 1 <= len(result['title']) <= 200: return None
    if result['note'] is not None and len(result['note']) > 5000: return None
    return result


def command_selections(messages, start, now):
    unique = {m['id']: m for m in messages}
    for command in sorted(unique.values(), key=lambda m: (m['timestamp'], m['id'])):
        options = parse_command(command.get('body', ''))
        if options is None or not command.get('context'): continue
        item = unique.get(command['context'])
        if command['timestamp'] < start or command['timestamp'] > now - 120: continue
        if item and (item['timestamp'] < start or not 0 <= command['timestamp'] - item['timestamp'] <= 86400): continue
        yield command, item, options


def selections(messages, start, now):
    for command, item, options in command_selections(messages, start, now):
        if item and item['type'] in {'text', 'image', 'video', 'audio', 'document', 'sticker'}:
            yield item, options['tags']


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
            raise RuntimeError(f'Meta media metadata unavailable: HTTP {response.status_code}, API code {response.json().get("error", {}).get("code", 0)}')
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
                raise RuntimeError(f'Meta media unavailable: HTTP {response.status_code}')
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
    mirrored = media_storage.backup(directory / filename, 'media/' + filename, mime) if media_storage.enabled() else {}
    media_storage.reserve_vercel((directory / filename).stat().st_size)
    if os.environ.get('MEDIA_PRIMARY') == 'r2':
        media_storage.verify_public(mirrored)
        return [{'url':mirrored['backup_url'], 'type':mime, **mirrored}]
    result = subprocess.run(['node', str(ROOT / 'receiver/scripts/upload-media.js'), str(directory / filename),
                             'media/' + filename, mime], capture_output=True, text=True, timeout=90)
    if result.returncode: raise RuntimeError('Public media upload failed')
    url = json.loads(result.stdout)['url']
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not (parsed.hostname or '').endswith('.public.blob.vercel-storage.com'):
        raise ValueError('Unexpected public media URL')
    return [{'url': url, 'type': mime, **mirrored}]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    endpoint = os.environ['WHATSAPP_INBOX_URL']
    parsed = urlsplit(endpoint)
    if parsed.scheme != 'https' or parsed.hostname != 'saved-finds-receiver.vercel.app' or parsed.path != '/api/inbox':
        raise ValueError('Unexpected inbox URL')
    directory = ROOT / 'docs/finds'
    checkpoint_file = directory / 'import-state.json'
    checkpoint = json.loads(checkpoint_file.read_text()) if checkpoint_file.exists() else {}
    with requests.get(endpoint, headers={'Authorization': 'Bearer ' + os.environ['INBOX_READ_TOKEN']},
                      params={'after': checkpoint.get('cursor', 0), 'retry': ','.join(checkpoint.get('retry_commands', []))},
                      timeout=90, allow_redirects=False) as response:
        if response.status_code != 200: raise RuntimeError('Private inbox unavailable')
        inbox = response.json()
    start = datetime.fromisoformat(os.environ['CAPTURE_START'].replace('Z', '+00:00')).timestamp()
    database = directory / 'finds.json'
    records = json.loads(database.read_text()) if database.exists() else []
    if args.publish:
        media_storage.prepare(records, directory, ROOT)
    by_id = {r['id']: r for r in records}
    retries = set()
    added = updated = 0
    for command, item, options in command_selections(inbox['messages'], start, datetime.now(timezone.utc).timestamp()):
        command_key = hashlib.sha256(command['id'].encode()).hexdigest()
        if not item:
            retries.add(command_key); continue
        key = hashlib.sha256(item['id'].encode()).hexdigest()[:24]
        old = by_id.get(key)
        revision = [command['timestamp'], command_key]
        if old and old.get('revision', [0, '']) >= revision: continue
        if not args.publish:
            if not old: added += 1
            else: updated += 1
            continue
        try:
            body = item['body']
            tags, method = tags_for(body, options['tags'])
            with tempfile.TemporaryDirectory() as temporary:
                attachments = old['attachments'] if old else media_attachment(item, Path(temporary), key)
            record = {'id':key, 'title':options['title'] or (old or {}).get('title') or body.strip().split('\n')[0][:120] or 'Saved attachment',
                      'note': options['note'] if options['note'] is not None else (old or {}).get('note', ''),
                      'body':body, 'saved_at':datetime.fromtimestamp(item['timestamp'],timezone.utc).isoformat(),
                      'tags':tags, 'tag_method':method, 'attachments':attachments, 'revision':revision}
            by_id[key] = record
            if old: updated += 1
            else: added += 1
        except Exception as error:
            retries.add(command_key)
            reason = str(error) if type(error) is RuntimeError and re.fullmatch(r'[A-Za-z0-9 :;,.-]{1,160}', str(error)) else type(error).__name__
            print(f'::warning::One selected item deferred ({reason}); other items continue.')
    if len(retries) > 100: raise RuntimeError('Retry queue full; checkpoint not advanced')
    if args.publish:
        records = list(by_id.values())
        media_storage.finish(records, directory)
        render(records, directory)
        database.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        checkpoint_file.write_text(json.dumps({'cursor':inbox['cursor'], 'retry_commands':sorted(retries)}) + '\n')
    print(f'{added} new selected item(s); {updated} updated; {len(retries)} deferred; mode={"publish" if args.publish else "preview"}.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Import failed ({type(error).__name__}); no content committed. Check receiver or Meta credentials.')
        raise SystemExit(1)
