import base64
from io import BytesIO
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.tts_handler import (
    INDIAN_FEMALE_VOICES,
    INDIAN_MALE_VOICES,
    _extract_gemini_audio,
    _get_gemini_api_key,
    text_to_speech,
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

    def test_finds_audio_in_nested_response_data(self):
        audio_data = b"nested-audio"
        response = {
            "result": {
                "parts": [{
                    "inline_data": {
                        "data": base64.b64encode(audio_data).decode(),
                        "mime_type": "audio/L16",
                    }
                }]
            }
        }

        self.assertEqual(
            _extract_gemini_audio(response),
            (audio_data, "audio/l16"),
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


class EdgeTtsRoutingTests(unittest.TestCase):
    def test_odia_uses_edge_tts_without_gemini_warning_or_fallback(self):
        audio = BytesIO(b"audio")
        with patch("utils.tts_handler.edge_tts", object()), \
             patch("utils.tts_handler._edge_tts_audio", return_value=audio) as edge_audio, \
             patch("utils.tts_handler._try_gemini_fallback") as gemini_fallback, \
             patch("utils.tts_handler.st.info"), \
             patch("utils.tts_handler.st.success"), \
             patch("utils.tts_handler.st.warning") as warning:
            result = text_to_speech("ନମସ୍କାର", language_code="or", voice="Female")

        self.assertIs(result, audio)
        edge_audio.assert_called_once_with(
            "ନମସ୍କାର",
            INDIAN_FEMALE_VOICES["or"],
            False,
        )
        gemini_fallback.assert_not_called()
        warning.assert_not_called()

    def test_odia_voice_maps_use_microsoft_indian_voices(self):
        self.assertEqual(INDIAN_FEMALE_VOICES["or"], "or-IN-SubhasiniNeural")
        self.assertEqual(INDIAN_MALE_VOICES["or"], "or-IN-SukantNeural")
