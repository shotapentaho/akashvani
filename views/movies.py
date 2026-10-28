import streamlit as st

from utils.movie_fetcher import extract_movie_title, get_imdb_reviews
from utils.translator import (
    create_movie_review_script,
    translate_to_language,
)
from utils.tts_handler import is_tts_available, text_to_speech


def render_movie_reviews(
    query,
    language_code,
    selected_language,
    speech_speed,
    voice_selection,
    client,
    serpapi_enabled,
    serpapi_key,
    results_count,
    record_api_call,
):
    st.session_state.api_calls_today += 1
    st.markdown("---")
    st.markdown("## 🎬 Movie Reviews")

    movie_title = extract_movie_title(query)
    if not movie_title:
        st.info("Please include the movie title, for example: movie review of Dune.")
        return

    if not serpapi_enabled:
        st.warning(
            "IMDb review search is not configured. Please try again later "
            "or contact support."
        )
        return

    try:
        with st.spinner(f"🔎 Finding IMDb reviews for '{movie_title}'..."):
            reviews = get_imdb_reviews(
                movie_title,
                serpapi_key,
                top_k=results_count,
            )
        record_api_call(
            "serpapi_imdb_reviews",
            movie_title,
            "success" if reviews else "failure",
            len(reviews),
        )
    except Exception as e:
        print(f"IMDb review search error: {e}")
        record_api_call("serpapi_imdb_reviews", movie_title, "failure", 0)
        st.error("IMDb reviews are temporarily unavailable. Please try again later.")
        return

    if not reviews:
        st.info(
            f"No IMDb review excerpts were found for '{movie_title}'. "
            "Try checking the movie title or using a shorter title."
        )
        return

    st.caption(
        "Short excerpts from IMDb review pages found through search. "
        "Open IMDb for each complete review."
    )
    for index, review in enumerate(reviews, start=1):
        st.markdown(f"### {index}. {review['title']}")
        review_text = review["text"]
        if language_code != "en":
            review_text = translate_to_language(
                review_text,
                language_code,
                client,
            )
        st.write(review_text)
        st.link_button("Read review on IMDb", review["url"])

    try:
        with st.spinner(f"✍️ Creating a spoken review in {selected_language}..."):
            review_script = create_movie_review_script(
                movie_title,
                reviews,
                language_code,
                client,
            )
        st.markdown("---")
        st.markdown(f"### 📝 Movie review script in {selected_language}")
        st.write(review_script)

        if is_tts_available(language_code, voice_selection):
            st.markdown(f"### 🔊 Listen in {selected_language}")
            audio = text_to_speech(
                review_script,
                language_code,
                slow=speech_speed == "Slow 🐢",
                voice=voice_selection,
            )
            if audio:
                st.audio(audio, format="audio/mp3")
            else:
                st.info(f"Voice narration is not available for {selected_language}.")
        else:
            st.info(f"Voice narration is not available for {selected_language}.")
    except Exception as e:
        print(f"Movie review script error: {e}")
        st.error(
            f"Could not create the spoken review in {selected_language}. "
            "The IMDb review excerpts are still available above."
        )
