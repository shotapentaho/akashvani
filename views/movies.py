import streamlit as st

from utils.movie_fetcher import (
    extract_movie_title,
    get_imdb_rating,
    get_imdb_reviews,
    get_rotten_tomatoes_rating,
    get_rotten_tomatoes_reviews,
)
from utils.translator import (
    create_movie_review_script,
    translate_to_language,
)
from utils.tts_handler import is_tts_available, text_to_speech
from utils.web_search_fetcher import get_youtube_search_results


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

    imdb_rating = None
    try:
        with st.spinner(f"🔎 Finding IMDb rating and director for '{movie_title}'..."):
            imdb_rating = get_imdb_rating(movie_title, serpapi_key)
        record_api_call(
            "serpapi_imdb_rating",
            movie_title,
            "success" if imdb_rating else "failure",
            int(bool(imdb_rating)),
        )
    except Exception as e:
        print(f"IMDb rating search error: {e}")
        record_api_call("serpapi_imdb_rating", movie_title, "failure", 0)
        st.warning("IMDb movie details are temporarily unavailable.")

    if imdb_rating:
        if imdb_rating.get("rating"):
            st.metric("IMDb rating (out of 10)", imdb_rating["rating"])
        for field, label in (
            ("director", "Director"),
            ("producer", "Producer"),
            ("actors", "Actors"),
            ("writers", "Writers"),
        ):
            if imdb_rating.get(field):
                st.write(f"**{label}:** {imdb_rating[field]}")
        st.link_button("View on IMDb", imdb_rating["url"])

    rotten_tomatoes_rating = None
    try:
        with st.spinner(
            f"🔎 Finding Rotten Tomatoes Tomatometer for '{movie_title}'..."
        ):
            rotten_tomatoes_rating = get_rotten_tomatoes_rating(
                movie_title,
                serpapi_key,
            )
        record_api_call(
            "serpapi_rotten_tomatoes_rating",
            movie_title,
            "success" if rotten_tomatoes_rating else "failure",
            int(bool(rotten_tomatoes_rating)),
        )
    except Exception as e:
        print(f"Rotten Tomatoes rating search error: {e}")
        record_api_call(
            "serpapi_rotten_tomatoes_rating",
            movie_title,
            "failure",
            0,
        )
        st.warning("The Rotten Tomatoes Tomatometer is temporarily unavailable.")

    if rotten_tomatoes_rating:
        st.metric(
            "Rotten Tomatoes Tomatometer (%)",
            rotten_tomatoes_rating["rating"],
        )
        st.link_button("View on Rotten Tomatoes", rotten_tomatoes_rating["url"])

    imdb_reviews = []
    try:
        with st.spinner(f"🔎 Finding IMDb reviews for '{movie_title}'..."):
            imdb_reviews = get_imdb_reviews(
                movie_title,
                serpapi_key,
                top_k=results_count,
            )
        record_api_call(
            "serpapi_imdb_reviews",
            movie_title,
            "success" if imdb_reviews else "failure",
            len(imdb_reviews),
        )
    except Exception as e:
        print(f"IMDb review search error: {e}")
        record_api_call("serpapi_imdb_reviews", movie_title, "failure", 0)
        st.warning("IMDb reviews are temporarily unavailable.")

    rotten_tomatoes_reviews = []
    try:
        with st.spinner(f"🔎 Finding Rotten Tomatoes reviews for '{movie_title}'..."):
            rotten_tomatoes_reviews = get_rotten_tomatoes_reviews(
                movie_title,
                serpapi_key,
                top_k=results_count,
            )
        record_api_call(
            "serpapi_rotten_tomatoes_reviews",
            movie_title,
            "success" if rotten_tomatoes_reviews else "failure",
            len(rotten_tomatoes_reviews),
        )
    except Exception as e:
        print(f"Rotten Tomatoes review search error: {e}")
        record_api_call(
            "serpapi_rotten_tomatoes_reviews",
            movie_title,
            "failure",
            0,
        )
        st.warning("Rotten Tomatoes reviews are temporarily unavailable.")

    reviews = imdb_reviews + rotten_tomatoes_reviews
    if imdb_reviews:
        st.markdown("### IMDb reviews")
        st.caption(
            "Short excerpts from IMDb review pages found through search. "
            "Open IMDb for each complete review."
        )
        _render_reviews(imdb_reviews, language_code, client)
    if rotten_tomatoes_reviews:
        st.markdown("### Rotten Tomatoes reviews")
        st.caption(
            "Short excerpts from Rotten Tomatoes review pages found through search. "
            "Open Rotten Tomatoes for each complete review."
        )
        _render_reviews(rotten_tomatoes_reviews, language_code, client)

    youtube_videos = []
    try:
        with st.spinner(f"🔎 Finding YouTube videos for '{movie_title}'..."):
            youtube_videos = get_youtube_search_results(
                f"{movie_title} movie",
                serpapi_key,
                top_k=results_count,
            )
        record_api_call(
            "serpapi_movie_youtube",
            movie_title,
            "success" if youtube_videos else "failure",
            len(youtube_videos),
        )
    except Exception as e:
        print(f"Movie YouTube search error: {e}")
        record_api_call("serpapi_movie_youtube", movie_title, "failure", 0)
        st.warning("YouTube movie videos are temporarily unavailable.")

    if youtube_videos:
        st.markdown("### YouTube videos")
        for index, video in enumerate(youtube_videos, start=1):
            st.markdown(f"**{video['title']}**")
            st.link_button(f"Watch on YouTube ({index})", video["url"])

    if not reviews:
        st.info(
            f"No review excerpts were found for '{movie_title}'. "
            "Try checking the movie title or using a shorter title."
        )
        return

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
            "The review excerpts are still available above."
        )


def _render_reviews(reviews, language_code, client):
    for index, review in enumerate(reviews, start=1):
        st.markdown(f"#### {index}. {review['title']}")
        review_text = review["text"]
        if language_code != "en":
            review_text = translate_to_language(
                review_text,
                language_code,
                client,
            )
        st.write(review_text)
        st.link_button(f"Read review on {review['source']}", review["url"])
