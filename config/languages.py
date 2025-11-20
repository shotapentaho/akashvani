# config/languages.py
"""
akashvani - Language Configuration
Supports 12 Indian languages with gTTS codes
Note: Some languages may not have TTS support
Project: akashvani | Version 1.0 | 2025-11-19
"""

INDIAN_LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Bengali": "bn",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Urdu": "ur",
    "Odia": "or",
}

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ur": "Urdu",
    "or": "Odia",
}

# Languages supported by gTTS (Google Text-to-Speech)
# As of 2025, gTTS supports these Indian languages
TTS_SUPPORTED_LANGUAGES = {
    "en",  # English
    "hi",  # Hindi
    "ta",  # Tamil
    "te",  # Telugu
    "kn",  # Kannada
    "ml",  # Malayalam
    "bn",  # Bengali
    "mr",  # Marathi
    "gu",  # Gujarati
    "pa",  # Punjabi
    "ur",  # Urdu
    # Note: "or" (Odia) is NOT currently supported by gTTS
}

LANGUAGE_INFO = {
    "en": {
        "name": "English",
        "flag": "🇮🇳",
        "native": "English",
        "speakers": "100+ Million",
        "region": "Pan-India",
        "tts_supported": True,
    },
    "hi": {
        "name": "Hindi",
        "flag": "🇮🇳",
        "native": "हिन्दी",
        "speakers": "345 Million",
        "region": "North India",
        "tts_supported": True,
    },
    "ta": {
        "name": "Tamil",
        "flag": "🇮🇳",
        "native": "தமிழ்",
        "speakers": "75 Million",
        "region": "South India",
        "tts_supported": True,
    },
    "te": {
        "name": "Telugu",
        "flag": "🇮🇳",
        "native": "తెలుగు",
        "speakers": "74 Million",
        "region": "South India",
        "tts_supported": True,
    },
    "kn": {
        "name": "Kannada",
        "flag": "🇮🇳",
        "native": "ಕನ್ನಡ",
        "speakers": "44 Million",
        "region": "South India",
        "tts_supported": True,
    },
    "ml": {
        "name": "Malayalam",
        "flag": "🇮🇳",
        "native": "മലയാളം",
        "speakers": "34 Million",
        "region": "South India",
        "tts_supported": True,
    },
    "bn": {
        "name": "Bengali",
        "flag": "🇮🇳",
        "native": "বাংলা",
        "speakers": "230 Million",
        "region": "East India",
        "tts_supported": True,
    },
    "mr": {
        "name": "Marathi",
        "flag": "🇮🇳",
        "native": "मराठी",
        "speakers": "83 Million",
        "region": "West India",
        "tts_supported": True,
    },
    "gu": {
        "name": "Gujarati",
        "flag": "🇮🇳",
        "native": "ગુજરાતી",
        "speakers": "54 Million",
        "region": "West India",
        "tts_supported": True,
    },
    "pa": {
        "name": "Punjabi",
        "flag": "🇮🇳",
        "native": "ਪੰਜਾਬੀ",
        "speakers": "125 Million",
        "region": "North India",
        "tts_supported": True,
    },
    "ur": {
        "name": "Urdu",
        "flag": "🇮🇳",
        "native": "اردو",
        "speakers": "70 Million",
        "region": "North India",
        "tts_supported": True,
    },
    "or": {
        "name": "Odia",
        "flag": "🇮🇳",
        "native": "ଓଡ଼ିଆ",
        "speakers": "42 Million",
        "region": "East India",
        "tts_supported": False,  # NOT supported by gTTS
    },
}

def get_language_code(language_name: str) -> str:
    """Get gTTS language code from language name"""
    return INDIAN_LANGUAGES.get(language_name, "en")

def get_language_name(code: str) -> str:
    """Get language name from code"""
    return LANGUAGE_NAMES.get(code, "English")

def get_all_languages() -> list:
    """Get list of all supported languages"""
    return list(INDIAN_LANGUAGES.keys())

def get_language_info(code: str) -> dict:
    """Get detailed language information"""
    return LANGUAGE_INFO.get(code, {})

def is_tts_supported(code: str) -> bool:
    """Check if language supports text-to-speech"""
    return code in TTS_SUPPORTED_LANGUAGES