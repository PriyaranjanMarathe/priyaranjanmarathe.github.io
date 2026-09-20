import importlib.util
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone

spec = importlib.util.spec_from_file_location('finds', Path(__file__).resolve().parents[1] / 'scripts/saved_finds.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
OWNER = 'whatsapp:+15550000001'
DEST = 'whatsapp:+14155238886'
START = datetime(2026, 9, 20, tzinfo=timezone.utc)


def msg(body, minute=1, **kwargs):
    return dict({'sid': 'SM' + f'{minute:032x}', 'body': body, 'from': OWNER, 'to': DEST,
                 'direction': 'inbound', 'date_created': f'Sun, 20 Sep 2026 00:{minute:02}:00 +0000'}, **kwargs)


class FindsTests(unittest.TestCase):
    def test_unselected_health_messages_never_publish(self):
        self.assertEqual(list(f.selections([msg('Weight 70'), msg('hello', 2)], OWNER, DEST, START)), [])

    def test_explicit_save_selects_previous_and_manual_tags(self):
        selected = list(f.selections([msg('A useful article'), msg('save #Science #history', 2)], OWNER, DEST, START))
        self.assertEqual(selected[0][0]['body'], 'A useful article')
        self.assertEqual(f.tags_for('', selected[0][1]), (['history', 'science'], 'chosen'))

    def test_owner_destination_direction_and_cutoff(self):
        for change in [{'from': 'whatsapp:+15550000002'}, {'to': 'whatsapp:+15550000003'}, {'direction': 'outbound-api'}]:
            self.assertEqual(list(f.selections([msg('private', **change), msg('save', 2)], OWNER, DEST, START)), [])
        self.assertEqual(list(f.selections([msg('old'), msg('save', 2)], OWNER, DEST, START.replace(hour=1))), [])

    def test_expiration_and_sandbox_commands(self):
        for messages in [[msg('old'), msg('save', 12)], [msg('join abc'), msg('save', 2)], [msg('old'), msg('stop', 2), msg('save', 3)]]:
            self.assertEqual(list(f.selections(messages, OWNER, DEST, START)), [])

    def test_ambiguous_same_second_is_not_published(self):
        self.assertEqual(list(f.selections([msg('private'), msg('save', sid='SM' + 'f' * 32)], OWNER, DEST, START)), [])

    def test_pagination_follows_all_pages(self):
        from unittest.mock import MagicMock
        client = f.Twilio('AC' + '0' * 32, 'test')
        one, two = MagicMock(), MagicMock()
        one.__enter__.return_value.json.return_value = {'messages': [1], 'next_page_uri': client.prefix + 'next'}
        two.__enter__.return_value.json.return_value = {'messages': [2], 'next_page_uri': None}
        client.get = MagicMock(side_effect=[one, two])
        self.assertEqual(list(client.pages(client.prefix + 'first', 'messages')), [1, 2])

    def test_missing_attachment_fails_import(self):
        client = f.Twilio('AC' + '0' * 32, 'test')
        client.pages = lambda *a: iter([])
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(RuntimeError):
            client.media(msg('image', num_media='1'), Path(directory), 'abc')

    def test_unknown_is_not_guessed(self):
        self.assertEqual(f.tags_for('कविता', []), (['untagged'], 'suggested'))

    def test_html_is_inert_and_unicode_preserved(self):
        record = {'id': 'abc', 'title': '<script>bad</script>', 'body': '{{ secrets }} <img onerror=bad> नमस्कार https://example.com/',
                  'saved_at': '2026-09-20', 'tags': ['science'], 'tag_method': 'chosen', 'attachments': []}
        with tempfile.TemporaryDirectory() as directory:
            f.render([record], Path(directory))
            page = (Path(directory) / 'index.html').read_text()
        self.assertNotIn('<img onerror', page)
        self.assertNotIn('<script>bad', page)
        self.assertIn('नमस्कार', page)
        self.assertIn('href="https://example.com/"', page)

    def test_external_api_paths_rejected_before_request(self):
        client = f.Twilio('AC' + '0' * 32, 'test')
        with self.assertRaises(ValueError):
            client.get('https://evil.example/')


if __name__ == '__main__':
    unittest.main()
