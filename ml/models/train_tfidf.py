"""Phase 2 baseline: TF-IDF + Logistic Regression complaint classifier.

Run from the project root:
    backend/venv/bin/python ml/models/train_tfidf.py

What it does:
1. Loads the clean dataset (data/processed/complaints_v1.csv)
2. Splits it 80% train / 20% validation (same category mix in both)
3. Turns text into numbers with TF-IDF
4. Trains Logistic Regression on the train part
5. Scores it on the validation part (accuracy, macro F1, per category)
6. Shows the words the model relies on most for each category
7. Saves the trained model and the scores to ml/artifacts/
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

SEED = 42


def word_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),  # single words and word pairs ("not working")
        min_df=2,  # ignore words that appear only once
        sublinear_tf=True,
    )


def char_vectorizer() -> TfidfVectorizer:
    # Pieces of 2-5 letters inside each word: "toot", "tuta", "tooti" share "too"/"oot".
    # Helps with typos and Hinglish spelling variations.
    return TfidfVectorizer(
        lowercase=True,
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=2,
        sublinear_tf=True,
    )


def build_pipeline(features: str) -> Pipeline:
    if features == "word":
        vec = word_vectorizer()
    elif features == "char":
        vec = char_vectorizer()
    else:  # both
        vec = FeatureUnion([("word", word_vectorizer()), ("char", char_vectorizer())])
    return Pipeline(
        [
            ("tfidf", vec),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)),
        ]
    )


def top_words(pipe: Pipeline, n: int = 8) -> dict:
    vocab = pipe.named_steps["tfidf"].get_feature_names_out()
    clf = pipe.named_steps["clf"]
    out = {}
    for i, label in enumerate(clf.classes_):
        best = clf.coef_[i].argsort()[::-1][:n]
        out[label] = [vocab[j] for j in best]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/complaints_v1.csv")
    parser.add_argument("--out-dir", default="ml/artifacts")
    parser.add_argument("--val-size", type=float, default=0.2)
    parser.add_argument(
        "--features",
        choices=["word", "char", "both"],
        default="word",
        help="word = whole words (baseline), char = letter pieces, both = combined",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    df = df.dropna(subset=["text", "category"])
    print(f"Loaded {len(df)} complaints from {args.data}")

    train_df, val_df = train_test_split(
        df, test_size=args.val_size, stratify=df["category"], random_state=SEED
    )
    print(f"Train: {len(train_df)}  |  Validation: {len(val_df)}\n")

    print(f"Features: {args.features}")
    pipe = build_pipeline(args.features)
    pipe.fit(train_df["text"], train_df["category"])

    pred = pipe.predict(val_df["text"])
    acc = accuracy_score(val_df["category"], pred)
    macro_f1 = f1_score(val_df["category"], pred, average="macro")

    print("=" * 60)
    print(f"ACCURACY : {acc:.3f}")
    print(f"MACRO F1 : {macro_f1:.3f}")
    print("=" * 60)
    print("\nPer-category report:")
    print(classification_report(val_df["category"], pred, digits=3))

    labels = list(pipe.named_steps["clf"].classes_)
    cm = confusion_matrix(val_df["category"], pred, labels=labels)
    print("Confusion matrix (rows = true, columns = predicted):")
    print(pd.DataFrame(cm, index=labels, columns=[label[:6] for label in labels]).to_string())

    by_source = {}
    if "source_model" in val_df.columns:
        print("\nAccuracy by generator model (validation):")
        val_eval = val_df.assign(correct=(pred == val_df["category"].to_numpy()))
        for src, grp in val_eval.groupby("source_model"):
            by_source[src] = round(float(grp["correct"].mean()), 4)
            print(f"  {src:15s} {grp['correct'].mean():.3f}  (n={len(grp)})")

    words = top_words(pipe)
    print("\nTop words per category (what the model looks at):")
    for label, ws in words.items():
        print(f"  {label:15s} {', '.join(ws)}")

    val_eval = val_df.assign(predicted=pred)
    wrong = val_eval[val_eval["predicted"] != val_eval["category"]]
    print(f"\nSome mistakes ({len(wrong)} total):")
    for _, row in wrong.head(8).iterrows():
        print(f"  true={row['category']:14s} pred={row['predicted']:14s} | {str(row['text'])[:80]}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = "tfidf_baseline" if args.features == "word" else f"tfidf_{args.features}"
    joblib.dump(pipe, out_dir / f"{name}.joblib")
    metrics = {
        "model": f"tfidf_{args.features} + logistic_regression",
        "features": args.features,
        "data": args.data,
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "seed": SEED,
        "n_train": len(train_df),
        "n_val": len(val_df),
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "accuracy_by_source": by_source,
        "n_mistakes": int(len(wrong)),
        "top_words": words,
    }
    (out_dir / f"{name}_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"\nSaved model   -> {out_dir / (name + '.joblib')}")
    print(f"Saved metrics -> {out_dir / (name + '_metrics.json')}")
    print(
        f"\nSUMMARY [{args.features}]  accuracy={acc:.3f}  macro_f1={macro_f1:.3f}  "
        f"mistakes={len(wrong)}  by_source={by_source}"
    )


if __name__ == "__main__":
    main()
