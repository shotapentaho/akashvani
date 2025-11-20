# utils/news_fetcher.py
"""
akashvani - News Fetching Utilities
Using NewsAPI for Indian news sources
FIXED: Safe null handling for all fields
"""

import requests
import streamlit as st
from typing import List, Dict

def get_top_news(query: str, api_key: str, top_k: int = 5) -> List[Dict]:
    """
    Fetch top news articles from Indian news sources
    
    Args:
        query: Search query
        api_key: NewsAPI key (from st.secrets["newsapi"]["api_key"])
        top_k: Number of articles to fetch
    
    Returns:
        List of article dictionaries
    """

    # Generic "everything" endpoint without domain filter (Free tier compatible)
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}+India&"
        f"apiKey={api_key}&"
        f"pageSize={top_k * 2}&"
        f"sortBy=publishedAt&"
        f"language=en"
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Check for API errors
            if data.get("status") != "ok":
                error_msg = data.get('message', 'Unknown error')
                st.error(f"❌  NewsAPI Error: {error_msg}")

                # Specific error handling
                if "apiKeyInvalid" in error_msg:
                    st.error("❌  Invalid API Key. Please check your .streamlit/secrets.toml")
                elif "rateLimited" in error_msg:
                    st.error("❌  Rate limit exceeded. Free tier: 100 requests/day")

                return []

            articles = data.get("articles", [])

            if len(articles) == 0:
                st.warning(f"⚠️ No articles found for '{query}'")
                return []

            return articles[:top_k]

        else:
            st.error(f"❌  NewsAPI Error: HTTP {response.status_code}")
            return []

    except requests.exceptions.Timeout:
        st.error("❌  Request timed out. NewsAPI server not responding.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"❌  Network Error: {e}")
        return []
    except Exception as e:
        st.error(f"❌  Unexpected Error: {e}")
        return []

def format_article(article: Dict) -> Dict:
    """
    Format article data for display with safe null handling
    
    Args:
        article: Raw article from NewsAPI
    
    Returns:
        Formatted article dictionary with safe defaults
    """
    return {
        "title": article.get("title") or "No Title",
        "description": article.get("description") or "",
        "content": article.get("content") or "",
        "source": article.get("source", {}).get("name") or "Unknown Source",
        "published_at": (article.get("publishedAt") or "N/A")[:10],
        "author": article.get("author") or "Unknown Author",
        "url": article.get("url") or "#",
        "image": article.get("urlToImage") or "",
    }

def get_article_content(article: Dict) -> str:
    """
    Extract main content from article with safe fallback
    
    Args:
        article: Formatted article dictionary
    
    Returns:
        Article content string (never None)
    """
    content = article.get("description") or article.get("content") or article.get("title") or "No content available"
    return content.strip()
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
~                                                                                                                                                                            