import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.languages import (
    INDIAN_LANGUAGES,
    LANGUAGE_INFO,
    LANGUAGE_NAMES,
    TTS_SUPPORTED_LANGUAGES,
)


class SanskritLanguageTests(unittest.TestCase):
    def test_sanskrit_is_available_in_language_configuration(self):
        self.assertEqual(INDIAN_LANGUAGES["Sanskrit"], "sa")
        self.assertEqual(LANGUAGE_NAMES["sa"], "Sanskrit")
        self.assertEqual(LANGUAGE_INFO["sa"]["native"], "संस्कृत")
        self.assertIn("sa", TTS_SUPPORTED_LANGUAGES)
