import altair as alt
import pandas as pd
import streamlit as st

from utils.movie_fetcher import (
    extract_movie_title,
    get_gemini_movie_ratings,
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


def _rerun_active_search():
    """Re-render the active search after a Streamlit button interaction."""
    st.session_state.last_search_fingerprint = None


def render_movie_reviews(
    query,
    language_code,
    selected_language,
    speech_speed,
    voice_selection,
    client,
    serpapi_enabled,
    serpapi_key,
    gemini_api_key,
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

    gemini_movie_data = None
    if gemini_api_key:
        try:
            with st.spinner(
                f"🔎 Finding grounded ratings and consensus for '{movie_title}'..."
            ):
                gemini_movie_data = get_gemini_movie_ratings(
                    movie_title,
                    gemini_api_key,
                )
            record_api_call(
                "gemini_movie_ratings",
                movie_title,
                "success" if gemini_movie_data else "failure",
                len(gemini_movie_data["ratings"]) if gemini_movie_data else 0,
            )
        except Exception as e:
            print(f"Gemini movie rating search error: {e}")
            record_api_call("gemini_movie_ratings", movie_title, "failure", 0)
            st.warning("Gemini movie ratings are temporarily unavailable.")

    gemini_ratings = (
        gemini_movie_data.get("ratings", []) if gemini_movie_data else []
    )
    if gemini_movie_data:
        st.markdown("### Ratings from Gemini")
        if gemini_ratings:
            # st.table(
            #     [
            #         {
            #             "Rating type": f"{rating['label']} ({rating['scale']})",
            #             "Rating": rating.get(
            #                 "rating_text",
            #                 f"{rating['rating']:g}",
            #             ),
            #         }
            #         for rating in gemini_ratings
            #     ]
            # )
            _render_gemini_rating_charts(
                gemini_ratings,
                language_code,
                speech_speed,
                voice_selection,
                client,
            )
        else:
            st.info("No ratings were found in the grounded results.")

    if not serpapi_enabled:
        _render_primary_ratings(
            None,
            None,
            gemini_ratings,
            language_code,
            client,
        )
        st.info(
            "IMDb and Rotten Tomatoes scores use Gemini when available. "
            "Review excerpts and YouTube videos require SerpAPI."
        )
        return

    imdb_rating = None
    try:
        with st.spinner(f"🔎 Finding IMDb rating and movie details for '{movie_title}'..."):
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

    _render_primary_ratings(
        imdb_rating,
        rotten_tomatoes_rating,
        gemini_ratings,
        language_code,
        client,
    )

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

    if rotten_tomatoes_rating:
        st.link_button("View on Rotten Tomatoes", rotten_tomatoes_rating["url"])
    if imdb_rating:
        for field, label in (
            ("release_date", "Release Date"),
            ("language", "Language"),
            ("director", "Director"),
            ("lead_cast", "Lead Cast"),
        ):
            if imdb_rating.get(field):
                st.write(f"**{label}:** {imdb_rating[field]}")

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


def _render_gemini_rating_charts(
    ratings,
    language_code,
    speech_speed,
    voice_selection,
    client,
):
    scale_10_sources = {"IMDb", "BookMyShow"}
    scale_100_sources = {"Rotten Tomatoes"}
    scale_100_labels = {"Tomatometer", "Popcornmeter"}

    chart_data = pd.DataFrame(
        [
            {
                "Rating": rating["label"],
                "Source": rating["source"],
                "Score": rating["rating"],
                "Scale": rating["scale"],
            }
            for rating in ratings
            if (
                rating["source"] in scale_10_sources
                or (
                    rating["source"] in scale_100_sources
                    and rating["label"] in scale_100_labels
                )
            )
        ],
        columns=["Rating", "Source", "Score", "Scale"],
    )
    chart_data_10 = chart_data[
        chart_data["Source"].isin(scale_10_sources)
        & (chart_data["Scale"] == 10)
    ]
    chart_data_100 = chart_data[
        chart_data["Source"].isin(scale_100_sources)
        & chart_data["Rating"].isin(scale_100_labels)
        & (chart_data["Scale"] == 100)
    ]

    chart_10 = (
        alt.Chart(chart_data_10)
        .mark_bar()
        .encode(
            x=alt.X("Rating:N", sort=None, axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 10])),
            color=alt.Color(
                "Rating:N",
                scale=alt.Scale(
                    domain=["IMDb rating", "BookMyShow user rating"],
                    range=["#f5c518", "#e85d04"],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Rating:N"),
                alt.Tooltip("Score:Q", format=".1f"),
            ],
        )
        .properties(title="IMDb and BookMyShow (Scale 10)")
    )
    chart_100 = (
        alt.Chart(chart_data_100)
        .mark_bar()
        .encode(
            x=alt.X("Rating:N", sort=None, axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "Rating:N",
                scale=alt.Scale(
                    domain=["Tomatometer", "Popcornmeter"],
                    range=["#e63946", "#457b9d"],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Rating:N"),
                alt.Tooltip("Score:Q", format=".1f"),
            ],
        )
        .properties(title="Tomatometer and Popcornmeter (Scale 100)")
    )

    columns = st.columns(2)
    if not chart_data_10.empty:
        columns[0].altair_chart(chart_10, use_container_width=True)
    else:
        columns[0].info("No IMDb or BookMyShow ratings found.")
    if not chart_data_100.empty:
        columns[1].altair_chart(chart_100, use_container_width=True)
    else:
        columns[1].info("No Tomatometer or Popcornmeter ratings found.")

    rating_summary = _build_rating_summary(ratings)
    if rating_summary and st.button(
        "🔊 Listen to ratings",
        key="movie_ratings_speech",
        on_click=_rerun_active_search,
    ):
        spoken_summary = rating_summary
        if language_code != "en":
            spoken_summary = translate_to_language(
                rating_summary,
                language_code,
                client,
            )
        if is_tts_available(language_code, voice_selection):
            audio = text_to_speech(
                spoken_summary,
                language_code,
                slow=speech_speed == "Slow 🐢",
                voice=voice_selection,
            )
            if audio:
                st.audio(audio, format="audio/mp3")
        else:
            st.info(f"Voice narration is not available for {language_code}.")


def _build_rating_summary(ratings):
    """Create a concise spoken summary for the four primary rating sources."""
    summary_parts = []
    for rating in ratings:
        if rating["source"] == "IMDb" and rating["scale"] == 10:
            summary_parts.append(f"IMDb is rated {rating['rating']:g} out of 10")
        elif rating["source"] == "BookMyShow" and rating["scale"] == 10:
            summary_parts.append(
                f"BookMyShow is rated {rating['rating']:g} out of 10"
            )
        elif (
            rating["source"] == "Rotten Tomatoes"
            and rating["label"] in {"Tomatometer", "Popcornmeter"}
            and rating["scale"] == 100
        ):
            summary_parts.append(
                f"{rating['label']} is {rating['rating']:g} out of 100"
            )
    if not summary_parts:
        return ""
    return "Here are the movie ratings: " + ". ".join(summary_parts) + "."


def _render_primary_ratings(
    imdb_rating,
    rotten_tomatoes_rating,
    gemini_ratings,
    language_code,
    client,
):
    gemini_imdb_rating = next(
        (
            rating["rating"]
            for rating in gemini_ratings
            if rating["source"] == "IMDb"
        ),
        None,
    )
    gemini_tomatometer = next(
        (
            rating["rating"]
            for rating in gemini_ratings
            if rating["source"] == "Rotten Tomatoes"
            and rating["label"] == "Tomatometer"
        ),
        None,
    )
    imdb_score = (imdb_rating or {}).get("rating")
    if imdb_score is None:
        imdb_score = gemini_imdb_rating
    tomatometer_score = (rotten_tomatoes_rating or {}).get("rating")
    if tomatometer_score is None:
        tomatometer_score = gemini_tomatometer
    scores = (
        ("IMDb rating (out of 10)", imdb_score),
        ("Rotten Tomatoes Tomatometer (%)", tomatometer_score),
    )
    columns = st.columns(len(scores))
    for column, (label, score) in zip(columns, scores):
        if language_code != "en":
            label = translate_to_language(label, language_code, client)
        column.metric(label, score if score is not None else "N/A")
