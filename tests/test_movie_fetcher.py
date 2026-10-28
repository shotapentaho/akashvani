import unittest
from unittest.mock import Mock, patch

from utils.movie_fetcher import (
    extract_movie_title,
    get_imdb_rating,
    get_imdb_reviews,
    get_rotten_tomatoes_reviews,
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
                "source": "IMDb",
            }],
        )
        self.assertEqual(get.call_args.kwargs["params"]["q"], 'site:imdb.com "Dune" reviews')

    @patch("utils.movie_fetcher.requests.get")
    def test_get_imdb_rating_from_title_result(self, get):
        response = Mock()
        response.json.return_value = {
            "knowledge_graph": {
                "directed_by": [{"name": "Denis Villeneuve"}],
                "produced_by": [{"name": "Mary Parent"}],
                "cast": [
                    {"name": "Timothée Chalamet"},
                    {"name": "Rebecca Ferguson"},
                ],
                "written_by": "Jon Spaihts, Denis Villeneuve, Eric Roth",
            },
            "organic_results": [
                {
                    "title": "Dune (2021) - IMDb",
                    "link": "https://www.imdb.com/title/tt1160419/",
                    "snippet": "IMDb rating: 8.0/10.",
                },
                {
                    "title": "Other result",
                    "link": "https://example.com/title/tt123/",
                    "snippet": "IMDb rating: 9.0/10.",
                },
            ]
        }
        get.return_value = response

        rating = get_imdb_rating("Dune", "api-key")

        self.assertEqual(
            rating,
            {
                "rating": 8.0,
                "director": "Denis Villeneuve",
                "producer": "Mary Parent",
                "actors": "Timothée Chalamet, Rebecca Ferguson",
                "writers": "Jon Spaihts, Denis Villeneuve, Eric Roth",
                "url": "https://www.imdb.com/title/tt1160419/",
            },
        )
        self.assertEqual(
            get.call_args.kwargs["params"]["q"],
            'site:imdb.com/title "Dune" IMDb rating director producer cast writer',
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_rotten_tomatoes_reviews_filters_search_results(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "Dune Reviews",
                    "link": "https://www.rottentomatoes.com/m/dune/reviews",
                    "snippet": "Critics praise the film.",
                },
                {
                    "title": "Rotten Tomatoes movie page",
                    "link": "https://www.rottentomatoes.com/m/dune",
                    "snippet": "A science fiction film.",
                },
                {
                    "title": "Other source",
                    "link": "https://example.com/m/dune/reviews",
                    "snippet": "Not Rotten Tomatoes.",
                },
            ]
        }
        get.return_value = response

        reviews = get_rotten_tomatoes_reviews("Dune", "api-key")

        self.assertEqual(
            reviews,
            [{
                "title": "Dune Reviews",
                "text": "Critics praise the film.",
                "url": "https://www.rottentomatoes.com/m/dune/reviews",
                "source": "Rotten Tomatoes",
            }],
        )
        self.assertEqual(
            get.call_args.kwargs["params"]["q"],
            'site:rottentomatoes.com/m "Dune" reviews',
        )


if __name__ == "__main__":
    unittest.main()
