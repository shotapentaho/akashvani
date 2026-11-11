"""
Analytics Dashboard Module
Real-time monitoring and usage statistics
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date

def show_dashboard():
    """Display analytics dashboard"""
    
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

    newsapi_today = gnews_today = serpapi_today = 0
    searches_today = users_today = 0
    if DB_AVAILABLE:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM api_calls WHERE api_name = 'newsapi' AND DATE(call_timestamp) = CURRENT_DATE),
                    (SELECT COUNT(*) FROM api_calls WHERE api_name = 'gnews' AND DATE(call_timestamp) = CURRENT_DATE),
                    (SELECT COUNT(*) FROM api_calls WHERE api_name = 'serpapi' AND DATE(call_timestamp) = CURRENT_DATE),
                    (SELECT COUNT(*) FROM search_queries WHERE DATE(call_timestamp) = CURRENT_DATE),
                    (SELECT COUNT(DISTINCT session_id) FROM search_queries WHERE DATE(call_timestamp) = CURRENT_DATE)
            """)
            result = cursor.fetchone()
            cursor.close()
            if result:
                newsapi_today, gnews_today, serpapi_today, searches_today, users_today = (
                    value or 0 for value in result
                )
        except Exception as e:
            print(f"Dashboard stats error: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
    else:
        newsapi_today = st.session_state.get("api_calls_today", 0)
    
    # ===== POPULAR SEARCHES =====
    st.markdown("---")
    st.subheader("🔥 Popular Searches (Last 7 Days)")
    search_df = pd.DataFrame(columns=['Query', 'Count', 'Last Searched'])
    
    if DB_AVAILABLE:
        try:
            popular_conn = get_connection()
            if popular_conn:
                cursor = popular_conn.cursor()
                cursor.execute("""
                    SELECT 
                        query_text, 
                        COUNT(*) as count,
                        MAX(call_timestamp) as last_search
                    FROM search_queries
                    WHERE call_timestamp > NOW() - INTERVAL '7 days'
                    GROUP BY query_text
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                popular_searches = cursor.fetchall()
                cursor.close()
                popular_conn.close()
                
                search_df = pd.DataFrame(
                    popular_searches,
                    columns=['Query', 'Count', 'Last Searched']
                )
        except Exception as e:
            print(f"Popular searches error: {e}")
    elif not DB_AVAILABLE:
        st.info("Database connection required for popular search data")

    chart_col, table_col = st.columns([2, 1])
    with chart_col:
        st.bar_chart(search_df.set_index('Query')['Count'])
    with table_col:
        st.dataframe(search_df, use_container_width=True, hide_index=True)
    
    # ===== LANGUAGE DISTRIBUTION =====
    st.markdown("---")
    st.subheader("🌍 Language Distribution (Last 7 Days)")
    lang_df = pd.DataFrame(columns=['Language', 'Searches'])
    
    if DB_AVAILABLE:
        try:
            lang_conn = get_connection()
            if lang_conn:
                cursor = lang_conn.cursor()
                cursor.execute("""
                    SELECT 
                        language_code,
                        COUNT(*) as count
                    FROM search_queries
                    WHERE call_timestamp > NOW() - INTERVAL '7 days'
                    GROUP BY language_code
                    ORDER BY count DESC
                """)
                
                lang_data = cursor.fetchall()
                cursor.close()
                lang_conn.close()
                
                lang_df = pd.DataFrame(lang_data, columns=['Language', 'Searches'])
        except Exception as e:
            print(f"Language distribution error: {e}")
    elif not DB_AVAILABLE:
        st.info("Database connection required for language data")

    col_chart, col_table = st.columns([2, 1])
    with col_chart:
        st.bar_chart(lang_df.set_index('Language'))
    with col_table:
        st.dataframe(lang_df, use_container_width=True, hide_index=True)
    
    # ===== RECENT API CALLS =====
    st.markdown("---")
    st.subheader("🔄 API Calls")
    
    if DB_AVAILABLE:
        try:
            recent_conn = get_connection()
            if recent_conn:
                cursor = recent_conn.cursor()
                cursor.execute("""
                    SELECT
                        api_name,
                        query_text,
                        response_status,
                        articles_count,
                        language_of_choice,
                        voice_speed,
                        voice_gender,
                        voice_duration,
                        call_timestamp
                    FROM public.api_calls
                    ORDER BY call_timestamp DESC
                """)
                
                api_calls = cursor.fetchall()
                cursor.close()
                recent_conn.close()
                
                if api_calls:
                    df_api = pd.DataFrame(
                        api_calls,
                        columns=[
                            "API Name",
                            "Query",
                            "Response Status",
                            "Articles",
                            "Language",
                            "Voice Speed",
                            "Voice Gender",
                            "Voice Duration",
                            "Call Timestamp",
                        ],
                    )
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
    
    # Close main connection if still open
    if DB_AVAILABLE and conn:
        try:
            conn.close()
        except:
            pass
