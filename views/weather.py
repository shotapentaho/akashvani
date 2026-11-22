import streamlit as st

from utils.translator import translate_to_language
from utils.tts_handler import text_to_speech
from utils.weather_fetcher import (
    extract_weather_location,
    get_current_weather,
    get_weather_condition,
    get_weather_locations,
    is_country_location,
)


def _get_aqi_display(aqi_value):
    """Return the standard AQI category and visual position for an AQI value."""
    aqi = float(aqi_value)
    categories = [
        (50, "Good", "#2e9d59"),
        (100, "Moderate", "#d9a514"),
        (150, "Unhealthy for sensitive groups", "#e87519"),
        (200, "Unhealthy", "#d94b4b"),
        (300, "Very unhealthy", "#8d4bb3"),
    ]

    for upper_bound, label, color in categories:
        if aqi <= upper_bound:
            break
    else:
        label, color = "Hazardous", "#7e1f3f"

    return {
        "value": int(aqi) if aqi.is_integer() else aqi,
        "label": label,
        "color": color,
        "position": min(max(aqi, 0), 500) / 5,
    }


def _render_aqi_display(aqi_value):
    display = _get_aqi_display(aqi_value)
    value = display["value"]
    label = display["label"]
    color = display["color"]
    position = display["position"]

    st.markdown(
        f"""
        <div style="
            border: 1px solid #d9e5ee;
            border-radius: 12px;
            padding: 0.75rem 0.85rem 0.7rem;
            margin-top: 0.8rem;
            background: linear-gradient(135deg, #ffffff, #f3f8fc);
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 0.5rem;
            ">
                <span style="font-size: 0.85rem; color: #587087;">
                    Air quality index
                </span>
                <strong style="font-size: 1.35rem; color: {color};">
                    {value}
                </strong>
            </div>
            <div style="
                color: {color};
                font-weight: 700;
                font-size: 0.95rem;
                margin: 0.1rem 0 0.55rem;
            ">
                {label}
            </div>
            <div style="
                position: relative;
                height: 10px;
                border-radius: 999px;
                background: linear-gradient(
                    to right,
                    #2e9d59 0% 10%,
                    #d9a514 10% 20%,
                    #e87519 20% 30%,
                    #d94b4b 30% 40%,
                    #8d4bb3 40% 60%,
                    #7e1f3f 60% 100%
                );
            ">
                <span style="
                    position: absolute;
                    left: calc({position}% - 6px);
                    top: -4px;
                    width: 12px;
                    height: 18px;
                    border: 2px solid #17324d;
                    border-radius: 5px;
                    background: #ffffff;
                    box-sizing: border-box;
                "></span>
            </div>
            <div style="
                display: flex;
                justify-content: space-between;
                color: #587087;
                font-size: 0.7rem;
                margin-top: 0.25rem;
            ">
                <span>Good</span>
                <span>Hazardous</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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

        if is_country_location(weather_location, weather_places):
            st.info(
                f"'{weather_location}' is a country. "
                "Please enter a city in that country to get the weather."
            )
            weather_selection_pending = True
        elif len(weather_places) > 1:
            st.session_state.weather_selection_query = query
            st.warning(
                f"Several places named '{weather_location}' were found. "
                "Click a location tile to see its weather."
            )
            selection_key = (
                f"weather_place_{weather_location.lower()}"
            )
            selected_place = st.session_state.get(selection_key)

            if not selected_place:
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
        temperature_f = weather.get("temperature_f")
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
            value=(
                f"{temperature}{unit} / {temperature_f}°F"
                if temperature_f is not None
                else f"{temperature}{unit}"
            ),
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
                        f"{forecast_day['temperature_max']}{unit} / "
                        f"{forecast_day.get('temperature_max_f')}°F",
                    )
                    st.metric(
                        "Low",
                        f"{forecast_day['temperature_min']}{unit} / "
                        f"{forecast_day.get('temperature_min_f')}°F",
                    )
                    if forecast_day.get("air_quality_index") is not None:
                        _render_aqi_display(
                            forecast_day["air_quality_index"]
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

        if temperature_f is not None:
            english_weather_text += (
                f" ({temperature_f} degrees Fahrenheit)"
            )

        if feels_like is not None:
            english_weather_text += (
                f", and it feels like "
                f"{feels_like} degrees Celsius"
            )

        english_weather_text += "."

        if forecast:
            english_weather_text += " The three-day forecast is: "
            forecast_sentences = []
            for forecast_day in forecast:
                forecast_label, _ = get_weather_condition(
                    forecast_day.get("weather_code")
                )
                forecast_sentence = (
                    f"On {forecast_day['date']}, the high will be "
                    f"{forecast_day['temperature_max']} degrees Celsius "
                    f"({forecast_day['temperature_max_f']} degrees "
                    f"Fahrenheit), and the low will be "
                    f"{forecast_day['temperature_min']} degrees Celsius "
                    f"({forecast_day['temperature_min_f']} degrees "
                    f"Fahrenheit), with {forecast_label.lower()} conditions"
                )
                if forecast_day.get("air_quality_index") is not None:
                    forecast_sentence += (
                        f" and an air quality index of "
                        f"{forecast_day['air_quality_index']}"
                    )
                forecast_sentences.append(forecast_sentence)
            english_weather_text += ". ".join(forecast_sentences) + "."

        try:
            record_api_call(
                "open-meteo",
                query,
                "success",
                1,
            )
        except Exception as e:
            print(f"Tracking error: {e}")

        slow_mode = speech_speed == "Slow 🐢"

        try:
            st.markdown("---")

            if language_code == "en":
                weather_text = english_weather_text
            else:
                with st.spinner(
                    f"🌐 Translating to {selected_language}..."
                ):
                    weather_text = translate_to_language(
                        english_weather_text,
                        language_code,
                        client,
                        fallback_to_source=False,
                    )

            st.write(f"**📝 Weather in {selected_language}:**")
            st.info(weather_text)

            st.write(f"**🔊 Listen in {selected_language}:**")
            audio = text_to_speech(
                weather_text,
                language_code,
                slow=slow_mode,
                voice=voice_selection,
            )

            if audio:
                st.audio(audio, format="audio/mp3")
            else:
                st.info(
                    f"Voice narration not available "
                    f"for {selected_language}"
                )

        except Exception as e:
            print(f"Translation/TTS error: {e}")
            st.warning(
                f"⚠️ Could not prepare the weather in "
                f"{selected_language}. Please try again."
            )

