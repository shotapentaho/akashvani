import streamlit as st

from utils.song_fetcher import get_song_results


def render_songs(
    query, serpapi_enabled, serpapi_key, results_count, db_tracking_enabled,
    track_search_query, language_code, duration_key, session_id,
    record_api_call,
):
    st.session_state.api_calls_today += 1
    st.markdown("---")
    st.markdown("## 🎵 Songs and Music")

    if not serpapi_enabled:
        st.warning(
            "Song search is not configured yet. Please try a news topic "
            "or contact support."
        )
    else:
        try:
            with st.spinner(f"🎵 Finding songs for '{query}'..."):
                song_results = get_song_results(
                    query,
                    serpapi_key,
                    top_k=results_count,
                )

            if song_results:
                st.success(f"Found {len(song_results)} music results.")
                for index, song in enumerate(song_results, start=1):
                    st.markdown(
                        f"### {index}. [{song['title']}]({song['url']})"
                    )
                    if song.get("description"):
                        st.caption(song["description"])
                    st.caption(f"Source: {song['source']}")

                try:
                    record_api_call(
                        "serpapi",
                        query,
                        "success",
                        len(song_results),
                    )
                except Exception as e:
                    print(f"Tracking error: {e}")

                if db_tracking_enabled:
                    try:
                        track_search_query(
                            query,
                            language_code,
                            len(song_results),
                            "serpapi",
                            duration_key,
                            st.session_state.session_id,
                        )
                    except Exception as e:
                        print(f"Tracking error: {e}")
            else:
                st.info(
                    "No songs were found. Try a language or artist, "
                    "for example: Malayalam songs."
                )
        except Exception as e:
            print(f"Song search error: {e}")
            st.error(
                "⚠️ Song search is temporarily unavailable. "
                "Please try again later."
            )
