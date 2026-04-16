import { analyzeMovie, analyzeReview, buildAssetUrl, explainReview } from "./api.js";
import {
  escapeHtml,
  formatDateTime,
  formatReleaseYear,
  formatSentiment,
  getPosterUrl,
  getQueryParam,
} from "./utils.js";

const SENTIMENT_ORDER = ["very negative", "negative", "neutral", "positive", "very positive"];

const movieStatus = document.getElementById("movie-status");
const movieSection = document.getElementById("movie-section");
const summarySection = document.getElementById("summary-section");
const reviewsSection = document.getElementById("reviews-section");
const explanationSection = document.getElementById("explanation-section");

const titleEl = document.getElementById("movie-title");
const releaseYearEl = document.getElementById("movie-release-year");
const ratingEl = document.getElementById("movie-rating");
const overviewEl = document.getElementById("movie-overview");
const posterEl = document.getElementById("movie-poster");
const overallSummaryText = document.getElementById("overall-summary-text");
const sentimentTableBody = document.getElementById("sentiment-table-body");
const reviewsList = document.getElementById("reviews-list");
const explanationPredictionEl = document.getElementById("explanation-prediction");
const explanationStatusEl = document.getElementById("explanation-status");
const explanationImageEl = document.getElementById("explanation-image");
const explanationLinkEl = document.getElementById("explanation-link");

function setStatus(message, isError = false) {
  movieStatus.textContent = message;
  movieStatus.classList.toggle("status-error", isError);
}

function renderMovieDetails(movie) {
  titleEl.textContent = movie.title || "Unknown title";
  releaseYearEl.textContent = formatReleaseYear(movie.release_date);
  ratingEl.textContent =
    typeof movie.vote_average === "number" ? `${movie.vote_average.toFixed(1)} / 10` : "Not available";
  overviewEl.textContent = movie.overview || "No overview available.";
  posterEl.src = getPosterUrl(movie.poster_path, "w500");
  posterEl.alt = `Poster for ${movie.title || "movie"}`;
}

function renderSummary(sentimentCounts, overallSummary) {
  sentimentTableBody.innerHTML = "";

  const totalReviews = overallSummary?.total_reviews ?? 0;
  const dominant = overallSummary?.dominant_sentiment
    ? formatSentiment(overallSummary.dominant_sentiment)
    : "Unavailable";
  overallSummaryText.textContent = `Total analyzed reviews: ${totalReviews}. Dominant sentiment: ${dominant}.`;

  SENTIMENT_ORDER.forEach((label) => {
    const count = sentimentCounts[label] ?? 0;
    const percentage = totalReviews > 0 ? ((count / totalReviews) * 100).toFixed(2) : "0.00";
    sentimentTableBody.innerHTML += `
      <tr>
        <td>${formatSentiment(label)}</td>
        <td>${count}</td>
        <td>${percentage}%</td>
      </tr>
    `;
  });
}

function renderReviewCard(review, reviewId) {
  const author = escapeHtml(review.author || "Anonymous");
  const date = escapeHtml(formatDateTime(review.created_at));
  const content = review.content || "";
  const safeContent = escapeHtml(content);
  const initialLabel = review.prediction?.label ? formatSentiment(review.prediction.label) : "Not analyzed";
  const hasContent = content.trim().length > 0;

  return `
    <article class="review-card" data-review-id="${reviewId}">
      <div class="review-header">
        <p><strong>${author}</strong> <span class="muted">(${date})</span></p>
        <span class="tag">${initialLabel}</span>
      </div>
      <p class="review-text">${safeContent || "Review content not available."}</p>
      <div class="review-actions">
        <button type="button" class="analyze-review-btn" data-review-id="${reviewId}" ${hasContent ? "" : "disabled"}>
          Analyze This Review
        </button>
        <button type="button" class="button-secondary explain-review-btn" data-review-id="${reviewId}" ${hasContent ? "" : "disabled"}>
          Explain Prediction
        </button>
      </div>
      <p class="review-result muted" id="result-${reviewId}">Use the buttons above for detailed output.</p>
    </article>
  `;
}

function attachReviewActions(reviewsById) {
  const analyzeButtons = document.querySelectorAll(".analyze-review-btn");
  const explainButtons = document.querySelectorAll(".explain-review-btn");

  analyzeButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const reviewId = button.dataset.reviewId;
      const review = reviewsById[reviewId];
      const resultEl = document.getElementById(`result-${reviewId}`);
      resultEl.textContent = "Analyzing selected review...";

      try {
        const response = await analyzeReview(review.content);
        const prediction = response.prediction;
        const label = formatSentiment(prediction.label);
        const confidence = (prediction.scores[prediction.label] * 100).toFixed(2);
        resultEl.textContent = `Prediction: ${label} (${confidence}% confidence).`;
      } catch (error) {
        resultEl.textContent = `Error: ${error.message}`;
      }
    });
  });

  explainButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const reviewId = button.dataset.reviewId;
      const review = reviewsById[reviewId];
      const resultEl = document.getElementById(`result-${reviewId}`);
      resultEl.textContent = "Generating LIME explanation...";
      explanationSection.hidden = false;
      explanationPredictionEl.textContent = "";
      explanationStatusEl.textContent = "Generating explanation image...";
      explanationImageEl.hidden = true;
      explanationImageEl.removeAttribute("src");
      explanationLinkEl.hidden = true;
      explanationSection.scrollIntoView({ behavior: "smooth", block: "start" });

      try {
        const response = await explainReview(review.content);
        const predictionLabel = formatSentiment(response.prediction.label);
        const rawImageUrl = response.image_url || buildAssetUrl(response.image_path);
        if (!rawImageUrl) {
          throw new Error("Explanation completed, but no PNG path was returned by the backend.");
        }
        const cacheSeparator = rawImageUrl.includes("?") ? "&" : "?";
        const imageUrl = `${rawImageUrl}${cacheSeparator}t=${Date.now()}`;

        explanationPredictionEl.textContent = `Latest explanation prediction: ${predictionLabel}`;
        explanationStatusEl.textContent = "Loading generated PNG...";
        explanationImageEl.alt = `LIME explanation for review by ${review.author || "anonymous user"}`;
        explanationImageEl.onload = () => {
          explanationStatusEl.textContent = "LIME explanation image generated successfully.";
        };
        explanationImageEl.onerror = () => {
          explanationStatusEl.textContent = "The explanation was generated, but the PNG could not be loaded in the browser.";
        };
        explanationImageEl.src = imageUrl;
        explanationImageEl.hidden = false;
        explanationLinkEl.href = imageUrl;
        explanationLinkEl.hidden = false;

        resultEl.textContent = "Explanation generated successfully and displayed below.";
      } catch (error) {
        resultEl.textContent = `Error: ${error.message}`;
        explanationStatusEl.textContent = `Error: ${error.message}`;
      }
    });
  });
}

function renderReviews(reviewsWithPredictions) {
  reviewsList.innerHTML = "";

  if (!reviewsWithPredictions.length) {
    reviewsList.innerHTML = "<p class='muted'>No reviews were found for this movie.</p>";
    return;
  }

  const reviewsById = {};
  const cardsHtml = reviewsWithPredictions
    .map((review, index) => {
      const normalized = { ...review, id: review.id || `review-${index}` };
      const reviewId = `review-${index}-${String(normalized.id).replace(/[^a-zA-Z0-9_-]/g, "-")}`;
      reviewsById[reviewId] = normalized;
      return renderReviewCard(normalized, reviewId);
    })
    .join("");

  reviewsList.innerHTML = cardsHtml;
  attachReviewActions(reviewsById);
}

async function loadMovieAnalysis(movieId) {
  setStatus("Loading movie metadata, reviews, and sentiment analysis...");

  try {
    const response = await analyzeMovie(movieId);
    renderMovieDetails(response.movie);
    renderSummary(response.sentiment_counts || {}, response.overall_summary || {});
    renderReviews(response.reviews_with_predictions || []);

    movieSection.hidden = false;
    summarySection.hidden = false;
    reviewsSection.hidden = false;
    setStatus("Movie analysis loaded.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

const movieId = getQueryParam("id");
if (!movieId) {
  setStatus("No movie id was provided in the URL query string.", true);
} else {
  loadMovieAnalysis(movieId);
}
