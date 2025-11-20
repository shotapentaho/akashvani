# utils/translator.py
"""
akashvani - Translation Utilities
Using OpenAI for text translation and summarization
Fixed for OpenAI v1.0+ API (client-based)
Fixed for 2-minute speech duration - longer summaries
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
        duration_mode: "short" (1 min), "standard" (1.5-2 min), or "long" (2-3 min)
    
    Returns:
        Summarized text (250-400+ words for 2-3 minutes of speech)
    """
    lang_name = LANGUAGE_NAMES.get(language_code, "English")
    
    # Set word count and max_tokens based on duration mode
    # Average speech rate: 120-150 words/min at slow pace
    # 1 token ≈ 0.75 words, so multiply by 1.33 to get tokens needed
    word_count_map = {
        "short": 150,      # ~1 minute @ 150 wpm
        "standard": 300,   # ~2 minutes @ 150 wpm
        "long": 450        # ~3 minutes @ 150 wpm
    }
    
    max_tokens_map = {
        "short": 400,      # 400 tokens ≈ 300 words
        "standard": 800,   # 800 tokens ≈ 600 words
        "long": 1200       # 1200 tokens ≈ 900 words
    }
    
    target_words = word_count_map.get(duration_mode, 300)
    max_tokens = max_tokens_map.get(duration_mode, 800)
    
    try:
        # More detailed prompt to ensure longer, comprehensive summaries
        system_prompt = f"""You are a senior-friendly news summarizer for Indian seniors (age 60+).

Your task: Summarize the following news article in {lang_name}.

IMPORTANT REQUIREMENTS:
1. Use SHORT, SIMPLE sentences (max 10-15 words per sentence)
2. AVOID technical terms and jargon
3. Make it EASY to understand
4. Target length: EXACTLY about {target_words} words (IMPORTANT: don't be brief, be thorough)
5. Include:
   - What happened (main event)
   - Who is involved
   - Why it matters
   - What happens next (if known)
6. Use simple vocabulary suitable for seniors
7. Make it engaging and interesting
8. DO NOT use bullet points or numbers, write in paragraph form
9. Use natural, conversational tone
10. IMPORTANT: Write LONGER summaries - aim for {target_words} words minimum

Return ONLY the summary text, nothing else. No meta-commentary, no explanations."""

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
        
        # Debug: Show word count in console (visible in Streamlit logs)
        word_count = len(summary.split())
        st.write(f"📊 Summary stats: {word_count} words (~{int(word_count/150)} min speech)")
        
        return summary
        
    except Exception as e:
        st.error(f"❌ Summary Error: {e}")
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
            max_tokens=100,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return text[:100]