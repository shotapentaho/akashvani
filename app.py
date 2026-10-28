"""
akashvani - Senior-Friendly News-to-Speech Application
Version: 1.4 | 2026-02-13
"""

import os
import uuid

import streamlit as st

from footer import render_footer
from views.movies import render_movie_reviews
from views.news import render_news
from views.songs import render_songs
from views.weather import render_weather


# ===== CRITICAL: Clear proxy environment variables FIRST =====
proxy_vars = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "NO_PROXY",
    "no_proxy",
    "ALL_PROXY",
    "all_proxy",
]

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
        "About": (
            "akashvani: News-to-Speech App for Senior Citizens | "
            "12 Indian Languages | Version 1.4"
        )
    },
)


from config.languages import (
    INDIAN_LANGUAGES,
    get_all_languages,
    get_language_info,
)
from utils.tts_handler import VOICE_OPTIONS
from utils.weather_fetcher import extract_weather_location
from utils.auto_search import (
    DEBOUNCE_MS,
    query_fingerprint,
    should_auto_run,
)
from utils.song_fetcher import is_song_query
from utils.movie_fetcher import is_movie_query


try:
    from st_keyup import st_keyup
except ImportError:
    # Fallback: plain text input (submit with Enter or blur).
    st_keyup = None


# ===== DATABASE TRACKING =====
DB_TRACKING_ENABLED = False
track_api_call = None
track_search_query = None

try:
    from utils.database import (
        get_supported_languages,
        track_api_call,
        track_search_query,
        track_user_session,
    )

    DB_TRACKING_ENABLED = True
    print("✅ DATABASE TRACKING ENABLED")

except Exception:
    print("⚠️ DATABASE TRACKING DISABLED")
    get_supported_languages = None


def record_api_call(
    api_name: str,
    query_text: str,
    response_status: str,
    articles_count: int = 0,
):
    if track_api_call is None:
        print(
            "❌ API tracking unavailable: database tracking module "
            "could not be loaded"
        )
        return
    track_api_call(api_name, query_text, response_status, articles_count)


# ===== HIDE DEFAULT STREAMLIT ELEMENTS =====
hide_default_header = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""

st.markdown(hide_default_header, unsafe_allow_html=True)


# ===== LOAD SECRETS =====
try:
    openai_api_key = st.secrets["openai"]["api_key"]
    news_api_key = st.secrets["newsapi"]["api_key"]
    gnews_api_key = st.secrets.get("gnewsapi", {}).get("api_key")
    serpapi_key = st.secrets.get("serpapi", {}).get("api_key")
    gemini_api_key = (
        st.secrets.get("gemini", {}).get("api_key")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )

    SERPAPI_ENABLED = bool(serpapi_key)

    if not news_api_key or not openai_api_key:
        raise ValueError("Required API keys are empty")

    from openai import OpenAI

    client = OpenAI(
        api_key=openai_api_key,
        timeout=30.0,
        max_retries=2,
    )

    print("✅ All systems ready")

except Exception as e:
    print(f"❌ Startup failed: {e}")
    st.error("⚠️ Service temporarily unavailable")
    st.info("📧 Please contact **support@cxloop.co** for assistance")
    st.markdown("---")
    st.info(
        "🔧 **Admin:** Visit the 🔍 Diagnostics page in the sidebar "
        "for detailed troubleshooting"
    )
    st.stop()


# ===== CUSTOM CSS =====
st.markdown(
    """
    <style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    body {
        font-size: 18px;
        background-color: #f8f9fa;
    }

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

    h1, h2, h3 {
        color: #1F77B4;
        font-weight: 700;
    }

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
    """,
    unsafe_allow_html=True,
)


# ===== SESSION STATE =====
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "api_calls_today" not in st.session_state:
    st.session_state.api_calls_today = 0

if "last_reset_date" not in st.session_state:
    from datetime import date

    st.session_state.last_reset_date = date.today()

if "last_session_track" not in st.session_state:
    st.session_state.last_session_track = 0


# ===== RESET COUNTER DAILY =====
from datetime import date

if st.session_state.last_reset_date != date.today():
    st.session_state.api_calls_today = 0
    st.session_state.last_reset_date = date.today()


# ===== HEADER =====
left_col, center_col, right_col = st.columns([2, 1, 2])

with left_col:
    st.markdown("## 📻 akashvani 🇮🇳")
    st.markdown("### News, Weather, Cricket and more: Spoken in your language")
    st.markdown("**News from Indian and International Trusted Sources**")


with center_col:
    st.markdown("")

    language_rows = (
        get_supported_languages() if get_supported_languages else []
    )
    if language_rows:
        language_options = [
            f"{language} ({tts_language})"
            for language, tts_language in language_rows
        ]
        language_codes = {
            f"{language} ({tts_language})": INDIAN_LANGUAGES.get(
                language,
                "en",
            )
            for language, tts_language in language_rows
        }
    else:
        language_options = get_all_languages()
        language_codes = INDIAN_LANGUAGES

    selected_language = st.selectbox(
        "Select Language",
        language_options,
        index=0,
        key="header_language_select",
        label_visibility="collapsed",
        help="Choose your preferred language for news reading",
    )


with right_col:
    st.markdown("")


language_code = language_codes[selected_language]
lang_info = get_language_info(language_code)


# ===== TRACK USER SESSION =====
if DB_TRACKING_ENABLED:
    try:
        import time

        current_time = time.time()

        if current_time - st.session_state.last_session_track > 60:
            track_user_session(
                session_id=st.session_state.session_id,
                language_code=language_code,
                page_view="main",
            )

            st.session_state.last_session_track = current_time

    except Exception as e:
        print(f"Session tracking error: {e}")


st.markdown("---")


# ===== SETTINGS =====
with st.container():
    col_speed, col_voice, col_duration, col_articles, col_ai = st.columns(
         [.5, .5, 1.2, 1, 1]
    )

    with col_speed:
        speech_speed = st.radio(
            "Speed",
            ["Normal ⚡", "Slow 🐢"],
            index=1,
            help="Slow is recommended for seniors",
        )

    with col_voice:
        voice_selection = st.radio(
            "Voice",
            VOICE_OPTIONS,
            help="Choose a female or male Indian-accented voice.",
        )

    with col_duration:
        duration_mode = st.radio(
            "Duration",
            ["Short (1 min)", "Standard (2 min)", "Long (3 min)"],
            index=1,
            help="Longer summaries = more detailed news coverage",
        )

        duration_info_map = {
            "Short (1 min)": "150 words",
            "Standard (2 min)": "300 words",
            "Long (3 min)": "450 words",
        }

        st.caption(
            f"Target: {duration_info_map.get(duration_mode, '')}"
        )

        duration_map = {
            "Short (1 min)": "short",
            "Standard (2 min)": "standard",
            "Long (3 min)": "long",
        }

        duration_key = duration_map.get(duration_mode, "standard")

    with col_articles:
        results_count = st.slider("Articles", 1, 10, 5)

    with col_ai:
        use_ai_summary = st.checkbox(
            "✓ AI Summary (Senior-Friendly)",
            value=True,
        )


st.markdown("---")


# ===== SEARCH INPUT =====
with st.container():
    search_placeholder = (
        "e.g., Elections, Stock Market, Cricket, Health, Weather, "
        "Technology, India vs Australia..."
    )

    if st_keyup is not None:
        # st_keyup does not support help= or placeholder=.
        st.markdown("**Search topic**")
        query = st_keyup(
            "",
            debounce=DEBOUNCE_MS,
            key="search_query",
        ) or ""

        st.caption(
            "Type a topic and pause for 2 seconds. Results appear automatically. "
            "For weather, try: weather in Mumbai."
        )
        st.caption(
            "For News, try: News around the world. or News from India or News from a particular state"
        )
        st.caption(
            "For Live Cricket: Cricket Score or India vs Australia score. "
        )
        st.caption(
            "For movie reviews, try: movie review of Dune."
        )
        

    else:
        st.markdown("**Search topic**")
        query = st.text_input(
            "",
            placeholder=search_placeholder,
            help=(
                "Type a topic and pause for 2 seconds. Results appear automatically. "
                "For weather, try 'weather in Mumbai'."
            ),
        )

# ===== PROCESS AND DISPLAY =====
_fingerprint = query_fingerprint(
    query,
    language_code,
    results_count,
    duration_key,
    speech_speed,
    voice_selection,
    use_ai_summary,
)

auto_search = should_auto_run(
    query,
    _fingerprint,
    st.session_state.get("last_search_fingerprint"),
)

if auto_search:
    st.session_state.last_search_fingerprint = _fingerprint

weather_selection_active = (
    st.session_state.get("weather_selection_query") == query
)

if auto_search or weather_selection_active:
    if not query or len(query.strip()) < 2:
        st.warning(
            "⚠️ Please enter a valid news topic "
            "(at least 2 characters)."
        )

    # ===== WEATHER SEARCH =====
    elif extract_weather_location(query):
        render_weather(
            query, language_code, selected_language, speech_speed,
            voice_selection, client, record_api_call,
        )

    elif is_movie_query(query):
        render_movie_reviews(
            query,
            language_code,
            selected_language,
            speech_speed,
            voice_selection,
            client,
            SERPAPI_ENABLED,
            serpapi_key,
            results_count,
            record_api_call,
        )

    elif is_song_query(query):
        render_songs(
            query, SERPAPI_ENABLED, serpapi_key, results_count,
            DB_TRACKING_ENABLED, track_search_query, language_code,
            duration_key, st.session_state.session_id, record_api_call,
        )

    else:
        render_news(
            query, language_code, results_count, duration_key, duration_mode,
            speech_speed, voice_selection, use_ai_summary, selected_language,
            client, news_api_key, gnews_api_key, gemini_api_key, serpapi_key,
            SERPAPI_ENABLED, DB_TRACKING_ENABLED, st.session_state.session_id,
            track_search_query, record_api_call,
        )


render_footer()
