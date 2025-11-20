# app.py
"""
akashvani - Senior-Friendly News-to-Speech Application
Listen to news in 12 Indian languages with AI summaries
Project: akashvani | Version 1.0 | 2025-11-20 13:30:43 UTC
Fixed for OpenAI v1.0+ API, safe null handling, gTTS language support, and 2-3 min speech mode
Author: CX Data & Analytics
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
from utils.news_fetcher import get_top_news, format_article, get_article_content
from utils.translator import translate_to_language, get_ai_summary
from utils.tts_handler import text_to_speech, get_speech_speed_display, is_language_supported

# ===== LOAD SECRETS & INITIALIZE OPENAI CLIENT =====
try:
    # Access nested secrets format
    openai_api_key = st.secrets["openai"]["api_key"]
    news_api_key = st.secrets["newsapi"]["api_key"]
    
    # Initialize OpenAI client (NEW v1.0+ API)
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
    page_title="akashvani - Senior News Reader",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "akashvani: News-to-Speech App for Senior Citizens | 12 Indian Languages | Version 1.0 | Author: shotapentaho"
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
    
    h1, h2, h3 { color: #1F77B4; font-weight: 700; }
    
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
    </style>
    """, unsafe_allow_html=True)

# ===== SESSION STATE =====
if 'last_language' not in st.session_state:
    st.session_state.last_language = "English"
if 'last_duration' not in st.session_state:
    st.session_state.last_duration = "standard"

# ===== HEADER =====
col1, col2 = st.columns([4, 1])
with col1:
    st.title("📻 akashvani")
    st.markdown("### Hear News in Your Language")
with col2:
    st.markdown("### 🇮🇳 भारत")

st.markdown("**News from Indian and International Sources**")
st.markdown("---")

# ===== SIDEBAR SETTINGS =====
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.markdown("### 🗣️ Language & Speech")
    selected_language = st.selectbox(
        "Select Language:",
        get_all_languages(),
        index=0,
        help="Choose your preferred language for news reading"
    )
    
    language_code = INDIAN_LANGUAGES[selected_language]
    lang_info = get_language_info(language_code)
    
    # Display language info
    if lang_info:
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"Native: {lang_info.get('native', 'N/A')}")
        with col2:
            st.caption(f"Speakers: {lang_info.get('speakers', 'N/A')}")
        
        # Show TTS support status
        tts_status = "✅ Voice Available" if lang_info.get('tts_supported', False) else "📝 Text Only"
        st.caption(f"Status: {tts_status}")
    
    st.markdown("---")
    
    # Speech Speed
    st.markdown("### 🎤 Speech Options")
    speech_speed = st.radio(
        "Speech Speed:",
        ["Normal ⚡", "Slow 🐢"],
        index=1,
        help="Slow is recommended for seniors (easier to follow)"
    )
    
    # Speech Duration (NEW!)
    st.markdown("### ⏱️ Speech Duration")
    duration_mode = st.radio(
        "How long should the speech be?",
        ["Short (1 min)", "Standard (2 min)", "Long (3 min)"],
        index=1,
        help="Longer summaries = more detailed news coverage"
    )
    
    # Display duration info with updated targets
    duration_info_map = {
        "Short (1 min)": "📝 150 words - Quick briefing",
        "Standard (2 min)": "📝 300 words - Recommended",
        "Long (3 min)": "📝 450 words - Deep dive"
    }
    st.markdown(f"<div class='duration-info'>{duration_info_map.get(duration_mode, '')}</div>", unsafe_allow_html=True)
    
    # Convert duration_mode to duration_key
    duration_map = {
        "Short (1 min)": "short",
        "Standard (2 min)": "standard",
        "Long (3 min)": "long"
    }
    duration_key = duration_map.get(duration_mode, "standard")
    
    # AI Summary
    use_ai_summary = st.checkbox(
        "✓ AI Summary (Senior-Friendly)",
        value=True,
        help="AI will simplify complex news into easy-to-understand language"
    )
    
    st.markdown("---")
    
    # Number of articles
    st.markdown("### 📊 Results")
    results_count = st.slider(
        "Number of Articles:",
        1, 10, 5,
        help="How many news articles to fetch"
    )
    
    st.markdown("---")
    st.markdown("### 💡 Tips for Best Experience")
    st.caption("✓ Use 'Slow' speech speed for clarity")
    st.caption("✓ Use 'Long' duration for detailed news")
    st.caption("✓ Enable AI Summary for easy understanding")
    st.caption("✓ Use headphones for better sound")
    st.caption("✓ Increase device volume appropriately")
    
    st.markdown("---")
    st.markdown("### ℹ️ About akashvani")
    st.caption("📻 Senior-friendly news reader")
    st.caption("🌍 12 Indian languages")
    st.caption("🤖 AI-powered summaries")
    st.caption("🔊 Natural speech output")
    st.caption("© 2025 CX Data & Analytics LLC")

# ===== MAIN QUERY INPUT =====
st.header("🔍 Search for News")

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    query = st.text_input(
        "What news are you interested in?",
        placeholder="e.g., Elections, Stock Market, Cricket, Health, Weather, Technology...",
        help="Type a topic you want to read about"
    )

with col2:
    search_button = st.button("🔍 Search", key="search_btn", use_container_width=True)

with col3:
    help_button = st.button("❓ Help", key="help_btn", use_container_width=True)

if help_button:
    with st.expander("📖 How to Use akashvani", expanded=True):
        st.markdown("""
        **akashvani** is a news reader designed for senior citizens to listen to news in their preferred language.
        
        ### **Step-by-Step Guide:**
        
        **Step 1:** Choose your preferred language from the left menu  
        **Step 2:** Select speech speed (Slow 🐢 recommended for clarity)  
        **Step 3:** Select speech duration (how long you want to listen)  
        **Step 4:** Optionally enable AI Summary for simpler explanations  
        **Step 5:** Type a news topic you're interested in  
        **Step 6:** Click 'Search' button to fetch articles  
        **Step 7:** Click on any article to expand and read  
        **Step 8:** Listen to the article in your language by clicking play  
        
        ### **💡 Tips for Best Experience:**
        - 🐢 Use **Slow** speech speed for better understanding
        - ⏱️ Use **Long** duration (3 min) for detailed news
        - ✅ Enable **AI Summary** for simpler language
        - 🔉 Use **headphones** for better sound quality
        - 📱 Increase **device volume** to comfortable level
        - 🔊 Play in **quiet environment** for best listening
        
        ### **🌍 Supported Languages:**
        English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Urdu, Odia
        
        ### **📝 Note:**
        Some languages have text-only mode (no audio). Select a language with voice support for audio narration.
        """)

# ===== PROCESS AND DISPLAY =====
if search_button:
    if not query or len(query.strip()) < 2:
        st.warning("⚠️ Please enter a valid news topic (at least 2 characters).")
    else:
        # Show loading message
        with st.spinner(f"📡 Fetching news in {selected_language}..."):
            articles = get_top_news(query, news_api_key, top_k=results_count)
        
        if not articles:
            st.error("❌ No news found for your query. Try a different topic!")
            st.info("""
            💡 **Try searching for popular topics:**
            - Elections, Sports, Cricket, Football
            - Business, Stock Market, Technology
            - Weather, Health, Science
            - India, India news, Breaking news
            """)
        else:
            st.markdown(f"<div class='success-box'>✅ Found {len(articles)} articles for '{query}'</div>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Check if TTS is supported for selected language
            tts_available = is_language_supported(language_code)
            
            if not tts_available:
                st.info(f"📝 **Text-only mode:** Voice narration is not available for {selected_language}. You can read the summaries below.")
            
            # Display each article
            for idx, article in enumerate(articles, 1):
                formatted_article = format_article(article)
                article_content = get_article_content(formatted_article)
                
                # Safely get title for expander
                article_title = formatted_article.get('title') or "No Title"
                
                # Article expander
                with st.expander(
                    f"📄 Article {idx}: {article_title[:65]}...",
                    expanded=(idx == 1)
                ):
                    # Article Title
                    st.subheader(article_title)
                    
                    # Source, Date, Author Info - WITH SAFE NULL HANDLING
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        source = formatted_article.get('source') or "Unknown Source"
                        st.caption(f"📰 {source[:50]}")
                    with col2:
                        published = formatted_article.get('published_at') or "N/A"
                        st.caption(f"📅 {published}")
                    with col3:
                        author = formatted_article.get('author') or "Unknown Author"
                        st.caption(f"✍️ {author[:30]}")
                    
                    st.markdown("---")
                    
                    # Get AI Summary and prepare content
                    if use_ai_summary:
                        with st.spinner(f"🤖 Creating {duration_mode.lower()} summary in {selected_language}..."):
                            # Pass client AND duration_key to translator function
                            summary = get_ai_summary(article_content, language_code, client, duration_key)
                        
                        st.write("**📝 Summary (Simplified for You):**")
                        st.info(summary)
                        audio_content = summary
                    else:
                        st.write("**📝 Article Content:**")
                        st.write(article_content)
                        audio_content = article_content
                    
                    st.markdown("---")
                    
                    # Translate if not English
                    if language_code != "en":
                        with st.spinner(f"🌐 Translating to {selected_language}..."):
                            # Pass client to translator function
                            audio_content = translate_to_language(audio_content, language_code, client)
                        
                        st.write(f"**🗣️ Content in {selected_language}:**")
                        st.success(audio_content)
                        st.markdown("---")
                    
                    # Text-to-Speech Section - ONLY IF TTS IS SUPPORTED
                    if tts_available:
                        st.write(f"**🔊 Listen to this article in {selected_language}:**")
                        
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            slow_mode = speech_speed == "Slow 🐢"
                            audio = text_to_speech(audio_content, language_code, slow=slow_mode)
                            
                            if audio:
                                st.audio(audio, format="audio/mp3")
                            # If audio is None, the error message is already shown in text_to_speech function
                        
                        with col2:
                            st.caption(f"Speed: {get_speech_speed_display(slow_mode)}")
                        
                        with col3:
                            article_url = formatted_article.get('url') or "#"
                            if article_url != "#":
                                st.caption(f"[🔗 Source]({article_url})")
                    else:
                        st.info("📝 Voice narration is not available for this language. Please read the text above.")
                        article_url = formatted_article.get('url') or "#"
                        if article_url != "#":
                            st.markdown(f"[🔗 Read Full Article on Source Website]({article_url})")
                    
                    st.markdown("---")
                    
                    # Link to Full Article
                    article_url = formatted_article.get('url') or "#"
                    if article_url != "#":
                        st.markdown(f"**[🔗 Read Full Article on Source Website]({article_url})**")

# ===== FOOTER =====
st.markdown("---")
footer_col1, footer_col2, footer_col3, footer_col4 = st.columns(4)

with footer_col1:
    st.caption("📱 Senior-Friendly")
with footer_col2:
    st.caption("🌍 12 Languages")
with footer_col3:
    st.caption("🤖 AI-Powered")
with footer_col4:
    st.caption("🔊 Voice Available")

st.caption("---")
st.caption("""
✨ **akashvani v1.0** | 12 Indian Languages | 1-3 Min Speech Duration  
🏗️ Built with Streamlit, OpenAI, gTTS & NewsAPI  
📅 Updated: 2025-11-20 13:30:43 UTC  
❤️ Built with love for accessibility | 🔗 Live: https://akashvani.cxloop.co
""")