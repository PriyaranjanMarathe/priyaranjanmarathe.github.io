"""Opt-in WhatsApp saves. Never print message bodies, numbers, or API responses."""
import argparse
from collections import Counter
import hashlib
import html
import json
import os
from pathlib import Path
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
TYPES = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp',
         'image/gif': '.gif', 'application/pdf': '.pdf', 'video/mp4': '.mp4',
         'audio/ogg': '.ogg', 'audio/mpeg': '.mp3', 'audio/mp4': '.m4a'}
RULES = {
    'technology': r'\b(software|programming|python|javascript|computer|technology)\b',
    'ai': r'\b(ai|llm|chatgpt|machine learning|artificial intelligence)\b',
    'science': r'\b(science|physics|astronomy|scientific)\b',
    'environment': r'\b(climate|environment|conservation|biodiversity)\b',
    'history': r'\b(history|historical|archaeology)\b',
    'literature': r'\b(poem|poetry|literature|novel)\b',
    'food': r'\b(recipe|cooking|cuisine)\b',
    'health': r'\b(health|exercise|nutrition|medicine)\b',
}


def date(message):
    return parsedate_to_datetime(message['date_created']).astimezone(timezone.utc)


def tags_for(body, explicit):
    if explicit:
        return sorted(set(t.lower() for t in explicit))[:12], 'chosen'
    return ([tag for tag, pattern in RULES.items() if re.search(pattern, body, re.I)]
            or ['untagged']), 'suggested'


def selections(messages, owner, destination, start):
    """Only `save #tags` opts in the immediately preceding item within 10 minutes."""
    eligible = [m for m in messages if m.get('direction') == 'inbound'
                and m.get('from') == owner and m.get('to') == destination]
    times = Counter(date(m) for m in eligible)
    previous = None
    for message in sorted(eligible, key=lambda m: (date(m), m['sid'])):
        # Twilio timestamps have second precision. Never guess ordering when tied.
        if times[date(message)] > 1:
            previous = None
            continue
        if (message.get('direction') != 'inbound' or message.get('from') != owner
                or message.get('to') != destination):
            continue
        text = (message.get('body') or '').strip()
        command = re.fullmatch(r'save(?:\s+#[\w-]+)*', text, re.I)
        if command:
            if (previous and date(message) >= start and date(previous) >= start
                    and timedelta(0) <= date(message) - date(previous) <= timedelta(minutes=10)):
                yield previous, re.findall(r'#([\w-]+)', text)
            previous = None
        elif re.match(r'^(join\b|stop$|start$|help$)', text, re.I):
            previous = None
        else:
            previous = message


class Twilio:
    def __init__(self, sid, token, key_sid=None):
        if not re.fullmatch(r'AC[0-9a-fA-F]{32}', sid):
            raise ValueError('Invalid account SID')
        self.prefix = f'/2010-04-01/Accounts/{sid}/'
        self.session = requests.Session()
        if key_sid and not re.fullmatch(r'SK[0-9a-fA-F]{32}', key_sid):
            raise ValueError('Invalid API key SID')
        self.session.auth = (key_sid or sid, token)

    def get(self, path, stream=False):
        # Only Twilio API paths can receive credentials. requests removes auth on
        # redirects to other hosts (Twilio media can use signed storage URLs).
        if not path.startswith(self.prefix) or '..' in path or '\\' in path:
            raise ValueError('Unexpected API path')
        response = self.session.get('https://api.twilio.com' + path, timeout=45, stream=stream)
        if response.status_code != 200:
            status = response.status_code
            try:
                code = int(response.json().get('code', 0))
            except (ValueError, TypeError):
                code = 0
            response.close()
            print(f'Twilio API error: HTTP {status}; code {code}')
            raise RuntimeError('Twilio request failed')
        return response

    def pages(self, path, key):
        seen = set()
        while path:
            if path in seen or len(seen) >= 1000:
                raise RuntimeError('Pagination limit reached; no changes published')
            seen.add(path)
            with self.get(path) as response:
                data = response.json()
            yield from data[key]
            path = data.get('next_page_uri')

    def messages(self, owner, destination, start):
        query = urlencode({'From': owner, 'To': destination,
                           'DateSent>': (start - timedelta(days=1)).date().isoformat(), 'PageSize': 1000})
        return list(self.pages(self.prefix + 'Messages.json?' + query, 'messages'))

    def media(self, message, directory, key):
        sid = message['sid']
        if not re.fullmatch(r'(SM|MM)[0-9a-fA-F]{32}', sid):
            raise ValueError('Invalid message identifier')
        base = self.prefix + f'Messages/{sid}/Media'
        attachments = []
        for number, item in enumerate(self.pages(base + '.json?PageSize=100', 'media_list')):
            mime = item['content_type'].split(';')[0].lower()
            if mime not in TYPES:
                raise ValueError('Unsupported attachment type; item left for retry')
            media_sid = item['sid']
            if not re.fullmatch(r'ME[0-9a-fA-F]{32}', media_sid):
                raise ValueError('Invalid media identifier')
            directory.mkdir(parents=True, exist_ok=True)
            filename = f'{key}-{number}{TYPES[mime]}'
            temporary = directory / (filename + '.part')
            try:
                with self.get(base + '/' + media_sid, stream=True) as response, temporary.open('wb') as output:
                    size = 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 20 * 1024 * 1024:
                            raise ValueError('Attachment exceeds 20 MB; item left for retry')
                        output.write(chunk)
                temporary.replace(directory / filename)
            finally:
                temporary.unlink(missing_ok=True)
            attachments.append({'url': '/finds/media/' + filename, 'type': mime})
        if len(attachments) != int(message.get('num_media', 0)):
            raise RuntimeError('Incomplete media response; item left for retry')
        return attachments


def linked_text(body):
    chunks = re.split(r'(https?://[^\s<>]+)', body)
    return ''.join(f'<a href="{html.escape(s, quote=True)}" rel="noreferrer noopener">{html.escape(s)}</a>'
                   if re.match(r'^https?://', s) else html.escape(s) for s in chunks)


def render(records, directory):
    directory.mkdir(parents=True, exist_ok=True)
    cards = []
    for record in sorted(records, key=lambda r: r['saved_at'], reverse=True):
        e = html.escape
        tag_links = ' '.join(f'<button class="tag" data-tag="{e(t, quote=True)}">#{e(t)}</button>' for t in record['tags'])
        media = []
        for attachment in record['attachments']:
            url, mime = e(attachment['url'], quote=True), attachment['type']
            if mime.startswith('image/'):
                media.append(f'<a href="{url}"><img loading="lazy" src="{url}" alt="Saved image; see accompanying text for context"></a>')
            elif mime.startswith(('video/', 'audio/')):
                kind = mime.split('/')[0]
                media.append(f'<{kind} controls preload="none" src="{url}"></{kind}>')
            else:
                media.append(f'<p><a href="{url}">Open saved PDF</a></p>')
        note = f'<div class="note">{linked_text(record.get("note", ""))}</div>' if record.get('note') else ''
        for preview in record.get('link_previews', []):
            if preview.get('source') != 'inaturalist': continue
            media.append(f'<figure><a href="{e(preview["url"], quote=True)}"><img loading="lazy" decoding="async" referrerpolicy="no-referrer" src="{e(preview["image_url"], quote=True)}" alt="{e(preview["title"], quote=True)}"></a>'
                         f'<figcaption class="meta"><a href="{e(preview["url"], quote=True)}">{e(preview["title"])}</a> · iNaturalist'
                         f' · Observed by {e(preview["observer"])} · <a href="{e(preview["photo_url"], quote=True)}">{e(preview["attribution"] or preview["license"].upper())}</a></figcaption></figure>')
        label = 'Suggested tags' if record['tag_method'] == 'suggested' else 'Tags'
        cards.append(f'''<article id="{record['id']}" data-tags="{e(json.dumps(record['tags']), quote=True)}">
<h2><a href="#{record['id']}">{e(record['title'])}</a></h2>
<p class="meta">Saved {e(record['saved_at'][:10])}</p>
{note}<div class="body">{linked_text(record['body'])}</div>{''.join(media)}
<p class="meta">{label}: {tag_links}</p></article>''')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Saved finds · Ranjan Marathe</title><style>
:root{color-scheme:light dark}body{max-width:760px;margin:40px auto;padding:0 20px;font:18px/1.65 Georgia,serif}a{color:light-dark(#075f9e,#8dcaff)}h1,h2,input,button,.meta{font-family:system-ui,sans-serif}h1{margin-bottom:0}h2{font-size:1.25rem;overflow-wrap:anywhere}.meta{font-size:.85rem;opacity:.8}article{border-top:1px solid #aaa6;padding:24px 0}.note{white-space:pre-wrap;border-left:3px solid #aaa8;padding:0 16px;margin:16px 0}.body{white-space:pre-wrap;overflow-wrap:anywhere}input{box-sizing:border-box;width:100%;padding:12px;font-size:1rem}button{cursor:pointer;padding:7px 12px;margin:4px;border:1px solid #aaa8;border-radius:18px;background:transparent;color:inherit}img,video,audio{max-width:100%;height:auto}img{margin-top:16px}#count{font:14px system-ui}nav{font:16px system-ui}</style>
<nav><a href="/">Home</a> · <a href="/blog/">Blog</a></nav><h1>Saved finds</h1>
<p>Social media is here to stay, I curate the best here.</p>
<p class="meta">Inspired by <a href="https://simonwillison.net/2024/Dec/22/link-blog/">Simon Willison’s link blog</a>.</p>
<label for="search">Search words or tags</label><input id="search" type="search" placeholder="Try science, history, or a phrase"><p><button id="clear">Show all</button><span id="count" role="status"></span></p><main>'''
    page += ''.join(cards) or '<p>No finds published yet.</p>'
    page += '''</main><script>
const search=document.querySelector('#search'),cards=[...document.querySelectorAll('article')];let selected='';
function filter(){const q=search.value.toLocaleLowerCase();let n=0;cards.forEach(c=>{c.hidden=!(c.textContent.toLocaleLowerCase().includes(q)&&(!selected||JSON.parse(c.dataset.tags).includes(selected)));if(!c.hidden)n++});document.querySelector('#count').textContent=n+' saved finds'+(selected?' · #'+selected:'')}
search.addEventListener('input',filter);document.querySelectorAll('[data-tag]').forEach(b=>b.addEventListener('click',()=>{selected=b.dataset.tag;filter()}));document.querySelector('#clear').addEventListener('click',()=>{selected='';search.value='';filter()});filter();
</script></html>'''
    (directory / 'index.html').write_text(page, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true', help='Write selected public content; otherwise only report counts')
    args = parser.parse_args()
    owner = os.environ['WHATSAPP_OWNER']
    destination = os.environ['WHATSAPP_SANDBOX']
    if not all(re.fullmatch(r'whatsapp:\+[1-9]\d{7,14}', n) for n in [owner, destination]):
        raise ValueError('Expected WhatsApp numbers in whatsapp:+countrycode format')
    start = datetime.fromisoformat(os.environ['CAPTURE_START'].replace('Z', '+00:00'))
    if start.tzinfo is None:
        raise ValueError('CAPTURE_START requires a timezone')
    key_sid = os.environ.get('TWILIO_API_KEY_SID')
    credential = os.environ['TWILIO_API_KEY_SECRET'] if key_sid else os.environ['TWILIO_AUTH_TOKEN']
    api = Twilio(os.environ['TWILIO_ACCOUNT_SID'], credential, key_sid)
    directory = ROOT / 'docs/finds'
    database = directory / 'finds.json'
    records = json.loads(database.read_text()) if database.exists() else []
    existing = {r['id'] for r in records}
    chosen = list(selections(api.messages(owner, destination, start), owner, destination, start))
    added = 0
    for message, explicit in chosen:
        key = hashlib.sha256(message['sid'].encode()).hexdigest()[:24]
        if key in existing:
            continue
        added += 1
        if not args.publish:
            continue
        body = message.get('body') or ''
        tags, method = tags_for(body, explicit)
        attachments = api.media(message, directory / 'media', key) if int(message.get('num_media', 0)) else []
        records.append({'id': key, 'title': (body.strip().split('\n')[0][:120] or 'Saved attachment'),
                        'body': body, 'saved_at': date(message).isoformat(), 'tags': tags,
                        'tag_method': method, 'attachments': attachments})
        existing.add(key)
    if args.publish:
        render(records, directory)
        database.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{added} new selected item(s); mode={"publish" if args.publish else "preview"}.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Do not expose authenticated URLs, message content, or numbers in logs.
        print(f'Import failed ({type(error).__name__}). No commit should be made; check configuration and Twilio status.')
        raise SystemExit(1)
