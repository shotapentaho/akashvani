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

    col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

    with col1:
        with st.expander("📋 Privacy Policy"):
            try:
                with open("privacy-policy.md", "r") as f:
                    st.markdown(f.read())

            except FileNotFoundError:
                st.error("Privacy policy file not found.")

    with col2:
        st.markdown(
            (
                '<a href="https://play.google.com/store/apps/details?id='
                'co.cxloop.akashvani&hl=en_US&gl=US&desktop=1" '
                'target="_blank" '
                'rel="noopener noreferrer">'
                "⭐⭐⭐⭐⭐ Rate us on Google Play"
                "</a>"
            ),
            unsafe_allow_html=True,
        )
