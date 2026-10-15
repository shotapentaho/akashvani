import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.weather_fetcher import extract_weather_location


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


if __name__ == "__main__":
    unittest.main()
