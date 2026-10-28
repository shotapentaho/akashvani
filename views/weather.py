import streamlit as st

from utils.translator import translate_to_language
from utils.tts_handler import text_to_speech
from utils.weather_fetcher import (
    extract_weather_location,
    get_current_weather,
    get_weather_condition,
    get_weather_locations,
)


def render_weather(
    query, language_code, selected_language, speech_speed, voice_selection,
    client, record_api_call,
):
    weather_location = extract_weather_location(query)
    weather = None
    weather_error = False
    weather_selection_pending = False

    try:
        with st.spinner(
            f"🌤️ Checking weather in {weather_location}..."
        ):
            weather_places = get_weather_locations(weather_location)

        if len(weather_places) > 1:
            st.session_state.weather_selection_query = query
            st.warning(
                f"Several places named '{weather_location}' were found. "
                "Click a location tile to see its weather."
            )
            selection_key = (
                f"weather_place_{weather_location.lower()}"
            )
            selected_place = st.session_state.get(selection_key)

            for row_start in range(0, len(weather_places), 3):
                row_places = weather_places[row_start:row_start + 3]
                columns = st.columns(3)
                for column, place_index in zip(
                    columns,
                    range(row_start, row_start + len(row_places)),
                ):
                    place = weather_places[place_index]
                    place_name = place.get("name") or weather_location
                    place_region = place.get("admin1")
                    place_country = place.get("country")
                    place_details = ", ".join(
                        str(part)
                        for part in [place_region, place_country]
                        if part
                    )
                    tile_label = f"📍 {place_name}"
                    if place_details:
                        tile_label += f"\n{place_details}"

                    with column:
                        if st.button(
                            tile_label,
                            key=f"{selection_key}_{place_index}",
                            use_container_width=True,
                        ):
                            st.session_state[selection_key] = place
                            selected_place = place

            if selected_place:
                weather = get_current_weather(
                    weather_location,
                    selected_place,
                )
                weather_selection_pending = False
            else:
                weather_selection_pending = True
        elif weather_places:
            weather = get_current_weather(
                weather_location,
                weather_places[0],
            )

    except Exception as e:
        print(f"Weather error: {e}")
        weather_error = True

    if weather_error:
        st.error(
            "⚠️ Weather service is not available right now. "
            "Please try again in a few minutes."
        )

    elif weather_selection_pending:
        pass

    elif not weather:
        st.warning(
            f"❌ Could not find a place named "
            f"'{weather_location}'. Please check the spelling "
            "or try a nearby city."
        )

    elif weather.get("temperature") is None:
        st.warning(
            "⚠️ Weather data for this place is incomplete right now. "
            "Please try again later."
        )

    else:
        display_location = ", ".join(
            str(part)
            for part in [
                weather.get("location"),
                weather.get("region"),
                weather.get("country"),
            ]
            if part
        )

        unit = weather.get("unit") or "°C"
        temperature = weather["temperature"]
        feels_like = weather.get("apparent_temperature")
        condition_label, condition_icon = get_weather_condition(
            weather.get("weather_code")
        )

        st.markdown("---")
        st.markdown("## 🌤️ Current Weather")
        st.markdown(f"### 📍 {display_location}")
        st.markdown(
            f"<div style='font-size: 3rem; line-height: 1.2'>"
            f"{condition_icon}</div><h3>{condition_label}</h3>",
            unsafe_allow_html=True,
        )

        st.metric(
            label="Temperature now",
            value=f"{temperature}{unit}",
        )

        if feels_like is not None:
            st.markdown(
                f"#### 🌡️ Feels like: **{feels_like}{unit}**"
            )

        forecast = weather.get("forecast") or []
        if forecast:
            st.markdown("### 📅 3-Day Forecast")
            forecast_columns = st.columns(len(forecast))
            for forecast_column, forecast_day in zip(
                forecast_columns,
                forecast,
            ):
                with forecast_column:
                    st.markdown(f"**{forecast_day['date']}**")
                    forecast_label, forecast_icon = get_weather_condition(
                        forecast_day.get("weather_code")
                    )
                    st.markdown(
                        f"<div style='font-size: 2.5rem; "
                        f"line-height: 1.2'>{forecast_icon}</div>"
                        f"<strong>{forecast_label}</strong>",
                        unsafe_allow_html=True,
                    )
                    st.metric(
                        "High",
                        f"{forecast_day['temperature_max']}{unit}",
                    )
                    st.metric(
                        "Low",
                        f"{forecast_day['temperature_min']}{unit}",
                    )

        if weather.get("timestamp"):
            timezone = weather.get("timezone", "")
            timezone_text = f" ({timezone})" if timezone else ""

            st.caption(
                f"🕒 Observed at: "
                f"{weather['timestamp']}{timezone_text}"
            )

        english_weather_text = (
            f"The current temperature in {display_location} "
            f"is {temperature} degrees Celsius"
        )

        if feels_like is not None:
            english_weather_text += (
                f", and it feels like "
                f"{feels_like} degrees Celsius"
            )

        english_weather_text += "."

        try:
            record_api_call(
                "open-meteo",
                query,
                "success",
                1,
            )
        except Exception as e:
            print(f"Tracking error: {e}")

        st.markdown("---")
        st.write("**📝 Weather in English:**")
        st.info(english_weather_text)

        slow_mode = speech_speed == "Slow 🐢"

        try:
            st.write("**🔊 Listen in English:**")

            audio_en = text_to_speech(
                english_weather_text,
                "en",
                slow=slow_mode,
                voice=voice_selection,
            )

            if audio_en:
                st.audio(audio_en, format="audio/mp3")

        except Exception as e:
            print(f"English TTS error: {e}")

        if language_code != "en":
            st.markdown("---")

            try:
                with st.spinner(
                    f"🌐 Translating to {selected_language}..."
                ):
                    translated_weather = translate_to_language(
                        english_weather_text,
                        language_code,
                        client,
                    )

                st.write(
                    f"**📝 Weather in {selected_language}:**"
                )
                st.success(translated_weather)

                st.write(
                    f"**🔊 Listen in {selected_language}:**"
                )

                audio_translated = text_to_speech(
                    translated_weather,
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
                        f"Voice narration not available "
                        f"for {selected_language}"
                    )

            except Exception as e:
                print(f"Translation/TTS error: {e}")
                st.warning(
                    "⚠️ Could not translate the weather. "
                    "The English version is shown above."
                )

