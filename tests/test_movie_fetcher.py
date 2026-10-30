import unittest
from unittest.mock import Mock, patch

from utils.movie_fetcher import (
    extract_movie_title,
    get_gemini_movie_ratings,
    get_imdb_rating,
    get_imdb_reviews,
    get_rotten_tomatoes_rating,
    get_rotten_tomatoes_reviews,
    is_movie_query,
    is_movie_review_query,
)


class MovieFetcherTests(unittest.TestCase):
    def test_movie_review_query_detection(self):
        self.assertTrue(is_movie_review_query("movie review of Dune"))
        self.assertTrue(is_movie_review_query("reviews for Interstellar"))
        self.assertTrue(is_movie_review_query("Oppenheimer review"))
        self.assertFalse(is_movie_review_query("movie news"))

    def test_movie_query_detection(self):
        for query in (
            "Dune movie",
            "movie Dune",
            "Dune rating",
            "movie rating of Dune",
            "reviews for Interstellar",
        ):
            with self.subTest(query=query):
                self.assertTrue(is_movie_query(query))
        self.assertFalse(is_movie_query("movie news"))
        self.assertFalse(is_movie_query("latest technology news"))

    def test_extract_movie_title_from_common_phrases(self):
        self.assertEqual(extract_movie_title("movie review of Dune"), "Dune")
        self.assertEqual(extract_movie_title("movie review Dune"), "Dune")
        self.assertEqual(extract_movie_title("Dune movie"), "Dune")
        self.assertEqual(extract_movie_title("Dune rating"), "Dune")
        self.assertEqual(extract_movie_title("movie rating of Dune"), "Dune")
        self.assertEqual(
            extract_movie_title("reviews for the movie Interstellar"),
            "Interstellar",
        )
        self.assertEqual(extract_movie_title("Oppenheimer review"), "Oppenheimer")
        self.assertEqual(extract_movie_title("movie review"), "")
        self.assertEqual(
            extract_movie_title("Drishyam: The Conclusion movie"),
            "Drishyam: The Conclusion",
        )

    def test_parse_gemini_movie_ratings_from_grounded_answer(self):
        response_text = (
            "Drishyam: The Conclusion holds the following ratings. "
            "IMDb Rating: 7.7 / 10 (based on user ratings). "
            "BookMyShow Rating: 8.7 / 10 (with over 155,000 votes). "
            "Rotten Tomatoes: 94% Tomatometer (by critics) and 90% "
            "Popcornmeter (by verified audience scores). Letterboxd: "
            "user distribution peaking around 3.5 to 4 out of 5 stars."
        )
        response = Mock()
        response.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": response_text}]},
                "groundingMetadata": {
                    "groundingChunks": [
                        {
                            "web": {
                                "title": "Rotten Tomatoes",
                                "uri": "https://www.rottentomatoes.com/m/drishyam",
                            }
                        },
                        {
                            "web": {
                                "title": "IMDb",
                                "uri": "https://www.imdb.com/title/tt123/",
                            }
                        },
                    ]
                },
            }]
        }

        with patch("utils.movie_fetcher.requests.post", return_value=response) as post:
            result = get_gemini_movie_ratings("Drishyam: The Conclusion", "key")

        self.assertEqual(
            result["ratings"],
            [
                {
                    "source": "Rotten Tomatoes",
                    "label": "Tomatometer",
                    "rating": 94.0,
                    "scale": 100,
                },
                {
                    "source": "Rotten Tomatoes",
                    "label": "Popcornmeter",
                    "rating": 90.0,
                    "scale": 100,
                },
                {
                    "source": "IMDb",
                    "label": "IMDb rating",
                    "rating": 7.7,
                    "scale": 10,
                },
                {
                    "source": "BookMyShow",
                    "label": "BookMyShow user rating",
                    "rating": 8.7,
                    "scale": 10,
                },
                {
                    "source": "Letterboxd",
                    "label": "Letterboxd user rating",
                    "rating": 3.5,
                    "scale": 5,
                    "rating_text": "3.5-4",
                },
            ],
        )
        self.assertEqual(
            result["sources"][0]["url"],
            "https://www.rottentomatoes.com/m/drishyam",
        )
        self.assertEqual(post.call_args.kwargs["params"], {"key": "key"})

    def test_parse_gemini_movie_ratings_ignores_unrelated_numbers(self):
        response_text = (
            "The 2024 film has 155,000 votes. "
            "IMDb rating: 7.7 / 10 based on 12,345 user ratings. "
            "BookMyShow rating unavailable."
        )

        from utils.movie_fetcher import _parse_gemini_movie_ratings

        self.assertEqual(
            _parse_gemini_movie_ratings(response_text),
            [{
                "source": "IMDb",
                "label": "IMDb rating",
                "rating": 7.7,
                "scale": 10,
            }],
        )

    def test_parse_gemini_movie_ratings_supports_score_before_source(self):
        response_text = (
            "The audience score is 8.4 out of 10 on BookMyShow. "
            "IMDb: 7.9/10."
        )

        from utils.movie_fetcher import _parse_gemini_movie_ratings

        self.assertEqual(
            _parse_gemini_movie_ratings(response_text),
            [
                {
                    "source": "IMDb",
                    "label": "IMDb rating",
                    "rating": 7.9,
                    "scale": 10,
                },
                {
                    "source": "BookMyShow",
                    "label": "BookMyShow user rating",
                    "rating": 8.4,
                    "scale": 10,
                },
            ],
        )

    def test_parse_gemini_movie_ratings_supports_bare_imdb_label(self):
        from utils.movie_fetcher import _parse_gemini_movie_ratings

        self.assertEqual(
            _parse_gemini_movie_ratings("IMDb 8.1. BookMyShow rating unavailable."),
            [{
                "source": "IMDb",
                "label": "IMDb rating",
                "rating": 8.1,
                "scale": 10,
            }],
        )

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
                "release_date": "October 22, 2021",
                "language": "English",
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
                "release_date": "October 22, 2021",
                "language": "English",
                "director": "Denis Villeneuve",
                "producer": "Mary Parent",
                "actors": "Timothée Chalamet, Rebecca Ferguson",
                "lead_cast": "Timothée Chalamet, Rebecca Ferguson",
                "writers": "Jon Spaihts, Denis Villeneuve, Eric Roth",
                "url": "https://www.imdb.com/title/tt1160419/",
            },
        )
        self.assertEqual(
            get.call_args.kwargs["params"]["q"],
            'site:imdb.com/title "Dune" IMDb rating release date language director cast',
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_imdb_rating_from_serpapi_answer_box(self, get):
        response = Mock()
        response.json.return_value = {
            "answer_box": {
                "title": "Dune (2021)",
                "rating": "8.0/10",
                "link": "https://www.imdb.com/title/tt1160419/",
            },
            "organic_results": [],
        }
        get.return_value = response

        self.assertEqual(
            get_imdb_rating("Dune", "api-key"),
            {
                "rating": 8.0,
                "url": "https://www.imdb.com/title/tt1160419/",
            },
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_imdb_rating_from_structured_knowledge_graph(self, get):
        response = Mock()
        response.json.return_value = {
            "knowledge_graph": {
                "aggregateRating": {
                    "ratingValue": "8.2",
                    "ratingCount": "12345",
                }
            },
            "organic_results": [
                {
                    "title": "Dune (2021) - IMDb",
                    "link": "https://www.imdb.com/title/tt1160419/",
                    "snippet": "Cast and crew information.",
                },
            ],
        }
        get.return_value = response

        rating = get_imdb_rating("Dune", "api-key")

        self.assertEqual(
            rating,
            {
                "rating": 8.2,
                "url": "https://www.imdb.com/title/tt1160419/",
            },
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_imdb_rating_from_knowledge_graph_without_organic_result(self, get):
        response = Mock()
        response.json.return_value = {
            "knowledge_graph": {
                "aggregateRating": {
                    "ratingValue": "8.2",
                    "ratingCount": "12345",
                }
            },
            "organic_results": [],
        }
        get.return_value = response

        self.assertEqual(get_imdb_rating("Dune", "api-key"), {"rating": 8.2})

    @patch("utils.movie_fetcher.requests.get")
    def test_get_imdb_rating_from_current_search_result_formats(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "Dune (2021) - IMDb",
                    "link": "https://www.imdb.com/title/tt1160419/",
                    "rich_snippet": {
                        "top": {
                            "detected_extensions": {"rating": 8.1},
                        }
                    },
                },
            ],
        }
        get.return_value = response

        self.assertEqual(
            get_imdb_rating("Dune", "api-key"),
            {
                "rating": 8.1,
                "url": "https://www.imdb.com/title/tt1160419/",
            },
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_imdb_rating_parses_common_labeled_snippet_formats(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "Dune (2021) - IMDb",
                    "link": "https://www.imdb.com/title/tt1160419/",
                    "snippet": "IMDb 8.1",
                },
            ],
        }
        get.return_value = response

        self.assertEqual(
            get_imdb_rating("Dune", "api-key"),
            {
                "rating": 8.1,
                "url": "https://www.imdb.com/title/tt1160419/",
            },
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_imdb_rating_continues_after_unrated_title_result(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "Dune (2021) - IMDb",
                    "link": "https://www.imdb.com/title/tt1160419/",
                    "snippet": "Cast and crew information.",
                },
                {
                    "title": "Dune (2021) | IMDb",
                    "link": "https://www.imdb.com/title/tt1160419/",
                    "snippet": "Rating: 8.0/10.",
                },
            ],
        }
        get.return_value = response

        self.assertEqual(
            get_imdb_rating("Dune", "api-key"),
            {
                "rating": 8.0,
                "url": "https://www.imdb.com/title/tt1160419/",
            },
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_rotten_tomatoes_rating_from_movie_result(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "Dune Reviews",
                    "link": "https://www.rottentomatoes.com/m/dune",
                    "snippet": "Tomatometer: 83%.",
                },
                {
                    "title": "Other source",
                    "link": "https://example.com/m/dune",
                    "snippet": "Tomatometer: 99%.",
                },
            ]
        }
        get.return_value = response

        rating = get_rotten_tomatoes_rating("Dune", "api-key")

        self.assertEqual(
            rating,
            {
                "rating": 83.0,
                "url": "https://www.rottentomatoes.com/m/dune",
            },
        )
        self.assertEqual(
            get.call_args.kwargs["params"]["q"],
            'site:rottentomatoes.com/m "Dune" Tomatometer',
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_rotten_tomatoes_rating_from_score_label_without_percent(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "Dune | Rotten Tomatoes",
                    "link": "https://www.rottentomatoes.com/m/dune",
                    "snippet": "Tomatometer score: 83",
                },
            ],
        }
        get.return_value = response

        self.assertEqual(
            get_rotten_tomatoes_rating("Dune", "api-key"),
            {
                "rating": 83.0,
                "url": "https://www.rottentomatoes.com/m/dune",
            },
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_rotten_tomatoes_rating_from_serpapi_answer_box(self, get):
        response = Mock()
        response.json.return_value = {
            "answer_box": {
                "title": "Dune | Rotten Tomatoes",
                "tomatometer": "83%",
                "link": "https://www.rottentomatoes.com/m/dune",
            },
            "organic_results": [],
        }
        get.return_value = response

        self.assertEqual(
            get_rotten_tomatoes_rating("Dune", "api-key"),
            {
                "rating": 83.0,
                "url": "https://www.rottentomatoes.com/m/dune",
            },
        )

    @patch("utils.movie_fetcher.requests.get")
    def test_get_rotten_tomatoes_rating_from_nested_rich_snippet(self, get):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "Drishyam: The Conclusion | Rotten Tomatoes",
                    "link": "https://www.rottentomatoes.com/m/drishyam_the_conclusion",
                    "rich_snippet": {
                        "top": {
                            "detected_extensions": {
                                "tomatometer": 83,
                            },
                        },
                    },
                },
            ],
        }
        get.return_value = response

        self.assertEqual(
            get_rotten_tomatoes_rating("Drishyam: The Conclusion", "api-key"),
            {
                "rating": 83,
                "url": "https://www.rottentomatoes.com/m/drishyam_the_conclusion",
            },
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
