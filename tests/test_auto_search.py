import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auto_search import is_auto_eligible, query_fingerprint, should_auto_run


class AutoSearchTests(unittest.TestCase):
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

    def test_should_auto_run(self):
        fp = query_fingerprint("health", "en")
        self.assertTrue(should_auto_run("health", fp, None))
        self.assertFalse(should_auto_run("health", fp, fp))
        self.assertFalse(should_auto_run("weather in", query_fingerprint("weather in"), None))


if __name__ == "__main__":
    unittest.main()
