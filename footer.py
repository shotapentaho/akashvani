import streamlit as st


def render_footer():
    tips_html = """
    <div class='header-tip'>
      <div>• Use Slow speed for clarity</div>
      <div>• Use Long duration for detailed news</div>
      <div>• Enable AI Summary for simpler language</div>
      <div>• Use headphones for better sound</div>
      <div>• Search cricket scores (e.g., India vs Aus)</div>
      <div>• Type a topic and pause for automatic search</div>
    </div>
    """
    st.markdown(tips_html, unsafe_allow_html=True)

    st.markdown("---")

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        st.caption("📱 Senior-Friendly")

    with f2:
        st.caption("🌍 12 Languages")

    with f3:
        st.caption("🤖 AI-Powered")

    with f4:
        st.caption("🏏 Live Cricket Scores")

    st.caption("---")

    st.caption(
        """
    ✨ Akashvani v1.4 from CX Data & Analytics LLC
    🗣️ 12 Indian languages · 1–3 min audio briefs · 🏏 Live cricket scores (SerpAPI)
    🔄 Dual API: NewsAPI + GNews (200 requests/day total)
    ⚡ Optimized: GPT-3.5-turbo with smart caching
    📊 Analytics: PostgreSQL insert-only tracking
    🏗️ Streamlit + OpenAI + gTTS + NewsAPI + GNews + SerpAPI + PostgreSQL
    ❤️ Crafted with accessibility in mind
    📧 Support: support@cxloop.co
    """
    )

    st.markdown("---")

    col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

    with col1:
        with st.expander("📋 Privacy Policy"):
            try:
                with open("privacy-policy.md", "r") as f:
                    st.markdown(f.read())

            except FileNotFoundError:
                st.error("Privacy policy file not found.")
