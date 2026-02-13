# config/__init__.py
"""akashvani - Configuration Package"""

from .languages import (
    INDIAN_LANGUAGES,
    LANGUAGE_NAMES,
    LANGUAGE_INFO,
    get_language_code,
    get_language_name,
    get_all_languages,
    get_language_info,
)

__all__ = [
    'INDIAN_LANGUAGES',
    'LANGUAGE_NAMES',
    'LANGUAGE_INFO',
    'get_language_code',
    'get_language_name',
    'get_all_languages',
    'get_language_info',
]
