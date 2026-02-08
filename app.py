# app.py
"""
akashvani - Senior-Friendly News-to-Speech Application
Single-page layout: language select centered in header row; tips top-right (left-aligned)
AI Summary checkbox on same row as Articles (after Articles)
Indian flag next to app title
CRICKET SCORES: Extracted from news articles (reliable, no scraping errors)
DUAL API: NewsAPI + GNews fallback for 200 requests/day
OPTIMIZED: GPT-3.5-turbo-0125 with caching (91% cost reduction)
TRACKING: PostgreSQL insert-only pattern for analytics
Project: akashvani | Version 1.3 | 2026-02-08
Author: CX Data & Analytics
Live Demo: https://akashvani.cxloop.co
"""

import streamlit as st
import uuid

# ===== PAGE CONFIG MUST BE FIRST STREAMLIT COMMAND =====
st.set_page_config(
    page_title="akashvani 📻 - Senior News Reader",
    page_icon="https://akashvani.cxloop.co/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "akashvani: News-to-Speech App for Senior Citizens | 12 Indian Languages | Version 1.3"
    }
)

from config.languages import (
    INDIAN_LANGUAGES,
    get_language_info,
    get_all_languages,
    is_tts_supported
)
from utils.news_fetcher import get_top_news, format_article, get_article_content, _is_cricket_score_query
from utils.translator import cached_translate, cached_summary
from utils.tts_handler import text_to_speech, get_speech_speed_display, is_language_supported
from utils.cricket_scraper import extract_score_from_article

# PostgreSQL tracking (insert-only) - with better error handling
DB_TRACKING_ENABLED = False
try:
    from utils.database import track_api_call, track_search_query, track_user_session
    DB_TRACKING_ENABLED = True
    print("=" * 60)
    print("✅ DATABASE TRACKING ENABLED")
    print(f"   - track_api_call: {track_api_call}")
    print(f"   - track_search_query: {track_search_query}")
    print("=" * 60)
except ImportError as e:
    print("=" * 60)
    print(f"⚠️ DATABASE TRACKING DISABLED - Import Error: {e}")
    print("=" * 60)
except Exception as e:
    print("=" * 60)
    print(f"❌ DATABASE TRACKING DISABLED - Error: {e}")
    print("=" * 60)

# Show tracking status
print(f"\n📊 DB_TRACKING_ENABLED = {DB_TRACKING_ENABLED}\n")

hide_default_header = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""

st.markdown(hide_default_header, unsafe_allow_html=True)

# ===== LOAD SECRETS & INITIALIZE OPENAI CLIENT =====
try:
    # Load API keys from Streamlit secrets
    openai_api_key = st.secrets["openai"]["api_key"]
    news_api_key = st.secrets["newsapi"]["api_key"]
    
    # Load GNews API key for fallback (optional)
    try:
        gnews_api_key = st.secrets["gnewsapi"]["api_key"]
    except KeyError:
        gnews_api_key = None

    # Validate API keys
    if not news_api_key or not openai_api_key:
        st.error("⚠️ Service temporarily unavailable")
        st.info("Please contact support@cxloop.co for assistance")
        st.stop()

    # DON'T initialize OpenAI client here - we'll do it in cached functions
    # This avoids caching issues with the client object
    client = None  # Placeholder (not used, we pass api_key directly to translator functions)
        
except KeyError as e:
    st.error("⚠️ Service temporarily unavailable")
    st.info("Please contact **support@cxloop.co** for assistance")
    print(f"Configuration error: {e}")  # Log for admins
    st.stop()
    
except Exception as e:
    st.error("⚠️ Service temporarily unavailable")
    st.info("Please contact **support@cxloop.co** for assistance")
    print(f"Startup error: {e}")  # Log for admins
    st.stop()

# ===== CUSTOM CSS FOR SENIOR FRIENDLY UI =====
st.markdown("""
    <style>
    * { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    body { font-size: 18px; background-color: #f8f9fa; }
    
    .stButton>button { 
        font-size: 18px; 
        padding: 12px 25px; 
        background-color: #FF6B6B;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #FF5252;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
    }
    
    .stTextInput>div>div>input { 
        font-size: 16px; 
        padding: 12px;
        border-radius: 8px;
        border: 2px solid #ddd;
    }
    
    .stSelectbox>div>div>select,
    .stRadio>div>label,
    .stCheckbox>label {
        font-size: 16px;
    }
    
    h1, h2, h3 { color: #1F77B4; font-weight: 700; display: inline-block; vertical-align: middle; }
    
    .info-box {
        background-color: #E8F4F8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1F77B4;
        font-size: 16px;
        margin: 10px 0;
    }
    
    .success-box {
        background-color: #D4EDDA;
        padding: 12px;
        border-radius: 8px;
        border-left: 5px solid #28a745;
        color: #155724;
    }
    
    .duration-info {
        background-color: #FFF9C4;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #FBC02D;
        font-size: 14px;
        margin: 10px 0;
    }
    
    .article-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }

    /* Compact header tip styling - left aligned text for better readability */
    .header-tip {
        background: #eef7ff;
        border-left: 4px solid #1F77B4;
        padding: 10px;
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.4;
        text-align: left;
    }
    .header-tip div {
        margin-bottom: 6px;
    }
    
    /* Cricket score styling - compact and crisp */
    .cricket-score-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .cricket-match-header {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 12px;
        text-align: center;
        border-bottom: 2px solid rgba(255,255,255,0.3);
        padding-bottom: 8px;
    }
    
    .cricket-team {
        font-size: 18px;
        font-weight: bold;
        margin: 8px 0;
        padding: 6px;
        background: rgba(255,255,255,0.1);
        border-radius: 6px;
    }
    
    .cricket-score {
        font-size: 24px;
        font-weight: bold;
        color: #ffd700;
    }
    
    .cricket-series {
        font-size: 13px;
        opacity: 0.85;
        margin-top: 8px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# ===== SESSION STATE =====
if 'last_language' not in st.session_state:
    st.session_state.last_language = "English"
if 'last_duration' not in st.session_state:
    st.session_state.last_duration = "standard"
if 'api_calls_today' not in st.session_state:
    st.session_state.api_calls_today = 0
if 'last_reset_date' not in st.session_state:
    from datetime import date
    st.session_state.last_reset_date = date.today()
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'last_session_track' not in st.session_state:
    st.session_state.last_session_track = 0

# Reset counter daily
from datetime import date
if st.session_state.last_reset_date != date.today():
    st.session_state.api_calls_today = 0
    st.session_state.last_reset_date = date.today()

# ===== HEADER (language select centered, tips top-right left-aligned) =====
left_col, center_col, right_col = st.columns([2, 1, 2])

with left_col:
    st.markdown("## 📻 akashvani 🇮🇳")
    st.markdown("### News spoken in your language")
    st.markdown("**News from Indian and International Trusted Sources**")

with center_col:
    st.markdown("")  # spacer for alignment
    selected_language = st.selectbox(
        "Select Language",
        get_all_languages(),
        index=0,
        key="header_language_select",
        label_visibility="collapsed",
        help="Choose your preferred language for news reading"
    )

with right_col:
    tips_html = """
    <div class='header-tip'>
      <div>• Use Slow speed for clarity</div>
      <div>• Use Long duration for detailed news</div>
      <div>• Enable AI Summary for simpler language</div>
      <div>• Use headphones for better sound</div>
      <div>• Search cricket scores (e.g., India vs Aus)</div>
    </div>
    """
    st.markdown(tips_html, unsafe_allow_html=True)

# derive language code and info after selection
language_code = INDIAN_LANGUAGES[selected_language]
lang_info = get_language_info(language_code)
tts_status = "✅ Voice" if lang_info.get('tts_supported', False) else "📝 Text-only"

# Track user session (insert-only) - NON-BLOCKING with throttling
if DB_TRACKING_ENABLED:
    try:
        import time
        current_time = time.time()
        
        # Only track once every 60 seconds to avoid excessive DB calls
        if current_time - st.session_state.last_session_track > 60:
            track_user_session(
                session_id=st.session_state.session_id,
                language_code=language_code,
                page_view='main'
            )
            st.session_state.last_session_track = current_time
    except Exception as e:
        # Non-critical error - don't break the UI
        print(f"Session tracking error (non-critical): {e}")

st.markdown("---")

# ===== SETTINGS (single-row layout with Articles slider and AI Summary checkbox) =====
with st.container():
    col_speed, col_duration, col_articles, col_ai = st.columns([1, 1.2, 1, 1.2])

    with col_speed:
        speech_speed = st.radio(
            "Speed",
            ["Normal ⚡", "Slow 🐢"],
            index=1,
            help="Slow is recommended for seniors"
        )

    with col_duration:
        duration_mode = st.radio(
            "Duration",
            ["Short (1 min)", "Standard (2 min)", "Long (3 min)"],
            index=1,
            help="Longer summaries = more detailed news coverage"
        )
        duration_info_map = {
            "Short (1 min)": "150 words",
            "Standard (2 min)": "300 words",
            "Long (3 min)": "450 words"
        }
        st.caption(f"Target: {duration_info_map.get(duration_mode,'')}")
        duration_map = {
            "Short (1 min)": "short",
            "Standard (2 min)": "standard",
            "Long (3 min)": "long"
        }
        duration_key = duration_map.get(duration_mode, "standard")

    with col_articles:
        results_count = st.slider("Articles", 1, 10, 5)

    with col_ai:
        use_ai_summary = st.checkbox("✓ AI Summary (Senior-Friendly)", value=True)

st.markdown("---")

# ===== SEARCH INPUT (on same page) =====
search_col, btn_col = st.columns([4, 1])

with search_col:
    query = st.text_input(
        "Search topic",
        placeholder="e.g., Elections, Stock Market, Cricket, Health, Weather, Technology, India vs Australia...",
        help="Type a topic you want to read about or cricket match (e.g., India vs Australia score)"
    )

with btn_col:
    search_button = st.button("🔍 Search", key="search_btn", use_container_width=True)

if st.button("❓ Help"):
    st.info("Choose language from the center above, set speed/duration/articles and AI Summary in the row below. Enter a topic and press Search. For cricket scores, search like 'India vs Australia score'. AI summary and audio will be generated.")

# ===== PROCESS AND DISPLAY =====
if search_button:
    if not query or len(query.strip()) < 2:
        st.warning("⚠️ Please enter a valid news topic (at least 2 characters).")
    else:
        # Track API calls (for session state counter)
        st.session_state.api_calls_today += 1
        
        # ===== FETCH NEWS WITH AUTOMATIC FALLBACK =====
        articles = []
        api_used = "NewsAPI"
        service_error = False
        
        # TRY NEWSAPI FIRST
        try:
            with st.spinner(f"📡 Fetching news for '{query}'..."):
                articles = get_top_news(query, news_api_key, top_k=results_count)
            
            if articles:
                api_used = "NewsAPI"
                
                print(f"\n{'='*60}")
                print(f"📊 TRACKING ATTEMPT")
                print(f"   Query: {query}")
                print(f"   Articles: {len(articles)}")
                print(f"   Language: {language_code}")
                print(f"   Duration: {duration_key}")
                print(f"   Session: {st.session_state.session_id}")
                print(f"   DB_TRACKING_ENABLED: {DB_TRACKING_ENABLED}")
                print(f"{'='*60}\n")
                
                # ✅ TRACK IN POSTGRESQL (INSERT ONLY)
                if DB_TRACKING_ENABLED:
                    try:
                        print(f"🔵 Starting track_api_call...")
                        track_api_call(
                            api_name="newsapi",
                            query_text=query,
                            response_status="success",
                            articles_count=len(articles)
                        )
                        
                        print(f"🔵 Starting track_search_query...")
                        track_search_query(
                            query_text=query,
                            language_code=language_code,
                            articles_count=len(articles),
                            api_used="newsapi",
                            duration_mode=duration_key,
                            session_id=st.session_state.session_id
                        )
                        
                        print(f"✅ TRACKING COMPLETED SUCCESSFULLY\n")
                    except Exception as e:
                        print(f"❌ TRACKING ERROR: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"⚠️ TRACKING SKIPPED - DB_TRACKING_ENABLED is False\n")
            else:
                # Track failed NewsAPI call
                if DB_TRACKING_ENABLED:
                    try:
                        track_api_call(
                            api_name="newsapi",
                            query_text=query,
                            response_status="failure",
                            articles_count=0
                        )
                    except Exception as e:
                        print(f"Tracking error: {e}")
        
        except Exception as e:
            print(f"NewsAPI error: {e}")  # Log for admins
            service_error = True
        
        # AUTOMATIC FALLBACK TO GNEWS IF NEWSAPI FAILED
        if not articles and gnews_api_key and not service_error:
            try:
                st.info("🔄 Switching to backup news source...")
                
                from utils.gnews_fetcher import get_gnews_articles
                
                with st.spinner(f"📡 Fetching news from backup source..."):
                    articles = get_gnews_articles(query, gnews_api_key, top_k=results_count)
                
                if articles:
                    api_used = "GNews"
                    st.success(f"✅ Found {len(articles)} articles from backup source")
                    
                    # ✅ TRACK IN POSTGRESQL (INSERT ONLY)
                    if DB_TRACKING_ENABLED:
                        try:
                            track_api_call(
                                api_name="gnews",
                                query_text=query,
                                response_status="success",
                                articles_count=len(articles)
                            )
                            track_search_query(
                                query_text=query,
                                language_code=language_code,
                                articles_count=len(articles),
                                api_used="gnews",
                                duration_mode=duration_key,
                                session_id=st.session_state.session_id
                            )
                        except Exception as e:
                            print(f"Tracking error: {e}")
                else:
                    # Track failed GNews call
                    if DB_TRACKING_ENABLED:
                        try:
                            track_api_call(
                                api_name="gnews",
                                query_text=query,
                                response_status="failure",
                                articles_count=0
                            )
                        except Exception as e:
                            print(f"Tracking error: {e}")
                        
            except Exception as e:
                print(f"GNews error: {e}")  # Log for admins
                service_error = True
                
                # Track GNews error
                if DB_TRACKING_ENABLED:
                    try:
                        track_api_call(
                            api_name="gnews",
                            query_text=query,
                            response_status="failure",
                            articles_count=0
                        )
                    except Exception as e:
                        print(f"Tracking error: {e}")
        
        # NO RESULTS FROM ANY API OR SERVICE ERROR
        if not articles:
            if service_error:
                # Generic error message for users
                st.error("⚠️ We're experiencing technical difficulties")
                st.info("📧 Please try again in a few minutes or contact **support@cxloop.co** for assistance")
            else:
                # Quota exhausted or no results
                st.error("❌ No news found at the moment")
                st.info("**This could be because:**\n- Daily news quota has been reached (resets at midnight UTC)\n- No recent articles available for this topic\n- Try a different search term")
                st.markdown("**Popular topics to try:** Elections, Sports, Business, Weather, Health, Technology, India, Cricket")
                st.markdown("---")
                st.info("📧 Need help? Contact **support@cxloop.co**")
        else:
            # 🏏 CRICKET SCORE EXTRACTION (if cricket query)
            if _is_cricket_score_query(query):
                st.markdown("---")
                st.markdown("### 🏏 Cricket Scores from Latest News")
                
                try:
                    # Try to extract scores from news articles
                    cricket_scores_found = []
                    for article in articles[:5]:  # Check first 5 articles
                        score = extract_score_from_article(article)
                        if score:
                            cricket_scores_found.append(score)
                    
                    if cricket_scores_found:
                        # Display first score found
                        match = cricket_scores_found[0]
                        
                        cricket_html = f"""
                        <div class='cricket-score-box'>
                            <div class='cricket-match-header'>🏏 {match['team1']} vs {match['team2']}</div>
                            <div class='cricket-team'>{match['team1']}: <span class='cricket-score'>{match['team1_score']}</span></div>
                            <div class='cricket-team'>{match['team2']}: <span class='cricket-score'>{match['team2_score']}</span></div>
                            <div class='cricket-series'>📅 {match['published']} | 📰 {match['source']}</div>
                        </div>
                        """
                        st.markdown(cricket_html, unsafe_allow_html=True)
                        
                        # Create speech text
                        score_text = f"Cricket score: {match['team1']} scored {match['team1_score']}. {match['team2']} scored {match['team2_score']}."
                        
                        # OPTIMIZED: Use cached translation
                        try:
                            if language_code != "en":
                                with st.spinner(f"🌐 Translating to {selected_language}..."):
                                    score_text_translated = cached_translate(score_text, language_code, openai_api_key)
                                st.write(f"**🗣️ Score in {selected_language}:**")
                                st.info(score_text_translated)
                                audio_text = score_text_translated
                            else:
                                audio_text = score_text
                            
                            # TTS
                            tts_available = is_language_supported(language_code)
                            if tts_available:
                                st.write(f"**🔊 Listen to score in {selected_language}:**")
                                slow_mode = speech_speed == "Slow 🐢"
                                audio = text_to_speech(audio_text, language_code, slow=slow_mode)
                                if audio:
                                    st.audio(audio, format="audio/mp3")
                        except Exception as e:
                            print(f"Translation/TTS error: {e}")  # Log for admins
                            # Don't show error to user, just skip audio
                        
                        if match['url']:
                            st.markdown(f"[📰 Read Full Article]({match['url']})")
                        
                        st.markdown("---")
                    else:
                        st.info("🏏 No cricket scores found in recent articles. Check news articles below for latest cricket updates.")
                except Exception as e:
                    print(f"Cricket score extraction error: {e}")  # Log for admins
                    # Don't show error to user, just skip cricket scores
            
            # ===== NEWS ARTICLES SECTION =====
            st.markdown("## 📰 News Articles")
            st.markdown(f"<div class='success-box'>✅ Found {len(articles)} articles for '{query}'</div>", unsafe_allow_html=True)
            st.markdown("---")

            tts_available = is_language_supported(language_code)
            if not tts_available:
                st.info(f"📝 Text-only mode: Voice narration not available for {selected_language} ({language_code}).")

            for idx, article in enumerate(articles, 1):
                try:
                    formatted_article = format_article(article)
                    article_content = get_article_content(formatted_article)
                    article_title = formatted_article.get('title') or "No Title"

                    with st.expander(f"📄 Article {idx}: {article_title[:80]}...", expanded=(idx == 1)):
                        st.subheader(article_title)

                        c1, c2, c3 = st.columns(3)
                        with c1:
                            source = formatted_article.get('source') or "Unknown Source"
                            st.caption(f"📰 {source[:50]}")
                        with c2:
                            published = formatted_article.get('published_at') or "N/A"
                            st.caption(f"📅 {published}")
                        with c3:
                            author = formatted_article.get('author') or "Unknown Author"
                            st.caption(f"✍️ {author[:30]}")

                        st.markdown("---")

                        # OPTIMIZED: Use cached summary with GPT-3.5-turbo-0125
                        try:
                            if use_ai_summary:
                                with st.spinner(f"🤖 Creating {duration_mode.lower()} summary..."):
                                    summary = cached_summary(article_content, language_code, openai_api_key, duration_key)
                                st.write("**📝 Summary (Simplified for You):**")
                                st.info(summary)
                                audio_content = summary
                            else:
                                st.write("**📝 Article Content:**")
                                st.write(article_content)
                                audio_content = article_content

                            st.markdown("---")

                            # OPTIMIZED: Use cached translation with GPT-3.5-turbo-0125
                            if language_code != "en":
                                with st.spinner(f"🌐 Translating to {selected_language}..."):
                                    audio_content = cached_translate(audio_content, language_code, openai_api_key)
                                st.write(f"**🗣️ Content in {selected_language}:**")
                                st.success(audio_content)
                                st.markdown("---")

                            # TTS playback
                            if tts_available:
                                st.write(f"**🔊 Listen to this article in {selected_language}:**")
                                pcol1, pcol2, pcol3 = st.columns([3, 1, 1])
                                with pcol1:
                                    slow_mode = speech_speed == "Slow 🐢"
                                    audio = text_to_speech(audio_content, language_code, slow=slow_mode)
                                    if audio:
                                        st.audio(audio, format="audio/mp3")
                                with pcol2:
                                    st.caption(f"Speed: {get_speech_speed_display(slow_mode)}")
                                with pcol3:
                                    article_url = formatted_article.get('url') or "#"
                                    if article_url != "#":
                                        st.caption(f"[🔗 Source]({article_url})")
                            else:
                                st.info("📝 Voice narration not available for this language. Read the text above.")
                                article_url = formatted_article.get('url') or "#"
                                if article_url != "#":
                                    st.markdown(f"[🔗 Read Full Article on Source Website]({article_url})")
                        
                        except Exception as e:
                            print(f"Article processing error for article {idx}: {e}")  # Log for admins
                            st.warning("⚠️ Unable to process this article")
                            st.info("📧 If this persists, contact **support@cxloop.co**")

                        st.markdown("---")
                
                except Exception as e:
                    print(f"Error displaying article {idx}: {e}")  # Log for admins
                    # Skip this article and continue with next one

# ===== FOOTER =====
st.markdown("---")
f1, f2, f3, f4 = st.columns(4)
with f1:
    st.caption("📱 Senior-Friendly")
with f2:
    st.caption("🌍 12 Languages")
with f3:
    st.caption("🤖 AI-Powered")
with f4:
    st.caption("🏏 Cricket Scores")

st.caption("---")
st.caption("""
✨ Akashvani v1.3 from CX Data & Analytics LLC
🗣️ 12 Indian languages · 1–3 min audio briefs · 🏏 Cricket scores from news
🔄 Dual API: NewsAPI + GNews (200 requests/day total)
⚡ Optimized: GPT-3.5-turbo-0125 with smart caching (91% cost reduction)
📊 Analytics: PostgreSQL insert-only tracking for real-time insights
🏗️ Streamlit + OpenAI + gTTS + NewsAPI + GNews + PostgreSQL
❤️  Crafted with accessibility in mind, delivering trusted news from reputable sources worldwide.
📧 Support: support@cxloop.co
""")

# ---------- Footer with Privacy Policy Link ----------
st.markdown("---")
col1, col2, col3 = st.columns([0.3, 0.4, 0.3])
with col1:
    with st.expander("📋 Privacy Policy"):
        try:
            with open("privacy-policy.md", "r") as f:
                st.markdown(f.read())
        except FileNotFoundError:
            st.error("Privacy policy file not found.")