"""
System Diagnostics Module
Comprehensive health checks and troubleshooting
"""

import streamlit as st
import pandas as pd
import os
import sys

def show_diagnostics():
    """Display system diagnostics"""
    
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
    st.markdown("### 3️⃣ Testing OpenAI Client...")
    
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
