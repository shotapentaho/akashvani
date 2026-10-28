import unittest
from unittest.mock import Mock, patch

from utils.movie_fetcher import (
    extract_movie_title,
    get_imdb_reviews,
    is_movie_review_query,
)


class MovieFetcherTests(unittest.TestCase):
    def test_movie_review_query_detection(self):
        self.assertTrue(is_movie_review_query("movie review of Dune"))
        self.assertTrue(is_movie_review_query("reviews for Interstellar"))
        self.assertTrue(is_movie_review_query("Oppenheimer review"))
        self.assertFalse(is_movie_review_query("movie news"))

    def test_extract_movie_title_from_common_phrases(self):
        self.assertEqual(extract_movie_title("movie review of Dune"), "Dune")
        self.assertEqual(extract_movie_title("movie review Dune"), "Dune")
        self.assertEqual(
            extract_movie_title("reviews for the movie Interstellar"),
            "Interstellar",
        )
        self.assertEqual(extract_movie_title("Oppenheimer review"), "Oppenheimer")
        self.assertEqual(extract_movie_title("movie review"), "")

    @patch("utils.movie_fetcher.requests.get")
    def test_get_imdb_reviews_filters_search_results(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "IMDb review",
                    "link": "https://www.imdb.com/review/rw123/",
                    "snippet": "An enjoyable film.",
                },
                {
                    "title": "IMDb title",
                    "link": "https://www.imdb.com/title/tt123/",
                    "snippet": "Not a review page.",
                },
                {
                    "title": "Other source",
                    "link": "https://example.com/review/",
                    "snippet": "Not IMDb.",
                },
            ]
        }
        get.return_value = response

        reviews = get_imdb_reviews("Dune", "api-key")

        response.raise_for_status.assert_called_once_with()
        self.assertEqual(
            reviews,
            [{
                "title": "IMDb review",
                "text": "An enjoyable film.",
                "url": "https://www.imdb.com/review/rw123/",
            }],
        )
        self.assertEqual(get.call_args.kwargs["params"]["q"], 'site:imdb.com "Dune" reviews')


if __name__ == "__main__":
    unittest.main()
