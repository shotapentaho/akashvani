"""
akashvani - GNews API Fallback Fetcher
Used when NewsAPI quota is exhausted
Provides seamless fallback with 100 additional requests/day
"""
import requests
import streamlit as st
from datetime import datetime
from typing import List, Dict

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_gnews_articles(query: str, api_key: str, top_k: int = 5) -> List[Dict]:
    """
    Fetch news from GNews API as fallback.
    
    Args:
        query: Search query
        api_key: GNews API key
        top_k: Number of articles to fetch
        
    Returns:
        List of formatted article dictionaries matching NewsAPI format
    """
    if not query or not api_key:
        return []
    
    try:
        # GNews API endpoint
        url = "https://gnews.io/api/v4/search"
        
        # Calculate date range (last 2 days to match NewsAPI)
        from datetime import timedelta
        two_days_ago = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        params = {
            "q": query,
            "lang": "en",
            "country": "in",  # Prefer Indian sources
            "max": min(top_k * 2, 10),  # GNews allows max 10 per request on free tier
            "from": two_days_ago,
            "token": api_key,  # GNews uses 'token' instead of 'apikey'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # Handle rate limiting
        if response.status_code == 429:
            st.error("⏳ GNews API rate limit also reached (100/day).")
            st.info("💡 Both NewsAPI and GNews quotas exhausted. Please wait until tomorrow.")
            return []
        
        if response.status_code == 403:
            st.error("❌ GNews API authentication failed. Check your API key in secrets.toml")
            return []
        
        if response.status_code != 200:
            st.warning(f"⚠️ GNews API error: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        if "articles" not in data:
            error_msg = data.get("message", "Unknown error")
            st.warning(f"⚠️ GNews API: {error_msg}")
            return []
        
        articles = data.get("articles", [])
        
        if not articles:
            return []
        
        # Format GNews articles to match NewsAPI format
        formatted = []
        for article in articles:
            formatted.append({
                "title": article.get("title", "No Title"),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "source": article.get("source", {}).get("name", "Unknown Source"),
                "published_at": _format_gnews_date(article.get("publishedAt", "")),
                "author": article.get("source", {}).get("name", "GNews"),
                "url": article.get("url", "#"),
                "image": article.get("image", ""),
            })
        
        return formatted[:top_k]  # Return only requested number
        
    except requests.exceptions.Timeout:
        st.warning("⚠️ GNews API timeout")
        return []
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ GNews network error: {str(e)[:100]}")
        return []
    except Exception as e:
        st.warning(f"⚠️ GNews error: {str(e)[:100]}")
        return []

def _format_gnews_date(date_str: str) -> str:
    """
    Format GNews date to readable format matching NewsAPI output.
    GNews format: "2026-02-07T12:30:00Z"
    Output format: "Feb 07, 2026"
    """
    if not date_str:
        return datetime.utcnow().strftime("%b %d, %Y")
    
    try:
        # Parse ISO format
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except:
        # Fallback to current date
        return datetime.utcnow().strftime("%b %d, %Y")
