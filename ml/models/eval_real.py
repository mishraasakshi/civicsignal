"""Test trained classifiers on REAL student complaints (never used for training).

Run from the project root:
    backend/venv/bin/python ml/models/eval_real.py

It scores every saved model (word / char / both) on data/processed/real_test_v1.csv:
  - ALL        : every kept response (98)
  - REAL ONLY  : responses not flagged as pasted (the number that matters most)
  - PASTED     : the batch that looked pasted in (for comparison)
The "correct answer" is our_label (from the labelling rules).
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score

MODELS = {
    "word": "tfidf_baseline.joblib",
    "char": "tfidf_char.joblib",
    "both": "tfidf_both.joblib",
}


def score(y_true, y_pred) -> dict:
    labels = sorted(set(y_true) | set(y_pred))
    return {
        "n": int(len(y_true)),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/real_test_v1.csv")
    parser.add_argument("--artifacts", default="ml/artifacts")
    parser.add_argument("--details", default="word", help="which model to print full details for")
    args = parser.parse_args()

    df = pd.read_csv(args.data).fillna("")
    real_mask = df["source"] == "real"
    print(f"Loaded {len(df)} real-survey complaints  (real: {real_mask.sum()}, pasted: {(~real_mask).sum()})\n")

    student = score(df.loc[real_mask, "our_label"], df.loc[real_mask, "student_label"])
    print(f"HUMAN BASELINE  students vs our rules (real only): accuracy={student['accuracy']:.3f}\n")

    results = {}
    print(f"{'model':6s} | {'ALL acc':>8s} {'ALL F1':>7s} | {'REAL acc':>8s} {'REAL F1':>8s} | {'PASTED acc':>10s}")
    print("-" * 64)
    for name, file in MODELS.items():
        path = Path(args.artifacts) / file
        if not path.exists():
            print(f"{name:6s} | (no saved model at {path} - skipped)")
            continue
        pipe = joblib.load(path)
        pred = pipe.predict(df["text"])
        df[f"pred_{name}"] = pred
        r_all = score(df["our_label"], pred)
        r_real = score(df.loc[real_mask, "our_label"], pred[real_mask.to_numpy()])
        r_paste = score(df.loc[~real_mask, "our_label"], pred[(~real_mask).to_numpy()])
        results[name] = {"all": r_all, "real_only": r_real, "pasted": r_paste}
        print(
            f"{name:6s} | {r_all['accuracy']:8.3f} {r_all['macro_f1']:7.3f} | "
            f"{r_real['accuracy']:8.3f} {r_real['macro_f1']:8.3f} | {r_paste['accuracy']:10.3f}"
        )

    col = f"pred_{args.details}"
    if col not in df.columns:
        return

    real = df[real_mask]
    print(f"\n=== Details for '{args.details}' on REAL ONLY ===")
    print(classification_report(real["our_label"], real[col], digits=3, zero_division=0))

    wrong = real[real[col] != real["our_label"]]
    print(f"Mistakes on real complaints ({len(wrong)} of {len(real)}):")
    for _, row in wrong.iterrows():
        print(f"  true={row['our_label']:14s} pred={row[col]:14s} | {row['text'][:85]}")

    out = Path(args.artifacts) / "real_eval_metrics.json"
    out.write_text(json.dumps({
        "data": args.data,
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "human_baseline_real_only": student,
        "models": results,
    }, indent=2))
    print(f"\nSaved metrics -> {out}")


if __name__ == "__main__":
    main()
