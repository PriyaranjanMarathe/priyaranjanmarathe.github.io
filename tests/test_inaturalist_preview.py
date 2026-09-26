import sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import inaturalist_preview as preview
from saved_finds import render

class ObservationPreviews(unittest.TestCase):
 def test_only_observation_urls_and_deduplication(self):
  self.assertEqual(preview.observation_ids('https://www.inaturalist.org/observations/123?x=1 https://inaturalist.org/observations/123 https://evil.test/observations/9 https://inaturalist.org.evil.test/observations/2'),['123'])
 def response(self,license='cc-by',host='static.inaturalist.org'):
  r=MagicMock();r.status_code=200;r.json.return_value={'results':[{'id':123,'taxon':{'preferred_common_name':'Butterfly'},'user':{'login':'observer'},'photos':[{'id':456,'license_code':license,'url':f'https://{host}/photos/456/square.jpg','attribution':'Photographer (CC BY 4.0)'}]}]};return r
 def test_external_photo_credit_and_no_copy(self):
  with patch.object(preview.requests,'get',return_value=self.response()) as get:
   result=preview.fetch_preview('123')
   self.assertEqual(result['image_url'],'https://static.inaturalist.org/photos/456/large.jpg')
   self.assertIn('Photographer',result['attribution']);self.assertEqual(get.call_count,1)
 def test_restricted_and_untrusted_photos_are_not_embedded(self):
  for response in [self.response(None),self.response('all-rights-reserved'),self.response(host='evil.test')]:
   with patch.object(preview.requests,'get',return_value=response):self.assertIsNone(preview.fetch_preview('123'))
 def test_api_failure_does_not_block_post_and_retries(self):
  record={'body':'https://inaturalist.org/observations/123'}
  with patch.object(preview,'fetch_preview',side_effect=preview.requests.Timeout),patch('builtins.print'):
   preview.enrich([record]);self.assertNotIn('link_previews',record)
  with patch.object(preview,'fetch_preview',return_value=None):preview.enrich([record]);self.assertEqual(record['link_previews'],[])
 def test_cached_preview_does_not_refetch(self):
  with patch.object(preview,'fetch_preview') as fetch:
   preview.enrich([{'body':'https://inaturalist.org/observations/123','link_previews':[]}]);fetch.assert_not_called()
 def test_caption_is_escaped_and_original_link_retained(self):
  with patch.object(preview.requests,'get',return_value=self.response()):item=preview.fetch_preview('123')
  item['attribution']='<script>bad</script>'
  record={'id':'test','title':'Test','body':item['url'],'saved_at':'2026-09-20','tags':[],'tag_method':'chosen','attachments':[],'link_previews':[item]}
  with tempfile.TemporaryDirectory() as d:
   render([record],Path(d));page=(Path(d)/'index.html').read_text()
   self.assertIn(item['image_url'],page);self.assertIn('referrerpolicy="no-referrer"',page)
   self.assertNotIn('<script>bad</script>',page);self.assertIn('&lt;script&gt;',page)

 def test_malformed_links_do_not_hide_valid_observations(self):
  for malformed in ['https://[broken', 'https://[not-an-ip]/', 'https://example.com：443/path']:
   with self.subTest(url=malformed):
    self.assertEqual(preview.observation_ids(malformed + ' https://inaturalist.org/observations/123'), ['123'])
 def test_malformed_post_does_not_block_other_previews(self):
  records=[{'body':'Forward with https://[broken', 'note':''}, {'body':'https://inaturalist.org/observations/123'}]
  with patch.object(preview,'fetch_preview',return_value={'title':'Butterfly'}) as fetch:
   preview.enrich(records)
  self.assertEqual(records[0]['body'],'Forward with https://[broken')
  self.assertEqual(records[1]['link_previews'],[{'title':'Butterfly'}])
  fetch.assert_called_once_with('123')
