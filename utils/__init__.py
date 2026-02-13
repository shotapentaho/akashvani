"""
Utils package for akashvani
Optimized imports with GPT-3.5-turbo and caching
PostgreSQL insert-only tracking
"""

from .translator import translate_to_language, get_ai_summary
from .news_fetcher import get_top_news, format_article, get_article_content, _is_cricket_score_query
from .tts_handler import text_to_speech, get_speech_speed_display, is_language_supported
from .cricket_scraper import extract_score_from_article

# Database tracking (optional)
try:
    from .database import (
        track_api_call,
        track_search_query,
        track_user_session
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

__all__ = [
    # Translator
    'translate_to_language',
    'get_ai_summary',

    # News fetcher
    'get_top_news',
    'format_article',
    'get_article_content',
    '_is_cricket_score_query',

    # TTS handler
    'text_to_speech',
    'get_speech_speed_display',
    'is_language_supported',

    # Cricket scraper
    'extract_score_from_article',

    # Database tracking (if available)
    'DATABASE_AVAILABLE',
]

if DATABASE_AVAILABLE:
    __all__.extend([
        'track_api_call',
        'track_search_query',
        'track_user_session',
    ])
