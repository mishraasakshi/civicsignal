"""Phase 3: sentence embeddings (MiniLM) + Logistic Regression complaint classifier.

Run from the project root:
    backend/venv/bin/python ml/models/train_embed.py

What it does:
1. Loads the synthetic dataset and makes the SAME 80/20 split as train_tfidf.py (seed 42)
2. Turns every complaint into 384 numbers that capture its meaning (an "embedding")
3. Trains Logistic Regression on the train embeddings
4. Scores it on the synthetic validation part
5. Scores it on the REAL student complaints (never used for training)
6. Compares with the TF-IDF result and the human baseline
7. Saves the classifier and the scores to ml/artifacts/

The first run downloads the embedding model (~470 MB) once into ml/.hf_cache/
(git-ignored); later runs reuse it.
"""

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

SEED = 42
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def score(y_true, y_pred) -> dict:
    labels = sorted(set(y_true) | set(y_pred))
    return {
        "n": int(len(y_true)),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
    }


def embed(texts: list[str], model_name: str, cache_dir: Path) -> np.ndarray:
    """Turn texts into embeddings. Results are cached so re-runs are instant."""
    key = hashlib.sha1((model_name + "\n" + "\n".join(texts)).encode("utf-8")).hexdigest()[:16]
    cache_file = cache_dir / f"emb_{key}.npy"
    if cache_file.exists():
        print(f"  (using cached embeddings: {cache_file.name})")
        return np.load(cache_file)

    from sentence_transformers import SentenceTransformer  # slow import, only when needed

    model = SentenceTransformer(model_name, device="cpu")
    vectors = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.save(cache_file, vectors)
    return vectors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/complaints_v1.csv")
    parser.add_argument("--real", default="data/processed/real_test_v1.csv")
    parser.add_argument("--out-dir", default="ml/artifacts")
    parser.add_argument("--val-size", type=float, default=0.2)
    parser.add_argument("--model-name", default=DEFAULT_MODEL)
    parser.add_argument("--C", type=float, default=1.0, help="higher = fits training data more tightly")
    parser.add_argument("--name", default="embed_minilm", help="file name for saved model/metrics")
    parser.add_argument("--hf-home", default="ml/.hf_cache", help="where the downloaded model is stored")
    args = parser.parse_args()

    # Keep the downloaded model inside the project (git-ignored) instead of ~/.cache
    os.environ.setdefault("HF_HOME", str(Path(args.hf_home).resolve()))

    out_dir = Path(args.out_dir)
    cache_dir = out_dir / "emb_cache"

    # 1. Same split as the TF-IDF baseline, so the comparison is fair
    df = pd.read_csv(args.data).dropna(subset=["text", "category"])
    train_df, val_df = train_test_split(
        df, test_size=args.val_size, stratify=df["category"], random_state=SEED
    )
    real_df = pd.read_csv(args.real).fillna("")
    real_mask = (real_df["source"] == "real").to_numpy()
    print(f"Synthetic: train {len(train_df)} | validation {len(val_df)}")
    print(f"Real test: {len(real_df)}  (genuine {real_mask.sum()}, pasted {(~real_mask).sum()})")

    # 2. Embeddings
    print(f"\nEmbedding model: {args.model_name}")
    all_texts = train_df["text"].tolist() + val_df["text"].tolist() + real_df["text"].tolist()
    vectors = embed(all_texts, args.model_name, cache_dir)
    n_tr, n_val = len(train_df), len(val_df)
    X_train, X_val, X_real = vectors[:n_tr], vectors[n_tr:n_tr + n_val], vectors[n_tr + n_val:]
    print(f"Each complaint is now {vectors.shape[1]} numbers")

    # 3. Train
    clf = LogisticRegression(C=args.C, max_iter=2000, class_weight="balanced", random_state=SEED)
    clf.fit(X_train, train_df["category"])

    # 4. Synthetic validation
    val_pred = clf.predict(X_val)
    syn = score(val_df["category"], val_pred)

    # 5. Real complaints
    real_pred = clf.predict(X_real)
    y_real = real_df["our_label"].to_numpy()
    r_all = score(y_real, real_pred)
    r_gen = score(y_real[real_mask], real_pred[real_mask])
    r_pas = score(y_real[~real_mask], real_pred[~real_mask])

    # 6. Compare with TF-IDF and humans (from eval_real.py's saved results, if present)
    tfidf_real, human = None, None
    prev = out_dir / "real_eval_metrics.json"
    if prev.exists():
        p = json.loads(prev.read_text())
        human = p.get("human_baseline_real_only", {}).get("accuracy")
        tfidf_real = p.get("models", {}).get("word", {}).get("real_only", {}).get("accuracy")

    print("\n" + "=" * 64)
    print(f"{'':28s} {'accuracy':>9s} {'macro F1':>9s}")
    print(f"{'Synthetic validation':28s} {syn['accuracy']:9.3f} {syn['macro_f1']:9.3f}")
    print(f"{'REAL genuine (most important)':28s} {r_gen['accuracy']:9.3f} {r_gen['macro_f1']:9.3f}")
    print(f"{'Real pasted batch':28s} {r_pas['accuracy']:9.3f} {r_pas['macro_f1']:9.3f}")
    print("=" * 64)
    if tfidf_real is not None:
        print(f"Compare on REAL genuine:  TF-IDF {tfidf_real:.3f}  ->  embeddings {r_gen['accuracy']:.3f}"
              f"  |  humans {human:.3f}")

    real_gen = real_df[real_mask].assign(predicted=real_pred[real_mask])
    print("\nPer-category report (REAL genuine only):")
    print(classification_report(real_gen["our_label"], real_gen["predicted"], digits=3, zero_division=0))

    wrong = real_gen[real_gen["predicted"] != real_gen["our_label"]]
    print(f"Mistakes on real complaints ({len(wrong)} of {len(real_gen)}):")
    for _, row in wrong.iterrows():
        print(f"  true={row['our_label']:14s} pred={row['predicted']:14s} | {row['text'][:85]}")

    # 7. Save
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"embedding_model": args.model_name, "classifier": clf}, out_dir / f"{args.name}.joblib")
    metrics = {
        "model": f"{args.model_name} + logistic_regression",
        "C": args.C,
        "data": args.data,
        "real_data": args.real,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "embedding_dim": int(vectors.shape[1]),
        "synthetic_val": syn,
        "real_all": r_all,
        "real_genuine": r_gen,
        "real_pasted": r_pas,
        "tfidf_real_genuine_accuracy": tfidf_real,
        "human_baseline_real_genuine": human,
    }
    (out_dir / f"{args.name}_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"\nSaved model   -> {out_dir / (args.name + '.joblib')}")
    print(f"Saved metrics -> {out_dir / (args.name + '_metrics.json')}")
    print(f"\nSUMMARY [{args.name} C={args.C}]  synthetic={syn['accuracy']:.3f}  "
          f"real_genuine={r_gen['accuracy']:.3f}  pasted={r_pas['accuracy']:.3f}")


if __name__ == "__main__":
    main()
