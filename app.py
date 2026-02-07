# app.py
"""
akashvani - Senior-Friendly News-to-Speech Application
Single-page layout: language select centered in header row; tips top-right (left-aligned)
AI Summary checkbox on same row as Articles (after Articles)
Indian flag next to app title
CRICKET SCORES: Extracted from news articles (reliable, no scraping errors)
Project: akashvani | Version 1.2 | 2026-02-07
Author: shotapentaho
Live Demo: https://akashvani.cxloop.co
"""

import streamlit as st
import openai
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
    openai_api_key = st.secrets["openai"]["api_key"]
    news_api_key = st.secrets["newsapi"]["api_key"]

    client = openai.OpenAI(api_key=openai_api_key)

    if not news_api_key or not openai_api_key:
        st.error("❌ Missing API keys in .streamlit/secrets.toml")
        st.stop()
except KeyError as e:
    st.error(f"❌ Secrets configuration error: {e}. Make sure your secrets.toml has [openai] and [newsapi] sections.")
    st.stop()
except Exception as e:
    st.error(f"❌ Error loading secrets: {e}")
    st.stop()

# ===== PAGE CONFIG =====

st.set_page_config(
    page_title="akashvani 📻 - Senior News Reader",
    page_icon="https://akashvani.cxloop.co/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "akashvani: News-to-Speech App for Senior Citizens | 12 Indian Languages | Version 1.2"
    }
)

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

# ===== HEADER (language select centered, tips top-right left-aligned) =====
left_col, center_col, right_col = st.columns([2, 1, 2])

with left_col:
    st.markdown("## 📻 akashvani 🇮🇳")
    st.markdown("### News spoken in your language")
    st.markdown("**News from Indian and International Trusted Sources**")

with center_col:
    st.markdown("")  # spacer for alignment
    selected_language = st.selectbox(
        "",  # empty label for compactness
        get_all_languages(),
        index=0,
        key="header_language_select",
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
        # ===== FETCH NEWS FIRST =====
        with st.spinner(f"📡 Fetching news for '{query}'..."):
            articles = get_top_news(query, news_api_key, top_k=results_count)

        if not articles:
            st.error("❌ No news found for your query. Try a different topic!")
            st.info("Try: Elections, Sports, Business, Weather, Health, Technology, India, Cricket")
        else:
            # 🏏 CRICKET SCORE EXTRACTION (if cricket query)
            if _is_cricket_score_query(query):
                st.markdown("---")
                st.markdown("### 🏏 Cricket Scores from Latest News")
                
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
                    
                    # Translate if needed
                    if language_code != "en":
                        with st.spinner(f"🌐 Translating to {selected_language}..."):
                            score_text_translated = translate_to_language(score_text, language_code, client)
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
                    
                    if match['url']:
                        st.markdown(f"[📰 Read Full Article]({match['url']})")
                    
                    st.markdown("---")
                else:
                    st.info("🏏 No cricket scores found in recent articles. Check news articles below for latest cricket updates.")
            
            # ===== NEWS ARTICLES SECTION =====
            st.markdown("## 📰 News Articles")
            st.markdown(f"<div class='success-box'>✅ Found {len(articles)} articles for '{query}'</div>", unsafe_allow_html=True)
            st.markdown("---")

            tts_available = is_language_supported(language_code)
            if not tts_available:
                st.info(f"📝 Text-only mode: Voice narration not available for {selected_language} ({language_code}).")

            for idx, article in enumerate(articles, 1):
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

                    # Create summary
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

                    # Translate if needed
                    if language_code != "en":
                        with st.spinner(f"🌐 Translating to {selected_language}..."):
                            audio_content = translate_to_language(audio_content, language_code, client)
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

                    st.markdown("---")

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
✨ Akashvani v1.2 from CX Data & Analytics LLC
🗣️ 12 Indian languages · 1–3 min audio briefs · 🏏 Cricket scores from news
🏗️ Streamlit + OpenAI + gTTS + NewsAPI
❤️  Crafted with accessibility in mind, delivering trusted news from reputable sources worldwide.
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
