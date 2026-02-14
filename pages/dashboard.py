"""
Analytics Dashboard Module
Real-time monitoring and usage statistics
"""

import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd

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
    
    # Initialize variables
    newsapi_today = 0
    gnews_today = 0
    serpapi_today = 0
    searches_today = 0
    users_today = 0
    
    # ===== API USAGE SECTION =====
    st.subheader("🔌 API Usage Monitor")
    
    if DB_AVAILABLE:
        try:
            cursor = conn.cursor()
            
            # Get all stats in one transaction
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM api_calls WHERE api_name = 'newsapi' AND DATE(call_timestamp) = CURRENT_DATE) as newsapi_count,
                    (SELECT COUNT(*) FROM api_calls WHERE api_name = 'gnews' AND DATE(call_timestamp) = CURRENT_DATE) as gnews_count,
                    (SELECT COUNT(*) FROM api_calls WHERE api_name = 'serpapi' AND DATE(call_timestamp) = CURRENT_DATE) as serpapi_count,
                    (SELECT COUNT(*) FROM search_queries WHERE DATE(call_timestamp) = CURRENT_DATE) as searches_count,
                    (SELECT COUNT(DISTINCT session_id) FROM search_queries WHERE DATE(call_timestamp) = CURRENT_DATE) as users_count
            """)
            
            result = cursor.fetchone()
            if result:
                newsapi_today = result[0] or 0
                gnews_today = result[1] or 0
                serpapi_today = result[2] or 0
                searches_today = result[3] or 0
                users_today = result[4] or 0
            
            cursor.close()
            
        except Exception as e:
            print(f"Query error: {e}")
            # Rollback on error
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            newsapi_today = 0
            gnews_today = 0
            serpapi_today = 0
            searches_today = 0
            users_today = 0
    else:
        newsapi_today = st.session_state.get('api_calls_today', 0)
    
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
    
    # ===== HISTORICAL API USAGE CHART =====
    st.markdown("---")
    st.subheader("📈 Historical API Usage (Last 7 Days)")
    
    if DB_AVAILABLE:
        # Create new connection for historical data
        history_conn = None
        try:
            history_conn = get_connection()
            if history_conn:
                cursor = history_conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        DATE(call_timestamp) as date,
                        api_name,
                        COUNT(*) as calls
                    FROM api_calls
                    WHERE call_timestamp >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(call_timestamp), api_name
                    ORDER BY date ASC
                """)
                
                history_data = cursor.fetchall()
                cursor.close()
                
                if history_data:
                    df_history = pd.DataFrame(history_data, columns=['Date', 'API', 'Calls'])
                    pivot_df = df_history.pivot(index='Date', columns='API', values='Calls').fillna(0)
                    
                    for api in ['newsapi', 'gnews', 'serpapi']:
                        if api not in pivot_df.columns:
                            pivot_df[api] = 0
                    
                    pivot_df = pivot_df.rename(columns={
                        'newsapi': 'NewsAPI',
                        'gnews': 'GNews',
                        'serpapi': 'SerpAPI'
                    })
                    
                    st.line_chart(pivot_df, use_container_width=True)
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    
                    with col_stat1:
                        total_newsapi = int(pivot_df['NewsAPI'].sum())
                        st.metric("NewsAPI (7 days)", total_newsapi)
                    
                    with col_stat2:
                        total_gnews = int(pivot_df['GNews'].sum())
                        st.metric("GNews (7 days)", total_gnews)
                    
                    with col_stat3:
                        total_serpapi = int(pivot_df['SerpAPI'].sum())
                        st.metric("SerpAPI (7 days)", total_serpapi)
                    
                    with st.expander("📊 View Raw Data"):
                        st.dataframe(df_history, use_container_width=True, hide_index=True)
                    
                else:
                    st.info("📭 No historical data available yet. Start using the app to see trends!")
            else:
                st.info("💾 Unable to fetch historical data")
                
        except Exception as e:
            print(f"Historical chart error: {e}")
            st.warning(f"⚠️ Unable to load historical data")
            if history_conn:
                try:
                    history_conn.rollback()
                except:
                    pass
        finally:
            if history_conn:
                try:
                    history_conn.close()
                except:
                    pass
    else:
        st.info("💾 Database connection required for historical data")
    
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
                # Create new connection for this query
                analytics_conn = get_connection()
                if analytics_conn:
                    cursor = analytics_conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM search_queries 
                        WHERE DATE(call_timestamp) = CURRENT_DATE - INTERVAL '1 day'
                    """)
                    yesterday_searches = cursor.fetchone()[0] or 0
                    delta = searches_today - yesterday_searches
                    st.metric("📈 vs Yesterday", f"{delta:+d}", f"{searches_today} today")
                    cursor.close()
                    analytics_conn.close()
                else:
                    st.metric("📈 vs Yesterday", "N/A")
            except Exception as e:
                print(f"Analytics error: {e}")
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
            popular_conn = get_connection()
            if popular_conn:
                cursor = popular_conn.cursor()
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
                cursor.close()
                popular_conn.close()
                
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
            lang_conn = get_connection()
            if lang_conn:
                cursor = lang_conn.cursor()
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
                cursor.close()
                lang_conn.close()
                
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
            recent_conn = get_connection()
            if recent_conn:
                cursor = recent_conn.cursor()
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
                cursor.close()
                recent_conn.close()
                
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
    
    # Close main connection if still open
    if DB_AVAILABLE and conn:
        try:
            conn.close()
        except:
            pass
