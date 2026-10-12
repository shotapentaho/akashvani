"""Charts-only views for the password-protected admin panel."""

import pandas as pd
import streamlit as st


def show_charts():
    """Display database-backed charts without tabular dashboard details."""
    st.header("📈 Admin Charts")
    st.markdown("API usage trends, response status, and recurring failures.")

    try:
        from utils.database import get_connection

        conn = get_connection()
    except Exception as exc:
        st.warning(f"⚠️ Database not available: {exc}")
        return

    if conn is None:
        st.info("💾 Database connection required for charts.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT call_date, response_status, COUNT(*)
            FROM public.api_calls
            GROUP BY call_date, response_status
            ORDER BY call_date DESC;
        """)
        rows = cursor.fetchall()

        if not rows:
            st.info("📭 No API call data is available yet.")
            return

        data = pd.DataFrame(
            rows,
            columns=["Call Date", "Response Status", "Calls"],
        )
        data["Response Status"] = data["Response Status"].fillna("unknown")
        chart_data = (
            data.pivot_table(
                index="Call Date",
                columns="Response Status",
                values="Calls",
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
        )
        st.line_chart(chart_data, use_container_width=True)

        st.markdown("---")
        st.subheader("📈 Historical API Usage (Last 7 Days)")
        cursor.execute("""
            SELECT
                call_date,
                api_name,
                COUNT(*) AS calls
            FROM public.api_calls
            WHERE call_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY call_date, api_name
            ORDER BY call_date ASC
        """)
        history_rows = cursor.fetchall()

        if history_rows:
            history_data = pd.DataFrame(
                history_rows,
                columns=["Date", "API", "Calls"],
            )
            history_chart = (
                history_data.pivot_table(
                    index="Date",
                    columns="API",
                    values="Calls",
                    aggfunc="sum",
                    fill_value=0,
                )
                .sort_index()
            )
            st.line_chart(history_chart, use_container_width=True)
        else:
            st.info("📭 No API usage data is available for the last 7 days.")

        st.markdown("---")
        st.subheader("⚠️ Searches with More Than 10 Failures in a Day")
        cursor.execute("""
            SELECT
                call_date,
                COALESCE(query_text, '(no search text)') AS search,
                COUNT(*) AS failure_count
            FROM public.api_calls
            WHERE response_status = 'failure'
              AND call_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY call_date, query_text
            HAVING COUNT(*) > 10
            ORDER BY call_date DESC, failure_count DESC
        """)
        failure_rows = cursor.fetchall()

        if failure_rows:
            failure_data = pd.DataFrame(
                failure_rows,
                columns=["Date", "Search", "Failures"],
            )
            st.bar_chart(
                failure_data.pivot_table(
                    index="Search",
                    columns="Date",
                    values="Failures",
                    aggfunc="sum",
                    fill_value=0,
                ),
                use_container_width=True,
            )
            st.dataframe(failure_data, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No search exceeded 10 failures on any day in the last 7 days.")
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        st.warning("⚠️ Unable to load API call chart data.")
    finally:
        try:
            conn.close()
        except Exception:
            pass