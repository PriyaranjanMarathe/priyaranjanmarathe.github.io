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
