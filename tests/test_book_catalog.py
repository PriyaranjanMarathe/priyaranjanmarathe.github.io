import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from saved_finds import render
ROOT=Path(__file__).resolve().parents[1]
class BookCatalogTests(unittest.TestCase):
    def setUp(self):
        self.records=json.loads((ROOT/'docs/finds/finds.json').read_text())
        self.catalog=(ROOT/'docs/finds/stories/my-library.html').read_text()
        self.books=json.loads(re.search(r'<script id="catalog-data" type="application/json">(.*?)</script>',self.catalog,re.S)[1])
    def test_all_books_are_available_without_leaving_page(self):
        self.assertEqual(len(self.books),158)
        self.assertEqual(self.catalog.count('class="owned-book"'),158)
        self.assertIn('ISBN-13: 9781416549444',self.catalog)
        self.assertIn('ISBN-10: 1416549447',self.catalog)
        self.assertIn('for="book-search">Search my books',self.catalog)
        self.assertNotIn('src="https://claude.ai',self.catalog)
    def test_existing_renderer_retains_catalog_on_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            render(self.records,Path(tmp));result=(Path(tmp)/'index.html').read_text()
            self.assertEqual(result,(ROOT/'docs/finds/index.html').read_text())
            self.assertIn('src="/finds/stories/my-library.html"',result)
            self.assertEqual(result.count('<article id='),len(self.records))
    def test_minimal_tags_keep_full_search_data(self):
        self.assertNotIn('class="book-tags"',self.catalog)
        self.assertNotIn('class="book-tag"',self.catalog)
        record=next(r for r in self.records if r['id']=='my-library')
        self.assertEqual(record['tags'],['books'])
        self.assertIn('surrealism',record['search_text'])
        self.assertIn('surrealism',self.books[1]['tags'])
    def test_controls_accessible_and_frame_resizes(self):
        for value in ['Sort books','Book topic','Book language','aria-live="polite"','tabindex="0"','<noscript>','linked-blog-story-resize','new ResizeObserver']:
            self.assertIn(value,self.catalog)
    def test_all_original_book_fields_preserved(self):
        for b in self.books:
            self.assertTrue(b['title'])
            self.assertIn('authors',b)
            self.assertIn('addedAt',b)
        self.assertEqual(self.books[-1]['title'],'The Gene')
        self.assertIn('Mukherjee',self.books[-1]['notes'])
