import streamlit as st


def render_footer():


    st.markdown("---")

    f1, f2, f3, f4, f5 = st.columns(5)

    with f1:
        st.caption("📱 Senior-Friendly")

    with f2:
        st.caption("🌍 12 Indian Languages")

    with f3:
        st.caption("🤖 AI-Powered: Text-To-Speech and Translation")

    with f4:
        st.caption("🏏 Live Cricket Scores")

    with f5:
        st.caption("☀️ Weather Forecast")

    st.caption("---")

    col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

    with col1:
        with st.expander("📋 Privacy Policy"):
            try:
                with open("privacy-policy.md", "r") as f:
                    st.markdown(f.read())

            except FileNotFoundError:
                st.error("Privacy policy file not found.")
