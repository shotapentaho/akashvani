import base64
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.tts_handler import (
    _extract_gemini_audio,
    _get_gemini_api_key,
)


class GeminiApiKeyTests(unittest.TestCase):
    def test_reads_nested_streamlit_secret(self):
        with patch("utils.tts_handler.st.secrets", {"gemini": {"api_key": "  nested-key  "}}):
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(_get_gemini_api_key(), "nested-key")

    def test_reads_top_level_gemini_environment_variable(self):
        with patch("utils.tts_handler.st.secrets", {}):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "  environment-key  "}, clear=True):
                self.assertEqual(_get_gemini_api_key(), "environment-key")

    def test_returns_none_when_no_key_is_configured(self):
        with patch("utils.tts_handler.st.secrets", {}):
            with patch.dict(os.environ, {}, clear=True):
                self.assertIsNone(_get_gemini_api_key())


class GeminiAudioResponseTests(unittest.TestCase):
    def test_finds_audio_after_non_audio_parts(self):
        audio_data = b"pcm-audio"
        response = {
            "candidates": [{
                "content": {
                    "parts": [
                        {"text": "ignored"},
                        {
                            "inlineData": {
                                "data": base64.b64encode(audio_data).decode(),
                                "mimeType": "audio/L16",
                            }
                        },
                    ]
                }
            }]
        }

        self.assertEqual(
            _extract_gemini_audio(response),
            (audio_data, "audio/l16"),
        )

    def test_accepts_snake_case_inline_data(self):
        audio_data = b"wav-audio"
        response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inline_data": {
                            "data": base64.b64encode(audio_data).decode(),
                            "mime_type": "audio/wav",
                        }
                    }]
                }
            }]
        }

        self.assertEqual(
            _extract_gemini_audio(response),
            (audio_data, "audio/wav"),
        )

    def test_includes_blocking_details_when_audio_is_missing(self):
        response = {
            "candidates": [{"finishReason": "SAFETY"}],
            "promptFeedback": {"blockReason": "SAFETY"},
        }

        with self.assertRaisesRegex(
            RuntimeError,
            r"finishReason=SAFETY.*blockReason=SAFETY.*responseKeys=candidates,promptFeedback",
        ):
            _extract_gemini_audio(response)
