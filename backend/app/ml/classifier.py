"""Complaint classifier used by the API (Phase 3 model: MiniLM embeddings + logistic regression).

The model is loaded ONCE (on the first request) and then reused, because loading it
takes a few seconds while predicting takes only milliseconds.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/app/ml/classifier.py -> project root
MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "embed_minilm.joblib"
HF_HOME = PROJECT_ROOT / "ml" / ".hf_cache"  # where the embedding model was downloaded
REVIEW_THRESHOLD = 0.5  # below this confidence, a human should check the category


@dataclass
class Prediction:
    category: str
    confidence: float
    top3: list[tuple[str, float]]
    needs_review: bool


class ComplaintClassifier:
    def __init__(self, model_path: Path = MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(f"{model_path} not found - run ml/models/train_embed.py first")
        bundle = joblib.load(model_path)
        self.model_name: str = bundle["embedding_model"]
        self.clf = bundle["classifier"]

        os.environ.setdefault("HF_HOME", str(HF_HOME))
        from sentence_transformers import SentenceTransformer  # slow import, only here

        self.encoder = SentenceTransformer(self.model_name, device="cpu")

    def predict(self, text: str) -> Prediction:
        vector = self.encoder.encode([text], normalize_embeddings=True)
        probs = self.clf.predict_proba(vector)[0]
        best = np.argsort(probs)[::-1][:3]
        top3 = [(str(self.clf.classes_[i]), round(float(probs[i]), 4)) for i in best]
        category, confidence = top3[0]
        return Prediction(category, confidence, top3, confidence < REVIEW_THRESHOLD)


@lru_cache(maxsize=1)
def get_classifier() -> ComplaintClassifier:
    """FastAPI dependency: the same classifier object for every request."""
    return ComplaintClassifier()
