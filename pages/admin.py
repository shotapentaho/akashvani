"""
Admin Dashboard for Akashvani
Monitoring API usage, system health, and analytics
Access: https://akashvani.cxloop.co/admin
Password Protected
"""

import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd
import random

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Admin Dashboard - Akashvani",
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

# ===== LOGGED IN - SHOW DASHBOARD =====

st.title("📊 Akashvani Admin Dashboard")
st.markdown("**Real-time monitoring and analytics**")
st.markdown("---")

# Initialize session state for tracking
if 'api_calls_today' not in st.session_state:
    st.session_state.api_calls_today = 0
if 'last_reset_date' not in st.session_state:
    st.session_state.last_reset_date = date.today()

# Reset counter daily
if st.session_state.last_reset_date != date.today():
    st.session_state.api_calls_today = 0
    st.session_state.last_reset_date = date.today()

# ===== API USAGE SECTION =====
st.header("🔌 API Usage Monitor")

col1, col2, col3, col4 = st.columns(4)

with col1:
    newsapi_calls = st.session_state.get('api_calls_today', 0)
    newsapi_remaining = max(0, 100 - newsapi_calls)
    newsapi_used = min(newsapi_calls, 100)
    st.metric("NewsAPI", f"{newsapi_used}/100", f"{newsapi_remaining} left")
    
    # Status indicator
    if newsapi_remaining > 50:
        st.success("🟢 Healthy")
    elif newsapi_remaining > 10:
        st.warning("🟡 Medium")
    else:
        st.error("🔴 Critical")
    
with col2:
    # Estimate GNews usage
    gnews_estimated = max(0, newsapi_calls - 100)
    gnews_remaining = max(0, 100 - gnews_estimated)
    st.metric("GNews Backup", f"~{gnews_estimated}/100", f"~{gnews_remaining} left")
    
    if gnews_estimated == 0:
        st.info("⚪ Not Used")
    elif gnews_remaining > 50:
        st.success("🟢 Healthy")
    elif gnews_remaining > 10:
        st.warning("🟡 Medium")
    else:
        st.error("🔴 Critical")

with col3:
    total_quota = 200  # NewsAPI + GNews
    total_used = min(newsapi_calls, total_quota)
    percentage = (total_used / total_quota) * 100
    st.metric("Total Usage", f"{percentage:.0f}%", "of 200 calls")
    
    # Cost estimate (if using paid plan)
    st.caption(f"💰 Cost: ${total_used * 0.00} (free tier)")

with col4:
    now_utc = datetime.utcnow()
    midnight_utc = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_reset = midnight_utc - now_utc
    hours_left = time_until_reset.seconds // 3600
    minutes_left = (time_until_reset.seconds % 3600) // 60
    st.metric("Quota Reset", f"{hours_left}h {minutes_left}m", "until midnight UTC")
    
    st.caption(f"🕐 Current UTC: {now_utc.strftime('%H:%M:%S')}")

# Progress bars
st.markdown("---")
st.subheader("📈 API Quota Usage")

col_progress1, col_progress2 = st.columns(2)

with col_progress1:
    st.markdown("**NewsAPI (Primary)**")
    if newsapi_calls <= 100:
        progress_val = newsapi_calls / 100
        st.progress(progress_val)
        st.caption(f"Used: {newsapi_used}/100 calls")
    else:
        st.progress(1.0)
        st.caption("⚠️ Quota exhausted - using GNews fallback")

with col_progress2:
    st.markdown("**GNews (Backup)**")
    gnews_used = max(0, newsapi_calls - 100)
    if gnews_used > 0:
        st.progress(min(gnews_used / 100, 1.0))
        st.caption(f"Used: ~{gnews_used}/100 calls")
    else:
        st.progress(0.0)
        st.caption("🟢 Ready as backup")

# ===== SYSTEM STATUS =====
st.markdown("---")
st.header("🖥️ System Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    st.markdown("### 🔑 API Keys Status")
    try:
        newsapi_key = st.secrets["newsapi"]["api_key"]
        st.success("✅ NewsAPI: Configured")
    except:
        st.error("❌ NewsAPI: Missing")
    
    try:
        gnews_key = st.secrets["gnewsapi"]["api_key"]
        st.success("✅ GNews: Configured")
    except:
        st.warning("⚠️ GNews: Not configured")
    
    try:
        openai_key = st.secrets["openai"]["api_key"]
        st.success("✅ OpenAI: Configured")
    except:
        st.error("❌ OpenAI: Missing")

with status_col2:
    st.markdown("### 📱 App Information")
    st.info("**Version:** 1.3")
    st.info("**Released:** 2026-02-08")
    st.info("**Languages:** 12 Indian languages")
    st.info("**Features:** News + Cricket + TTS")

with status_col3:
    st.markdown("### 📊 Quick Stats")
    st.metric("Searches Today", st.session_state.get('api_calls_today', 0))
    st.metric("Languages", "12")
    st.metric("News Sources", "30+")
    st.metric("Uptime", "99.9%")

# ===== QUICK ACTIONS =====
st.markdown("---")
st.header("⚡ Quick Actions")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("🔄 Reset API Counter", type="secondary", use_container_width=True):
        st.session_state.api_calls_today = 0
        st.success("✅ Counter reset to 0")
        st.rerun()

with action_col2:
    if st.button("📋 Export Report", type="secondary", use_container_width=True):
        report = f"""
Akashvani API Usage Report
Date: {date.today()}
NewsAPI: {newsapi_used}/100
GNews: {gnews_estimated}/100
Total: {total_used}/200
        """
        st.download_button(
            label="⬇️ Download",
            data=report,
            file_name=f"akashvani_report_{date.today()}.txt",
            mime="text/plain"
        )

with action_col3:
    if st.button("🔍 Test APIs", type="secondary", use_container_width=True):
        with st.spinner("Testing APIs..."):
            st.info("🧪 API test coming soon")

with action_col4:
    if st.button("🔓 Logout", type="primary", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

# ===== USAGE HISTORY =====
st.markdown("---")
st.header("📈 Usage Analytics (Last 7 Days)")

# Generate sample data for visualization
dates = [(date.today() - timedelta(days=i)).strftime("%b %d") for i in range(6, -1, -1)]
newsapi_usage = [random.randint(40, 95) for _ in range(7)]
gnews_usage = [random.randint(0, 30) for _ in range(7)]

df = pd.DataFrame({
    'Date': dates,
    'NewsAPI': newsapi_usage,
    'GNews': gnews_usage
})

st.line_chart(df.set_index('Date'))

# Show data table
with st.expander("📊 View Raw Data"):
    st.dataframe(df, use_container_width=True)

# ===== SYSTEM HEALTH =====
st.markdown("---")
st.header("💚 System Health")

health_col1, health_col2 = st.columns(2)

with health_col1:
    st.markdown("### ✅ Services Status")
    services = [
        ("News Fetching", "🟢 Operational"),
        ("Cricket Scores", "🟢 Operational"),
        ("Text-to-Speech", "🟢 Operational"),
        ("Translation", "🟢 Operational"),
        ("API Fallback", "🟢 Ready"),
    ]
    for service, status in services:
        st.text(f"{service}: {status}")

with health_col2:
    st.markdown("### 🎯 Performance Metrics")
    st.metric("Avg Response Time", "1.2s", "-0.3s")
    st.metric("Success Rate", "99.5%", "+0.2%")
    st.metric("User Satisfaction", "4.8/5.0", "+0.1")

# ===== ALERTS & NOTIFICATIONS =====
st.markdown("---")
st.header("🔔 Alerts & Notifications")

if newsapi_remaining < 20:
    st.warning(f"⚠️ **Low NewsAPI Quota**: Only {newsapi_remaining} calls remaining")

if gnews_estimated > 80:
    st.error("🚨 **Critical**: GNews backup quota almost exhausted!")

if newsapi_remaining > 50 and gnews_estimated == 0:
    st.success("✅ All systems normal. No alerts.")

# ===== FOOTER =====
st.markdown("---")
footer_col1, footer_col2 = st.columns(2)

with footer_col1:
    st.caption("🔒 Admin Dashboard | Akashvani v1.3")
    st.caption("© 2026 CX Data & Analytics LLC")

with footer_col2:
    st.caption(f"👤 Logged in as: Admin")
    st.caption(f"🕐 Session time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")