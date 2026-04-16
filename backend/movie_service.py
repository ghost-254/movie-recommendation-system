from typing import Any, Dict, List

import requests


class TMDbService:
    """Service layer for TMDb API operations."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key = (api_key or "").strip()
        self.base_url = "https://api.themoviedb.org/3"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("TMDB_API_KEY is not set. Please configure it in environment variables.")

    def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        self._ensure_api_key()
        query_params = {"api_key": self.api_key, "language": "en-US", **(params or {})}
        response = requests.get(f"{self.base_url}{endpoint}", params=query_params, timeout=20)

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"TMDb request failed: {response.text}") from exc

        return response.json()

    def search_movies(self, query: str, page: int = 1) -> Dict[str, Any]:
        data = self._request(
            "/search/movie",
            {
                "query": query,
                "include_adult": "false",
                "page": page,
            },
        )

        results = []
        for movie in data.get("results", []):
            results.append(
                {
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "release_date": movie.get("release_date"),
                    "overview": movie.get("overview"),
                    "poster_path": movie.get("poster_path"),
                    "vote_average": movie.get("vote_average"),
                    "vote_count": movie.get("vote_count"),
                }
            )

        return {
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 0),
            "total_results": data.get("total_results", 0),
            "results": results,
        }

    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        movie = self._request(f"/movie/{movie_id}")
        return {
            "id": movie.get("id"),
            "title": movie.get("title"),
            "release_date": movie.get("release_date"),
            "overview": movie.get("overview"),
            "runtime": movie.get("runtime"),
            "genres": movie.get("genres", []),
            "poster_path": movie.get("poster_path"),
            "backdrop_path": movie.get("backdrop_path"),
            "vote_average": movie.get("vote_average"),
            "vote_count": movie.get("vote_count"),
            "original_language": movie.get("original_language"),
        }

    def get_movie_reviews(self, movie_id: int, page: int = 1) -> List[Dict[str, Any]]:
        payload = self._request(f"/movie/{movie_id}/reviews", {"page": page})
        reviews = []
        for item in payload.get("results", []):
            author_details = item.get("author_details", {}) or {}
            reviews.append(
                {
                    "id": item.get("id"),
                    "author": item.get("author"),
                    "content": item.get("content", ""),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "url": item.get("url"),
                    "rating": author_details.get("rating"),
                }
            )
        return reviews
