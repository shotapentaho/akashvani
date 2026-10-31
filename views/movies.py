import altair as alt
import pandas as pd
import streamlit as st

from utils.movie_fetcher import (
    extract_movie_title,
    get_gemini_movie_ratings,
    get_imdb_reviews,
    get_rotten_tomatoes_reviews,
)
from utils.translator import (
    create_movie_review_script,
    translate_to_language,
)
from utils.tts_handler import is_tts_available, text_to_speech
from utils.web_search_fetcher import get_youtube_search_results


def _cached_movie_rating(movie_title, source, loader):
    """Reuse one rating snapshot for a movie during the current session."""
    cache = st.session_state.setdefault("movie_rating_cache", {})
    cache_key = (movie_title.casefold(), source)
    if cache_key not in cache:
        cache[cache_key] = loader()
    return cache[cache_key]


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
    st.markdown("## 🎬 Movie Ratings")

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
                gemini_movie_data = _cached_movie_rating(
                    movie_title,
                    "gemini",
                    lambda: get_gemini_movie_ratings(
                        movie_title,
                        gemini_api_key,
                    ),
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
                movie_title,
                language_code,
                speech_speed,
                voice_selection,
                client,
            )
        else:
            st.info("No ratings were found in the grounded results.")

    _render_primary_ratings(
        gemini_ratings,
        language_code,
        client,
    )

    if not serpapi_enabled:
        st.info(
            "Movie ratings use Gemini. Review excerpts and YouTube videos "
            "require SerpAPI."
        )
        return

    youtube_videos = []
    try:
        with st.spinner(f"🔎 Finding YouTube videos for '{movie_title}'..."):
            youtube_videos = _cached_movie_rating(
                movie_title,
                "serpapi_youtube",
                lambda: get_youtube_search_results(
                    f'"{movie_title}" movie rating review',
                    serpapi_key,
                    top_k=results_count,
                ),
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


def _build_rating_chart_data(ratings):
    """Keep one chart row for every supported rating returned by Gemini."""
    scale_10_sources = {"IMDb", "BookMyShow"}
    scale_100_labels = {"Tomatometer", "Popcornmeter"}
    chart_rows = []

    for rating in ratings:
        source = rating.get("source")
        label = rating.get("label")
        scale = rating.get("scale")
        if (
            (source in scale_10_sources and scale == 10)
            or (
                source == "Rotten Tomatoes"
                and label in scale_100_labels
                and scale == 100
            )
        ):
            chart_rows.append(
                {
                    "Rating": label,
                    "Source": source,
                    "Score": float(rating["rating"]),
                    "Scale": scale,
                    "Order": len(chart_rows),
                }
            )

    label_counts = {}
    for row in chart_rows:
        label_counts[row["Rating"]] = label_counts.get(row["Rating"], 0) + 1
    label_indexes = {}
    for row in chart_rows:
        label = row["Rating"]
        label_indexes[label] = label_indexes.get(label, 0) + 1
        row["Chart Rating"] = (
            f"{label} ({label_indexes[label]})"
            if label_counts[label] > 1
            else label
        )

    return pd.DataFrame(
        chart_rows,
        columns=["Rating", "Chart Rating", "Source", "Score", "Scale", "Order"],
    )


def _render_gemini_rating_charts(
    ratings,
    movie_title,
    language_code,
    speech_speed,
    voice_selection,
    client,
):
    chart_data = _build_rating_chart_data(ratings)
    chart_data_10 = chart_data[
        chart_data["Source"].isin({"IMDb", "BookMyShow"})
        & (chart_data["Scale"] == 10)
    ]
    chart_data_100 = chart_data[
        (chart_data["Source"] == "Rotten Tomatoes")
        & chart_data["Rating"].isin({"Tomatometer", "Popcornmeter"})
        & (chart_data["Scale"] == 100)
    ]

    chart_10 = (
        alt.Chart(chart_data_10)
        .mark_bar()
        .encode(
            x=alt.X(
                "Chart Rating:N",
                sort=alt.SortField(field="Order", order="ascending"),
                axis=alt.Axis(labelAngle=-35),
            ),
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
            x=alt.X(
                "Chart Rating:N",
                sort=alt.SortField(field="Order", order="ascending"),
                axis=alt.Axis(labelAngle=-35),
            ),
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

    letterboxd_ratings = [
        rating
        for rating in ratings
        if rating["source"] == "Letterboxd" and rating["scale"] == 5
    ]
    if letterboxd_ratings:
        rating = letterboxd_ratings[0]
        rating_text = rating.get("rating_text", f"{rating['rating']:g}")
        st.markdown("#### Letterboxd")
        st.metric("User rating", _format_letterboxd_stars(rating["rating"]))
        st.caption(f"{rating_text} out of 5 stars")

    rating_summary = _build_rating_summary(ratings, movie_title)
    if rating_summary:
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


def _format_letterboxd_stars(rating):
    """Render a five-star Letterboxd score, supporting half-star values."""
    rounded_rating = max(0, min(5, round(float(rating) * 2) / 2))
    full_stars = int(rounded_rating)
    half_star = rounded_rating % 1 == 0.5
    empty_stars = 5 - full_stars - int(half_star)
    return "★" * full_stars + ("⯨" if half_star else "") + "☆" * empty_stars


def _build_rating_summary(ratings, movie_title):
    """Create a concise spoken summary of the displayed movie ratings."""
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
        elif rating["source"] == "Letterboxd" and rating["scale"] == 5:
            rating_text = rating.get("rating_text", f"{rating['rating']:g}")
            summary_parts.append(
                f"Letterboxd is rated around {rating_text} out of 5 stars"
            )
    if not summary_parts:
        return ""
    return (
        f"Ratings for {movie_title}: "
        + ". ".join(summary_parts)
        + "."
    )


def _render_primary_ratings(
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
    scores = (
        ("IMDb rating (out of 10)", gemini_imdb_rating),
        ("Rotten Tomatoes Tomatometer (%)", gemini_tomatometer),
    )
    columns = st.columns(len(scores))
    for column, (label, score) in zip(columns, scores):
        if language_code != "en":
            label = translate_to_language(label, language_code, client)
        column.metric(label, score if score is not None else "N/A")
