"""
akashvani - News Fetching Utilities

Full, self-contained news_fetcher with:
- Robust handling of malformed API responses (articles as strings/non-dicts)
- Retries/backoff for network resilience
- Curated international domains (includes Indian + global, BBC etc.)
- Two-step search (qInTitle then q)
- Query-derived token extraction (no hard-coded country alias lists)
- Boosting / optional requiring of query-token matches
- Deduplication, simple relevance scoring, safe date parsing
- Streamlit caching (st.cache_data)
"""
from typing import List, Dict, Optional, Any, Iterable
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
import re

# Curated list of international news domains (includes major Indian outlets + global sources).
INTERNATIONAL_DOMAINS = [
    # Major Indian outlets
    "timesofindia.indiatimes.com",
    "thehindu.com",
    "indianexpress.com",
    "hindustantimes.com",
    "livemint.com",
    "economictimes.indiatimes.com",
    "ndtv.com",
    "news18.com",
    "deccanchronicle.com",
    "theprint.in",
    "scroll.in",
    "thewire.in",
    "telegraphindia.com",
    "business-standard.com",
    "firstpost.com",
    "outlookindia.com",
    # BBC
    "bbc.co.uk",
    "bbc.com",
    # Other international sources
    "reuters.com",
    "apnews.com",
    "cnn.com",
    "nytimes.com",
    "theguardian.com",
    "aljazeera.com",
    "washingtonpost.com",
    "bloomberg.com",
    "financialtimes.com",
    "ft.com",
    "axios.com",
    "thetimes.co.uk",
    "theglobeandmail.com",
    "smh.com.au",
]

def _requests_session_with_retries(
    total: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist=(429, 500, 502, 503, 504),
) -> requests.Session:
    """
    Create a requests.Session configured with retry/backoff logic.
    """
    session = requests.Session()
    retries = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def _safe_date(iso_str: Optional[str]) -> str:
    """
    Parse publishedAt returned by NewsAPI to YYYY-MM-DD, safely.
    """
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", iso_str)
        if m:
            return m.group(1)
        return iso_str[:10] if isinstance(iso_str, str) else "N/A"

def format_article(article: Any) -> Dict:
    """
    Normalize an article into a dict with safe defaults.

    Accepts:
      - dict (NewsAPI article)
      - str (title or url)
      - other types (converted to string)

    Handles `source` being either a dict or a string.
    """
    # If article is a string (e.g. title or url), convert to a minimal dict.
    if isinstance(article, str):
        s = article.strip()
        is_url = s.startswith("http://") or s.startswith("https://")
        return {
            "title": s if not is_url else "No Title",
            "description": "",
            "content": "",
            "source": "Unknown Source",
            "published_at": "N/A",
            "author": "Unknown Author",
            "url": s if is_url else "#",
            "image": "",
            "_raw_published_at": "",
        }

    if not isinstance(article, dict):
        # Fallback for unexpected types
        s = str(article) if article is not None else ""
        return {
            "title": s or "No Title",
            "description": "",
            "content": "",
            "source": "Unknown Source",
            "published_at": "N/A",
            "author": "Unknown Author",
            "url": "#",
            "image": "",
            "_raw_published_at": "",
        }

    # Handle source field being either dict or str
    src = article.get("source")
    if isinstance(src, dict):
        source_name = src.get("name") or "Unknown Source"
    elif isinstance(src, str):
        source_name = src or "Unknown Source"
    else:
        source_name = "Unknown Source"

    return {
        "title": article.get("title") or "No Title",
        "description": article.get("description") or "",
        "content": article.get("content") or "",
        "source": source_name,
        "published_at": _safe_date(article.get("publishedAt")),
        "author": article.get("author") or "Unknown Author",
        "url": article.get("url") or "#",
        "image": article.get("urlToImage") or "",
        "_raw_published_at": article.get("publishedAt") or "",
    }

def _score_article(formatted: Dict, query: str) -> float:
    """
    Compute a simple relevance score between the user query and a formatted article.
    We weigh title matches highest, then description, then content. Also add a tiny recency boost.
    """
    q = (query or "").lower().strip()
    if not q:
        return 0.0

    title = (formatted.get("title") or "").lower()
    desc = (formatted.get("description") or "").lower()
    content = (formatted.get("content") or "").lower()

    score = 0.0

    # Exact phrase in title
    if q in title:
        score += 50.0

    # Token matching
    tokens = [t for t in re.split(r"\s+", q) if t]
    tokens = [t for t in tokens if len(t) > 2] or tokens

    for t in tokens:
        if t in title:
            score += 10.0
        if t in desc:
            score += 3.0
        if t in content:
            score += 1.0

    # small recency boost (very small to not dominate relevance)
    raw_dt = formatted.get("_raw_published_at", "")
    try:
        dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
        score += (dt.timestamp() / 86400.0) * 1e-6
    except Exception:
        pass

    return score

def _dedupe_articles(articles: List[Any]) -> List[Any]:
    """
    Deduplicate articles by URL or title. Accepts articles that may be dicts or strings.
    Preserves first occurrence order.
    """
    seen = set()
    deduped = []
    for a in articles:
        if isinstance(a, dict):
            url = (a.get("url") or "").strip()
            title = (a.get("title") or "").strip()
            key = url or title
        else:
            s = str(a).strip()
            url = s if s.startswith("http://") or s.startswith("https://") else ""
            key = url or s
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(a)
    return deduped

def _extract_search_tokens(query: str) -> List[str]:
    """
    Derive useful search tokens from the raw user query string.

    Returns tokens in descending priority order:
      - Full cleaned phrase first (helps phrase matching)
      - Then unique word tokens (length > 2)
    """
    if not query:
        return []

    q = query.strip().lower()
    tokens: List[str] = [q]  # full phrase first

    # Split into words (letters, numbers, underscores, apostrophes), filter out short tokens
    words = re.findall(r"\b[\w']+\b", q)
    words = [w for w in words if len(w) > 2]

    seen = set()
    for w in words:
        if w not in seen:
            seen.add(w)
            tokens.append(w)

    return tokens

def _matches_query_tokens(article: Dict, tokens: Iterable[str]) -> bool:
    """
    Return True if any token appears in the article's title/description/content.
    Tokens are assumed lowercased.
    """
    if not tokens:
        return False
    combined = " ".join([
        (article.get("title") or ""),
        (article.get("description") or ""),
        (article.get("content") or "")
    ]).lower()
    for t in tokens:
        if not t:
            continue
        if t in combined:
            return True
    return False

def _filter_or_boost_by_query_tokens(formatted_articles: List[Dict], query_tokens: List[str], require_match: bool = False) -> List[Dict]:
    """
    Use the user's raw query tokens to prefer articles that contain those tokens.

    - If require_match=True: return only articles that match any token (fall back to original list if none match).
    - If require_match=False: return matched articles first, then others (boost).
    """
    if not query_tokens:
        return formatted_articles

    matched = []
    unmatched = []
    for a in formatted_articles:
        if _matches_query_tokens(a, query_tokens):
            matched.append(a)
        else:
            unmatched.append(a)

    if require_match:
        return matched or formatted_articles

    return matched + unmatched

@st.cache_data(ttl=300)
def get_top_news(
    query: str,
    api_key: str,
    top_k: int = 5,
    use_international_domains: bool = True,
    require_query_match: bool = False,
) -> List[Dict]:
    """
    Fetch and return the most relevant news articles for `query`.

    Key behavior:
    - Uses retries/backoff for network resilience.
    - Performs a qInTitle search first, then a broader q search if needed.
    - Uses the user's raw query tokens (phrase + words) to boost or optionally require matches
      in the returned articles. No hard-coded country alias lists are used.
    - Optionally restricts sources to a curated international domain list (includes BBC).
    - Deduplicates, formats, scores, sorts, and returns top_k results.
    """
    if not query or not api_key:
        st.error("❌ Missing query or API key for NewsAPI")
        return []

    session = _requests_session_with_retries()
    base_url = "https://newsapi.org/v2/everything"
    headers = {"Authorization": api_key}

    # Derive tokens directly from the user's query (phrase + word tokens)
    query_tokens = _extract_search_tokens(query)

    # Domain parameter (None if not restricting to international domains)
    domains_param = ",".join(INTERNATIONAL_DOMAINS) if use_international_domains else None

    def _fetch(params: Dict) -> List[Any]:
        try:
            resp = session.get(base_url, params=params, timeout=10, headers=headers)
            if resp.status_code != 200:
                try:
                    data = resp.json()
                    msg = data.get("message", "")
                except Exception:
                    msg = resp.text or f"HTTP {resp.status_code}"
                st.error(f"❌ NewsAPI Error: {msg} (HTTP {resp.status_code})")
                return []
            data = resp.json()
            if data.get("status") != "ok":
                st.error(f"❌ NewsAPI returned error: {data.get('message', 'Unknown')}")
                return []
            return data.get("articles", []) or []
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. NewsAPI server not responding.")
            return []
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Network Error: {e}")
            return []
        except Exception as e:
            st.error(f"❌ Unexpected Error: {e}")
            return []

    # 1) Focused search in title first (high precision)
    params_title_search = {
        "qInTitle": query,
        "pageSize": max(top_k, 10),
        "language": "en",
        "sortBy": "relevancy",
    }
    if domains_param:
        params_title_search["domains"] = domains_param

    articles = _fetch(params_title_search)

    # 2) If not enough, broaden search (use raw query; no automatic 'India' append)
    if len(articles) < top_k:
        params_broad_search = {
            "q": query,
            "pageSize": max(top_k * 3, 20),
            "language": "en",
            "sortBy": "relevancy",
        }
        if domains_param:
            params_broad_search["domains"] = domains_param

        articles_broad = _fetch(params_broad_search)
        combined = articles + articles_broad
    else:
        combined = articles

    if not combined:
        st.warning(f"⚠️ No articles found for '{query}'")
        return []

    # Deduplicate raw results
    combined = _dedupe_articles(combined)

    # Format and score
    formatted = [format_article(a) for a in combined]
    for a in formatted:
        a["_relevance_score"] = _score_article(a, query)

    # Use user-derived tokens to boost or require matches
    if query_tokens:
        formatted = _filter_or_boost_by_query_tokens(formatted, query_tokens, require_match=require_query_match)

    # Final sort by relevance score and recency
    formatted.sort(key=lambda x: (x.get("_relevance_score", 0.0), x.get("_raw_published_at", "")), reverse=True)

    # Prepare final results and remove internal keys
    result: List[Dict] = []
    for a in formatted[:top_k]:
        cleaned = {k: v for k, v in a.items() if not k.startswith("_")}
        result.append(cleaned)

    if len(result) == 0:
        st.warning(f"⚠️ No relevant articles after filtering for '{query}'")

    return result

def get_article_content(article: Any) -> str:
    """
    Extract main content from article with safe fallback.

    Accepts dict or string. Always returns a stripped string.
    """
    if isinstance(article, str):
        return article.strip() or "No content available"
    if not isinstance(article, dict):
        s = str(article)
        return s.strip() or "No content available"
    content = article.get("description") or article.get("content") or article.get("title") or "No content available"
    return content.strip()