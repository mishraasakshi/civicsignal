"""Phase 3b: find similar complaints (FAISS) and group repeated problems (DBSCAN).

Run from the project root:
    backend/venv/bin/python ml/models/cluster_complaints.py
    backend/venv/bin/python ml/models/cluster_complaints.py --query "B block geyser kharab hai"

What it does:
1. Turns every real complaint into an embedding (384 numbers about its meaning)
2. FAISS: builds a fast "most similar" search index over them
   - lists near-duplicates (almost the same complaint sent twice)
   - shows the most similar complaints for a query sentence
3. DBSCAN: groups complaints that sit close together ("same problem")
   - complaints that match nothing are "noise" = one-off problems
4. Saves the groups to data/processed/ (git-ignored, contains complaint text)
   and a text-free summary to ml/artifacts/cluster_metrics.json
"""

import argparse
import json
import multiprocessing as mp
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_embed import DEFAULT_MODEL, embed  # noqa: E402  (same model + cache as Phase 3a)

DEFAULT_QUERIES = [
    "B block geyser kharab hai, garam paani nahi aa raha",
    "mess should have a token system instead of fixed monthly fee",
    "wifi is not working in the hostel at night",
]


def embed_safely(texts: list[str], model_name: str, cache_dir: Path) -> np.ndarray:
    """Run the embedding model (PyTorch) in a separate helper process.

    On macOS, PyTorch and FAISS each ship their own copy of OpenMP; loading both
    in one process crashes ("segmentation fault") or freezes. Keeping PyTorch in a
    child process means this main process only ever loads FAISS.
    """
    with mp.get_context("spawn").Pool(1) as pool:
        return pool.apply(embed, (texts, model_name, cache_dir)).astype("float32")


def build_index(vectors: np.ndarray):
    import faiss  # imported here so --help works even without faiss

    # Vectors are normalised, so inner product = cosine similarity (1.0 = identical meaning)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors.astype("float32"))
    return index, faiss


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/real_test_v1.csv")
    parser.add_argument("--out-dir", default="ml/artifacts")
    parser.add_argument("--groups-out", default="data/processed/real_clusters_v1.csv")
    parser.add_argument("--model-name", default=DEFAULT_MODEL)
    parser.add_argument("--hf-home", default="ml/.hf_cache")
    parser.add_argument(
        "--eps",
        type=float,
        default=0.30,
        help="max cosine distance to count as 'same problem' (smaller = stricter)",
    )
    parser.add_argument("--min-samples", type=int, default=2, help="smallest group size")
    parser.add_argument(
        "--dup-threshold", type=float, default=0.90, help="similarity counted as near-duplicate"
    )
    parser.add_argument("--query", action="append", help="sentence to search for (can repeat)")
    args = parser.parse_args()

    os.environ.setdefault("HF_HOME", str(Path(args.hf_home).resolve()))
    out_dir = Path(args.out_dir)

    # 1. Embeddings
    df = pd.read_csv(args.data).fillna("")
    texts = df["text"].tolist()
    print(f"Loaded {len(df)} complaints from {args.data}")
    print(f"Embedding model: {args.model_name}")
    vectors = embed_safely(texts, args.model_name, out_dir / "emb_cache")

    # 2. FAISS index (embeddings for the search queries are made first, still without FAISS loaded)
    queries = args.query or DEFAULT_QUERIES
    q_vecs = embed_safely(queries, args.model_name, out_dir / "emb_cache")
    index, faiss = build_index(vectors)
    faiss.write_index(index, str(out_dir / "real_v1.faiss"))
    print(f"FAISS index: {index.ntotal} complaints\n")

    # 2a. Near-duplicates: each complaint's closest other complaint
    sims, ids = index.search(vectors, 2)  # [0] is itself, [1] is its nearest neighbour
    dup_pairs = sorted(
        {
            tuple(sorted((i, int(ids[i, 1]))))
            for i in range(len(df))
            if sims[i, 1] >= args.dup_threshold
        }
    )
    print("=" * 70)
    print(f"NEAR-DUPLICATES (similarity >= {args.dup_threshold}): {len(dup_pairs)} pairs")
    for a, b in dup_pairs:
        print(f"  {float(vectors[a] @ vectors[b]):.2f}  | {texts[a][:60]}")
        print(f"        | {texts[b][:60]}")

    # 2b. Search: most similar complaints to a new sentence
    q_sims, q_ids = index.search(q_vecs, 3)
    print("\n" + "=" * 70)
    print("SIMILAR-COMPLAINT SEARCH (top 3)")
    for q, row_s, row_i in zip(queries, q_sims, q_ids, strict=True):
        print(f"\n  Query: {q}")
        for s, i in zip(row_s, row_i, strict=True):
            print(f"    {s:.2f}  [{df.loc[i, 'our_label']}] {texts[i][:70]}")

    # 3. DBSCAN groups
    labels = DBSCAN(eps=args.eps, min_samples=args.min_samples, metric="cosine").fit_predict(
        vectors
    )
    df["group"] = labels
    sizes = Counter(labels[labels != -1])
    n_noise = int((labels == -1).sum())

    print("\n" + "=" * 70)
    print(f"DBSCAN GROUPS  eps={args.eps}  min_samples={args.min_samples}")
    print(
        f"{len(sizes)} groups | {len(df) - n_noise} complaints in groups | {n_noise} one-off (noise)"
    )

    groups_info, pure_total = [], 0
    for g, size in sizes.most_common():
        members = df[df["group"] == g]
        main_cat, main_n = Counter(members["our_label"]).most_common(1)[0]
        pure_total += main_n
        n_genuine = int((members["source"] == "real").sum())
        groups_info.append(
            {
                "group": int(g),
                "size": int(size),
                "main_category": main_cat,
                "purity": round(main_n / size, 3),
                "genuine": n_genuine,
            }
        )
        print(
            f"\n  Group {g}: {size} complaints | mostly {main_cat} ({main_n}/{size}) | genuine {n_genuine}"
        )
        for _, r in members.iterrows():
            print(f"    [{r['our_label'][:12]:12s}] {r['text'][:70]}")

    in_groups = len(df) - n_noise
    purity = round(pure_total / in_groups, 3) if in_groups else 0.0
    print("\n" + "=" * 70)
    print(
        f"Purity (share of grouped complaints matching their group's main category): {purity:.3f}"
    )

    # 4. Save
    Path(args.groups_out).parent.mkdir(parents=True, exist_ok=True)
    df[["id", "text", "our_label", "source", "group"]].to_csv(args.groups_out, index=False)
    metrics = {
        "data": args.data,
        "model": args.model_name,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "eps": args.eps,
        "min_samples": args.min_samples,
        "n_complaints": int(len(df)),
        "n_groups": len(sizes),
        "n_in_groups": int(in_groups),
        "n_noise": n_noise,
        "purity": purity,
        "near_duplicate_pairs": len(dup_pairs),
        "groups": groups_info,
    }
    (out_dir / "cluster_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"Saved groups  -> {args.groups_out}  (git-ignored)")
    print(f"Saved index   -> {out_dir / 'real_v1.faiss'}  (git-ignored)")
    print(f"Saved metrics -> {out_dir / 'cluster_metrics.json'}")
    print(
        f"\nSUMMARY  groups={len(sizes)}  grouped={in_groups}  noise={n_noise}  "
        f"purity={purity:.3f}  near_dups={len(dup_pairs)}"
    )


if __name__ == "__main__":
    main()
