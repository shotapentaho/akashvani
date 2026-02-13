"""
PostgreSQL database connection and tracking functions
Insert-only pattern for analytics
Auto-detects schema and adapts queries
"""

import psycopg2
import streamlit as st
from datetime import datetime

def get_connection():
    """
    Get PostgreSQL connection with timeout
    Returns None if connection fails
    """
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            connect_timeout=5
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def get_table_columns(cursor, table_name):
    """Get list of columns for a table"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name=%s
    """, (table_name,))
    return [row[0] for row in cursor.fetchall()]


def track_api_call(api_name: str, query_text: str, response_status: str, articles_count: int = 0):
    """Track API call in database (insert-only)"""
    try:
        conn = get_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Get columns for api_calls table
        columns = get_table_columns(cursor, 'api_calls')
        
        # Build INSERT query based on available columns
        fields = ['api_name', 'query_text', 'response_status', 'articles_count']
        values = [api_name, query_text, response_status, articles_count]
        placeholders = ['%s', '%s', '%s', '%s']
        
        # Add timestamp columns if they exist
        if 'call_date' in columns:
            fields.append('call_date')
            values.append(None)  # Will use CURRENT_DATE
            placeholders.append('CURRENT_DATE')
        
        if 'call_timestamp' in columns:
            fields.append('call_timestamp')
            values.append(None)  # Will use NOW()
            placeholders.append('NOW()')
        elif 'created_at' in columns:
            fields.append('created_at')
            values.append(None)
            placeholders.append('NOW()')
        
        # Remove None values (for SQL functions)
        values = [v for v in values if v is not None]
        
        # Build query
        query = f"""
            INSERT INTO api_calls ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        """
        
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Tracked API call: {api_name} - {query_text}")
    except Exception as e:
        print(f"❌ API tracking error: {e}")
        import traceback
        traceback.print_exc()


def track_search_query(query_text: str, language_code: str, articles_count: int, 
                       api_used: str, duration_mode: str, session_id: str):
    """Track search query in database (insert-only)"""
    try:
        conn = get_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Get columns for search_queries table
        columns = get_table_columns(cursor, 'search_queries')
        
        # Build INSERT query based on available columns
        fields = ['query_text', 'language_code', 'articles_count', 'api_used', 'duration_mode']
        values = [query_text, language_code, articles_count, api_used, duration_mode]
        placeholders = ['%s', '%s', '%s', '%s', '%s']
        
        # Add session_id if column exists
        if 'session_id' in columns:
            fields.append('session_id')
            values.append(session_id)
            placeholders.append('%s')
        
        # Add timestamp columns if they exist
        if 'call_date' in columns:
            fields.append('call_date')
            values.append(None)
            placeholders.append('CURRENT_DATE')
        
        if 'call_timestamp' in columns:
            fields.append('call_timestamp')
            values.append(None)
            placeholders.append('NOW()')
        elif 'created_at' in columns:
            fields.append('created_at')
            values.append(None)
            placeholders.append('NOW()')
        
        # Remove None values (for SQL functions)
        values = [v for v in values if v is not None]
        
        # Build query
        query = f"""
            INSERT INTO search_queries ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        """
        
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Tracked search: {query_text} ({language_code})")
    except Exception as e:
        print(f"❌ Search tracking error: {e}")
        import traceback
        traceback.print_exc()


def track_user_session(session_id: str, language_code: str, page_view: str):
    """Track user session in database (insert-only)"""
    try:
        conn = get_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Get columns for user_sessions table
        columns = get_table_columns(cursor, 'user_sessions')
        
        # Build INSERT query based on available columns
        fields = ['language_code', 'page_view']
        values = [language_code, page_view]
        placeholders = ['%s', '%s']
        
        # Add session_id if column exists
        if 'session_id' in columns:
            fields.insert(0, 'session_id')
            values.insert(0, session_id)
            placeholders.insert(0, '%s')
        
        # Add timestamp columns if they exist
        if 'call_date' in columns:
            fields.append('call_date')
            values.append(None)
            placeholders.append('CURRENT_DATE')
        
        if 'call_timestamp' in columns:
            fields.append('call_timestamp')
            values.append(None)
            placeholders.append('NOW()')
        elif 'created_at' in columns:
            fields.append('created_at')
            values.append(None)
            placeholders.append('NOW()')
        
        # Remove None values (for SQL functions)
        values = [v for v in values if v is not None]
        
        # Build query
        query = f"""
            INSERT INTO user_sessions ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        """
        
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Tracked session: {session_id}")
    except Exception as e:
        print(f"❌ Session tracking error: {e}")
        import traceback
        traceback.print_exc()
