import unittest
from unittest.mock import Mock, patch

from utils.web_search_fetcher import (
    get_bbc_search_results,
    get_gemini_search_results,
    get_serpapi_news_results,
    get_youtube_search_results,
)


class WebSearchFetcherTests(unittest.TestCase):
    @patch("utils.web_search_fetcher.requests.post")
    def test_gemini_returns_answer_and_grounded_sources(self, post):
        response = Mock()
        response.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": "A current answer."}]},
                "groundingMetadata": {
                    "groundingChunks": [
                        {"web": {"title": "Source", "uri": "https://example.com/story"}}
                    ]
                },
            }]
        }
        post.return_value = response

        results = get_gemini_search_results("Obama Ohio speech", "key")

        response.raise_for_status.assert_called_once_with()
        self.assertEqual(results[0]["source"], "Gemini")
        self.assertEqual(results[1]["url"], "https://example.com/story")

    @patch("utils.web_search_fetcher.requests.get")
    def test_bbc_filters_to_news_articles_path(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {"title": "BBC", "link": "https://www.bbc.com/news/articles/c1abc"},
                {"title": "Other", "link": "https://www.bbc.com/news/world"},
            ]
        }
        get.return_value = response

        results = get_bbc_search_results("Obama Ohio speech", "key")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "BBC News")

    @patch("utils.web_search_fetcher.requests.get")
    def test_serpapi_returns_google_news_results(self, get):
        response = Mock()
        response.json.return_value = {
            "news_results": [
                {
                    "title": "Trump News",
                    "snippet": "Latest reporting.",
                    "link": "https://example.com/trump",
                    "source": {"name": "Example News"},
                }
            ]
        }
        get.return_value = response

        results = get_serpapi_news_results("Trump News", "key")

        self.assertEqual(results[0]["title"], "Trump News")
        self.assertEqual(results[0]["source"], "Example News")
        self.assertEqual(get.call_args.kwargs["params"]["engine"], "google_news")

    @patch("utils.web_search_fetcher.requests.get")
    def test_youtube_returns_video_results(self, get):
        response = Mock()
        response.json.return_value = {
            "video_results": [
                {"title": "Speech", "link": "https://www.youtube.com/watch?v=abc"}
            ]
        }
        get.return_value = response

        results = get_youtube_search_results("Obama Ohio speech", "key")

        self.assertEqual(results[0]["source"], "YouTube")
        self.assertEqual(results[0]["url"], "https://www.youtube.com/watch?v=abc")
        self.assertEqual(get.call_args.kwargs["params"]["tbm"], "vid")


if __name__ == "__main__":
    unittest.main()
