import time
import uuid
from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap  # noqa: F401  # Included for interpretability extensions.
from lime.lime_text import LimeTextExplainer

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
        self.explainer = LimeTextExplainer(class_names=SENTIMENT_LABELS)

    def explain_review(self, review_text: str) -> Dict[str, object]:
        text = review_text.strip() if isinstance(review_text, str) else ""
        if not text:
            raise ValueError("A non-empty review_text field is required.")

        prediction = self.model_service.predict_review_sentiment(text)
        predicted_label_index = prediction["label_index"]

        # LIME perturbs the input text and queries model probabilities to build a local explanation.
        explanation = self.explainer.explain_instance(
            text_instance=text,
            classifier_fn=self.model_service.predict_proba,
            labels=[predicted_label_index],
            num_features=10,
            num_samples=500,
        )

        figure = explanation.as_pyplot_figure(label=predicted_label_index)
        figure.tight_layout()

        filename = f"lime_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
        file_path = self.output_dir / filename
        figure.savefig(file_path, dpi=200, bbox_inches="tight")
        plt.close(figure)

        return {
            "prediction": prediction,
            "image_path": f"/static/explanations/{filename}",
        }
