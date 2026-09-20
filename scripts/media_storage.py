"""Verified R2 mirrors and a one-way switch away from Vercel media storage."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlsplit

import requests

MAX_FILE = 20 * 1024 * 1024
SWITCH_BYTES = 900_000_000
BACKUP_LIMIT = 9_000_000_000
KEY = re.compile(r'media/[a-f0-9]{24}\.(jpg|png|webp|gif|pdf|mp4|ogg|mp3|m4a)')


def enabled():
    return os.environ.get('R2_BACKUP_ENABLED') == 'true'


def reserve_vercel(size):
    """Reserve bytes within this batch so a large import cannot cross the limit."""
    if not enabled() or os.environ.get('MEDIA_PRIMARY') == 'r2':
        return
    used = int(os.environ['VERCEL_MEDIA_BYTES'])
    if used + size >= SWITCH_BYTES:
        os.environ['MEDIA_PRIMARY'] = 'r2'
    else:
        os.environ['VERCEL_MEDIA_BYTES'] = str(used + size)


def public_base():
    base = os.environ['R2_PUBLIC_BASE_URL'].rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Invalid R2 public URL')
    return base


def client():
    import boto3
    from botocore.config import Config
    account = os.environ['R2_ACCOUNT_ID']
    if not re.fullmatch(r'[a-f0-9]{32}', account):
        raise ValueError('Invalid R2 account')
    return boto3.client('s3', endpoint_url=f'https://{account}.r2.cloudflarestorage.com',
                       region_name='auto', aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
                       aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
                       config=Config(connect_timeout=15, read_timeout=60, retries={'max_attempts':3},
                                     request_checksum_calculation='when_required', response_checksum_validation='when_required'))


def digest_stream(chunks):
    digest = hashlib.sha256()
    size = 0
    for chunk in chunks:
        size += len(chunk)
        if size > MAX_FILE:
            raise ValueError('Oversized media')
        digest.update(chunk)
    return digest.hexdigest(), size


def backup(file, key, mime):
    if not KEY.fullmatch(key):
        raise ValueError('Invalid media key')
    data = Path(file).read_bytes()
    if len(data) > MAX_FILE:
        raise ValueError('Oversized media')
    digest = hashlib.sha256(data).hexdigest()
    storage = client()
    bucket = os.environ['R2_BUCKET']
    used = 0
    for page_number, page in enumerate(storage.get_paginator('list_objects_v2').paginate(Bucket=bucket)):
        if page_number >= 100:
            raise RuntimeError('Backup inventory safety limit reached')
        used += sum(item['Size'] for item in page.get('Contents', []) if item['Key'] != key)
        if used + len(data) > BACKUP_LIMIT:
            raise RuntimeError('R2 backup stopped at 9 GB safety limit')
    storage.put_object(Bucket=bucket, Key=key, Body=data, ContentType=mime,
                       CacheControl='public, max-age=31536000, immutable', Metadata={'sha256':digest})
    response = storage.get_object(Bucket=bucket, Key=key)
    try:
        actual = digest_stream(response['Body'].iter_chunks(chunk_size=65536))
    finally:
        response['Body'].close()
    if actual != (digest, len(data)):
        raise ValueError('R2 backup verification failed')
    return {'backup_url':public_base() + '/' + key, 'sha256':digest, 'size':len(data)}


def validate_attachment_url(url):
    parsed = urlsplit(url)
    vercel = parsed.scheme == 'https' and (parsed.hostname or '').endswith('.public.blob.vercel-storage.com')
    r2 = enabled() and url.startswith(public_base() + '/media/')
    if parsed.username or parsed.password or parsed.query or parsed.fragment or not (vercel or r2):
        raise ValueError('Unexpected media URL')
    key = parsed.path.lstrip('/') if vercel else url[len(public_base()) + 1:]
    if not KEY.fullmatch(key):
        raise ValueError('Unexpected media path')
    return key


def verify_public(attachment):
    url = attachment['backup_url']
    if not url.startswith(public_base() + '/media/'):
        raise ValueError('Unexpected backup origin')
    with requests.get(url, stream=True, timeout=60, allow_redirects=False) as response:
        response.raise_for_status()
        if digest_stream(response.iter_content(65536)) != (attachment['sha256'], attachment['size']):
            raise ValueError('Public R2 media verification failed')


def prepare(records, directory, root):
    """Backfill only missing mirrors; switch all URLs before reaching capacity."""
    if not enabled():
        return
    state_file = directory / 'media-state.json'
    state = json.loads(state_file.read_text()) if state_file.exists() else {'primary':'vercel'}
    attachments = [a for record in records for a in record.get('attachments', [])]
    for attachment in attachments:
        if attachment.get('backup_url'):
            continue
        key = validate_attachment_url(attachment['url'])
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'media'
            with requests.get(attachment['url'], stream=True, timeout=60, allow_redirects=False) as response:
                response.raise_for_status()
                size = 0
                with file.open('wb') as output:
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > MAX_FILE: raise ValueError('Oversized media')
                        output.write(chunk)
            attachment.update(backup(file, key, attachment['type']))
    if state['primary'] != 'r2':
        result = subprocess.run(['node', str(root / 'receiver/scripts/upload-media.js'), '--usage'],
                                capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError('Unable to check Vercel capacity')
        usage = json.loads(result.stdout)['bytes']
        state['vercel_media_bytes'] = usage
        os.environ['VERCEL_MEDIA_BYTES'] = str(usage)
        if usage >= SWITCH_BYTES:
            # Public delivery must work for every attachment before changing any URL.
            for attachment in attachments: verify_public(attachment)
            state['primary'] = 'r2'
    if state['primary'] == 'r2':
        for attachment in attachments:
            if attachment['url'] != attachment['backup_url']:
                attachment.setdefault('vercel_url', attachment['url'])
            attachment['url'] = attachment['backup_url']
    os.environ['MEDIA_PRIMARY'] = state['primary']
    directory.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2) + '\n')


def finish(records, directory):
    """Complete a capacity switch triggered by new media within this batch."""
    if not enabled() or os.environ.get('MEDIA_PRIMARY') != 'r2':
        return
    state_file = directory / 'media-state.json'
    state = json.loads(state_file.read_text())
    if state['primary'] == 'r2':
        return
    attachments = [a for record in records for a in record.get('attachments', [])]
    for attachment in attachments: verify_public(attachment)
    for attachment in attachments:
        if attachment['url'] != attachment['backup_url']:
            attachment.setdefault('vercel_url', attachment['url'])
        attachment['url'] = attachment['backup_url']
    state['primary'] = 'r2'
    state_file.write_text(json.dumps(state, indent=2) + '\n')
