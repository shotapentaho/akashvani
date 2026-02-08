

-- ===== DROP EXISTING TABLES (IF EXISTS) =====

DROP TABLE IF EXISTS api_calls CASCADE;
DROP TABLE IF EXISTS search_queries CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS openai_calls CASCADE;

-- Drop materialized views if they exist
DROP MATERIALIZED VIEW IF EXISTS daily_api_usage CASCADE;
DROP MATERIALIZED VIEW IF EXISTS hourly_api_usage CASCADE;
DROP MATERIALIZED VIEW IF EXISTS popular_searches CASCADE;

-- Drop functions if they exist
DROP FUNCTION IF EXISTS refresh_dashboard_views() CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_data() CASCADE;

-- ===== TABLE 1: API Calls (Insert-only, no updates) =====
CREATE TABLE api_calls (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) NOT NULL,  -- 'newsapi' or 'gnews'
    call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    call_date DATE DEFAULT CURRENT_DATE,
    query_text TEXT,
    response_status VARCHAR(20),  -- 'success' or 'failure'
    articles_count INTEGER DEFAULT 0
);

-- ===== TABLE 2: Search Queries (Insert-only) =====
CREATE TABLE search_queries (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    language_code VARCHAR(10),
    articles_count INTEGER,
    api_used VARCHAR(50),
    duration_mode VARCHAR(20),
    user_session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== TABLE 3: User Sessions (Insert-only) =====
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    language_code VARCHAR(10),
    page_view VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== TABLE 4: OpenAI API Calls (Cost tracking) =====
CREATE TABLE openai_calls (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50),  -- 'translation' or 'summarization'
    language_code VARCHAR(10),
    tokens_used INTEGER,
    estimated_cost DECIMAL(10, 6),
    model_name VARCHAR(50) DEFAULT 'gpt-3.5-turbo-0125',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== INDEXES FOR FAST AGGREGATION QUERIES =====

-- API Calls indexes
CREATE INDEX idx_api_calls_date ON api_calls(call_date);
CREATE INDEX idx_api_calls_timestamp ON api_calls(call_timestamp);
CREATE INDEX idx_api_calls_api_name ON api_calls(api_name);
CREATE INDEX idx_api_calls_date_api_name ON api_calls(call_date, api_name);

-- Search Queries indexes
CREATE INDEX idx_search_queries_created_at ON search_queries(created_at);
CREATE INDEX idx_search_queries_query_text ON search_queries(query_text);
CREATE INDEX idx_search_queries_language ON search_queries(language_code);

-- User Sessions indexes
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_user_sessions_created_at ON user_sessions(created_at);

-- OpenAI Calls indexes
CREATE INDEX idx_openai_calls_created_at ON openai_calls(created_at);
CREATE INDEX idx_openai_calls_operation ON openai_calls(operation_type);

-- ===== MATERIALIZED VIEWS FOR FASTER DASHBOARD QUERIES =====

-- Daily API usage summary (refresh periodically)
CREATE MATERIALIZED VIEW daily_api_usage AS
SELECT 
    call_date,
    api_name,
    COUNT(*) as call_count,
    SUM(articles_count) as total_articles,
    COUNT(CASE WHEN response_status = 'success' THEN 1 END) as success_count,
    COUNT(CASE WHEN response_status = 'failure' THEN 1 END) as failure_count
FROM api_calls
GROUP BY call_date, api_name
ORDER BY call_date DESC, api_name;

-- Create index on materialized view
CREATE INDEX idx_daily_api_usage_date ON daily_api_usage(call_date);

-- Hourly API usage summary (for real-time monitoring)
CREATE MATERIALIZED VIEW hourly_api_usage AS
SELECT 
    DATE_TRUNC('hour', call_timestamp) as hour,
    api_name,
    COUNT(*) as call_count
FROM api_calls
WHERE call_timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', call_timestamp), api_name
ORDER BY hour DESC;

-- Popular searches view
CREATE MATERIALIZED VIEW popular_searches AS
SELECT 
    query_text,
    COUNT(*) as search_count,
    MAX(created_at) as last_searched,
    COUNT(DISTINCT user_session_id) as unique_users
FROM search_queries
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY query_text
ORDER BY search_count DESC
LIMIT 100;

-- ===== FUNCTION TO REFRESH MATERIALIZED VIEWS =====
CREATE OR REPLACE FUNCTION refresh_dashboard_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_api_usage;
    REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_api_usage;
    REFRESH MATERIALIZED VIEW CONCURRENTLY popular_searches;
END;
$$ LANGUAGE plpgsql;

-- ===== AUTOMATIC CLEANUP (Optional: Delete old data) =====
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Keep only last 90 days of detailed API calls
    DELETE FROM api_calls WHERE call_date < CURRENT_DATE - INTERVAL '90 days';
    
    -- Keep only last 30 days of search queries
    DELETE FROM search_queries WHERE created_at < NOW() - INTERVAL '30 days';
    
    -- Keep only last 30 days of user sessions
    DELETE FROM user_sessions WHERE created_at < NOW() - INTERVAL '30 days';
    
    -- Keep only last 60 days of OpenAI calls
    DELETE FROM openai_calls WHERE created_at < NOW() - INTERVAL '60 days';
END;
$$ LANGUAGE plpgsql;

-- ===== SCHEDULE AUTOMATIC TASKS (Using pg_cron extension) =====
-- Uncomment if pg_cron is available:
-- SELECT cron.schedule('refresh-views', '*/15 * * * *', 'SELECT refresh_dashboard_views()');
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data()');

-- ===== VERIFICATION QUERIES =====
-- Run these to verify setup:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- SELECT matviewname FROM pg_matviews WHERE schemaname = 'public';
-- SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public';