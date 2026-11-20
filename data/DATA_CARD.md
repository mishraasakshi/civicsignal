# Data card

The data card lives in [docs/data_card.md](../docs/data_card.md): synthetic training data
(1,416 complaints), the real test set (98 anonymous student complaints), labelling rules,
privacy steps and known gaps.

Real responses are never committed: `data/raw/` and `data/processed/` are git-ignored, and
`data/real/real_complaints_template.csv` shows only the expected columns.
