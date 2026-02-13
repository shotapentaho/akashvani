# utils/translator.py
"""
akashvani - Translation Utilities
Using OpenAI for text translation and summarization
Version: 1.4 | 2026-02-13
"""

import streamlit as st
from config.languages import LANGUAGE_NAMES

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
            max_tokens=1500,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ Translation Error: {e}")
        return text

def get_ai_summary(text: str, language_code: str, client, duration_mode: str = "standard") -> str:
    """
    Create senior-friendly summary using OpenAI
    
    Args:
        text: Text to summarize
        language_code: Target language code
        client: OpenAI client instance
        duration_mode: "short" (1 min), "standard" (2 min), or "long" (3 min)
    
    Returns:
        Summarized text (150-450 words for 1-3 minutes of speech)
    """
    lang_name = LANGUAGE_NAMES.get(language_code, "English")
    
    # Word count targets
    word_count_map = {
        "short": 150,      # ~1 minute
        "standard": 300,   # ~2 minutes
        "long": 450        # ~3 minutes
    }
    
    max_tokens_map = {
        "short": 400,
        "standard": 800,
        "long": 1200
    }
    
    target_words = word_count_map.get(duration_mode, 300)
    max_tokens = max_tokens_map.get(duration_mode, 800)
    
    try:
        system_prompt = f"""You are a senior-friendly news summarizer for Indian seniors (age 60+).

Your task: Summarize the following news article in {lang_name}.

REQUIREMENTS:
1. Use SHORT, SIMPLE sentences (max 10-15 words per sentence)
2. AVOID technical terms and jargon
3. Make it EASY to understand
4. Target length: EXACTLY about {target_words} words
5. Include:
   - What happened (main event)
   - Who is involved
   - Why it matters
   - What happens next (if known)
6. Use simple vocabulary suitable for seniors
7. Make it engaging and interesting
8. DO NOT use bullet points or numbers, write in paragraph form
9. Use natural, conversational tone

Return ONLY the summary text, nothing else."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Article to summarize:\n\n{text}"
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        st.error(f"❌ Summary Error: {e}")
        return text
