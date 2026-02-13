"""
Admin Panel for Akashvani v1.4
Combined Diagnostics & Dashboard with Password Protection
Access: https://akashvani.cxloop.co/🔐_Admin
"""

import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="🔐 Admin Panel - Akashvani",
    page_icon="🔐",
    layout="wide",
)

# ===== PASSWORD PROTECTION =====
def check_password():
    """Returns True if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["admin_password"] == st.secrets.get("admin", {}).get("password", "admin123"):
            st.session_state["password_correct"] = True
            del st.session_state["admin_password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.markdown("### 🔐 Admin Access Required")
        st.text_input(
            "Enter Admin Password", 
            type="password", 
            on_change=password_entered, 
            key="admin_password",
            placeholder="Enter password..."
        )
        st.caption("⚠️ This area is restricted to administrators only")
        st.info("💡 **Hint:** Check `.streamlit/secrets.toml` for the admin password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.markdown("### 🔐 Admin Access Required")
        st.text_input(
            "Enter Admin Password", 
            type="password", 
            on_change=password_entered, 
            key="admin_password",
            placeholder="Enter password..."
        )
        st.error("❌ Incorrect password. Access denied.")
        return False
    else:
        # Password correct
        return True

if not check_password():
    st.stop()

# ===== LOGGED IN - SHOW ADMIN PANEL =====

# Header with logout button
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("🔐 Akashvani Admin Panel")
    st.markdown("**System Diagnostics & Analytics Dashboard**")
with header_col2:
    st.markdown("")
    st.markdown("")
    if st.button("🔓 Logout", type="primary", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

st.markdown("---")

# ===== TABS =====
tab1, tab2 = st.tabs(["🔍 System Diagnostics", "📊 Analytics Dashboard"])

# ===== TAB 1: DIAGNOSTICS =====
with tab1:
    st.header("🔍 System Diagnostics")
    st.markdown("Comprehensive system health check and troubleshooting")
    st.markdown("---")
    
    # Clear proxy vars
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy', 'ALL_PROXY', 'all_proxy']
    for var in proxy_vars:
        os.environ.pop(var, None)
    
    diagnostics = []
    
    # ===== 1. CHECK API KEYS =====
    st.markdown("### 1️⃣ Checking API Keys...")
    
    try:
        openai_key = st.secrets["openai"]["api_key"]
        diagnostics.append(("✅", "OpenAI API key", f"{openai_key[:10]}...{openai_key[-4:]}"))
        st.success(f"✅ OpenAI API key: `{openai_key[:10]}...{openai_key[-4:]}`")
    except Exception as e:
        diagnostics.append(("❌", "OpenAI API key", str(e)))
        st.error(f"❌ OpenAI API key: `{e}`")
    
    try:
        news_key = st.secrets["newsapi"]["api_key"]
        diagnostics.append(("✅", "NewsAPI key", f"{news_key[:10]}...{news_key[-4:]}"))
        st.success(f"✅ NewsAPI key: `{news_key[:10]}...{news_key[-4:]}`")
    except Exception as e:
        diagnostics.append(("❌", "NewsAPI key", str(e)))
        st.error(f"❌ NewsAPI key: `{e}`")
    
    try:
        gnews_key = st.secrets.get("gnewsapi", {}).get("api_key")
        if gnews_key:
            diagnostics.append(("✅", "GNews API key", f"{gnews_key[:10]}...{gnews_key[-4:]}"))
            st.success(f"✅ GNews API key: `{gnews_key[:10]}...{gnews_key[-4:]}`")
        else:
            diagnostics.append(("⚠️", "GNews API key", "Not configured (optional)"))
            st.info("⚠️ GNews API key: Not configured (optional)")
    except Exception as e:
        diagnostics.append(("⚠️", "GNews API key", str(e)))
        st.warning(f"⚠️ GNews API key: `{e}`")
    
    try:
        serpapi_key = st.secrets.get("serpapi", {}).get("api_key")
        if serpapi_key:
            diagnostics.append(("✅", "SerpAPI key", f"{serpapi_key[:10]}...{serpapi_key[-4:]}"))
            st.success(f"✅ SerpAPI key: `{serpapi_key[:10]}...{serpapi_key[-4:]}`")
        else:
            diagnostics.append(("⚠️", "SerpAPI key", "Not configured (optional)"))
            st.info("⚠️ SerpAPI key: Not configured (optional)")
    except Exception as e:
        diagnostics.append(("⚠️", "SerpAPI key", str(e)))
        st.warning(f"⚠️ SerpAPI key: `{e}`")
    
    st.markdown("---")
    
    # ===== 2. CHECK PYTHON PACKAGES =====
    st.markdown("### 2️⃣ Checking Python Packages...")
    
    try:
        import openai
        diagnostics.append(("✅", "OpenAI module", f"v{openai.__version__}"))
        st.success(f"✅ OpenAI: `v{openai.__version__}`")
        st.code(f"Location: {openai.__file__}", language="text")
    except Exception as e:
        diagnostics.append(("❌", "OpenAI module", str(e)))
        st.error(f"❌ OpenAI: `{e}`")
    
    try:
        import httpx
        diagnostics.append(("✅", "httpx", f"v{httpx.__version__}"))
        st.success(f"✅ httpx: `v{httpx.__version__}`")
    except Exception as e:
        diagnostics.append(("❌", "httpx", str(e)))
        st.error(f"❌ httpx: `{e}`")
    
    try:
        import streamlit
        diagnostics.append(("✅", "Streamlit", f"v{streamlit.__version__}"))
        st.success(f"✅ Streamlit: `v{streamlit.__version__}`")
    except Exception as e:
        diagnostics.append(("❌", "Streamlit", str(e)))
        st.error(f"❌ Streamlit: `{e}`")
    
    try:
        import gtts
        diagnostics.append(("✅", "gTTS", f"v{gtts.__version__}"))
        st.success(f"✅ gTTS: `v{gtts.__version__}`")
    except Exception as e:
        diagnostics.append(("❌", "gTTS", str(e)))
        st.error(f"❌ gTTS: `{e}`")
    
    try:
        import requests
        diagnostics.append(("✅", "requests", f"v{requests.__version__}"))
        st.success(f"✅ requests: `v{requests.__version__}`")
    except Exception as e:
        diagnostics.append(("❌", "requests", str(e)))
        st.error(f"❌ requests: `{e}`")
    
    st.markdown("---")
    
    # ===== 3. TEST OPENAI CLIENT =====
    st.markdown("### 3��⃣ Testing OpenAI Client...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        diagnostics.append(("✅", "OpenAI client", type(client).__name__))
        st.success(f"✅ Client created: `{type(client).__name__}`")
        
    except TypeError as e:
        diagnostics.append(("❌", "OpenAI client TypeError", str(e)))
        st.error(f"❌ **TypeError:** `{e}`")
        
        st.markdown("---")
        st.error("**Root Cause:** httpx version incompatibility")
        st.markdown("### 🔧 Fix:")
        st.code("""
cd ~/akashvani
source venv/bin/activate
pip uninstall -y openai httpx
pip install httpx==0.27.0
pip install openai==1.54.0
pkill -f streamlit
streamlit run app.py
        """, language="bash")
        
        with st.expander("🔍 Full Traceback"):
            import traceback
            st.code(traceback.format_exc())
        
    except Exception as e:
        diagnostics.append(("❌", "OpenAI client error", str(e)))
        st.error(f"❌ Error: `{e}`")
        with st.expander("🔍 Full Traceback"):
            import traceback
            st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # ===== 4. TEST API CONNECTION =====
    st.markdown("### 4️⃣ Testing OpenAI API Connection...")
    
    try:
        with st.spinner("Making test API call..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'test successful' in exactly 2 words"}],
                max_tokens=10
            )
            result = response.choices[0].message.content
            diagnostics.append(("✅", "API call", result))
            st.success(f"✅ API Response: `{result}`")
    except Exception as e:
        diagnostics.append(("⚠️", "API call failed", str(e)))
        st.warning(f"⚠️ API call failed: `{e}`")
        st.info("This usually means an invalid API key or network issue")
    
    st.markdown("---")
    
    # ===== 5. CHECK UTILS MODULES =====
    st.markdown("### 5️⃣ Checking Utils Modules...")
    
    modules = [
        ("config.languages", "INDIAN_LANGUAGES"),
        ("utils.translator", "translate_to_language"),
        ("utils.news_fetcher", "get_top_news"),
        ("utils.tts_handler", "text_to_speech"),
        ("utils.cricket_scraper", "extract_score_from_article"),
        ("utils.cricket_live", "get_live_cricket_scores"),
    ]
    
    for module_name, attr_name in modules:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            getattr(module, attr_name)
            diagnostics.append(("✅", module_name, "OK"))
            st.success(f"✅ `{module_name}`")
        except Exception as e:
            diagnostics.append(("❌", module_name, str(e)))
            st.error(f"❌ `{module_name}`: `{e}`")
    
    st.markdown("---")
    
    # ===== 6. CHECK DATABASE =====
    st.markdown("### 6️⃣ Checking Database Connection...")
    
    try:
        from utils.database import get_connection
        conn_test = get_connection()
        if conn_test:
            diagnostics.append(("✅", "PostgreSQL", "Connected"))
            st.success("✅ PostgreSQL: Connected")
            
            cursor = conn_test.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_calls")
            api_count = cursor.fetchone()[0]
            st.info(f"📊 Total API calls tracked: {api_count}")
            
            cursor.close()
            conn_test.close()
        else:
            diagnostics.append(("❌", "PostgreSQL", "Connection failed"))
            st.error("❌ PostgreSQL: Connection failed")
    except ImportError:
        diagnostics.append(("⚠️", "PostgreSQL", "Module not installed (optional)"))
        st.warning("⚠️ PostgreSQL: Module not installed (optional)")
    except Exception as e:
        diagnostics.append(("⚠️", "PostgreSQL", str(e)))
        st.warning(f"⚠️ PostgreSQL: `{e}`")
    
    st.markdown("---")
    
    # ===== SUMMARY =====
    st.markdown("## ✅ Diagnostics Complete!")
    
    st.markdown("### 📊 Summary:")
    
    summary_df = []
    for emoji, test, result in diagnostics:
        summary_df.append({"Status": emoji, "Test": test, "Result": result})
    
    df = pd.DataFrame(summary_df)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    total = len(diagnostics)
    success = sum(1 for d in diagnostics if d[0] == "✅")
    warnings = sum(1 for d in diagnostics if d[0] == "⚠️")
    errors = sum(1 for d in diagnostics if d[0] == "❌")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tests", total)
    with col2:
        st.metric("Passed", success)
    with col3:
        st.metric("Warnings", warnings)
    with col4:
        st.metric("Errors", errors)
    
    st.markdown("---")
    
    if errors > 0:
        st.error("⚠️ Some tests failed. Please review errors above.")
    elif warnings > 0:
        st.warning("⚠️ All critical tests passed, but some optional features are unavailable.")
    else:
        st.success("🎉 All tests passed! System is healthy.")

# ===== TAB 2: DASHBOARD =====
with tab2:
    st.header("📊 Analytics Dashboard")
    st.markdown("Real-time monitoring and usage statistics")
    st.markdown("---")
    
    # ===== CONNECT TO DATABASE =====
    try:
        from utils.database import get_connection
        
        conn = get_connection()
        DB_AVAILABLE = conn is not None
        
        if DB_AVAILABLE:
            st.success("✅ Database Connected")
        else:
            st.warning("⚠️ Database connection failed - showing limited data")
            DB_AVAILABLE = False
            
    except Exception as e:
        st.warning(f"⚠️ Database not available - showing limited data")
        print(f"Database error: {e}")
        DB_AVAILABLE = False
        conn = None
    
    # ===== API USAGE SECTION =====
    st.subheader("🔌 API Usage Monitor")
    
    if DB_AVAILABLE:
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM api_calls 
                WHERE api_name = 'newsapi' 
                  AND DATE(call_timestamp) = CURRENT_DATE
            """)
            newsapi_today = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM api_calls 
                WHERE api_name = 'gnews' 
                  AND DATE(call_timestamp) = CURRENT_DATE
            """)
            gnews_today = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM api_calls 
                WHERE api_name = 'serpapi' 
                  AND DATE(call_timestamp) = CURRENT_DATE
            """)
            serpapi_today = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM search_queries 
                WHERE DATE(call_timestamp) = CURRENT_DATE
            """)
            searches_today = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT session_id) 
                FROM search_queries 
                WHERE DATE(call_timestamp) = CURRENT_DATE
            """)
            users_today = cursor.fetchone()[0]
            
        except Exception as e:
            print(f"Query error: {e}")
            newsapi_today = 0
            gnews_today = 0
            serpapi_today = 0
            searches_today = 0
            users_today = 0
    else:
        newsapi_today = st.session_state.get('api_calls_today', 0)
        gnews_today = 0
        serpapi_today = 0
        searches_today = newsapi_today
        users_today = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        newsapi_remaining = max(0, 100 - newsapi_today)
        st.metric("NewsAPI", f"{newsapi_today}/100", f"{newsapi_remaining} left")
        
        if newsapi_remaining > 50:
            st.success("🟢 Healthy")
        elif newsapi_remaining > 10:
            st.warning("🟡 Medium")
        else:
            st.error("🔴 Critical")
        
    with col2:
        gnews_remaining = max(0, 100 - gnews_today)
        st.metric("GNews Backup", f"{gnews_today}/100", f"{gnews_remaining} left")
        
        if gnews_today == 0:
            st.info("⚪ Not Used")
        elif gnews_remaining > 50:
            st.success("🟢 Healthy")
        elif gnews_remaining > 10:
            st.warning("🟡 Medium")
        else:
            st.error("🔴 Critical")
    
    with col3:
        st.metric("SerpAPI (Cricket)", f"{serpapi_today}/100", f"{100 - serpapi_today} left")
        
        if serpapi_today == 0:
            st.info("⚪ Not Used")
        elif serpapi_today < 50:
            st.success("🟢 Healthy")
        elif serpapi_today < 80:
            st.warning("🟡 Medium")
        else:
            st.error("🔴 Critical")
    
    with col4:
        now_utc = datetime.utcnow()
        midnight_utc = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_until_reset = midnight_utc - now_utc
        hours_left = time_until_reset.seconds // 3600
        minutes_left = (time_until_reset.seconds % 3600) // 60
        st.metric("Quota Reset", f"{hours_left}h {minutes_left}m", "until midnight UTC")
        st.caption(f"🕐 UTC: {now_utc.strftime('%H:%M:%S')}")
    
    # Progress bars
    st.markdown("---")
    st.subheader("📈 API Quota Usage")
    
    col_progress1, col_progress2, col_progress3 = st.columns(3)
    
    with col_progress1:
        st.markdown("**NewsAPI (Primary)**")
        if newsapi_today <= 100:
            st.progress(newsapi_today / 100)
            st.caption(f"Used: {newsapi_today}/100 calls")
        else:
            st.progress(1.0)
            st.caption("⚠️ Quota exhausted")
    
    with col_progress2:
        st.markdown("**GNews (Backup)**")
        if gnews_today > 0:
            st.progress(min(gnews_today / 100, 1.0))
            st.caption(f"Used: {gnews_today}/100 calls")
        else:
            st.progress(0.0)
            st.caption("🟢 Ready as backup")
    
    with col_progress3:
        st.markdown("**SerpAPI (Cricket)**")
        if serpapi_today > 0:
            st.progress(min(serpapi_today / 100, 1.0))
            st.caption(f"Used: {serpapi_today}/100 calls")
        else:
            st.progress(0.0)
            st.caption("🟢 Ready for cricket")
    
    # ===== REAL-TIME ANALYTICS =====
    st.markdown("---")
    st.subheader("📊 Real-Time Analytics")
    
    analytics_col1, analytics_col2, analytics_col3, analytics_col4 = st.columns(4)
    
    with analytics_col1:
        st.metric("🔍 Searches Today", searches_today)
    
    with analytics_col2:
        st.metric("👥 Unique Users", users_today)
    
    with analytics_col3:
        if DB_AVAILABLE:
            try:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM search_queries 
                    WHERE DATE(call_timestamp) = CURRENT_DATE - INTERVAL '1 day'
                """)
                yesterday_searches = cursor.fetchone()[0]
                delta = searches_today - yesterday_searches
                st.metric("📈 vs Yesterday", f"{delta:+d}", f"{searches_today} today")
            except:
                st.metric("📈 vs Yesterday", "N/A")
        else:
            st.metric("📈 vs Yesterday", "N/A")
    
    with analytics_col4:
        total_api_calls = newsapi_today + gnews_today + serpapi_today
        if searches_today > 0:
            success_rate = (total_api_calls / searches_today) * 100
            st.metric("✅ Success Rate", f"{success_rate:.1f}%")
        else:
            st.metric("✅ Success Rate", "N/A")
    
    # ===== POPULAR SEARCHES =====
    st.markdown("---")
    st.subheader("🔥 Popular Searches (Last 24 Hours)")
    
    if DB_AVAILABLE:
        try:
            cursor.execute("""
                SELECT 
                    query_text, 
                    COUNT(*) as count,
                    MAX(call_timestamp) as last_search
                FROM search_queries
                WHERE call_timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY query_text
                ORDER BY count DESC
                LIMIT 10
            """)
            
            popular_searches = cursor.fetchall()
            
            if popular_searches:
                search_df = pd.DataFrame(
                    popular_searches,
                    columns=['Query', 'Count', 'Last Searched']
                )
                st.dataframe(search_df, use_container_width=True, hide_index=True)
            else:
                st.info("No searches yet today")
                
        except Exception as e:
            print(f"Popular searches error: {e}")
            st.info("Unable to load popular searches")
    else:
        st.info("Database connection required for this feature")
    
    # ===== LANGUAGE DISTRIBUTION =====
    st.markdown("---")
    st.subheader("🌍 Language Distribution (Today)")
    
    if DB_AVAILABLE:
        try:
            cursor.execute("""
                SELECT 
                    language_code,
                    COUNT(*) as count
                FROM search_queries
                WHERE DATE(call_timestamp) = CURRENT_DATE
                GROUP BY language_code
                ORDER BY count DESC
            """)
            
            lang_data = cursor.fetchall()
            
            if lang_data:
                lang_df = pd.DataFrame(lang_data, columns=['Language', 'Searches'])
                
                col_chart, col_table = st.columns([2, 1])
                
                with col_chart:
                    st.bar_chart(lang_df.set_index('Language'))
                
                with col_table:
                    st.dataframe(lang_df, use_container_width=True, hide_index=True)
            else:
                st.info("No data yet today")
                
        except Exception as e:
            print(f"Language distribution error: {e}")
            st.info("Unable to load language data")
    else:
        st.info("Database connection required for this feature")
    
    # ===== RECENT API CALLS =====
    st.markdown("---")
    st.subheader("🔄 Recent API Calls (Last 50)")
    
    if DB_AVAILABLE:
        try:
            cursor.execute("""
                SELECT 
                    api_name,
                    query_text,
                    response_status,
                    articles_count,
                    call_timestamp
                FROM api_calls
                ORDER BY call_timestamp DESC
                LIMIT 50
            """)
            
            api_calls = cursor.fetchall()
            if api_calls:
                df_api = pd.DataFrame(api_calls, columns=['API', 'Query', 'Status', 'Articles', 'Timestamp'])
                st.dataframe(df_api, use_container_width=True, height=300, hide_index=True)
            else:
                st.info("No API calls recorded yet")
        except Exception as e:
            print(f"Recent API calls error: {e}")
            st.info("Unable to load recent API calls")
    else:
        st.info("Database connection required for this feature")
    
    # ===== QUICK ACTIONS =====
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("🔄 Refresh Data", type="secondary", use_container_width=True, key="refresh_btn"):
            st.rerun()
    
    with action_col2:
        if st.button("📋 Export Report", type="secondary", use_container_width=True, key="export_btn"):
            total_api_calls = newsapi_today + gnews_today + serpapi_today
            success_rate = ((total_api_calls) / max(searches_today, 1)) * 100
            
            report = f"""
Akashvani API Usage Report
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

API Usage Today:
- NewsAPI: {newsapi_today}/100
- GNews: {gnews_today}/100
- SerpAPI: {serpapi_today}/100
- Total: {total_api_calls}

Analytics:
- Searches Today: {searches_today}
- Unique Users: {users_today}
- Success Rate: {success_rate:.1f}%

Database: {"Connected" if DB_AVAILABLE else "Disconnected"}
            """
            st.download_button(
                label="⬇️ Download Report",
                data=report,
                file_name=f"akashvani_report_{date.today()}.txt",
                mime="text/plain",
                key="download_report"
            )
    
    with action_col3:
        if st.button("🗑️ Clear Cache", type="secondary", use_container_width=True, key="clear_cache_btn"):
            st.cache_data.clear()
            st.success("✅ Cache cleared")
    
    # ===== ALERTS =====
    st.markdown("---")
    st.subheader("🔔 Alerts & Notifications")
    
    newsapi_remaining = 100 - newsapi_today
    gnews_remaining = 100 - gnews_today
    serpapi_remaining = 100 - serpapi_today
    
    alerts = []
    
    if newsapi_remaining < 20:
        alerts.append(("warning", f"⚠️ **Low NewsAPI Quota**: Only {newsapi_remaining} calls remaining"))
    
    if gnews_today > 80:
        alerts.append(("error", "🚨 **Critical**: GNews backup quota almost exhausted!"))
    
    if serpapi_today > 80:
        alerts.append(("warning", f"⚠️ **High SerpAPI Usage**: {serpapi_today}/100 calls used"))
    
    if not DB_AVAILABLE:
        alerts.append(("warning", "⚠️ **Database Disconnected**: Analytics features limited."))
    
    if len(alerts) == 0:
        st.success("✅ All systems normal. No alerts.")
    else:
        for alert_type, message in alerts:
            if alert_type == "error":
                st.error(message)
            elif alert_type == "warning":
                st.warning(message)
            else:
                st.info(message)
    
    # Close database connection
    if DB_AVAILABLE and conn:
        try:
            conn.close()
        except:
            pass

# ===== FOOTER =====
st.markdown("---")
footer_col1, footer_col2 = st.columns(2)

with footer_col1:
    st.caption("🔒 Admin Panel | Akashvani v1.4")
    st.caption("© 2026 CX Data & Analytics LLC")
    st.caption("📧 Support: support@cxloop.co")

with footer_col2:
    st.caption(f"👤 Logged in as: Admin")
    st.caption(f"🕐 Session: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")