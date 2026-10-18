import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.weather_fetcher import (
    extract_weather_location,
    get_weather_condition,
    get_current_weather,
    get_weather_locations,
)


class ExtractWeatherLocationTests(unittest.TestCase):
    def test_supported_queries(self):
        cases = {
            "weather in Mumbai": "Mumbai",
            "what is the weather in Delhi": "Delhi",
            "What's the weather in Delhi?": "Delhi",
            "temperature at Bengaluru": "Bengaluru",
            "current temperature for Chennai": "Chennai",
            "weather Mumbai": "Mumbai",
            "temperature at New Delhi": "New Delhi",
            "weather in Bengaluru, India!": "Bengaluru, India",
            "weather in  San   Francisco ?": "San Francisco",
        }
        for query, expected in cases.items():
            self.assertEqual(extract_weather_location(query), expected, query)

    def test_non_weather_or_no_location(self):
        for query in [
            "", None, "weather", "weather in", "temperature at ?", "India election news",
            "weather forecast", "weather news", "climate change and weather patterns hurting farmers in India",
        ]:
            self.assertIsNone(extract_weather_location(query), query)


class CurrentWeatherTests(unittest.TestCase):
    def test_weather_condition_visuals(self):
        self.assertEqual(get_weather_condition(0), ("Sunny", "☀️"))
        self.assertEqual(get_weather_condition(63), ("Rainy", "🌧️"))
        self.assertEqual(get_weather_condition(2), ("Partly cloudy", "🌤️"))
        self.assertEqual(
            get_weather_condition(999),
            ("Weather unavailable", "🌡️"),
        )

    def _geocode_response(self):
        response = Mock()
        response.json.return_value = {
            "results": [
                {
                    "name": "Shrewsbury",
                    "admin1": "England",
                    "country": "United Kingdom",
                    "country_code": "GB",
                    "latitude": 52.7,
                    "longitude": -2.75,
                },
                {
                    "name": "Shrewsbury",
                    "admin1": "Massachusetts",
                    "country": "United States",
                    "country_code": "US",
                    "latitude": 42.3,
                    "longitude": -71.7,
                },
            ]
        }
        return response

    @patch("utils.weather_fetcher.requests.get")
    def test_ambiguous_name_returns_all_matching_places(self, mock_get):
        mock_get.return_value = self._geocode_response()

        places = get_weather_locations("Shrewsbury")

        self.assertEqual(len(places), 2)
        self.assertEqual(mock_get.call_count, 1)

    @patch("utils.weather_fetcher.requests.get")
    def test_explicit_state_hint_selects_matching_geocode_result(self, mock_get):
        geocode_response = self._geocode_response()
        forecast_response = Mock()
        forecast_response.json.return_value = {
            "current": {
                "temperature_2m": 12,
                "apparent_temperature": 11,
                "weather_code": 2,
                "time": "2026-10-17T12:00",
            },
            "daily": {
                "time": ["2026-10-17", "2026-10-18", "2026-10-19"],
                "temperature_2m_max": [15, 16, 17],
                "temperature_2m_min": [7, 8, 9],
                "weather_code": [2, 3, 61],
            },
            "timezone": "America/New_York",
        }
        mock_get.side_effect = [geocode_response, forecast_response]

        weather = get_current_weather("Shrewsbury, MA")

        self.assertEqual(weather["region"], "Massachusetts")
        self.assertEqual(weather["country"], "United States")
        self.assertEqual(mock_get.call_args_list[0].kwargs["params"]["count"], 10)
        forecast_params = mock_get.call_args_list[1].kwargs["params"]
        self.assertEqual(forecast_params["forecast_days"], 3)
        self.assertEqual(
            forecast_params["daily"],
            "temperature_2m_max,temperature_2m_min,weather_code",
        )
        self.assertEqual(len(weather["forecast"]), 3)
        self.assertEqual(weather["forecast"][1]["temperature_max"], 16)

    @patch("utils.weather_fetcher.requests.get")
    def test_explicit_country_hint_selects_matching_geocode_result(self, mock_get):
        mock_get.return_value = self._geocode_response()

        places = get_weather_locations("Shrewsbury UK")

        self.assertEqual(len(places), 1)
        self.assertEqual(places[0]["country"], "United Kingdom")

    @patch("utils.weather_fetcher.requests.get")
    def test_duplicate_display_locations_are_returned_once(self, mock_get):
        response = Mock()
        response.json.return_value = {
            "results": [
                {
                    "name": "Sambalpur",
                    "admin1": "Chhattisgarh",
                    "admin2": "District A",
                    "country": "India",
                    "country_code": "IN",
                    "latitude": 21.47,
                    "longitude": 83.97,
                },
                {
                    "name": "Sambalpur",
                    "admin1": "Chhattisgarh",
                    "admin2": "District B",
                    "country": "India",
                    "country_code": "IN",
                    "latitude": 21.48,
                    "longitude": 83.98,
                },
            ]
        }
        mock_get.return_value = response

        places = get_weather_locations("Sambalpur")

        self.assertEqual(len(places), 1)
        self.assertEqual(places[0]["name"], "Sambalpur")


if __name__ == "__main__":
    unittest.main()
