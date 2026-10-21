import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.news_fetcher import (
    ICC_HIGHLIGHTS_URL,
    INTERNATIONAL_DOMAINS,
    _fetch_icc_highlight_articles,
    _is_cricket_highlights_query,
)


class NewsSourceTests(unittest.TestCase):
    def test_requested_news_sources_are_searchable(self):
        self.assertIn("indiatoday.in", INTERNATIONAL_DOMAINS)
        self.assertIn("thedailystar.net", INTERNATIONAL_DOMAINS)
        self.assertIn("icc-cricket.com", INTERNATIONAL_DOMAINS)

    def test_cricket_highlights_query_detection(self):
        self.assertTrue(_is_cricket_highlights_query("Cricket T20 highlights"))
        self.assertFalse(_is_cricket_highlights_query("Cricket T20 score"))

    def test_icc_highlights_page_is_converted_to_articles(self):
        session = Mock()
        response = Mock()
        response.text = (
            '<a href="/videos/icc-highlights">T20 Highlights</a>'
        )
        session.get.return_value = response

        articles = _fetch_icc_highlight_articles(session)

        response.raise_for_status.assert_called_once_with()
        self.assertEqual(articles[0]["title"], "T20 Highlights")
        self.assertEqual(
            articles[0]["url"],
            "https://www.icc-cricket.com/videos/icc-highlights",
        )
        self.assertEqual(articles[0]["source"], "International Cricket Council")

    def test_icc_highlights_page_falls_back_to_category_url(self):
        session = Mock()
        response = Mock()
        response.text = "<html><body>No links</body></html>"
        session.get.return_value = response

        articles = _fetch_icc_highlight_articles(session)

        self.assertEqual(articles[0]["url"], ICC_HIGHLIGHTS_URL)


if __name__ == "__main__":
    unittest.main()
