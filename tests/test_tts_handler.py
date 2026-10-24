import base64
import os
import sys
import unittest
import wave
from io import BytesIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.tts_handler import (
    INDIAN_FEMALE_VOICES,
    INDIAN_MALE_VOICES,
    _extract_gemini_audio,
    _gemini_tts_audio,
    _get_gemini_api_key,
    _split_gemini_text,
    is_tts_available,
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
    def test_combines_audio_for_long_text(self):
        response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "data": base64.b64encode(b"pcm-part").decode(),
                            "mimeType": "audio/L16",
                        }
                    }]
                }
            }]
        }
        long_text = "sentence " * 400

        with patch("utils.tts_handler.requests.post") as post:
            post.return_value.json.return_value = response
            audio = _gemini_tts_audio(long_text, "Female", False, "key")

        self.assertGreater(post.call_count, 1)
        with wave.open(audio, "rb") as wav_file:
            self.assertEqual(
                wav_file.readframes(wav_file.getnframes()),
                b"pcm-part" * post.call_count,
            )

    def test_retries_when_gemini_returns_no_audio(self):
        audio_data = b"pcm-audio!"
        no_audio_response = {
            "candidates": [{"finishReason": "OTHER"}],
            "modelVersion": "gemini-2.5-flash-preview-tts",
        }
        audio_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "data": base64.b64encode(audio_data).decode(),
                            "mimeType": "audio/L16",
                        }
                    }]
                }
            }]
        }

        with patch("utils.tts_handler.time.sleep"), patch(
            "utils.tts_handler.requests.post"
        ) as post:
            post.return_value.json.side_effect = [
                no_audio_response,
                audio_response,
            ]
            audio = _gemini_tts_audio("ନମସ୍କାର", "Female", False, "key")

        self.assertEqual(post.call_count, 2)
        with wave.open(audio, "rb") as wav_file:
            self.assertEqual(wav_file.readframes(wav_file.getnframes()), audio_data)

    def test_splits_long_text_at_sentence_boundaries(self):
        text = "First sentence. " + ("word " * 500) + "Final sentence."

        chunks = _split_gemini_text(text, max_chars=100)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 100 for chunk in chunks))
        self.assertEqual(" ".join(chunks), " ".join(text.split()))

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
    def test_odia_is_available_for_both_voice_choices(self):
        self.assertTrue(is_tts_available("or", "Female"))
        self.assertTrue(is_tts_available("or", "Male"))

    def test_odia_uses_microsoft_edge_female_voice(self):
        self.assertEqual(INDIAN_FEMALE_VOICES["or"], "or-IN-SubhasiniNeural")
        with patch("utils.tts_handler.edge_tts", object()), patch(
            "utils.tts_handler._edge_tts_audio",
            return_value=BytesIO(b"odia-female"),
        ) as edge_audio, patch(
            "utils.tts_handler._try_gemini_fallback"
        ) as gemini_fallback:
            audio = text_to_speech("ନମସ୍କାର", "or", voice="Female")

        edge_audio.assert_called_once_with(
            "ନମସ୍କାର", "or-IN-SubhasiniNeural", False
        )
        gemini_fallback.assert_not_called()
        self.assertEqual(audio.read(), b"odia-female")

    def test_odia_uses_microsoft_edge_male_voice(self):
        self.assertEqual(INDIAN_MALE_VOICES["or"], "or-IN-SukantNeural")
        with patch("utils.tts_handler.edge_tts", object()), patch(
            "utils.tts_handler._edge_tts_audio",
            return_value=BytesIO(b"odia-male"),
        ) as edge_audio, patch(
            "utils.tts_handler._try_gemini_fallback"
        ) as gemini_fallback:
            audio = text_to_speech("ନମସ୍କାର", "or", voice="Male")

        edge_audio.assert_called_once_with(
            "ନମସ୍କାର", "or-IN-SukantNeural", False
        )
        gemini_fallback.assert_not_called()
        self.assertEqual(audio.read(), b"odia-male")
