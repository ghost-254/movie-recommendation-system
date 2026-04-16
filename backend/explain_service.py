import time
import uuid
import os
from pathlib import Path
from typing import Dict

from model_service import SENTIMENT_LABELS, SentimentModelService


class ReviewExplainService:
    """
    Generates LIME explanations for a single review and saves explanation images
    to backend/static/explanations/.
    """

    def __init__(self, model_service: SentimentModelService, output_dir: str = "./static/explanations") -> None:
        self.model_service = model_service
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.explainer = None

    def _get_explainer(self):
        if self.explainer is not None:
            return self.explainer

        from lime.lime_text import LimeTextExplainer

        self.explainer = LimeTextExplainer(class_names=SENTIMENT_LABELS)
        return self.explainer

    @staticmethod
    def _limit_text_for_explanation(text: str, max_words: int) -> Dict[str, object]:
        words = text.split()
        if len(words) <= max_words:
            return {
                "text": text,
                "was_truncated": False,
                "original_word_count": len(words),
                "used_word_count": len(words),
            }

        half = max_words // 2
        limited_words = words[:half] + words[-(max_words - half) :]
        return {
            "text": " ".join(limited_words),
            "was_truncated": True,
            "original_word_count": len(words),
            "used_word_count": len(limited_words),
        }

    def explain_review(self, review_text: str) -> Dict[str, object]:
        text = review_text.strip() if isinstance(review_text, str) else ""
        if not text:
            raise ValueError("A non-empty review_text field is required.")

        prediction = self.model_service.predict_review_sentiment(text)
        predicted_label_index = prediction["label_index"]
        explainer = self._get_explainer()
        max_words = int(os.getenv("LIME_MAX_WORDS", "180"))
        num_samples = int(os.getenv("LIME_NUM_SAMPLES", "120"))
        num_features = int(os.getenv("LIME_NUM_FEATURES", "10"))
        limited = self._limit_text_for_explanation(text, max_words=max_words)

        # LIME perturbs the input text and queries model probabilities to build a local explanation.
        explanation = explainer.explain_instance(
            text_instance=limited["text"],
            classifier_fn=lambda texts: self.model_service.predict_proba(list(texts), batch_size=8),
            labels=[predicted_label_index],
            num_features=num_features,
            num_samples=num_samples,
        )

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        figure = explanation.as_pyplot_figure(label=predicted_label_index)
        figure.tight_layout()

        filename = f"lime_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
        file_path = self.output_dir / filename
        figure.savefig(file_path, dpi=200, bbox_inches="tight")
        plt.close(figure)

        return {
            "prediction": prediction,
            "image_path": f"/static/explanations/{filename}",
            "explanation_text_was_truncated": limited["was_truncated"],
            "explanation_original_word_count": limited["original_word_count"],
            "explanation_used_word_count": limited["used_word_count"],
            "lime_num_samples": num_samples,
        }
