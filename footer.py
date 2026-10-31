from pathlib import Path

import streamlit as st


def render_footer():
    st.markdown("---")

    f1, f2, f3 = st.columns(3)

    with f1:
        st.caption("📱 Senior-Friendly")

    with f2:
        st.caption("🤖 News-To-Speech your language of choice")

    with f3:
        st.caption("☀️  Weather 🏏 Live Cricket Scores 🎬 movie ratings 🎵 songs ")

    st.caption("---")

    col1, col2 = st.columns([0.3, 0.4])

    with col1:
        with st.expander("📋 Privacy Policy"):
            privacy_policy_path = Path(__file__).with_name("privacy-policy.md")
            if privacy_policy_path.is_file():
                st.markdown(privacy_policy_path.read_text(encoding="utf-8"))
            else:
                st.error("Privacy policy file not found.")

    with col2:
        st.markdown(
            '<a href="market://details?id=co.cxloop.akashvani" '
            'target="_self">📱 Open in Google Play app</a>',
            unsafe_allow_html=True,
        )
