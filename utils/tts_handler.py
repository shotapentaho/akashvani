# utils/tts_handler.py
"""
akashvani - Text-to-Speech Utilities
Using gTTS/Edge TTS with Gemini audio fallback for Indian languages
Version: 1.4 | 2026-02-13
"""

from gtts import gTTS
from gtts.lang import tts_langs
from io import BytesIO
import streamlit as st
import asyncio
import base64
import binascii
import os
import re
import wave
import requests
from collections.abc import Mapping
from typing import Optional

try:
    import edge_tts
except ImportError:
    edge_tts = None

# Get list of gTTS supported languages
SUPPORTED_TTS_LANGS = tts_langs()

VOICE_OPTIONS = [
    "Female",
    "Male",
]

INDIAN_FEMALE_VOICES = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "bn": "bn-IN-TanishaaNeural",
    "gu": "gu-IN-DhwaniNeural",
    "kn": "kn-IN-SapnaNeural",
    "ml": "ml-IN-SobhanaNeural",
    "mr": "mr-IN-AarohiNeural",
    "pa": "pa-IN-VaaniNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural",
    "ur": "ur-IN-GulNeural",
    "or": "or-IN-SubhasiniNeural",
}

INDIAN_MALE_VOICES = {
    "en": "en-IN-PrabhatNeural",
    "hi": "hi-IN-MadhurNeural",
    "bn": "bn-IN-BashkarNeural",
    "gu": "gu-IN-NiranjanNeural",
    "kn": "kn-IN-GaganNeural",
    "ml": "ml-IN-MidhunNeural",
    "mr": "mr-IN-ManoharNeural",
    "pa": "pa-IN-OjasNeural",
    "ta": "ta-IN-ValluvarNeural",
    "te": "te-IN-MohanNeural",
    "ur": "ur-IN-SalmanNeural",
    "or": "or-IN-SukantNeural",
}

# Gemini's public native-audio preview model supports multilingual speech,
# including Odia, while gTTS does not.
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_TTS_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)
GEMINI_VOICES = {
    "Female": "Kore",
    "Male": "Puck",
}
GEMINI_TTS_CHUNK_SIZE = 1800


def is_language_supported(language_code: str) -> bool:
    """
    Check if a language is supported by gTTS
    
    Args:
        language_code: Language code (e.g., 'hi', 'ta', 'or')
    
    Returns:
        True if supported, False otherwise
    """
    return language_code.lower() in SUPPORTED_TTS_LANGS


def is_tts_available(language_code: str, voice: str = "Female") -> bool:
    """Return whether the selected voice has a configured TTS provider."""
    language_code = language_code.lower()
    indian_voices = (
        INDIAN_MALE_VOICES if voice == "Male" else INDIAN_FEMALE_VOICES
    )
    return language_code in indian_voices or is_language_supported(language_code)


def get_supported_languages_list() -> dict:
    """
    Get dictionary of supported TTS languages
    
    Returns:
        Dictionary of supported language codes
    """
    return SUPPORTED_TTS_LANGS

def calculate_speech_duration(text: str, slow: bool = False) -> float:
    """
    Calculate approximate speech duration in seconds
    
    Args:
        text: Text to speak
        slow: If True, slower speech (~120 wpm), else normal (~150 wpm)
    
    Returns:
        Duration in seconds (approximate)
    """
    word_count = len(text.split())
    words_per_minute = 120 if slow else 150
    minutes = word_count / words_per_minute
    seconds = minutes * 60
    return seconds

def _edge_tts_audio(text: str, voice: str, slow: bool) -> BytesIO:
    """Generate MP3 audio with a Microsoft Indian male voice."""
    rate = "-20%" if slow else "+0%"

    async def generate_audio() -> bytes:
        communicator = edge_tts.Communicate(text, voice, rate=rate)
        chunks = []
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    audio_bytes = asyncio.run(generate_audio())
    return BytesIO(audio_bytes)


def _get_gemini_api_key() -> Optional[str]:
    """Read the optional Gemini API key from Streamlit secrets or the environment."""
    try:
        secret_config = st.secrets.get("gemini", {})
        if isinstance(secret_config, Mapping):
            api_key = secret_config.get("api_key")
            if api_key:
                return str(api_key).strip() or None
        for secret_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            api_key = st.secrets.get(secret_name)
            if api_key:
                return str(api_key).strip() or None
    except Exception:
        pass
    for environment_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        api_key = os.getenv(environment_name)
        if api_key:
            return api_key.strip() or None
    return None


def _pcm_to_wav_audio(audio_bytes: bytes, sample_rate: int = 24000) -> BytesIO:
    """Wrap Gemini's raw 16-bit PCM response in a browser-playable WAV container."""
    audio = BytesIO()
    with wave.open(audio, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)
    audio.seek(0)
    return audio


def _split_gemini_text(text: str, max_chars: int = GEMINI_TTS_CHUNK_SIZE) -> list[str]:
    """Split narration into API-sized chunks without cutting words."""
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?।॥])\s+", text.strip())
    chunks = []
    current = []
    current_length = 0

    for sentence in sentences:
        if not sentence:
            continue
        if len(sentence) > max_chars:
            words = sentence.split()
            for word in words:
                separator_length = 1 if current else 0
                if current and current_length + separator_length + len(word) > max_chars:
                    chunks.append(" ".join(current))
                    current = []
                    current_length = 0
                current.append(word)
                current_length += separator_length + len(word)
            continue

        separator_length = 1 if current else 0
        if current and current_length + separator_length + len(sentence) > max_chars:
            chunks.append(" ".join(current))
            current = []
            current_length = 0
        current.append(sentence)
        current_length += separator_length + len(sentence)

    if current:
        chunks.append(" ".join(current))
    return chunks or [text]


def _gemini_no_audio_error(response_data: Mapping) -> RuntimeError:
    """Describe why a Gemini response did not contain usable audio."""
    candidates = response_data.get("candidates", [])
    finish_reasons = [
        candidate.get("finishReason")
        for candidate in candidates
        if isinstance(candidate, Mapping) and candidate.get("finishReason")
    ]
    prompt_feedback = response_data.get("promptFeedback")
    details = []
    if finish_reasons:
        details.append(f"finishReason={','.join(map(str, finish_reasons))}")
    if isinstance(prompt_feedback, Mapping):
        block_reason = prompt_feedback.get("blockReason")
        if block_reason:
            details.append(f"blockReason={block_reason}")
    details.append(f"responseKeys={','.join(sorted(map(str, response_data.keys())))}")
    return RuntimeError(f"Gemini returned no audio data ({'; '.join(details)})")


def _iter_gemini_inline_data(value: object):
    """Yield inline data objects from nested Gemini response values."""
    if isinstance(value, Mapping):
        for key in ("inlineData", "inline_data"):
            inline_data = value.get(key)
            if isinstance(inline_data, Mapping):
                yield inline_data
        for child in value.values():
            yield from _iter_gemini_inline_data(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_gemini_inline_data(child)


def _extract_gemini_audio(response_data: Mapping) -> tuple[bytes, str]:
    """Find and decode the audio inline part in a Gemini response."""
    for inline_data in _iter_gemini_inline_data(response_data):
        encoded_data = inline_data.get("data")
        if not isinstance(encoded_data, str) or not encoded_data:
            continue
        try:
            audio_bytes = base64.b64decode(encoded_data, validate=True)
        except (binascii.Error, ValueError, TypeError) as error:
            raise RuntimeError("Gemini returned invalid audio data") from error
        if audio_bytes:
            return audio_bytes, str(
                inline_data.get("mimeType")
                or inline_data.get("mime_type")
                or ""
            ).lower()

    raise _gemini_no_audio_error(response_data)


def _gemini_tts_audio(
    text: str,
    voice: str,
    slow: bool,
    api_key: str,
    model: str = GEMINI_TTS_MODEL,
) -> BytesIO:
    """Generate speech with Gemini's native audio output."""
    pcm_chunks = []

    for text_chunk in _split_gemini_text(text):
        prompt = f"Read the following text exactly in its original language:\n{text_chunk}"
        if slow:
            prompt = (
                "Speak clearly at a deliberately slow, senior-friendly pace. "
                f"Read the following text exactly in its original language:\n{text_chunk}"
            )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": GEMINI_VOICES.get(voice, GEMINI_VOICES["Female"])
                        }
                    }
                },
            },
        }
        response = requests.post(
            GEMINI_TTS_ENDPOINT.format(model=model),
            params={"key": api_key},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        response_data = response.json()
        audio_bytes, mime_type = _extract_gemini_audio(response_data)

        if not audio_bytes:
            raise RuntimeError("Gemini returned empty audio data")
        if "wav" in mime_type:
            with wave.open(BytesIO(audio_bytes), "rb") as wav_file:
                pcm_chunks.append(wav_file.readframes(wav_file.getnframes()))
        elif "l16" in mime_type or "pcm" in mime_type or not mime_type:
            pcm_chunks.append(audio_bytes)
        elif "mpeg" in mime_type or "mp3" in mime_type:
            if len(_split_gemini_text(text)) > 1:
                raise RuntimeError(
                    "Gemini returned MP3 audio for a multi-part narration"
                )
            audio = BytesIO(audio_bytes)
            audio.seek(0)
            return audio
        else:
            pcm_chunks.append(audio_bytes)

    if not pcm_chunks:
        raise RuntimeError("Gemini returned empty audio data")
    return _pcm_to_wav_audio(b"".join(pcm_chunks))


def _try_gemini_fallback(
    text: str,
    voice: str,
    slow: bool,
) -> Optional[BytesIO]:
    """Try Gemini only when an optional API key is configured."""
    api_key = _get_gemini_api_key()
    if not api_key:
        return None
    model = os.getenv("GEMINI_TTS_MODEL", GEMINI_TTS_MODEL)
    return _gemini_tts_audio(text, voice, slow, api_key, model)


def text_to_speech(
    text: str,
    language_code: str = "en",
    slow: bool = False,
    voice: str = "Default",
) -> Optional[BytesIO]:
    """
    Convert text to speech using Google Text-to-Speech
    
    Args:
        text: Text to convert
        language_code: Language code (e.g., 'hi', 'ta', 'or')
        slow: If True, speak slowly (good for seniors)
        voice: Voice style to use
    
    Returns:
        BytesIO object containing MP3 audio or None on error
    """
    try:
        if not text or len(text.strip()) == 0:
            st.error("❌ No text to convert to speech")
            return None
        
        # Calculate estimated duration
        estimated_duration = calculate_speech_duration(text, slow)
        word_count = len(text.split())
        
        # Show duration estimate
        minutes = int(estimated_duration // 60)
        seconds = int(estimated_duration % 60)
        st.info(f"🎵 Generating audio... ({word_count} words ≈ {minutes}m {seconds}s at {'Slow' if slow else 'Normal'} speed)")
        
        mp3_fp = None
        provider_error = None

        # Generate Indian voices with Edge TTS when available.
        indian_voices = (
            INDIAN_MALE_VOICES if voice == "Male" else INDIAN_FEMALE_VOICES
        )
        indian_voice = indian_voices.get(language_code.lower())
        if indian_voice:
            try:
                if edge_tts is not None:
                    mp3_fp = _edge_tts_audio(text, indian_voice, slow)
                else:
                    raise RuntimeError("Microsoft Edge TTS is not installed")
            except Exception as error:
                provider_error = error
        elif is_language_supported(language_code):
            try:
                tts = gTTS(text, lang=language_code, slow=slow, tld="co.in")
                mp3_fp = BytesIO()
                tts.write_to_fp(mp3_fp)
            except Exception as error:
                provider_error = error

        if mp3_fp is None:
            try:
                mp3_fp = _try_gemini_fallback(text, voice, slow)
                if mp3_fp is not None:
                    st.info("ℹ️ Audio generated with Gemini fallback.")
            except Exception as error:
                provider_error = error

        if mp3_fp is None:
            if provider_error is not None:
                raise RuntimeError(
                    f"Primary TTS and Gemini fallback failed: {provider_error}"
                ) from provider_error
            st.info(
                "ℹ️ Gemini fallback is not configured. Add a Gemini API key "
                "to enable speech for languages unavailable to the primary provider."
            )
            return None

        mp3_fp.seek(0)
        
        # Show success message
        st.success(f"✅ Audio ready! Duration: ~{minutes}m {seconds}s")
        
        return mp3_fp
    
    except ValueError as e:
        st.error(f"❌ Invalid language code: {language_code}")
        return None
    except Exception as e:
        st.error(f"❌ Text-to-Speech Error: {e}")
        return None

def get_speech_speed_display(is_slow: bool) -> str:
    """Get display string for speech speed"""
    return "🐢 Slow (Senior-Friendly)" if is_slow else "⚡ Normal"

def get_audio_file_name(article_title: str, lang_code: str) -> str:
    """
    Generate audio filename
    
    Args:
        article_title: Article title
        lang_code: Language code
    
    Returns:
        Formatted filename
    """
    clean_title = "".join(c for c in article_title if c.isalnum() or c.isspace())[:30]
    return f"{clean_title.replace(' ', '_')}_{lang_code}.mp3"
