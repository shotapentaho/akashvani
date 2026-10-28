# utils/translator.py
"""
akashvani - Translation Utilities
Using OpenAI for text translation and summarization
Version: 1.4 | 2026-02-13
"""

import streamlit as st
from config.languages import LANGUAGE_NAMES


def is_non_english_script(text: str) -> bool:
    """Return True when text contains alphabetic characters outside ASCII."""
    return any(character.isalpha() and not character.isascii() for character in text or "")


def translate_query_to_english(text: str, client) -> str:
    """Translate a non-English search query to English for news APIs."""
    if not text or not is_non_english_script(text):
        return text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate the search query to English. "
                        "Return only the translated query."
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=100,
            temperature=0,
        )
        return response.choices[0].message.content.strip() or text
    except Exception as e:
        print(f"Search query translation error: {e}")
        return text


def get_ai_search_result(query: str, client):
    """Return an OpenAI-backed result when the news providers have no results."""
    if not query or client is None:
        return []

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer the user's search query clearly and concisely. "
                        "Use your available knowledge, state when information "
                        "may be outdated, and do not invent sources or facts."
                    ),
                },
                {"role": "user", "content": query},
            ],
            max_tokens=1000,
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        if not content:
            return []

        return [{
            "title": f"AI result: {query}",
            "description": content,
            "content": content,
            "source": "OpenAI",
            "author": "OpenAI",
            "url": "#",
        }]
    except Exception as e:
        print(f"OpenAI search fallback error: {e}")
        return []


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
            model="gpt-4o-mini",
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


def create_movie_review_script(
    movie_title: str,
    reviews: list,
    language_code: str,
    client,
) -> str:
    """Create a short spoken script based only on the supplied IMDb excerpts."""
    lang_name = LANGUAGE_NAMES.get(language_code, "English")
    review_text = "\n\n".join(
        f"- {review['text']}" for review in reviews if review.get("text")
    )
    if not review_text:
        raise ValueError("At least one review excerpt is required")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Create a clear, conversational spoken script in {lang_name} "
                    "that summarizes the opinions in the provided movie-review "
                    "excerpts. Use simple language for senior listeners. "
                    "Mention that opinions may differ. Do not invent plot details, "
                    "facts, or consensus, and do not reproduce the reviews "
                    "verbatim. Return only the script."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Movie: {movie_title}\n\n"
                    f"IMDb review excerpts:\n{review_text}"
                ),
            },
        ],
        max_tokens=300,
        temperature=0.3,
    )
    script = response.choices[0].message.content.strip()
    if not script:
        raise ValueError("The movie review script was empty")
    return script


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
            model="gpt-4o-mini",
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
