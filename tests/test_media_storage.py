import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import media_storage as media


class MediaBackup(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'R2_BACKUP_ENABLED':'true', 'R2_PUBLIC_BASE_URL':'https://media.example.com', 'R2_BUCKET':'test'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.key = 'media/' + 'a' * 24 + '.jpg'
        self.original = 'https://test.public.blob.vercel-storage.com/' + self.key
        self.attachment = {'url':self.original, 'type':'image/jpeg', 'backup_url':'https://media.example.com/' + self.key,
                           'size':3, 'sha256':hashlib.sha256(b'abc').hexdigest()}

    def test_upload_is_verified_by_reading_back_bytes(self):
        storage = MagicMock()
        body = storage.get_object.return_value['Body']
        body.iter_chunks.return_value = iter([b'abc'])
        with tempfile.TemporaryDirectory() as temp, patch.object(media, 'client', return_value=storage):
            file = Path(temp) / 'test'; file.write_bytes(b'abc')
            result = media.backup(file, self.key, 'image/jpeg')
            self.assertEqual(result['sha256'], self.attachment['sha256'])
            self.assertEqual(result['size'], 3)
            body.close.assert_called_once()
            body.iter_chunks.return_value = iter([b'bad'])
            with self.assertRaises(ValueError): media.backup(file, self.key, 'image/jpeg')

    def test_small_store_keeps_vercel_and_does_not_redownload_backups(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(media.subprocess, 'run', return_value=MagicMock(returncode=0, stdout='{"bytes":100}')), patch.object(media, 'backup') as backup:
            media.prepare([{'attachments':[self.attachment]}], Path(temp), Path(temp))
            self.assertEqual(self.attachment['url'], self.original)
            backup.assert_not_called()

    def test_capacity_switch_is_sticky_and_covers_existing_records(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(media.subprocess, 'run', return_value=MagicMock(returncode=0, stdout='{"bytes":900000000}')) as usage, patch.object(media, 'verify_public') as verify:
            records = [{'attachments':[self.attachment]}]
            media.prepare(records, Path(temp), Path(temp))
            self.assertEqual(self.attachment['url'], self.attachment['backup_url'])
            self.assertEqual(self.attachment['vercel_url'], self.original)
            self.assertEqual(json.loads((Path(temp)/'media-state.json').read_text())['primary'], 'r2')
            verify.assert_called_once()
            media.prepare(records, Path(temp), Path(temp))
            usage.assert_called_once()

    def test_failed_public_verification_does_not_switch_any_urls(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(media.subprocess, 'run', return_value=MagicMock(returncode=0, stdout='{"bytes":900000000}')), patch.object(media, 'verify_public', side_effect=ValueError('unavailable')):
            with self.assertRaises(ValueError): media.prepare([{'attachments':[self.attachment]}], Path(temp), Path(temp))
            self.assertEqual(self.attachment['url'], self.original)
            self.assertFalse((Path(temp)/'media-state.json').exists())

    def test_untrusted_source_cannot_be_downloaded(self):
        for url in ['http://test.public.blob.vercel-storage.com/'+self.key,
                    'https://evil.example/'+self.key, self.original+'?token=private']:
            with self.assertRaises(ValueError): media.validate_attachment_url(url)

    def test_large_batch_switches_before_next_vercel_upload(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(media, 'verify_public'):
            path = Path(temp) / 'media-state.json'
            path.write_text('{"primary":"vercel"}')
            os.environ['MEDIA_PRIMARY'] = 'vercel'
            os.environ['VERCEL_MEDIA_BYTES'] = '890000000'
            media.reserve_vercel(5_000_000)
            self.assertEqual(os.environ['MEDIA_PRIMARY'], 'vercel')
            media.reserve_vercel(6_000_000)
            self.assertEqual(os.environ['MEDIA_PRIMARY'], 'r2')
            media.finish([{'attachments':[self.attachment]}], Path(temp))
            self.assertEqual(json.loads(path.read_text())['primary'], 'r2')
            self.assertEqual(self.attachment['url'], self.attachment['backup_url'])
