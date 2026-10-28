import streamlit as st

from utils.auto_search import news_query_variants
from utils.cricket_scraper import extract_score_from_article
from utils.news_fetcher import (
    _is_cricket_score_query,
    format_article,
    get_article_content,
    get_top_news,
)
from utils.translator import (
    get_ai_search_result,
    get_ai_summary,
    translate_query_to_english,
    translate_to_language,
)
from utils.tts_handler import (
    get_speech_speed_display,
    is_tts_available,
    text_to_speech,
)
from utils.web_search_fetcher import (
    get_bbc_search_results,
    get_gemini_search_results,
    get_youtube_search_results,
)


def render_news(
    query, language_code, results_count, duration_key, duration_mode,
    speech_speed, voice_selection, use_ai_summary, selected_language, client,
    news_api_key, gnews_api_key, gemini_api_key, serpapi_key, serpapi_enabled,
    db_tracking_enabled, session_id, track_search_query, record_api_call,
):
            st.session_state.api_calls_today += 1

            articles = []
            api_used = "NewsAPI"
            service_error = False
            news_query = translate_query_to_english(query, client)
            search_queries = news_query_variants(news_query)

            # ===== TRY NEWSAPI FIRST =====
            try:
                with st.spinner(
                    f"📡 Fetching news for '{query}'..."
                ):
                    for search_query in search_queries:
                        articles.extend(
                            get_top_news(
                                search_query,
                                news_api_key,
                                top_k=results_count,
                                show_no_results_warning=False,
                            )
                        )

                    deduplicated = {}
                    for article in articles:
                        key = article.get("url") or article.get("title")
                        if key and key not in deduplicated:
                            deduplicated[key] = article
                    articles = list(deduplicated.values())[:results_count]

                if articles:
                    api_used = "NewsAPI"

                    try:
                        record_api_call(
                            "newsapi",
                            query,
                            "success",
                            len(articles),
                        )
                    except Exception as e:
                        print(f"Tracking error: {e}")

                    if db_tracking_enabled:
                        try:
                            track_search_query(
                                query,
                                language_code,
                                len(articles),
                                "newsapi",
                                duration_key,
                                st.session_state.session_id,
                            )

                        except Exception as e:
                            print(f"Tracking error: {e}")
                else:
                    try:
                        record_api_call(
                            "newsapi",
                            query,
                            "failure",
                            0,
                        )
                    except Exception as e:
                        print(f"Tracking error: {e}")

            except Exception as e:
                print(f"NewsAPI error: {e}")
                service_error = True


            # ===== FALLBACK TO GNEWS =====
            if not articles and gnews_api_key:
                try:
                    from utils.gnews_fetcher import get_gnews_articles

                    with st.spinner(
                        "📡 Fetching news from backup source..."
                    ):
                        for search_query in search_queries:
                            articles.extend(
                                get_gnews_articles(
                                    search_query,
                                    gnews_api_key,
                                    top_k=results_count,
                                )
                            )

                    deduplicated = {}
                    for article in articles:
                        key = article.get("url") or article.get("title")
                        if key and key not in deduplicated:
                            deduplicated[key] = article
                    articles = list(deduplicated.values())[:results_count]

                    if articles:
                        api_used = "GNews"

                        st.success(
                            f"✅ Found {len(articles)} articles "
                            "from backup source"
                        )

                        try:
                            record_api_call(
                                "gnews",
                                query,
                                "success",
                                len(articles),
                            )
                        except Exception as e:
                            print(f"Tracking error: {e}")

                        if db_tracking_enabled:
                            try:
                                track_search_query(
                                    query,
                                    language_code,
                                    len(articles),
                                    "gnews",
                                    duration_key,
                                    st.session_state.session_id,
                                )

                            except Exception as e:
                                print(f"Tracking error: {e}")
                    else:
                        try:
                            record_api_call(
                                "gnews",
                                query,
                                "failure",
                                0,
                            )
                        except Exception as e:
                            print(f"Tracking error: {e}")

                except Exception as e:
                    print(f"GNews error: {e}")
                    service_error = True


            # ===== LIVE WEB SEARCH FALLBACK =====
            if not articles:
                web_articles = []
                with st.spinner("🌐 Searching live web sources..."):
                    if gemini_api_key:
                        gemini_articles = get_gemini_search_results(
                            news_query,
                            gemini_api_key,
                            results_count,
                        )
                        web_articles.extend(gemini_articles)
                        try:
                            record_api_call(
                                "gemini",
                                query,
                                "success" if gemini_articles else "failure",
                                len(gemini_articles),
                            )
                        except Exception as e:
                            print(f"Tracking error: {e}")

                    if serpapi_key:
                        bbc_articles = get_bbc_search_results(
                            news_query,
                            serpapi_key,
                            results_count,
                        )
                        web_articles.extend(bbc_articles)
                        try:
                            record_api_call(
                                "serpapi",
                                query,
                                "success" if bbc_articles else "failure",
                                len(bbc_articles),
                            )
                        except Exception as e:
                            print(f"Tracking error: {e}")

                        youtube_articles = get_youtube_search_results(
                            news_query,
                            serpapi_key,
                            results_count,
                        )
                        web_articles.extend(youtube_articles)
                        try:
                            record_api_call(
                                "serpapi",
                                query,
                                "success" if youtube_articles else "failure",
                                len(youtube_articles),
                            )
                        except Exception as e:
                            print(f"Tracking error: {e}")

                deduplicated = {}
                for article in web_articles:
                    key = article.get("url") or article.get("title")
                    if key and key != "#" and key not in deduplicated:
                        deduplicated[key] = article
                articles = list(deduplicated.values())[:results_count]

                if articles:
                    api_used = "Live web search"
                    service_error = False

            # ===== OPENAI FALLBACK =====
            if not articles:
                with st.spinner("🤖 Searching with AI..."):
                    articles = get_ai_search_result(news_query, client)

                if articles:
                    api_used = "OpenAI"
                    service_error = False
                    st.info(
                        "🤖 No recent articles were found. "
                        "Here is an OpenAI-generated answer based on available knowledge."
                    )

                    try:
                        record_api_call(
                            "openai",
                            query,
                            "success",
                            len(articles),
                        )
                    except Exception as e:
                        print(f"Tracking error: {e}")

            # ===== NO RESULTS =====
            if not articles:
                if service_error:
                    st.error(
                        "⚠️ We're experiencing technical difficulties"
                    )
                    st.info(
                        "📧 Please try again in a few minutes or contact "
                        "**support@cxloop.co**"
                    )

                else:
                    st.error("❌ No news found at the moment")
                    st.info(
                        "**This could be because:**\n"
                        "- Daily news quota reached "
                        "(resets at midnight UTC)\n"
                        "- No recent articles for this topic\n"
                        "- Try a different search term"
                    )

                    st.markdown(
                        "**Popular topics:** Elections, Sports, Business, "
                        "Weather, Health, Technology, India, Cricket"
                    )


            # ===== DISPLAY RESULTS =====
            else:
                # ===== CRICKET SCORES =====
                if _is_cricket_score_query(news_query):
                    st.markdown("---")
                    st.markdown("## 🏏 Cricket Scores")

                    live_score_found = False

                    # ===== TRY SERPAPI =====
                    if serpapi_enabled:
                        try:
                            from utils.cricket_live import (
                                get_live_cricket_scores,
                                display_cricket_score,
                                create_cricket_score_speech,
                            )

                            with st.spinner(
                                "🔍 Fetching live cricket scores..."
                            ):
                                match_data = get_live_cricket_scores(news_query)

                            if match_data:
                                live_score_found = True

                                try:
                                    record_api_call(
                                        "serpapi",
                                        query,
                                        "success",
                                        1,
                                    )
                                except Exception as e:
                                    print(f"Tracking error: {e}")

                                display_cricket_score(match_data)

                                english_score_text = (
                                    create_cricket_score_speech(
                                        match_data
                                    )
                                )
                                slow_mode = speech_speed == "Slow 🐢"

                                if language_code == "en":
                                    st.markdown("---")
                                    st.write("**📝 Score in English:**")
                                    st.info(english_score_text)

                                    try:
                                        st.write("**🔊 Listen in English:**")

                                        audio_en = text_to_speech(
                                            english_score_text,
                                            "en",
                                            slow=slow_mode,
                                            voice=voice_selection,
                                        )

                                        if audio_en:
                                            st.audio(
                                                audio_en,
                                                format="audio/mp3",
                                            )

                                    except Exception as e:
                                        print(f"English TTS error: {e}")
                                else:
                                    st.markdown("---")

                                    try:
                                        with st.spinner(
                                            f"🌐 Translating to "
                                            f"{selected_language}..."
                                        ):
                                            score_text_translated = (
                                                translate_to_language(
                                                    english_score_text,
                                                    language_code,
                                                    client,
                                                )
                                            )

                                        st.write(
                                            f"**📝 Score in "
                                            f"{selected_language}:**"
                                        )
                                        st.success(score_text_translated)

                                        tts_available = is_tts_available(
                                            language_code, voice_selection
                                        )

                                        if tts_available:
                                            st.write(
                                                f"**🔊 Listen in "
                                                f"{selected_language}:**"
                                            )

                                            audio_translated = (
                                                text_to_speech(
                                                    score_text_translated,
                                                    language_code,
                                                    slow=slow_mode,
                                                    voice=voice_selection,
                                                )
                                            )

                                            if audio_translated:
                                                st.audio(
                                                    audio_translated,
                                                    format="audio/mp3",
                                                )

                                        else:
                                            st.info(
                                                "Voice narration not available "
                                                f"for {selected_language}"
                                            )

                                    except Exception as e:
                                        print(
                                            f"Translation/TTS error: {e}"
                                        )

                                if match_data.get("url"):
                                    st.markdown(
                                        "[📰 Full Match Details]"
                                        f"({match_data['url']})"
                                    )

                        except Exception as e:
                            print(f"SerpAPI error: {e}")
                            live_score_found = False


                    # ===== FALLBACK: NEWS EXTRACTION =====
                    if not live_score_found:
                        if serpapi_enabled:
                            st.info(
                                "🏏 No live scores via SerpAPI. "
                                "Checking news articles..."
                            )

                        try:
                            cricket_scores_found = []

                            for article in articles[:5]:
                                score = extract_score_from_article(article)

                                if score:
                                    cricket_scores_found.append(score)

                            if cricket_scores_found:
                                match = cricket_scores_found[0]

                                cricket_html = f"""
                                <div class='cricket-score-box'>
                                    <div class='cricket-match-header'>
                                        🏏 {match['team1']} vs {match['team2']}
                                    </div>
                                    <div class='cricket-team'>
                                        {match['team1']}:
                                        <span class='cricket-score'>
                                            {match['team1_score']}
                                        </span>
                                    </div>
                                    <div class='cricket-team'>
                                        {match['team2']}:
                                        <span class='cricket-score'>
                                            {match['team2_score']}
                                        </span>
                                    </div>
                                    <div class='cricket-series'>
                                        📅 {match['published']} |
                                        📰 {match['source']}
                                    </div>
                                </div>
                                """

                                st.markdown(
                                    cricket_html,
                                    unsafe_allow_html=True,
                                )

                                score_text = (
                                    f"Cricket score: "
                                    f"{match['team1']} scored "
                                    f"{match['team1_score']}. "
                                    f"{match['team2']} scored "
                                    f"{match['team2_score']}."
                                )
                                slow_mode = speech_speed == "Slow 🐢"

                                if language_code == "en":
                                    st.write("**📝 Score in English:**")
                                    st.info(score_text)

                                    try:
                                        st.write("**🔊 Listen in English:**")

                                        audio_en = text_to_speech(
                                            score_text,
                                            "en",
                                            slow=slow_mode,
                                            voice=voice_selection,
                                        )

                                        if audio_en:
                                            st.audio(
                                                audio_en,
                                                format="audio/mp3",
                                            )

                                    except Exception as e:
                                        print(f"English TTS error: {e}")
                                else:
                                    st.markdown("---")

                                    try:
                                        with st.spinner(
                                            f"🌐 Translating to "
                                            f"{selected_language}..."
                                        ):
                                            score_text_translated = (
                                                translate_to_language(
                                                    score_text,
                                                    language_code,
                                                    client,
                                                )
                                            )

                                        st.write(
                                            f"**📝 Score in "
                                            f"{selected_language}:**"
                                        )
                                        st.success(score_text_translated)

                                        audio_translated = text_to_speech(
                                            score_text_translated,
                                            language_code,
                                            slow=slow_mode,
                                            voice=voice_selection,
                                        )

                                        if audio_translated:
                                            st.audio(
                                                audio_translated,
                                                format="audio/mp3",
                                            )
                                        else:
                                            st.info(
                                                "Voice narration not available "
                                                f"for {selected_language}"
                                            )

                                    except Exception as e:
                                        print(
                                            f"Translation/TTS error: {e}"
                                        )

                                if match.get("url"):
                                    st.markdown(
                                        f"[📰 Read Full Article]({match['url']})"
                                    )

                            else:
                                st.info(
                                    "🏏 No cricket scores found in recent "
                                    "articles. Check news articles below."
                                )

                        except Exception as e:
                            print(f"Cricket extraction error: {e}")

                    st.markdown("---")


                # ===== NEWS ARTICLES =====
                st.markdown("## 📰 News Articles")

                st.markdown(
                    f"<div class='success-box'>"
                    f"✅ Found {len(articles)} articles for '{query}'"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("---")

                for idx, article in enumerate(articles, 1):
                    try:
                        formatted_article = format_article(article)
                        article_content = get_article_content(
                            formatted_article
                        )
                        article_title = (
                            formatted_article.get("title")
                            or "No Title"
                        )

                        with st.expander(
                            f"📄 Article {idx}: "
                            f"{article_title[:80]}...",
                            expanded=(idx == 1),
                        ):
                            st.subheader(article_title)

                            c1, c2, c3 = st.columns(3)

                            with c1:
                                st.caption(
                                    f"📰 "
                                    f"{formatted_article.get('source', 'Unknown')[:50]}"
                                )

                            with c2:
                                st.caption(
                                    f"📅 "
                                    f"{formatted_article.get('published_at', 'N/A')}"
                                )

                            with c3:
                                st.caption(
                                    f"✍️ "
                                    f"{formatted_article.get('author', 'Unknown')[:30]}"
                                )

                            st.markdown("---")

                            try:
                                if use_ai_summary:
                                    with st.spinner(
                                        f"🤖 Creating "
                                        f"{duration_mode.lower()} summary..."
                                    ):
                                        summary = get_ai_summary(
                                            article_content,
                                            language_code,
                                            client,
                                            duration_key,
                                        )

                                    st.write(
                                        "**📝 Summary "
                                        "(Simplified for You):**"
                                    )
                                    st.info(summary)
                                    audio_content = summary

                                else:
                                    st.write("**📝 Article Content:**")
                                    st.write(article_content)
                                    audio_content = article_content

                                st.markdown("---")

                                if language_code != "en":
                                    with st.spinner(
                                        f"🌐 Translating to "
                                        f"{selected_language}..."
                                    ):
                                        audio_content = (
                                            translate_to_language(
                                                audio_content,
                                                language_code,
                                                client,
                                            )
                                        )

                                    st.write(
                                        f"**🗣️ Content in "
                                        f"{selected_language}:**"
                                    )
                                    st.success(audio_content)
                                    st.markdown("---")

                                st.write(
                                    f"**🔊 Listen to this article in "
                                    f"{selected_language}:**"
                                )

                                pcol1, pcol2, pcol3 = st.columns(
                                    [3, 1, 1]
                                )

                                with pcol1:
                                    slow_mode = speech_speed == "Slow 🐢"

                                    audio = text_to_speech(
                                        audio_content,
                                        language_code,
                                        slow=slow_mode,
                                        voice=voice_selection,
                                    )

                                    if audio:
                                        st.audio(
                                            audio,
                                            format="audio/mp3",
                                        )
                                    else:
                                        st.info(
                                            "📝 Voice narration not available "
                                            f"for {selected_language}"
                                        )

                                with pcol2:
                                    st.caption(
                                        f"Speed: "
                                        f"{get_speech_speed_display(slow_mode)}"
                                    )

                                with pcol3:
                                    article_url = (
                                        formatted_article.get("url")
                                        or "#"
                                    )

                                    if article_url != "#":
                                        st.markdown(
                                            f"[🔗 Read Full Article]"
                                            f"({article_url})"
                                        )

                            except Exception as e:
                                print(
                                    f"Article processing error: {e}"
                                )
                                st.warning(
                                    "⚠️ Unable to process this article"
                                )

                            st.markdown("---")

                    except Exception as e:
                        print(
                            f"Error displaying article {idx}: {e}"
                        )
