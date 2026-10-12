"""Charts-only views for the password-protected admin panel."""

import pandas as pd
import streamlit as st


def show_charts():
    """Display database-backed charts without tabular dashboard details."""
    st.header("📈 Admin Charts")
    st.markdown("API call trends grouped by response status.")

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
        cursor.close()

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
