import os
from pathlib import Path
from threading import Lock
from typing import Dict, List

from huggingface_hub import snapshot_download
import numpy as np

SENTIMENT_LABELS = ["very negative", "negative", "neutral", "positive", "very positive"]
MODEL_FILES = [
    "config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
]


class SentimentModelService:
    """
    Loads a fine-tuned DistilBERT SST-5 model from ./saved_sst5_model
    and exposes single/batch prediction helpers.
    """

    def __init__(self, model_dir: str = "./saved_sst5_model", load_on_startup: bool = False) -> None:
        self.model_dir = Path(model_dir)
        self.device = None
        self.tokenizer = None
        self.model = None
        self.torch = None
        self.load_error = None
        self._load_lock = Lock()
        if load_on_startup:
            self.load_model()

    @property
    def is_ready(self) -> bool:
        return self.model is not None and self.tokenizer is not None and self.load_error is None

    def _missing_model_files(self) -> List[str]:
        return [filename for filename in MODEL_FILES if not (self.model_dir / filename).exists()]

    def _download_model_if_configured(self) -> None:
        missing_files = self._missing_model_files()
        if not missing_files:
            return

        model_repo = os.getenv("HF_MODEL_REPO", "").strip()
        if not model_repo:
            self.load_error = (
                f"Missing model files in {self.model_dir.resolve()}: {', '.join(missing_files)}. "
                "Add the files locally or set HF_MODEL_REPO so the backend can download them from Hugging Face."
            )
            return

        self.model_dir.mkdir(parents=True, exist_ok=True)
        token = os.getenv("HF_TOKEN", "").strip() or None
        revision = os.getenv("HF_MODEL_REVISION", "main").strip() or "main"

        try:
            snapshot_download(
                repo_id=model_repo,
                repo_type="model",
                revision=revision,
                token=token,
                local_dir=str(self.model_dir),
                allow_patterns=[*MODEL_FILES, "training_args.bin"],
            )
        except Exception as exc:  # noqa: BLE001
            self.load_error = (
                f"Failed to download model files from Hugging Face repo '{model_repo}'. "
                f"Original error: {exc}"
            )

    def _load_model(self) -> None:
        if not self.model_dir.exists() or self._missing_model_files():
            self._download_model_if_configured()

        if self.load_error:
            return

        if not self.model_dir.exists():
            self.load_error = (
                f"Model directory not found at {self.model_dir.resolve()}. "
                "Expected fine-tuned SST-5 files under ./saved_sst5_model."
            )
            return

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.torch = torch
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir)
            self.model.to(self.device)
            self.model.eval()
            self.load_error = None
        except Exception as exc:  # noqa: BLE001
            self.model = None
            self.tokenizer = None
            self.load_error = (
                f"Failed to load model from {self.model_dir.resolve()}. "
                f"Please verify files in ./saved_sst5_model. Original error: {exc}"
            )

    def load_model(self) -> None:
        if self.is_ready:
            return

        with self._load_lock:
            if self.is_ready:
                return
            self.load_error = None
            self._load_model()

    def _ensure_model_ready(self) -> None:
        if not self.is_ready:
            self.load_model()

        if not self.is_ready:
            raise RuntimeError(self.load_error or "Model is not loaded.")

    @staticmethod
    def _clean_text(text: str) -> str:
        if not isinstance(text, str):
            return ""
        return text.strip()

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        self._ensure_model_ready()

        normalized = [self._clean_text(text) for text in texts]
        encoded = self.tokenizer(
            normalized,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}

        with self.torch.no_grad():
            logits = self.model(**encoded).logits
            probabilities = self.torch.softmax(logits, dim=-1).cpu().numpy()

        return probabilities

    def predict_review_sentiment(self, text: str) -> Dict[str, object]:
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            raise ValueError("Review text must be non-empty.")

        probabilities = self.predict_proba([cleaned_text])[0]
        label_index = int(np.argmax(probabilities))
        label = SENTIMENT_LABELS[label_index]

        return {
            "label_index": label_index,
            "label": label,
            "scores": {
                SENTIMENT_LABELS[index]: float(probability)
                for index, probability in enumerate(probabilities)
            },
        }

    def predict_reviews_batch(self, reviews: List[str]) -> List[Dict[str, object]]:
        if not isinstance(reviews, list):
            raise ValueError("reviews must be a list of strings.")
        if not reviews:
            return []

        probabilities_batch = self.predict_proba(reviews)
        predictions = []
        for probabilities in probabilities_batch:
            label_index = int(np.argmax(probabilities))
            label = SENTIMENT_LABELS[label_index]
            predictions.append(
                {
                    "label_index": label_index,
                    "label": label,
                    "scores": {
                        SENTIMENT_LABELS[index]: float(probability)
                        for index, probability in enumerate(probabilities)
                    },
                }
            )

        return predictions
