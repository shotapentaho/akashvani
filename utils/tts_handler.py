# utils/tts_handler.py
"""
akashvani - Text-to-Speech Utilities
Using gTTS for audio generation in supported Indian languages
Version: 1.4 | 2026-02-13
"""

from gtts import gTTS
from gtts.lang import tts_langs
from io import BytesIO
import streamlit as st
import asyncio
from typing import Optional

try:
    import edge_tts
except ImportError:
    edge_tts = None

# Get list of gTTS supported languages
SUPPORTED_TTS_LANGS = tts_langs()

VOICE_OPTIONS = [
    "Female (Current)",
    "Male (Indian)",
    "Indian Accent",
]

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
}


def is_language_supported(language_code: str) -> bool:
    """
    Check if a language is supported by gTTS
    
    Args:
        language_code: Language code (e.g., 'hi', 'ta', 'or')
    
    Returns:
        True if supported, False otherwise
    """
    return language_code.lower() in SUPPORTED_TTS_LANGS

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


def text_to_speech(
    text: str,
    language_code: str = "en",
    slow: bool = False,
    voice: str = "Female (Current)",
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
        
        # Check if language is supported
        if not is_language_supported(language_code):
            st.warning(f"🔇 Text-to-Speech is not available for this language (Code: {language_code.upper()})")
            st.info("📝 You can still read the text summary above. Consider translating to a supported language like English or Hindi.")
            return None
        
        # Calculate estimated duration
        estimated_duration = calculate_speech_duration(text, slow)
        word_count = len(text.split())
        
        # Show duration estimate
        minutes = int(estimated_duration // 60)
        seconds = int(estimated_duration % 60)
        st.info(f"🎵 Generating audio... ({word_count} words ≈ {minutes}m {seconds}s at {'Slow' if slow else 'Normal'} speed)")
        
        # Generate male Indian voices with Edge TTS when selected.
        if voice == "Male (Indian)":
            male_voice = INDIAN_MALE_VOICES.get(language_code.lower())
            if edge_tts is not None and male_voice:
                mp3_fp = _edge_tts_audio(text, male_voice, slow)
            else:
                st.info(
                    "ℹ️ A male Indian voice is not available for this "
                    "language here, so the current voice is being used."
                )
                tts = gTTS(text, lang=language_code, slow=slow)
                mp3_fp = BytesIO()
                tts.write_to_fp(mp3_fp)
        else:
            # Google's co.in endpoint provides an Indian English accent.
            tld = "co.in" if voice == "Indian Accent" else "com"
            tts = gTTS(text, lang=language_code, slow=slow, tld=tld)
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)

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
