import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from meta_finds import selections

class MetaSelections(unittest.TestCase):
    def setUp(self):
        self.item = {'id': 'a', 'timestamp': 1000, 'type': 'text', 'body': 'Useful URL', 'context': None}
        self.command = {'id': 'b', 'timestamp': 1001, 'type': 'text', 'body': 'save #blogging', 'context': 'a'}

    def test_explicit_reply_out_of_order_and_duplicates(self):
        found = list(selections([self.command, self.item, self.command], 900, 2000))
        self.assertEqual(found, [(self.item, ['blogging'])])

    def test_unquoted_save_does_not_guess(self):
        self.command['context'] = None
        self.assertEqual(list(selections([self.item, self.command], 900, 2000)), [])

    def test_missing_context_cannot_publish_unrelated_forward(self):
        self.command['context'] = 'missing'
        self.assertEqual(list(selections([self.item, self.command], 900, 2000)), [])

    def test_unselected_and_recent_and_before_cutoff(self):
        self.assertEqual(list(selections([self.item], 900, 2000)), [])
        self.assertEqual(list(selections([self.item, self.command], 900, 1002)), [])
        self.assertEqual(list(selections([self.item, self.command], 1001, 2000)), [])

    def test_unsupported_item_not_published(self):
        self.item['type'] = 'contacts'
        self.assertEqual(list(selections([self.item, self.command], 900, 2000)), [])

class CustomFields(unittest.TestCase):
    def test_common_punctuation_and_field_typos(self):
        from meta_finds import parse_command
        for command in ['save: #science, #reading.\nTitel: My title\nNotes: My note',
                        '**Save** #science; #reading\n**Title:** My title\n**Note**: My note']:
            self.assertEqual(parse_command(command), {'tags':['science','reading'],'title':'My title','note':'My note'})

    def test_separate_recent_attachments_remain_ambiguous(self):
        from meta_finds import selections
        image={'id':'image','type':'image','timestamp':1000,'body':'picture'}
        command={'id':'save','type':'text','timestamp':1100,'body':'save #science'}
        self.assertEqual(list(selections([image,command],900,2000)),[(image,['science'])])
        another={**image,'id':'another','timestamp':1020}
        self.assertEqual(list(selections([image,another,command],900,2000)),[])
        self.assertEqual(list(selections([image,{**command,'timestamp':1700}],900,2000)),[])
        self.assertEqual(list(selections([image,{**command,'context':'missing'}],900,2000)),[])

    def test_common_whitespace_linebreak_and_case_variations(self):
        from meta_finds import parse_command
        for command in [
            '  SAVE\t#Science  \r\n\r\n  title :  My title  \r\n  NOTE : My note',
            '\ufeffsave\u00a0#Science\u00a0\nTitle: My title\nNote: My note',
            '\n\nsave #Science\n\nTitle: My title\n\nNote: My note\n',
        ]:
            with self.subTest(command=command):
                self.assertEqual(parse_command(command), {'tags':['Science'],'title':'My title','note':'My note'})

    def test_invalid_or_ambiguous_commands_stay_unpublished(self):
        from meta_finds import parse_command
        for command in ['save #science\nTitle:   \nNote: hello',
                        'save #science\nTitle: One\n title : Two',
                        'save #science\nNote: One\n NOTE : Two',
                        'save #science\nTitle: ' + 'a'*201,
                        'save #science\nNote: ' + 'a'*5001,
                        'save this image', 'save #science\nUnexpected field']:
            with self.subTest(command=command[:50]):
                self.assertIsNone(parse_command(command))

    def test_rejection_diagnostics_exclude_private_text_and_deduplicate(self):
        from meta_finds import rejected_commands
        invalid={'id':'a','timestamp':1000,'body':'save private text','context':'target'}
        unlinked={'id':'b','timestamp':1000,'body':'save #science'}
        result=rejected_commands([invalid,invalid,unlinked],900,2000)
        self.assertEqual(sum(result.values()),2)
        self.assertNotIn('private text',str(result))
        self.assertEqual(rejected_commands([invalid],900,1001),{})

    def test_save_line_trailing_whitespace_before_fields(self):
        from meta_finds import parse_command
        self.assertEqual(parse_command('save #science \nTitle: My title\nNote: My note'),
                         {'tags':['science'], 'title':'My title', 'note':'My note'})

    def test_title_multiline_note_and_tags(self):
        from meta_finds import parse_command
        self.assertEqual(parse_command('save #Science\nTitle: My title\nNote: First line\nSecond line'),
                         {'tags':['Science'],'title':'My title','note':'First line\nSecond line'})
    def test_ambiguous_fields_rejected(self):
        from meta_finds import parse_command
        for text in ['save\nSurprise', 'save\nTitle: a\nTitle: b', 'save\nTitle:']:
            self.assertIsNone(parse_command(text))
    def test_notes_and_titles_are_escaped(self):
        import tempfile
        from saved_finds import render
        with tempfile.TemporaryDirectory() as d:
            record={'id':'a','title':'<script>bad</script>','body':'hello','note':'<img onerror=bad>',
                    'saved_at':'2026-09-20','tags':[],'tag_method':'chosen','attachments':[]}
            render([record],Path(d))
            html=(Path(d)/'index.html').read_text()
            self.assertIn('&lt;img onerror=bad&gt;',html)
            self.assertNotIn('<script>bad</script>',html)

class FailureIsolation(unittest.TestCase):
    def test_unlinked_save_recovers_attachment_from_previous_poll(self):
        import tempfile, json, os, time
        from unittest.mock import patch, MagicMock
        import meta_finds
        now=int(time.time())
        command={'id':'save','timestamp':now-200,'type':'text','body':'save #science\nTitle: Inferred'}
        image={'id':'image','timestamp':now-300,'type':'image','body':'picture'}
        responses=[]
        for messages in [[command],[image,command]]:
            response=MagicMock(); response.__enter__.return_value=response; response.status_code=200
            response.json.return_value={'messages':messages,'cursor':1234}; responses.append(response)
        with tempfile.TemporaryDirectory() as d, patch.object(meta_finds,'ROOT',Path(d)), patch.object(meta_finds.requests,'get',side_effect=responses), patch.object(meta_finds,'media_attachment',return_value=[]), patch('sys.argv',['meta_finds','--publish']), patch('builtins.print'), patch.dict(os.environ,{'WHATSAPP_INBOX_URL':'https://saved-finds-receiver.vercel.app/api/inbox','INBOX_READ_TOKEN':'test','CAPTURE_START':'2026-01-01T00:00:00Z'}):
            meta_finds.main()
            records=json.loads((Path(d)/'docs/finds/finds.json').read_text())
            self.assertEqual(len(records),1)
            self.assertEqual(records[0]['title'],'Inferred')

    def test_failed_media_does_not_block_text_and_is_retried(self):
        import tempfile, json, os, time
        from unittest.mock import patch, MagicMock
        import meta_finds
        now=int(time.time())
        messages=[{'id':'image','timestamp':now-400,'type':'image','body':'image','media':{'id':'1'}},
                  {'id':'text','timestamp':now-400,'type':'text','body':'text'},
                  {'id':'save1','timestamp':now-200,'type':'text','body':'save #one','context':'image'},
                  {'id':'save2','timestamp':now-200,'type':'text','body':'save #two\nTitle: Custom\nNote: My note','context':'text'}]
        response=MagicMock();response.__enter__.return_value=response;response.status_code=200
        response.json.return_value={'messages':messages,'cursor':1234}
        def attachment(item,*args):
            if item['id']=='image':raise RuntimeError('test failure')
            return []
        with tempfile.TemporaryDirectory() as d, patch.object(meta_finds,'ROOT',Path(d)), patch.object(meta_finds.requests,'get',return_value=response), patch.object(meta_finds,'media_attachment',side_effect=attachment), patch('sys.argv',['meta_finds','--publish']), patch.dict(os.environ,{'WHATSAPP_INBOX_URL':'https://saved-finds-receiver.vercel.app/api/inbox','INBOX_READ_TOKEN':'test','CAPTURE_START':'2026-01-01T00:00:00Z'}):
            with patch("builtins.print"):
                meta_finds.main()
            records=json.loads((Path(d)/'docs/finds/finds.json').read_text())
            state=json.loads((Path(d)/'docs/finds/import-state.json').read_text())
            self.assertEqual(len(records),1);self.assertEqual(records[0]['title'],'Custom');self.assertEqual(records[0]['note'],'My note')
            self.assertEqual(len(state['retry_commands']),1);self.assertEqual(state['cursor'],1234)

class PostAliasTests(unittest.TestCase):
    def test_post_alias_preserves_multiline_comment(self):
        from meta_finds import parse_command
        self.assertEqual(parse_command('save #nature\nTitle: Garter snake\nPost: Look at the eyes 👀\nSecond line'), {'tags':['nature'], 'title':'Garter snake', 'note':'Look at the eyes 👀\nSecond line'})
    def test_post_and_note_cannot_silently_overwrite(self):
        from meta_finds import parse_command
        self.assertIsNone(parse_command('save #nature\nPost: First\nNote: Second'))

class PhotoGroups(unittest.TestCase):
    def messages(self):
        photos=[{'id':str(i),'timestamp':1000+i//2,'type':'image','body':'caption' if i==0 else ''} for i in range(3)]
        command={'id':'save','timestamp':1053,'type':'text','body':'save #nature\nTitle: Album\nNote: My note'}
        return photos,command
    def test_photo_burst_one_selection_stable_order(self):
        from meta_finds import command_selections
        photos,command=self.messages()
        found=list(command_selections([command]+list(reversed(photos))+[photos[0]],900,2000))
        self.assertEqual(len(found),1)
        self.assertEqual([p['id'] for p in found[0][1]['_photos']],['0','1','2'])
        self.assertEqual(found[0][1]['body'],'caption')
        self.assertEqual(found[0][2]['note'],'My note')
    def test_separate_groups_or_mixed_media_are_ambiguous(self):
        from meta_finds import reply_target
        for change in ['time','type']:
            photos,command=self.messages()
            if change=='time': photos[-1]['timestamp']=1020
            else: photos[-1]['type']='video'
            self.assertIsNone(reply_target(command,{p['id']:p for p in photos},900))
    def test_gallery_failure_does_not_return_partial_attachments(self):
        from meta_finds import selected_attachments
        from unittest.mock import patch
        photos,_=self.messages()
        with patch('meta_finds.media_attachment',side_effect=[[{'url':'one'}],RuntimeError('failed')]):
            with self.assertRaises(RuntimeError): selected_attachments({'_photos':photos},Path('/tmp'))
    def test_all_photos_get_distinct_storage_keys(self):
        from meta_finds import selected_attachments
        from unittest.mock import patch
        photos,_=self.messages()
        with patch('meta_finds.media_attachment',side_effect=lambda p,d,k:[{'url':k}]) as upload:
            result=selected_attachments({'_photos':photos},Path('/tmp'))
        self.assertEqual(len({a['url'] for a in result}),3)
        self.assertEqual(upload.call_count,3)
