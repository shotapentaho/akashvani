"""
akashvani - News Fetching Utilities

Full, self-contained news_fetcher with:
- Robust handling of malformed API responses (articles as strings/non-dicts)
- Retries/backoff for network resilience
- Curated international domains (includes Indian + global, BBC etc.)
- Single search strategy to reduce API calls
- Query-derived token extraction (no hard-coded country alias lists)
- Boosting / optional requiring of query-token matches
- Deduplication, simple relevance scoring, safe date parsing
- Streamlit caching (st.cache_data) with 1 hour TTL
- DATE FILTERING: Only fetches articles from last 2 days
- IMPROVED DATE DISPLAY: Never shows "N/A"
- CRICKET SCORE DETECTION: Prioritizes espncricinfo.com for cricket score queries
- AUTOMATIC FALLBACK: If ESPN Cricinfo has no results, searches all cricket sources
- RATE LIMIT HANDLING: Better error messages and retry logic
"""  
from typing import List, Dict, Optional, Any, Iterable  
import requests  
import streamlit as st  
from requests.adapters import HTTPAdapter  
from urllib3.util import Retry  
from datetime import datetime, timedelta  
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
    #Cricket
    "espncricinfo.com",
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

# Cricket-specific domain
CRICKET_DOMAIN = "espncricinfo.com"

def _requests_session_with_retries(
    total: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist=(500, 502, 503, 504),  # Removed 429 from retry list
) -> requests.Session:
    """
    Create a requests.Session configured with retry/backoff logic.
    Note: 429 (rate limit) is NOT in retry list - we handle it separately
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

def _is_cricket_score_query(query: str) -> bool:
    """
    Detect if the user is asking for cricket scores or match results.
    
    Args:
        query: User's search query
        
    Returns:
        True if query is about cricket scores, False otherwise
    """
    q_lower = query.lower().strip()
    
    # Cricket score/match indicators
    score_keywords = ["score", "scorecard", "result", "match", "live", "vs", "versus", "v/s"]
    cricket_keywords = ["cricket", "test", "odi", "t20", "ipl", "world cup", "series"]
    team_keywords = [
        "india", "pakistan", "australia", "england", "south africa", "new zealand",
        "sri lanka", "bangladesh", "west indies", "afghanistan", "zimbabwe", "ireland",
        "rcb", "csk", "mi", "kkr", "dc", "rr", "pbks", "srh", "gt", "lsg"  # IPL teams
    ]
    
    # Check if query contains cricket-related terms
    has_score_keyword = any(keyword in q_lower for keyword in score_keywords)
    has_cricket_keyword = any(keyword in q_lower for keyword in cricket_keywords)
    has_team_keyword = any(keyword in q_lower for keyword in team_keywords)
    
    # Check for "vs" pattern (India vs Australia, RCB vs CSK, etc.)
    has_vs_pattern = bool(re.search(r'\b\w+\s+(vs|versus|v/s)\s+\w+\b', q_lower))
    
    # It's a cricket score query if:
    # 1. Has score keyword AND (cricket keyword OR team keyword OR vs pattern)
    # 2. OR has vs pattern AND cricket keyword
    # 3. OR has cricket keyword AND score keyword
    
    is_cricket_query = (
        (has_score_keyword and (has_cricket_keyword or has_team_keyword or has_vs_pattern)) or
        (has_vs_pattern and has_cricket_keyword) or
        (has_cricket_keyword and has_score_keyword)
    )
    
    return is_cricket_query

def _enhance_cricket_query(query: str) -> str:
    """
    Enhance cricket query with additional keywords for better results.
    
    Args:
        query: Original user query
        
    Returns:
        Enhanced query with cricket-specific keywords
    """
    q = query.strip()
    q_lower = q.lower()
    
    # Add "cricket" if not present
    if "cricket" not in q_lower:
        q = f"{q} cricket"
    
    # Add score-related terms if asking about match
    if any(word in q_lower for word in ["vs", "versus", "v/s"]) and "score" not in q_lower:
        q = f"{q} score"
    
    return q

def _safe_date(iso_str: Optional[str]) -> str:
    """
    Parse publishedAt returned by NewsAPI to readable format, safely.
    Returns format: "Jan 15, 2026" instead of "N/A".
    """
    if not iso_str:
        # Return today's date as fallback instead of N/A
        return datetime.utcnow().strftime("%b %d, %Y")  
        
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        # Return more readable format: "Jan 15, 2026"
        return dt.strftime("%b %d, %Y")
    except Exception:
        # Try to extract just the date part
        m = re.match(r"(\d{4}-\d{2}-\d{2})", iso_str)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d")
                return dt.strftime("%b %d, %Y")
            except:
                return m.group(1)
        # Last resort: return today's date
        return datetime.utcnow().strftime("%b %d, %Y")

def _relative_time(iso_str: Optional[str]) -> str:
    """
    Convert ISO timestamp to relative time like '2 hours ago' or 'Yesterday'
    """
    if not iso_str:
        return "Recently"  
        
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=dt.tzinfo)
        diff = now - dt
        
        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                mins = diff.seconds // 60
                return f"{mins} min ago" if mins > 0 else "Just now"
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime("%b %d, %Y")
    except:
        return "Recently"

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
            "published_at": datetime.utcnow().strftime("%b %d, %Y"),
            "author": "Unknown Author",
            "url": s if is_url else "#",
            "image": "",
            "_raw_published_at": datetime.utcnow().isoformat(),
        }

    if not isinstance(article, dict):
        # Fallback for unexpected types
        s = str(article) if article is not None else ""
        return {
            "title": s or "No Title",
            "description": "",
            "content": "",
            "source": "Unknown Source",
            "published_at": datetime.utcnow().strftime("%b %d, %Y"),
            "author": "Unknown Author",
            "url": "#",
            "image": "",
            "_raw_published_at": datetime.utcnow().isoformat(),
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
        "_raw_published_at": article.get("publishedAt") or datetime.utcnow().isoformat(),
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

@st.cache_data(ttl=3600)  # Cache for 1 hour instead of 5 minutes to reduce API calls
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
    - Uses retries/backoff for network resilience (but NOT for 429 rate limits)
    - Single search strategy to minimize API calls
    - Uses the user's raw query tokens (phrase + words) to boost or optionally require matches
      in the returned articles. No hard-coded country alias lists are used.
    - Optionally restricts sources to a curated international domain list (includes BBC).
    - CRICKET SCORE DETECTION: Automatically detects cricket score queries and searches all sources
    - AUTOMATIC FALLBACK: If no results, tries broader search
    - Deduplicates, formats, scores, sorts, and returns top_k results.
    - ONLY FETCHES ARTICLES FROM LAST 2 DAYS
    - RATE LIMIT HANDLING: Shows helpful error messages on 429 errors
    """
    if not query or not api_key:
        st.error("❌ Missing query or API key for NewsAPI")
        return []

    session = _requests_session_with_retries()
    base_url = "https://newsapi.org/v2/everything"
    headers = {"Authorization": api_key}

    # Calculate date 2 days ago for filtering
    two_days_ago = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d')

    # 🏏 CRICKET SCORE DETECTION
    is_cricket_query = _is_cricket_score_query(query)
    
    if is_cricket_query:
        st.info("🏏 Cricket detected! Searching all cricket sources...")
        # Use ALL domains for cricket (not just ESPN) to get more results
        domains_param = ",".join(INTERNATIONAL_DOMAINS)
        enhanced_query = _enhance_cricket_query(query)
    else:
        # Use international domains as before
        domains_param = ",".join(INTERNATIONAL_DOMAINS) if use_international_domains else None
        enhanced_query = query

    # Derive tokens directly from the enhanced query (phrase + word tokens)
    query_tokens = _extract_search_tokens(enhanced_query)

    def _fetch(params: Dict) -> List[Any]:
        try:
            resp = session.get(base_url, params=params, timeout=10, headers=headers)
            
            # Handle rate limiting (429)
            if resp.status_code == 429:
                st.error("⏳ **Rate Limit Reached** - NewsAPI allows 100 requests/day on free tier.")
                st.info("💡 **Solutions:**\n- Wait until tomorrow (resets at midnight UTC)\n- Upgrade to paid plan at newsapi.org/pricing")
                
                # Check if retry-after header exists
                retry_after = resp.headers.get('Retry-After', '3600')
                try:
                    wait_minutes = int(retry_after) // 60
                    st.warning(f"⏱️ Please wait approximately {wait_minutes} minutes before trying again.")
                except:
                    st.warning("⏱️ Please wait before trying again.")
                
                return []
            
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
            error_str = str(e)
            if "429" in error_str:
                st.error("⏳ **Rate Limit Reached** - Too many requests to NewsAPI.")
                st.info("💡 Your daily quota is exhausted. Please try again tomorrow.")
            else:
                st.error(f"❌ Network Error: {e}")
            return []
        except Exception as e:
            st.error(f"❌ Unexpected Error: {e}")
            return []

    # SINGLE SEARCH STRATEGY - Reduces API calls by 50%
    params_search = {
        "q": enhanced_query,
        "pageSize": max(top_k * 2, 10),  # Get enough results in one call
        "language": "en",
        "sortBy": "publishedAt",  # Get latest first
        "from": two_days_ago,      # Only last 2 days
    }
    if domains_param:
        params_search["domains"] = domains_param

    articles = _fetch(params_search)
    combined = articles

    # Final check - if still no results
    if not combined:
        if is_cricket_query:
            st.warning(f"🏏 No cricket articles found for '{query}' in the last 2 days")
            st.info("💡 Tip: Try different team names or check if matches happened recently")
        else:
            st.warning(f"⚠️ No articles found for '{query}' in the last 2 days")
        return []

    # Deduplicate raw results
    combined = _dedupe_articles(combined)

    # Format and score
    formatted = [format_article(a) for a in combined]
    for a in formatted:
        a["_relevance_score"] = _score_article(a, enhanced_query)

    # 🏏 BOOST ESPN CRICINFO: Add bonus points to ESPN articles in cricket queries
    if is_cricket_query:
        for a in formatted:
            source_url = (a.get("url") or "").lower()
            if "espncricinfo.com" in source_url:
                a["_relevance_score"] = a.get("_relevance_score", 0.0) + 30.0  # Big boost for ESPN

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
        if is_cricket_query:
            st.warning(f"🏏 No relevant cricket articles after filtering for '{query}' in the last 2 days")
        else:
            st.warning(f"⚠️ No relevant articles after filtering for '{query}' in the last 2 days")

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
