import { API_BASE_URL } from "./config.js";

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const requestOptions = { ...options };

  if (requestOptions.body) {
    requestOptions.headers = {
      "Content-Type": "application/json",
      ...(requestOptions.headers || {}),
    };
  }

  const response = await fetch(url, requestOptions);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      payload && typeof payload === "object" && payload.error
        ? payload.error
        : `Request failed (${response.status}).`;
    throw new Error(message);
  }

  return payload;
}

function normalizeReviewText(reviewText) {
  if (typeof reviewText !== "string") {
    throw new Error("Review text must be a string.");
  }

  const trimmed = reviewText.trim();
  if (!trimmed) {
    throw new Error("Review text is required.");
  }

  return trimmed;
}

export function buildAssetUrl(path) {
  if (!path) {
    return "";
  }

  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function searchMovies(query) {
  return request(`/api/search-movies?query=${encodeURIComponent(query)}`);
}

export function getMovie(movieId) {
  return request(`/api/movie/${movieId}`);
}

export function getMovieReviews(movieId) {
  return request(`/api/movie/${movieId}/reviews`);
}

export function analyzeMovie(movieId) {
  return request(`/api/analyze-movie/${movieId}`);
}

export function analyzeReview(reviewText) {
  return request("/api/analyze-review", {
    method: "POST",
    body: JSON.stringify({ review_text: normalizeReviewText(reviewText) }),
  });
}

export function analyzeReviewsBatch(reviews) {
  if (!Array.isArray(reviews)) {
    throw new Error("Batch reviews must be an array.");
  }

  return request("/api/analyze-reviews-batch", {
    method: "POST",
    body: JSON.stringify({ reviews }),
  });
}

export function explainReview(reviewText) {
  return request("/api/explain-review", {
    method: "POST",
    body: JSON.stringify({ review_text: normalizeReviewText(reviewText) }),
  });
}
