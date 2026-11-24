"""Professional, date-filtered analytics dashboard for the admin panel."""

from calendar import monthrange
from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st


def _one_month_ago(value: date) -> date:
    """Return the same day in the previous calendar month when possible."""
    year = value.year if value.month > 1 else value.year - 1
    month = value.month - 1 if value.month > 1 else 12
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def _date_series(start_date: date, end_date: date) -> pd.DatetimeIndex:
    return pd.date_range(start=start_date, end=end_date, freq="D")


def _empty_frame(columns):
    return pd.DataFrame(columns=columns)


def _load_dashboard_data(conn, start_date: date, end_date: date):
    """Load all dashboard aggregates for the selected inclusive date range."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'api_calls'
            """
        )
        api_columns = {row[0] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'search_queries'
            """
        )
        search_columns = {row[0] for row in cursor.fetchall()}

        api_date = "call_date" if "call_date" in api_columns else (
            "DATE(call_timestamp)" if "call_timestamp" in api_columns
            else "DATE(created_at)"
        )
        search_date = (
            "created_at" if "created_at" in search_columns
            else "call_timestamp" if "call_timestamp" in search_columns
            else "call_date"
        )
        session_column = next(
            (
                column
                for column in ("session_id", "user_session_id")
                if column in search_columns
            ),
            None,
        )
        unique_users = (
            f"COUNT(DISTINCT NULLIF({session_column}, ''))"
            if session_column
            else "0"
        )

        cursor.execute(
            f"""
            SELECT
                COUNT(*) AS total_calls,
                COUNT(*) FILTER (WHERE response_status = 'success') AS successful_calls,
                COUNT(*) FILTER (WHERE response_status = 'failure') AS failed_calls,
                COALESCE(SUM(articles_count), 0) AS articles
            FROM public.api_calls
            WHERE {api_date} BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        totals = cursor.fetchone() or (0, 0, 0, 0)

        cursor.execute(
            f"""
            SELECT
                {api_date} AS day,
                COUNT(*) AS calls,
                COUNT(*) FILTER (WHERE response_status = 'success') AS successful_calls,
                COUNT(*) FILTER (WHERE response_status = 'failure') AS failed_calls
            FROM public.api_calls
            WHERE {api_date} BETWEEN %s AND %s
            GROUP BY day
            ORDER BY day
            """,
            (start_date, end_date),
        )
        trend = pd.DataFrame(
            cursor.fetchall(),
            columns=["Date", "API Requests", "Successful Requests", "Failed Requests"],
        )

        cursor.execute(
            f"""
            SELECT api_name AS "API", COUNT(*) AS "API Requests"
            FROM public.api_calls
            WHERE {api_date} BETWEEN %s AND %s
            GROUP BY api_name
            ORDER BY "API Requests" DESC
            """,
            (start_date, end_date),
        )
        api_usage = pd.DataFrame(cursor.fetchall(), columns=["API", "API Requests"])

        cursor.execute(
            f"""
            SELECT
                LOWER(BTRIM(query_text)) AS "Query",
                COUNT(*) AS "Searches"
            FROM public.api_calls
            WHERE {api_date} BETWEEN %s AND %s
              AND query_text IS NOT NULL
              AND BTRIM(query_text) <> ''
            GROUP BY LOWER(BTRIM(query_text))
            ORDER BY "Searches" DESC
            LIMIT 10
            """,
            (start_date, end_date),
        )
        popular_searches = pd.DataFrame(
            cursor.fetchall(), columns=["Query", "Searches"]
        )

        language_column = (
            "language_of_choice" if "language_of_choice" in api_columns else None
        )
        if language_column:
            cursor.execute(
                f"""
                SELECT BTRIM({language_column}) AS "Language", COUNT(*) AS "Searches"
                FROM public.api_calls
                WHERE {api_date} BETWEEN %s AND %s
                  AND {language_column} IS NOT NULL
                  AND BTRIM({language_column}) <> ''
                GROUP BY BTRIM({language_column})
                ORDER BY "Searches" DESC
                """,
                (start_date, end_date),
            )
            languages = pd.DataFrame(
                cursor.fetchall(), columns=["Language", "Searches"]
            )
        else:
            languages = _empty_frame(["Language", "Searches"])

        cursor.execute(
            f"""
            SELECT
                COUNT(*) AS searches,
                {unique_users} AS users
            FROM public.search_queries
            WHERE DATE({search_date}) BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        search_totals = cursor.fetchone() or (0, 0)

        cursor.execute(
            f"""
            SELECT
                {search_date}::date AS "Date",
                COUNT(*) AS "Searches",
                {unique_users} AS "Users"
            FROM public.search_queries
            WHERE DATE({search_date}) BETWEEN %s AND %s
            GROUP BY "Date"
            ORDER BY "Date"
            """,
            (start_date, end_date),
        )
        search_trend = pd.DataFrame(
            cursor.fetchall(), columns=["Date", "Searches", "Users"]
        )

        timestamp_column = next(
            (
                column
                for column in ("call_timestamp", "created_at")
                if column in api_columns
            ),
            None,
        )
        detail_columns = [
            "api_name",
            "query_text",
            "response_status",
            "articles_count",
            "language_of_choice",
            timestamp_column or api_date,
        ]
        selected_detail_columns = [
            column
            for column in detail_columns
            if column in api_columns or column == api_date
        ]
        detail_select = ", ".join(selected_detail_columns)
        cursor.execute(
            f"""
            SELECT {detail_select}
            FROM public.api_calls
            WHERE {api_date} BETWEEN %s AND %s
            ORDER BY {timestamp_column or api_date} DESC
            LIMIT 500
            """,
            (start_date, end_date),
        )
        details = cursor.fetchall()
        label_by_column = {
            "api_name": "API",
            "query_text": "Query",
            "response_status": "Status",
            "articles_count": "Articles",
            "language_of_choice": "Language",
            "call_timestamp": "Timestamp",
            "created_at": "Timestamp",
            api_date: "Date",
        }
        detail_labels = [label_by_column[column] for column in selected_detail_columns]
        api_details = pd.DataFrame(details, columns=detail_labels)

        return {
            "totals": totals,
            "search_totals": search_totals,
            "trend": trend,
            "search_trend": search_trend,
            "api_usage": api_usage,
            "popular_searches": popular_searches,
            "languages": languages,
            "api_details": api_details,
        }
    finally:
        cursor.close()


def _normalise_trends(data, start_date: date, end_date: date):
    """Fill missing days so charts do not hide zero-activity dates."""
    dates = _date_series(start_date, end_date)
    if data.empty:
        return pd.DataFrame(
            {
                "Date": dates,
                "API Requests": 0,
                "Successful Requests": 0,
                "Failed Requests": 0,
                "Searches": 0,
                "Users": 0,
            }
        )
    data = data.copy()
    data["Date"] = pd.to_datetime(data["Date"])
    return data.set_index("Date").reindex(dates, fill_value=0).rename_axis("Date").reset_index()


def show_dashboard():
    """Display the date-filtered analytics dashboard."""
    today = date.today()
    default_start = _one_month_ago(today)

    st.title("akashvani view")
    st.caption("Monitor API usage, search activity, and platform health.")

    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1.2])
    with filter_col1:
        start_date = st.date_input(
            "From",
            value=default_start,
            max_value=today,
            key="analytics_from_date",
        )
    with filter_col2:
        end_date = st.date_input(
            "To",
            value=today,
            max_value=today,
            key="analytics_to_date",
        )
    with filter_col3:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.caption(f"Showing {start_date:%b %d, %Y} – {end_date:%b %d, %Y}")

    if start_date > end_date:
        st.error("The From date must be on or before the To date.")
        return

    try:
        from utils.database import get_connection

        conn = get_connection()
    except Exception as exc:
        st.error(f"Database connection failed: {exc}")
        return

    if conn is None:
        st.info("Connect the database to view analytics for this date range.")
        return

    try:
        data = _load_dashboard_data(conn, start_date, end_date)
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error("Unable to load analytics for the selected date range.")
        st.caption(str(exc))
        return
    finally:
        conn.close()

    total_calls, successful_calls, failed_calls, articles = data["totals"]
    searches, users = data["search_totals"]
    success_rate = (successful_calls / total_calls * 100) if total_calls else 0
    trend = _normalise_trends(data["trend"], start_date, end_date)
    search_trend = _normalise_trends(data["search_trend"], start_date, end_date)
    trend["Searches"] = search_trend["Searches"]
    trend["Users"] = search_trend["Users"]

    st.markdown("### Performance snapshot")
    metric_cols = st.columns(6)
    metrics = [
        ("API requests", total_calls, "Selected period"),
        ("Successful requests", successful_calls, f"{success_rate:.1f}% success rate"),
        ("Failed requests", failed_calls, "Needs attention" if failed_calls else "No failures"),
        ("Searches", searches, "Search activity"),
        ("Unique users", users, "Distinct sessions"),
        ("Articles", articles, "Articles returned"),
    ]
    for column, (label, value, help_text) in zip(metric_cols, metrics):
        column.metric(label, f"{value:,}", help=help_text)

    st.markdown("### Activity trends")
    trend_data = trend.melt(
        id_vars="Date",
        value_vars=["API Requests", "Searches"],
        var_name="Metric",
        value_name="Count",
    )
    activity_chart = (
        alt.Chart(trend_data)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Count:Q", title="Activity"),
            color=alt.Color("Metric:N", title=None),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Metric:N"),
                alt.Tooltip("Count:Q", format=","),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(activity_chart, use_container_width=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("### API usage")
        if data["api_usage"].empty:
            st.info("No API calls in this date range.")
        else:
            api_chart = (
                alt.Chart(data["api_usage"])
                .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                .encode(
                    x=alt.X("API Requests:Q", title="API requests"),
                    y=alt.Y("API:N", sort="-x", title=None),
                    color=alt.Color("API:N", legend=None),
                    tooltip=["API:N", alt.Tooltip("API Requests:Q", title="API requests", format=",")],
                )
                .properties(height=220)
            )
            st.altair_chart(api_chart, use_container_width=True)

    with chart_col2:
        st.markdown("### Popular searches")
        if data["popular_searches"].empty:
            st.info("No search terms in this date range.")
        else:
            search_chart = (
                alt.Chart(data["popular_searches"])
                .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                .encode(
                    x=alt.X("Searches:Q", title="Searches"),
                    y=alt.Y("Query:N", sort="-x", title=None),
                    color=alt.Color("Searches:Q", legend=None),
                    tooltip=["Query:N", alt.Tooltip("Searches:Q", format=",")],
                )
                .properties(height=220)
            )
            st.altair_chart(search_chart, use_container_width=True)

    lower_col1, lower_col2 = st.columns(2)
    with lower_col1:
        st.markdown("### Language usage")
        if data["languages"].empty:
            st.info("No language data in this date range.")
        else:
            st.bar_chart(
                data["languages"].set_index("Language"),
                y="Searches",
                use_container_width=True,
            )
    with lower_col2:
        st.markdown("### Daily success rate")
        rate_data = trend[["Date", "API Requests", "Successful Requests"]].copy()
        rate_data["Success rate"] = (
            rate_data["Successful Requests"].div(
                rate_data["API Requests"].replace(0, pd.NA)
            ).fillna(0) * 100
        )
        st.line_chart(
            rate_data.set_index("Date")[["Success rate"]],
            y="Success rate",
            use_container_width=True,
        )

    with st.expander("View API call details"):
        if data["api_details"].empty:
            st.info("No API calls in this date range.")
        else:
            st.dataframe(
                data["api_details"],
                use_container_width=True,
                hide_index=True,
                height=320,
            )

    st.caption(
        f"Updated {datetime.utcnow():%Y-%m-%d %H:%M} UTC · "
        f"Data range: {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}"
    )
