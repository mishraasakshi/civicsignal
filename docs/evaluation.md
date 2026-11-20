# Model evaluation

> Rule: every number here comes from a script in `ml/models/` and is saved in
> `ml/artifacts/*_metrics.json`. Nothing is estimated by hand.

## Data

| Set | Size | Source | Used for |
| :--- | :---: | :--- | :--- |
| Synthetic | 1,416 (1,132 train / 284 validation) | LLMs on Groq (gpt-oss-120b, qwen3.8-27b, gpt-oss-20b), seed 42; English, Hinglish, short, typo-heavy, casual styles | training + validation |
| Real test set | 98 | Anonymous Google Form, 108 responses (14-18 Nov 2026); 5 naming a person, 4 non-complaints and 1 duplicate removed | **testing only - never trained on** |

The 98 real complaints split into **58 genuine** responses and **40 suspected pasted** ones (they
arrived one every ~20-30 s in the same polished style), so each group is scored separately.
Labels follow fixed rules (see the [data card](data_card.md)); students' own category choices
were kept to measure a **human baseline**: students agree with the rules on 84.5 % of genuine
responses.

## Category classifier

Metric: accuracy and macro-F1 over 8 categories.

| Model | Synthetic val. acc. | Real genuine (58) acc. / macro-F1 | Real pasted (40) acc. | All real (98) acc. / macro-F1 |
| :--- | :---: | :---: | :---: | :---: |
| TF-IDF words + logistic regression | 96.8 % | 55.2 % / 0.49 | 85.0 % | 67.3 % / 0.61 |
| TF-IDF characters + logistic regression | 97.2 % | 55.2 % / 0.51 | 85.0 % | 67.3 % / 0.65 |
| TF-IDF words + characters + logistic regression | 97.2 % | 46.6 % / 0.46 | 85.0 % | 62.2 % / 0.63 |
| **Multilingual MiniLM embeddings + logistic regression (deployed)** | 95.8 % | **65.5 % / 0.63** | **92.5 %** | **76.5 % / 0.76** |

Scripts: `ml/models/train_tfidf.py`, `ml/models/train_embed.py`, `ml/models/eval_real.py`.

**Findings**

- **Synthetic-to-real gap.** All models score ~96-97 % on synthetic validation but far lower on
  genuine student writing. Synthetic accuracy alone would have badly overstated quality.
- **Embeddings generalise better.** The multilingual MiniLM model gains about 10 points on
  genuine complaints over the best TF-IDF model, mainly on Hinglish and on wording the
  generator never produced. It was adopted because it wins on the *real* test set, not on
  synthetic validation (where TF-IDF is slightly higher).
- **Where it still fails:** mess-policy complaints (tokens, rebates, menu voting) and topics the
  generator never covered (drugs, monkeys) drift to `other`. Only 2 genuine `water_plumbing`
  examples exist, so per-class scores are unreliable.
- **Safety net:** predictions below 50 % confidence are flagged `needs_review` so a supervisor
  checks the category.

## Repeated-problem groups

`ml/models/cluster_complaints.py`: DBSCAN on the MiniLM embeddings (cosine distance,
`eps=0.30`, `min_samples=2`) over the 98 real complaints.

| Groups | Complaints in groups | One-off (noise) | Purity | Near-duplicate pairs (similarity >= 0.90) |
| :---: | :---: | :---: | :---: | :---: |
| 9 | 30 | 68 | 83.3 % | 0 |

Purity = share of grouped complaints that match their group's main category. Each group is then
summarised by an LLM (`ml/models/summarize_groups.py`, Groq via LangChain) into a JSON object
(title, summary, category, urgency, suggested action) validated with Pydantic, with one retry on
invalid output and a cache so re-runs cost no extra requests.

## Similar-complaint search

Embeddings are stored per complaint; the supervisor-only `/api/similar` endpoint ranks complaints
by cosine similarity. In the production rehearsal, an English query found a Hinglish complaint
about the same problem with similarity 0.72 (cross-language matching works because the model is
multilingual).

## Not evaluated yet

- Retrieval precision@k on hand-labelled duplicate pairs (needs a labelled pair set).
- Supervisor acceptance rate of suggested groups (needs real supervisor usage).
