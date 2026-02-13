# app.py
"""
akashvani - Senior-Friendly News-to-Speech Application
Version: 1.4 | 2026-02-13
"""

import streamlit as st
import uuid
import os

# ===== CRITICAL: Clear proxy environment variables FIRST =====
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy', 'ALL_PROXY', 'all_proxy']
for var in proxy_vars:
    if var in os.environ:
        print(f"⚠️ Clearing proxy variable: {var}")
        os.environ.pop(var, None)

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="akashvani 📻 - Senior News Reader",
    page_icon="https://akashvani.cxloop.co/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "akashvani: News-to-Speech App for Senior Citizens | 12 Indian Languages | Version 1.4"
    }
)

from config.languages import (
    INDIAN_LANGUAGES,
    get_language_info,
    get_all_languages,
    is_tts_supported
)
from utils.news_fetcher import get_top_news, format_article, get_article_content, _is_cricket_score_query
from utils.translator import translate_to_language, get_ai_summary
from utils.tts_handler import text_to_speech, get_speech_speed_display, is_language_supported
from utils.cricket_scraper import extract_score_from_article

# Database tracking
DB_TRACKING_ENABLED = False
try:
    from utils.database import track_api_call, track_search_query, track_user_session
    DB_TRACKING_ENABLED = True
    print("✅ DATABASE TRACKING ENABLED")
except:
    print("⚠️ DATABASE TRACKING DISABLED")

hide_default_header = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_default_header, unsafe_allow_html=True)

# ===== LOAD SECRETS (SIMPLIFIED - No diagnostics in main app) =====
try:
    openai_api_key = st.secrets["openai"]["api_key"]
    news_api_key = st.secrets["newsapi"]["api_key"]
    gnews_api_key = st.secrets.get("gnewsapi", {}).get("api_key")
    serpapi_key = st.secrets.get("serpapi", {}).get("api_key")
    SERPAPI_ENABLED = bool(serpapi_key)
    
    if not news_api_key or not openai_api_key:
        raise ValueError("Required API keys are empty")
    
    # Create OpenAI client
    from openai import OpenAI
    client = OpenAI(
        api_key=openai_api_key,
        timeout=30.0,
        max_retries=2
    )
    print("✅ All systems ready")
        
except Exception as e:
    print(f"❌ Startup failed: {e}")
    st.error("⚠️ Service temporarily unavailable")
    st.info("📧 Please contact **support@cxloop.co** for assistance")
    st.markdown("---")
    st.info("🔧 **Admin:** Visit the 🔍 Diagnostics page in the sidebar for detailed troubleshooting")
    st.stop()

# ===== CUSTOM CSS =====
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
    
    h1, h2, h3 { color: #1F77B4; font-weight: 700; }
    
    .success-box {
        background-color: #D4EDDA;
        padding: 12px;
        border-radius: 8px;
        border-left: 5px solid #28a745;
        color: #155724;
    }
    
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
    </style>
    """, unsafe_allow_html=True)

# ===== SESSION STATE =====
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'api_calls_today' not in st.session_state:
    st.session_state.api_calls_today = 0
if 'last_reset_date' not in st.session_state:
    from datetime import date
    st.session_state.last_reset_date = date.today()
if 'last_session_track' not in st.session_state:
    st.session_state.last_session_track = 0

# Reset counter daily
from datetime import date
if st.session_state.last_reset_date != date.today():
    st.session_state.api_calls_today = 0
    st.session_state.last_reset_date = date.today()

# ===== HEADER =====
left_col, center_col, right_col = st.columns([2, 1, 2])

with left_col:
    st.markdown("## 📻 akashvani 🇮🇳")
    st.markdown("### News spoken in your language")
    st.markdown("**News from Indian and International Trusted Sources**")

with center_col:
    st.markdown("")
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

language_code = INDIAN_LANGUAGES[selected_language]
lang_info = get_language_info(language_code)

# Track user session
if DB_TRACKING_ENABLED:
    try:
        import time
        current_time = time.time()
        if current_time - st.session_state.last_session_track > 60:
            track_user_session(
                session_id=st.session_state.session_id,
                language_code=language_code,
                page_view='main'
            )
            st.session_state.last_session_track = current_time
    except Exception as e:
        print(f"Session tracking error: {e}")

st.markdown("---")

# ===== SETTINGS =====
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

# ===== SEARCH INPUT =====
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
        st.session_state.api_calls_today += 1
        
        articles = []
        api_used = "NewsAPI"
        service_error = False
        
        # TRY NEWSAPI FIRST
        try:
            with st.spinner(f"📡 Fetching news for '{query}'..."):
                articles = get_top_news(query, news_api_key, top_k=results_count)
            
            if articles:
                api_used = "NewsAPI"
                if DB_TRACKING_ENABLED:
                    try:
                        track_api_call("newsapi", query, "success", len(articles))
                        track_search_query(query, language_code, len(articles), "newsapi", duration_key, st.session_state.session_id)
                    except Exception as e:
                        print(f"Tracking error: {e}")
            else:
                if DB_TRACKING_ENABLED:
                    try:
                        track_api_call("newsapi", query, "failure", 0)
                    except Exception as e:
                        print(f"Tracking error: {e}")
        
        except Exception as e:
            print(f"NewsAPI error: {e}")
            service_error = True
        
        # FALLBACK TO GNEWS
        if not articles and gnews_api_key and not service_error:
            try:
                st.info("🔄 Switching to backup news source...")
                from utils.gnews_fetcher import get_gnews_articles
                
                with st.spinner(f"📡 Fetching news from backup source..."):
                    articles = get_gnews_articles(query, gnews_api_key, top_k=results_count)
                
                if articles:
                    api_used = "GNews"
                    st.success(f"✅ Found {len(articles)} articles from backup source")
                    if DB_TRACKING_ENABLED:
                        try:
                            track_api_call("gnews", query, "success", len(articles))
                            track_search_query(query, language_code, len(articles), "gnews", duration_key, st.session_state.session_id)
                        except Exception as e:
                            print(f"Tracking error: {e}")
                else:
                    if DB_TRACKING_ENABLED:
                        try:
                            track_api_call("gnews", query, "failure", 0)
                        except:
                            pass
                        
            except Exception as e:
                print(f"GNews error: {e}")
                service_error = True
        
        # NO RESULTS
        if not articles:
            if service_error:
                st.error("⚠️ We're experiencing technical difficulties")
                st.info("📧 Please try again in a few minutes or contact **support@cxloop.co**")
            else:
                st.error("❌ No news found at the moment")
                st.info("**This could be because:**\n- Daily news quota reached (resets at midnight UTC)\n- No recent articles for this topic\n- Try a different search term")
                st.markdown("**Popular topics:** Elections, Sports, Business, Weather, Health, Technology, India, Cricket")
        else:
            # 🏏 CRICKET SCORES
            if _is_cricket_score_query(query):
                st.markdown("---")
                st.markdown("## 🏏 Cricket Scores")
                
                live_score_found = False
                
                # TRY SERPAPI
                if SERPAPI_ENABLED:
                    try:
                        from utils.cricket_live import get_live_cricket_scores, display_cricket_score, create_cricket_score_speech
                        
                        with st.spinner("🔍 Fetching live cricket scores..."):
                            match_data = get_live_cricket_scores(query)
                        
                        if match_data:
                            live_score_found = True
                            
                            if DB_TRACKING_ENABLED:
                                try:
                                    track_api_call("serpapi", query, "success", 1)
                                except:
                                    pass
                            
                            display_cricket_score(match_data)
                            english_score_text = create_cricket_score_speech(match_data)
                            
                            st.markdown("---")
                            st.write("**📝 Score in English:**")
                            st.info(english_score_text)
                            
                            try:
                                st.write("**🔊 Listen in English:**")
                                slow_mode = speech_speed == "Slow 🐢"
                                audio_en = text_to_speech(english_score_text, "en", slow=slow_mode)
                                if audio_en:
                                    st.audio(audio_en, format="audio/mp3")
                            except Exception as e:
                                print(f"English TTS error: {e}")
                            
                            if language_code != "en":
                                st.markdown("---")
                                try:
                                    with st.spinner(f"🌐 Translating to {selected_language}..."):
                                        score_text_translated = translate_to_language(english_score_text, language_code, client)
                                    st.write(f"**📝 Score in {selected_language}:**")
                                    st.success(score_text_translated)
                                    
                                    tts_available = is_language_supported(language_code)
                                    if tts_available:
                                        st.write(f"**🔊 Listen in {selected_language}:**")
                                        audio_translated = text_to_speech(score_text_translated, language_code, slow=slow_mode)
                                        if audio_translated:
                                            st.audio(audio_translated, format="audio/mp3")
                                    else:
                                        st.info(f"Voice narration not available for {selected_language}")
                                except Exception as e:
                                    print(f"Translation/TTS error: {e}")
                            
                            if match_data.get('url'):
                                st.markdown(f"[📰 Full Match Details]({match_data['url']})")
                    
                    except Exception as e:
                        print(f"SerpAPI error: {e}")
                        live_score_found = False
                
                # FALLBACK: NEWS EXTRACTION
                if not live_score_found:
                    if SERPAPI_ENABLED:
                        st.info("🏏 No live scores via SerpAPI. Checking news articles...")
                    
                    try:
                        cricket_scores_found = []
                        for article in articles[:5]:
                            score = extract_score_from_article(article)
                            if score:
                                cricket_scores_found.append(score)
                        
                        if cricket_scores_found:
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
                            
                            score_text = f"Cricket score: {match['team1']} scored {match['team1_score']}. {match['team2']} scored {match['team2_score']}."
                            
                            st.write("**📝 Score in English:**")
                            st.info(score_text)
                            
                            try:
                                st.write("**🔊 Listen in English:**")
                                slow_mode = speech_speed == "Slow 🐢"
                                audio_en = text_to_speech(score_text, "en", slow=slow_mode)
                                if audio_en:
                                    st.audio(audio_en, format="audio/mp3")
                            except Exception as e:
                                print(f"English TTS error: {e}")
                            
                            if language_code != "en":
                                st.markdown("---")
                                try:
                                    with st.spinner(f"🌐 Translating to {selected_language}..."):
                                        score_text_translated = translate_to_language(score_text, language_code, client)
                                    st.write(f"**📝 Score in {selected_language}:**")
                                    st.success(score_text_translated)
                                    
                                    tts_available = is_language_supported(language_code)
                                    if tts_available:
                                        st.write(f"**🔊 Listen in {selected_language}:**")
                                        audio_translated = text_to_speech(score_text_translated, language_code, slow=slow_mode)
                                        if audio_translated:
                                            st.audio(audio_translated, format="audio/mp3")
                                except Exception as e:
                                    print(f"Translation/TTS error: {e}")
                            
                            if match['url']:
                                st.markdown(f"[📰 Read Full Article]({match['url']})")
                        else:
                            st.info("🏏 No cricket scores found in recent articles. Check news articles below.")
                    except Exception as e:
                        print(f"Cricket extraction error: {e}")
                
                st.markdown("---")
            
            # ===== NEWS ARTICLES =====
            st.markdown("## 📰 News Articles")
            st.markdown(f"<div class='success-box'>✅ Found {len(articles)} articles for '{query}'</div>", unsafe_allow_html=True)
            st.markdown("---")

            tts_available = is_language_supported(language_code)
            if not tts_available:
                st.info(f"📝 Text-only mode: Voice narration not available for {selected_language}")

            for idx, article in enumerate(articles, 1):
                try:
                    formatted_article = format_article(article)
                    article_content = get_article_content(formatted_article)
                    article_title = formatted_article.get('title') or "No Title"

                    with st.expander(f"📄 Article {idx}: {article_title[:80]}...", expanded=(idx == 1)):
                        st.subheader(article_title)

                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.caption(f"📰 {formatted_article.get('source', 'Unknown')[:50]}")
                        with c2:
                            st.caption(f"📅 {formatted_article.get('published_at', 'N/A')}")
                        with c3:
                            st.caption(f"✍️ {formatted_article.get('author', 'Unknown')[:30]}")

                        st.markdown("---")

                        try:
                            if use_ai_summary:
                                with st.spinner(f"🤖 Creating {duration_mode.lower()} summary..."):
                                    summary = get_ai_summary(article_content, language_code, client, duration_key)
                                st.write("**📝 Summary (Simplified for You):**")
                                st.info(summary)
                                audio_content = summary
                            else:
                                st.write("**📝 Article Content:**")
                                st.write(article_content)
                                audio_content = article_content

                            st.markdown("---")

                            if language_code != "en":
                                with st.spinner(f"🌐 Translating to {selected_language}..."):
                                    audio_content = translate_to_language(audio_content, language_code, client)
                                st.write(f"**🗣️ Content in {selected_language}:**")
                                st.success(audio_content)
                                st.markdown("---")

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
                                st.info("📝 Voice narration not available for this language")
                                article_url = formatted_article.get('url') or "#"
                                if article_url != "#":
                                    st.markdown(f"[🔗 Read Full Article]({article_url})")
                        
                        except Exception as e:
                            print(f"Article processing error: {e}")
                            st.warning("⚠️ Unable to process this article")

                        st.markdown("---")
                
                except Exception as e:
                    print(f"Error displaying article {idx}: {e}")

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
    st.caption("🏏 Live Cricket Scores")

st.caption("---")
st.caption("""
✨ Akashvani v1.4 from CX Data & Analytics LLC
🗣️ 12 Indian languages · 1–3 min audio briefs · 🏏 Live cricket scores (SerpAPI)
🔄 Dual API: NewsAPI + GNews (200 requests/day total)
⚡ Optimized: GPT-3.5-turbo with smart caching
📊 Analytics: PostgreSQL insert-only tracking
🏗️ Streamlit + OpenAI + gTTS + NewsAPI + GNews + SerpAPI + PostgreSQL
❤️  Crafted with accessibility in mind
📧 Support: support@cxloop.co
""")

st.markdown("---")
col1, col2, col3 = st.columns([0.3, 0.4, 0.3])
with col1:
    with st.expander("📋 Privacy Policy"):
        try:
            with open("privacy-policy.md", "r") as f:
                st.markdown(f.read())
        except FileNotFoundError:
            st.error("Privacy policy file not found.")