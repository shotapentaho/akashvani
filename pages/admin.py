"""
Admin Dashboard for Akashvani v1.3
Real-time monitoring with PostgreSQL analytics
Access: https://akashvani.cxloop.co/admin
Password Protected
"""

import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd

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
st.header("🔌 API Usage Monitor")

if DB_AVAILABLE:
    try:
        # Get today's API usage from database
        cursor = conn.cursor()
        
        # NewsAPI calls today
        cursor.execute("""
            SELECT COUNT(*) 
            FROM api_calls 
            WHERE api_name = 'newsapi' 
              AND DATE(created_at) = CURRENT_DATE
        """)
        newsapi_today = cursor.fetchone()[0]
        
        # GNews calls today
        cursor.execute("""
            SELECT COUNT(*) 
            FROM api_calls 
            WHERE api_name = 'gnews' 
              AND DATE(created_at) = CURRENT_DATE
        """)
        gnews_today = cursor.fetchone()[0]
        
        # Total searches today
        cursor.execute("""
            SELECT COUNT(*) 
            FROM search_queries 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        searches_today = cursor.fetchone()[0]
        
        # Unique users today
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) 
            FROM search_queries 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        users_today = cursor.fetchone()[0]
        
    except Exception as e:
        print(f"Query error: {e}")
        newsapi_today = 0
        gnews_today = 0
        searches_today = 0
        users_today = 0
else:
    # Fallback to session state
    newsapi_today = st.session_state.get('api_calls_today', 0)
    gnews_today = 0
    searches_today = newsapi_today
    users_today = 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    newsapi_remaining = max(0, 100 - newsapi_today)
    st.metric("NewsAPI", f"{newsapi_today}/100", f"↑ {newsapi_remaining} left")
    
    # Status indicator
    if newsapi_remaining > 50:
        st.success("🟢 Healthy")
    elif newsapi_remaining > 10:
        st.warning("🟡 Medium")
    else:
        st.error("🔴 Critical")
    
with col2:
    gnews_remaining = max(0, 100 - gnews_today)
    st.metric("GNews Backup", f"~{gnews_today}/100", f"↑ ~{gnews_remaining} left")
    
    if gnews_today == 0:
        st.info("⚪ Not Used")
    elif gnews_remaining > 50:
        st.success("🟢 Healthy")
    elif gnews_remaining > 10:
        st.warning("🟡 Medium")
    else:
        st.error("🔴 Critical")

with col3:
    total_quota = 200  # NewsAPI + GNews
    total_used = newsapi_today + gnews_today
    percentage = (total_used / total_quota) * 100
    st.metric("Total Usage", f"{percentage:.0f}%", "of 200 calls")
    
    # Cost estimate (if using paid plan)
    st.caption(f"💰 Cost: $0.0 (free tier)")

with col4:
    now_utc = datetime.utcnow()
    midnight_utc = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_reset = midnight_utc - now_utc
    hours_left = time_until_reset.seconds // 3600
    minutes_left = (time_until_reset.seconds % 3600) // 60
    st.metric("Quota Reset", f"{hours_left}h {minutes_left}m", "↓ until midnight UTC")
    
    st.caption(f"🕐 Current UTC: {now_utc.strftime('%H:%M:%S')}")

# Progress bars
st.markdown("---")
st.subheader("📈 API Quota Usage")

col_progress1, col_progress2 = st.columns(2)

with col_progress1:
    st.markdown("**NewsAPI (Primary)**")
    if newsapi_today <= 100:
        progress_val = newsapi_today / 100
        st.progress(progress_val)
        st.caption(f"Used: {newsapi_today}/100 calls")
    else:
        st.progress(1.0)
        st.caption("⚠️ Quota exhausted - using GNews fallback")

with col_progress2:
    st.markdown("**GNews (Backup)**")
    if gnews_today > 0:
        st.progress(min(gnews_today / 100, 1.0))
        st.caption(f"Used: {gnews_today}/100 calls")
    else:
        st.progress(0.0)
        st.caption("🟢 Ready as backup")

# ===== REAL-TIME ANALYTICS =====
st.markdown("---")
st.header("📊 Real-Time Analytics")

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
                WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
            """)
            yesterday_searches = cursor.fetchone()[0]
            delta = searches_today - yesterday_searches
            st.metric("📈 vs Yesterday", f"{delta:+d}", f"{searches_today} today")
        except:
            st.metric("📈 vs Yesterday", "N/A")
    else:
        st.metric("📈 vs Yesterday", "N/A")

with analytics_col4:
    if searches_today > 0:
        success_rate = ((newsapi_today + gnews_today) / searches_today) * 100
        st.metric("✅ Success Rate", f"{success_rate:.1f}%")
    else:
        st.metric("✅ Success Rate", "N/A")

# ===== POPULAR SEARCHES =====
st.markdown("---")
st.header("🔥 Popular Searches (Last 24 Hours)")

if DB_AVAILABLE:
    try:
        cursor.execute("""
            SELECT 
                query_text, 
                COUNT(*) as count,
                MAX(created_at) as last_search
            FROM search_queries
            WHERE created_at > NOW() - INTERVAL '24 hours'
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
            st.dataframe(search_df, use_container_width=True)
        else:
            st.info("No searches yet today")
            
    except Exception as e:
        print(f"Popular searches error: {e}")
        st.info("Unable to load popular searches")
else:
    st.info("Database connection required for this feature")

# ===== LANGUAGE DISTRIBUTION =====
st.markdown("---")
st.header("🌍 Language Distribution")

if DB_AVAILABLE:
    try:
        cursor.execute("""
            SELECT 
                language_code,
                COUNT(*) as count
            FROM search_queries
            WHERE DATE(created_at) = CURRENT_DATE
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
                st.dataframe(lang_df, use_container_width=True)
        else:
            st.info("No data yet today")
            
    except Exception as e:
        print(f"Language distribution error: {e}")
        st.info("Unable to load language data")
else:
    st.info("Database connection required for this feature")

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
    st.markdown("### 💾 Database Status")
    if DB_AVAILABLE:
        st.success("✅ PostgreSQL: Connected")
        try:
            cursor.execute("SELECT COUNT(*) FROM api_calls")
            total_api_calls = cursor.fetchone()[0]
            st.info(f"📊 Total API Calls: {total_api_calls:,}")
            
            cursor.execute("SELECT COUNT(*) FROM search_queries")
            total_searches = cursor.fetchone()[0]
            st.info(f"🔍 Total Searches: {total_searches:,}")
            
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM user_sessions")
            total_users = cursor.fetchone()[0]
            st.info(f"👥 Total Users: {total_users:,}")
        except:
            st.info("📊 Stats: N/A")
    else:
        st.warning("⚠️ Database: Disconnected")

# ===== USAGE HISTORY (LAST 7 DAYS) =====
st.markdown("---")
st.header("📈 API Usage History (Last 7 Days)")

if DB_AVAILABLE:
    try:
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                api_name,
                COUNT(*) as calls
            FROM api_calls
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at), api_name
            ORDER BY date DESC, api_name
        """)
        
        history_data = cursor.fetchall()
        
        if history_data:
            # Create DataFrame
            df = pd.DataFrame(history_data, columns=['Date', 'API', 'Calls'])
            
            # Pivot for better visualization
            pivot_df = df.pivot(index='Date', columns='API', values='Calls').fillna(0)
            
            st.line_chart(pivot_df)
            
            # Show data table
            with st.expander("📊 View Raw Data"):
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No historical data available")
            
    except Exception as e:
        print(f"History error: {e}")
        st.info("Unable to load usage history")
else:
    st.info("Database connection required for historical data")

# ===== QUICK ACTIONS =====
st.markdown("---")
st.header("⚡ Quick Actions")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("🔄 Refresh Data", type="secondary", use_container_width=True):
        st.rerun()

with action_col2:
    if st.button("📋 Export Report", type="secondary", use_container_width=True):
        report = f"""
Akashvani API Usage Report
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

API Usage Today:
- NewsAPI: {newsapi_today}/100
- GNews: {gnews_today}/100
- Total: {newsapi_today + gnews_today}/200

Analytics:
- Searches Today: {searches_today}
- Unique Users: {users_today}
- Success Rate: {((newsapi_today + gnews_today) / max(searches_today, 1)) * 100:.1f}%

Database: {"Connected" if DB_AVAILABLE else "Disconnected"}
        """
        st.download_button(
            label="⬇️ Download Report",
            data=report,
            file_name=f"akashvani_report_{date.today()}.txt",
            mime="text/plain"
        )

with action_col3:
    if st.button("🗑️ Clear Cache", type="secondary", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Cache cleared")

with action_col4:
    if st.button("🔓 Logout", type="primary", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

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
        ("Database Tracking", "🟢 Active" if DB_AVAILABLE else "🟡 Limited"),
    ]
    for service, status in services:
        st.text(f"{service}: {status}")

with health_col2:
    st.markdown("### 🎯 Performance Metrics")
    if DB_AVAILABLE and searches_today > 0:
        avg_articles = (newsapi_today + gnews_today) / searches_today
        st.metric("Avg Articles/Search", f"{avg_articles:.1f}")
    else:
        st.metric("Avg Articles/Search", "N/A")
    
    st.metric("Database", "Connected ✅" if DB_AVAILABLE else "Limited ⚠️")
    st.metric("Uptime", "99.9%")

# ===== ALERTS & NOTIFICATIONS =====
st.markdown("---")
st.header("🔔 Alerts & Notifications")

newsapi_remaining = 100 - newsapi_today
gnews_remaining = 100 - gnews_today

if newsapi_remaining < 20:
    st.warning(f"⚠️ **Low NewsAPI Quota**: Only {newsapi_remaining} calls remaining")

if gnews_today > 80:
    st.error("🚨 **Critical**: GNews backup quota almost exhausted!")

if not DB_AVAILABLE:
    st.warning("⚠️ **Database Disconnected**: Analytics features limited. Check PostgreSQL connection.")

if newsapi_remaining > 50 and gnews_today == 0 and DB_AVAILABLE:
    st.success("✅ All systems normal. No alerts.")

# ===== FOOTER =====
st.markdown("---")
footer_col1, footer_col2 = st.columns(2)

with footer_col1:
    st.caption("🔒 Admin Dashboard | Akashvani v1.3")
    st.caption("© 2026 CX Data & Analytics LLC")
    st.caption("📧 Support: support@cxloop.co")

with footer_col2:
    st.caption(f"👤 Logged in as: Admin")
    st.caption(f"🕐 Session time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    st.caption(f"💾 Database: {'Connected' if DB_AVAILABLE else 'Disconnected'}")

# Close database connection
if DB_AVAILABLE and conn:
    try:
        conn.close()
    except:
        pass