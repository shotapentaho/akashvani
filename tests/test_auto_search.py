import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auto_search import (
    DEBOUNCE_MS,
    is_auto_eligible,
    news_query_variants,
    query_fingerprint,
    should_auto_run,
)
from utils.translator import is_non_english_script, translate_query_to_english
from utils.translator import get_ai_search_result


class AutoSearchTests(unittest.TestCase):
    def test_auto_search_waits_two_seconds(self):
        self.assertEqual(DEBOUNCE_MS, 2000)

    def test_ineligible(self):
        for q in [None, "", "  ", "a", "ab", "123", "??",
                  "weather", "weather in", "Weather In  ", "temperature at",
                  "what is the weather in", "current temperature for"]:
            self.assertFalse(is_auto_eligible(q), q)

    def test_eligible(self):
        for q in ["weather in Mumbai", "cricket", "health", "India vs Australia score",
                  "technology", "business news", "weather Mumbai"]:
            self.assertTrue(is_auto_eligible(q), q)

    def test_fingerprint_normalizes(self):
        self.assertEqual(query_fingerprint(" Health  News ", "en"), query_fingerprint("health news", "en"))
        self.assertNotEqual(query_fingerprint("health", "en"), query_fingerprint("health", "hi"))

    def test_news_query_variants(self):
        self.assertEqual(
            news_query_variants("  Latest NEWS in India  "),
            ("  Latest NEWS in India  ", "Latest in India"),
        )
        self.assertEqual(
            news_query_variants("Severe weather"),
            ("Severe weather", "weather"),
        )
        self.assertEqual(news_query_variants("newspaper headlines"), ("newspaper headlines",))
        self.assertEqual(news_query_variants("news"), ("news",))

    def test_should_auto_run(self):
        fp = query_fingerprint("health", "en")
        self.assertTrue(should_auto_run("health", fp, None))
        self.assertFalse(should_auto_run("health", fp, fp))
        self.assertFalse(should_auto_run("weather in", query_fingerprint("weather in"), None))

    def test_non_english_script_detection(self):
        self.assertTrue(is_non_english_script("अर्थव्यवस्था"))
        self.assertTrue(is_non_english_script("economy अर्थव्यवस्था"))
        self.assertFalse(is_non_english_script("economy news"))

    def test_query_translation_skips_english(self):
        client = object()
        self.assertEqual(translate_query_to_english("economy news", client), "economy news")

    def test_query_translation_translates_non_english_script(self):
        client = Mock()
        client.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content="economy"))
        ]

        self.assertEqual(translate_query_to_english("अर्थव्यवस्था", client), "economy")
        client.chat.completions.create.assert_called_once()

    def test_ai_search_fallback_returns_article(self):
        client = Mock()
        client.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content="An answer from OpenAI."))
        ]

        result = get_ai_search_result("technology", client)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "OpenAI")
        self.assertEqual(result[0]["content"], "An answer from OpenAI.")

    def test_ai_search_fallback_handles_empty_response(self):
        client = Mock()
        client.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content=""))
        ]

        self.assertEqual(get_ai_search_result("technology", client), [])


if __name__ == "__main__":
    unittest.main()
