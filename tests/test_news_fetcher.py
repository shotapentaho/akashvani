import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.news_fetcher import INTERNATIONAL_DOMAINS


class NewsSourceTests(unittest.TestCase):
    def test_requested_news_sources_are_searchable(self):
        self.assertIn("indiatoday.in", INTERNATIONAL_DOMAINS)
        self.assertIn("thedailystar.net", INTERNATIONAL_DOMAINS)


if __name__ == "__main__":
    unittest.main()
