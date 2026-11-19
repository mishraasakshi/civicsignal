"""Find past complaints that mean the same thing as a new one.

Same maths as a FAISS flat index (cosine similarity of normalised embeddings), done
with numpy. This keeps FAISS out of the API process: on macOS, FAISS and PyTorch in one
process crash. For a few thousand complaints numpy takes well under a millisecond.
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from app.ml.classifier import PROJECT_ROOT, get_classifier

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "real_test_v1.csv"  # until the database exists
DUPLICATE_THRESHOLD = 0.90  # this similar = probably the same complaint sent twice


@dataclass
class Match:
    id: str
    text: str
    category: str
    score: float


class SimilarIndex:
    def __init__(
        self,
        ids: list[str],
        texts: list[str],
        categories: list[str],
        encode: Callable[[list[str]], np.ndarray],
    ):
        self.ids, self.texts, self.categories = ids, texts, categories
        self.encode = encode
        self.vectors = encode(texts).astype("float32")  # one row of 384 numbers per complaint

    def __len__(self) -> int:
        return len(self.ids)

    def search(self, text: str, k: int = 5, min_score: float = 0.0) -> list[Match]:
        query = self.encode([text]).astype("float32")[0]
        scores = self.vectors @ query  # cosine similarity with every stored complaint
        best = np.argsort(scores)[::-1][:k]
        return [
            Match(self.ids[i], self.texts[i], self.categories[i], round(float(scores[i]), 4))
            for i in best
            if scores[i] >= min_score
        ]


@lru_cache(maxsize=1)
def get_similar_index(data_path: Path = DATA_PATH) -> SimilarIndex:
    if not data_path.exists():
        raise FileNotFoundError(f"{data_path} not found")
    df = pd.read_csv(data_path).fillna("")
    encoder = get_classifier().encoder  # reuse the model already loaded for /classify

    def encode(texts: list[str]) -> np.ndarray:
        return encoder.encode(texts, batch_size=64, normalize_embeddings=True)

    return SimilarIndex(df["id"].tolist(), df["text"].tolist(), df["our_label"].tolist(), encode)
