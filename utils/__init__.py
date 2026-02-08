"""
Utils package for akashvani
Optimized imports with GPT-3.5-turbo-0125 and caching
"""

from .translator import cached_translate, cached_summary
from .news_fetcher import get_top_news, format_article, get_article_content
from .tts_handler import text_to_speech, get_speech_speed_display, is_language_supported
from .cricket_scraper import extract_score_from_article

__all__ = [
    # Translator (optimized with caching)
    'cached_translate',
    'cached_summary',
    
    # News fetcher
    'get_top_news',
    'format_article',
    'get_article_content',
    
    # TTS handler
    'text_to_speech',
    'get_speech_speed_display',
    'is_language_supported',
    
    # Cricket scraper
    'extract_score_from_article',
]