import unittest
from unittest.mock import Mock, patch

from utils.song_fetcher import get_song_results, is_song_query


class SongFetcherTests(unittest.TestCase):
    def test_song_query_detection(self):
        self.assertTrue(is_song_query("Malayalam song"))
        self.assertTrue(is_song_query("Tamil music"))
        self.assertFalse(is_song_query("Malayalam news"))

    @patch("utils.song_fetcher.requests.get")
    def test_song_results_use_video_search(self, mock_get):
        response = Mock()
        response.json.return_value = {
            "video_results": [
                {
                    "title": "Malayalam song",
                    "link": "https://www.youtube.com/watch?v=123",
                    "snippet": "A song",
                    "source": "YouTube",
                }
            ]
        }
        mock_get.return_value = response

        results = get_song_results("Malayalam song", "secret", top_k=3)

        response.raise_for_status.assert_called_once_with()
        self.assertEqual(results[0]["title"], "Malayalam song")
        self.assertEqual(results[0]["url"], "https://www.youtube.com/watch?v=123")
        self.assertEqual(mock_get.call_args.kwargs["params"]["tbm"], "vid")


if __name__ == "__main__":
    unittest.main()
