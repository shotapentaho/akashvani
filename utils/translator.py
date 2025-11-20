# utils/translator.py
"""
akashvani - Translation Utilities
Using OpenAI for text translation and summarization
Fixed for OpenAI v1.0+ API (client-based)
"""

import streamlit as st
from config.languages import LANGUAGE_NAMES
from typing import Optional

def translate_to_language(text: str, target_lang_code: str, client) -> str:
    """
    Translate text to target Indian language using OpenAI
    
    Args:
        text: Text to translate
        target_lang_code: Target language code (e.g., 'hi', 'ta', 'or')
        client: OpenAI client instance
    
    Returns:
        Translated text
    """
    if target_lang_code == "en":
        return text

    lang_name = LANGUAGE_NAMES.get(target_lang_code, "English")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate the following news content to {lang_name}. Keep it simple and clear for senior citizens. Return only the translated text."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=500,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌  Translation Error: {e}")
        return text

def get_ai_summary(text: str, language_code: str, client) -> str:
    """
    Create senior-friendly summary using OpenAI
    
    Args:
        text: Text to summarize
        language_code: Target language code
        client: OpenAI client instance
    
    Returns:
        Summarized text
    """
    lang_name = LANGUAGE_NAMES.get(language_code, "English")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"Summarize this news in {lang_name} for senior citizens (age 60+). Use short, simple sentences. Avoid technical terms. Make it easy to understand. Keep it under 150 words."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌  Summary Error: {e}")
        return text

def get_news_headline_highlight(text: str, client) -> str:
    """
    Create a highlighted key point from the news
    
    Args:
        text: News text
        client: OpenAI client instance
    
    Returns:
        Key highlight
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Extract the most important 1-2 sentences from this news article. Make it impactful and easy to understand."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=50,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return text[:100]
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                             