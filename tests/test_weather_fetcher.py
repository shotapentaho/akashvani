import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.weather_fetcher import extract_weather_location, get_current_weather


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
    @patch("utils.weather_fetcher.requests.get")
    def test_explicit_state_hint_selects_matching_geocode_result(self, mock_get):
        geocode_response = Mock()
        geocode_response.json.return_value = {
            "results": [
                {
                    "name": "Shrewsbury",
                    "admin1": "England",
                    "country": "United Kingdom",
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
        forecast_response = Mock()
        forecast_response.json.return_value = {
            "current": {
                "temperature_2m": 12,
                "apparent_temperature": 11,
                "time": "2026-10-17T12:00",
            },
            "timezone": "America/New_York",
        }
        mock_get.side_effect = [geocode_response, forecast_response]

        weather = get_current_weather("Shrewsbury, MA")

        self.assertEqual(weather["region"], "Massachusetts")
        self.assertEqual(weather["country"], "United States")
        self.assertEqual(mock_get.call_args_list[0].kwargs["params"]["count"], 10)


if __name__ == "__main__":
    unittest.main()
