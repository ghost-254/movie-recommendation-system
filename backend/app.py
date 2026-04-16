import os
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

from explain_service import ReviewExplainService
from model_service import SENTIMENT_LABELS, SentimentModelService
from movie_service import TMDbService

BASE_DIR = Path(__file__).resolve().parent


def load_env_file(env_path: Path) -> None:
    """Load key=value pairs from a local .env file without extra dependencies."""
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get_allowed_origins() -> Any:
    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    if frontend_url:
        return [frontend_url, "http://127.0.0.1:5500", "http://localhost:5500"]
    return "*"


def build_sentiment_count_template() -> Dict[str, int]:
    return {label: 0 for label in SENTIMENT_LABELS}


def build_overall_sentiment_summary(sentiment_counts: Dict[str, int]) -> Dict[str, Any]:
    total_reviews = sum(sentiment_counts.values())
    if total_reviews == 0:
        return {
            "total_reviews": 0,
            "dominant_sentiment": None,
            "distribution_percent": {label: 0.0 for label in SENTIMENT_LABELS},
            "note": "No reviews were available for analysis.",
        }

    dominant_sentiment = max(SENTIMENT_LABELS, key=lambda label: sentiment_counts[label])
    distribution_percent = {
        label: round((sentiment_counts[label] / total_reviews) * 100.0, 2)
        for label in SENTIMENT_LABELS
    }

    return {
        "total_reviews": total_reviews,
        "dominant_sentiment": dominant_sentiment,
        "distribution_percent": distribution_percent,
    }


def extract_review_text(payload: Dict[str, Any]) -> str:
    text = (
        payload.get("review_text")
        or payload.get("review")
        or payload.get("text")
        or ""
    )
    text = text.strip() if isinstance(text, str) else ""
    if not text:
        raise ValueError("A non-empty review_text field is required.")
    return text


def normalize_reviews_batch(items: Any) -> List[str]:
    if not isinstance(items, list):
        raise ValueError("reviews must be an array.")

    normalized = []
    for item in items:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = str(item.get("content") or item.get("text") or "").strip()
        else:
            text = str(item).strip()

        if text:
            normalized.append(text)

    return normalized


def error_response(message: str, status_code: int = 400, details: Any = None):
    payload = {"error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


load_env_file(BASE_DIR / ".env")
load_env_file(BASE_DIR / ".env.local")

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(
    app,
    resources={
        r"/api/*": {"origins": get_allowed_origins()},
        r"/static/*": {"origins": get_allowed_origins()},
        r"/health": {"origins": "*"},
    },
)

model_service = SentimentModelService(model_dir=str(BASE_DIR / "saved_sst5_model"))
movie_service = TMDbService(api_key=os.getenv("TMDB_API_KEY", "").strip())
explain_service = ReviewExplainService(
    model_service=model_service,
    output_dir=str(BASE_DIR / "static" / "explanations"),
)


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "model_loaded": model_service.is_ready,
            "model_error": model_service.load_error,
            "tmdb_configured": movie_service.is_configured,
        }
    )


@app.get("/api/search-movies")
def search_movies():
    query = request.args.get("query", "").strip()
    if not query:
        return error_response("Query parameter 'query' is required.", 400)

    try:
        results = movie_service.search_movies(query)
        return jsonify(results)
    except RuntimeError as exc:
        return error_response(str(exc), 500)
    except Exception as exc:
        return error_response("Failed to search movies.", 500, str(exc))


@app.get("/api/movie/<int:movie_id>")
def get_movie(movie_id: int):
    try:
        movie = movie_service.get_movie_details(movie_id)
        return jsonify(movie)
    except RuntimeError as exc:
        return error_response(str(exc), 500)
    except Exception as exc:
        return error_response("Failed to fetch movie details.", 500, str(exc))


@app.get("/api/movie/<int:movie_id>/reviews")
def get_movie_reviews(movie_id: int):
    try:
        reviews = movie_service.get_movie_reviews(movie_id)
        return jsonify(
            {
                "movie_id": movie_id,
                "total_reviews": len(reviews),
                "reviews": reviews,
            }
        )
    except RuntimeError as exc:
        return error_response(str(exc), 500)
    except Exception as exc:
        return error_response("Failed to fetch movie reviews.", 500, str(exc))


@app.get("/api/analyze-movie/<int:movie_id>")
def analyze_movie(movie_id: int):
    try:
        movie = movie_service.get_movie_details(movie_id)
        reviews = movie_service.get_movie_reviews(movie_id)
        review_texts = [review.get("content", "") for review in reviews]
        predictions = model_service.predict_reviews_batch(review_texts) if review_texts else []

        sentiment_counts = build_sentiment_count_template()
        reviews_with_predictions = []
        for review, prediction in zip(reviews, predictions):
            sentiment_counts[prediction["label"]] += 1
            merged = {**review, "prediction": prediction}
            reviews_with_predictions.append(merged)

        summary = build_overall_sentiment_summary(sentiment_counts)
        return jsonify(
            {
                "movie": movie,
                "reviews": reviews,
                "predictions": predictions,
                "reviews_with_predictions": reviews_with_predictions,
                "sentiment_counts": sentiment_counts,
                "overall_summary": summary,
            }
        )
    except RuntimeError as exc:
        return error_response(str(exc), 500)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response("Failed to analyze movie reviews.", 500, str(exc))


@app.post("/api/analyze-review")
def analyze_single_review():
    payload = request.get_json(silent=True) or {}
    try:
        review_text = extract_review_text(payload)
        prediction = model_service.predict_review_sentiment(review_text)
        return jsonify({"review_text": review_text, "prediction": prediction})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except RuntimeError as exc:
        return error_response(str(exc), 500)
    except Exception as exc:
        return error_response("Failed to analyze review.", 500, str(exc))


@app.post("/api/analyze-reviews-batch")
def analyze_reviews_batch():
    payload = request.get_json(silent=True) or {}
    try:
        reviews = normalize_reviews_batch(payload.get("reviews"))
        predictions = model_service.predict_reviews_batch(reviews) if reviews else []

        sentiment_counts = build_sentiment_count_template()
        for prediction in predictions:
            sentiment_counts[prediction["label"]] += 1

        return jsonify(
            {
                "total_reviews": len(reviews),
                "predictions": predictions,
                "sentiment_counts": sentiment_counts,
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except RuntimeError as exc:
        return error_response(str(exc), 500)
    except Exception as exc:
        return error_response("Failed to analyze reviews batch.", 500, str(exc))


@app.post("/api/explain-review")
def explain_single_review():
    payload = request.get_json(silent=True) or {}
    try:
        review_text = extract_review_text(payload)
        explanation = explain_service.explain_review(review_text)
        image_path = explanation.get("image_path")
        if image_path:
            explanation["image_url"] = f"{request.host_url.rstrip('/')}{image_path}"
        return jsonify({"review_text": review_text, **explanation})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except RuntimeError as exc:
        return error_response(str(exc), 500)
    except Exception as exc:
        return error_response("Failed to explain review.", 500, str(exc))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
