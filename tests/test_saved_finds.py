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

    def test_display_labels_preserve_normalized_filter_keys(self):
        record = {'id': 'story', 'title': 'Story', 'body': '', 'saved_at': '2026-10-27',
                  'tags': ['whatsappideas', 'science'], 'tag_labels': {'whatsappideas': 'WhatsAppIdeas'},
                  'tag_method': 'chosen', 'attachments': []}
        with tempfile.TemporaryDirectory() as directory:
            f.render([record], Path(directory))
            page = (Path(directory) / 'index.html').read_text(encoding='utf-8')
        self.assertIn('data-tag="whatsappideas">#WhatsAppIdeas</button>', page)
        self.assertIn('data-tag="science">#science</button>', page)
        self.assertEqual(f.tags_for('', ['WhatsAppIdeas']), (['whatsappideas'], 'chosen'))

    def test_api_key_auth_keeps_account_resource_path(self):
        client = f.Twilio('AC' + '0' * 32, 'secret', 'SK' + '1' * 32)
        self.assertEqual(client.session.auth, ('SK' + '1' * 32, 'secret'))
        self.assertIn('AC' + '0' * 32, client.prefix)

    def test_local_story_embeds_inline_with_sandbox_and_search_text(self):
        record = {'id': 'story', 'title': 'VP story', 'body': '', 'saved_at': '2026-11-05',
                  'tags': ['history'], 'tag_method': 'suggested', 'attachments': [],
                  'search_text': 'Harry Truman <script>bad</script>',
                  'embedded_story': {'path': '/finds/stories/vice-presidents.html', 'title': 'Sixteen "VPs"'}}
        with tempfile.TemporaryDirectory() as directory:
            f.render([record], Path(directory))
            page = (Path(directory) / 'index.html').read_text()
        self.assertIn('src="/finds/stories/vice-presidents.html"', page)
        self.assertIn('sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"', page)
        self.assertNotIn('allow-same-origin', page)
        self.assertIn('title="Sixteen &quot;VPs&quot;"', page)
        self.assertIn('data-search="Harry Truman &lt;script&gt;bad&lt;/script&gt;"', page)
        self.assertIn('f.contentWindow===event.source', page)
        self.assertIn('Number.isFinite(data.height)', page)
        self.assertIn("data.type!=='linked-blog-story-scroll'", page)
        self.assertIn('Number.isFinite(data.top)', page)
        self.assertIn('data.top<=frame.offsetHeight', page)

    def test_story_embed_rejects_external_or_unsafe_paths(self):
        record = {'id': 'story', 'title': 'VP story', 'body': '', 'saved_at': '2026-11-05',
                  'tags': [], 'tag_method': 'chosen', 'attachments': []}
        for path in ['https://evil.example/story.html', '//evil.example/story.html',
                     '/finds/stories/../private.html', '/finds/stories/x.html?code=bad',
                     'javascript:alert(1)', '/finds/stories/x.html" onload="bad', None]:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                record['embedded_story'] = {'path': path}
                f.render([record], Path(directory))
                self.assertNotIn('<iframe', (Path(directory) / 'index.html').read_text())

    def test_external_api_paths_rejected_before_request(self):
        client = f.Twilio('AC' + '0' * 32, 'test')
        with self.assertRaises(ValueError):
            client.get('https://evil.example/')


if __name__ == '__main__':
    unittest.main()
