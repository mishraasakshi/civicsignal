# CivicSignal Model Evaluation & Benchmark Log

> **Rule:** Every number recorded in this document must come directly from a reproducible script execution. No invented or simulated scores.

---

## 1. Evaluation Methodology

### A. Model A: Category Classifier
- **Target Metric**: Macro-averaged F1 score, per-class precision and recall.
- **Evaluation Sets**:
  - Synthetic Validation Set: To evaluate model convergence and hyperparameters.
  - Real-Only Test Set: Complaints collected directly from Amity students via Google Form (never seen in training).
  - Synthetic-to-Real Generalization Gap: $\Delta = \text{Macro F1}_{\text{val}} - \text{Macro F1}_{\text{real}}$.
- **Models Compared**:
  - Baseline: TF-IDF (word 1–2-grams + character 3–5-grams) + Logistic Regression / Linear SVM.
  - Candidate: `paraphrase-multilingual-MiniLM-L12-v2` dense embeddings + Logistic Regression.
  - *Decision Gate:* The embedding model is adopted only if it strictly outperforms the TF-IDF baseline on the real test set.

### B. Model B: Semantic Duplicate Retrieval
- **Metrics**: Precision@5 and Recall@5 evaluated on 300–500 hand-labelled complaint pairs (Same Issue, Different Issue, Ambiguous).
- **Composite Scoring Formula**:
  $$S = w_t \cdot \text{text\_similarity} + w_l \cdot \text{location\_similarity} + w_d \cdot \text{date\_proximity}$$

### C. Model C: Geospatial Hotspots
- **Algorithm**: `DBSCAN(metric='haversine', eps=radius_in_radians, min_samples=2)`
- **Evaluation**: Supervisor cluster confirmation rate (% of suggested clusters accepted).

---

## 2. Benchmark Log Table

*(Results will be populated upon completion of Phase 2 and Phase 3 scripts)*

| Date | Model | Dataset Version | Macro F1 (Val) | Macro F1 (Real Test) | Generalization Gap | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| *Pending Phase 2* | Baseline TF-IDF + LogReg | v1-synthetic | TBD | TBD | TBD | Scheduled |
| *Pending Phase 2* | Baseline TF-IDF + Linear SVM | v1-synthetic | TBD | TBD | TBD | Scheduled |
| *Pending Phase 2* | Multilingual MiniLM + LogReg | v1-synthetic | TBD | TBD | TBD | Scheduled |
