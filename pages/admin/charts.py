"""Calendar-driven API usage views for the password-protected admin panel."""

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st


def show_charts():
    """Display professional, date-filtered API usage charts."""
    today = date.today()
    default_start = today.replace(day=1)

    st.title("API Usage View")
    st.caption("Explore API requests, response health, and recurring failures by date.")

    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1.2])
    with filter_col1:
        start_date = st.date_input(
            "From",
            value=default_start,
            max_value=today,
            key="api_usage_from_date",
        )
    with filter_col2:
        end_date = st.date_input(
            "To",
            value=today,
            max_value=today,
            key="api_usage_to_date",
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
        st.info("Connect the database to view API usage for this date range.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                call_date AS "Date",
                COALESCE(response_status, 'unknown') AS "Status",
                COUNT(*) AS "API Requests"
            FROM public.api_calls
            WHERE call_date BETWEEN %s AND %s
            GROUP BY call_date, response_status
            ORDER BY call_date
            """,
            (start_date, end_date),
        )
        status_data = pd.DataFrame(
            cursor.fetchall(),
            columns=["Date", "Status", "API Requests"],
        )

        cursor.execute(
            """
            SELECT
                call_date AS "Date",
                api_name AS "API",
                COUNT(*) AS "API Requests"
            FROM public.api_calls
            WHERE call_date BETWEEN %s AND %s
            GROUP BY call_date, api_name
            ORDER BY call_date, api_name
            """,
            (start_date, end_date),
        )
        api_data = pd.DataFrame(
            cursor.fetchall(),
            columns=["Date", "API", "API Requests"],
        )

        cursor.execute(
            """
            SELECT
                call_date AS "Date",
                COALESCE(query_text, '(no search text)') AS "Search",
                COUNT(*) AS "Failures"
            FROM public.api_calls
            WHERE response_status = 'failure'
              AND call_date BETWEEN %s AND %s
            GROUP BY call_date, query_text
            HAVING COUNT(*) > 10
            ORDER BY call_date DESC, "Failures" DESC
            """,
            (start_date, end_date),
        )
        failure_data = pd.DataFrame(
            cursor.fetchall(),
            columns=["Date", "Search", "Failures"],
        )
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error("Unable to load API usage for the selected date range.")
        st.caption(str(exc))
        return
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()

    if status_data.empty:
        st.info("No API request data is available for this date range.")
        return

    total_requests = int(status_data["API Requests"].sum())
    successful_requests = int(
        status_data.loc[status_data["Status"].eq("success"), "API Requests"].sum()
    )
    failed_requests = int(
        status_data.loc[status_data["Status"].eq("failure"), "API Requests"].sum()
    )
    success_rate = successful_requests / total_requests * 100 if total_requests else 0

    metric_cols = st.columns(4)
    for column, label, value, help_text in zip(
        metric_cols,
        ["API requests", "Successful requests", "Failed requests", "Success rate"],
        [total_requests, successful_requests, failed_requests, f"{success_rate:.1f}%"],
        ["Selected period", "Selected period", "Selected period", "Selected period"],
    ):
        column.metric(label, f"{value:,}" if isinstance(value, int) else value, help=help_text)

    st.markdown("### Request status over time")
    status_chart = (
        alt.Chart(status_data)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("API Requests:Q", title="API requests"),
            color=alt.Color("Status:N", title="Response status"),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Status:N", title="Response status"),
                alt.Tooltip("API Requests:Q", title="API requests", format=","),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(status_chart, use_container_width=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("### Requests by API")
        if api_data.empty:
            st.info("No API breakdown is available.")
        else:
            api_summary = (
                api_data.groupby("API", as_index=False)["API Requests"]
                .sum()
                .sort_values("API Requests", ascending=False)
            )
            st.bar_chart(
                api_summary.set_index("API"),
                y="API Requests",
                use_container_width=True,
            )

    with chart_col2:
        st.markdown("### Daily request volume")
        daily_data = (
            api_data.groupby("Date", as_index=False)["API Requests"]
            .sum()
            .set_index("Date")
        )
        st.line_chart(daily_data, y="API Requests", use_container_width=True)

    st.markdown("### Searches with more than 10 failures")
    if failure_data.empty:
        st.success("No search exceeded 10 failures in the selected date range.")
    else:
        st.dataframe(failure_data, use_container_width=True, hide_index=True)
