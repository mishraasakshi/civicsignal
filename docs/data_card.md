# Data Card: CivicSignal synthetic complaints v1

- File: data/processed/complaints_v1.csv
- Rows: 1416 (1425 generated, 9 exact duplicates removed)
- Created: 2026-11-13 with ml/data_gen/generate.py (seed 42) via Groq API
- Models: gpt-oss-120b 817 rows, qwen3.8-27b 569 rows, gpt-oss-20b 30 rows (column source_model)
- Categories: cleanliness 192, security 180, furniture 179, water_plumbing 178, mess_food 177, other 175, internet_wifi 173, electrical 162
- Styles: English, Hinglish, short, typo-heavy, casual

## Cleaning
- Keyword auto-correct disabled (substring bug, e.g. ac matched packed)
- Exact duplicates removed after lowercasing and normalising spaces

## Known limitations
- Synthetic text written by LLMs, not real students
- Labels come from the generator model; about 30 rows checked by hand
- Near-duplicates (same meaning, different words) not removed yet

## Intended use
- Training and validation of the category classifier
- Final test set will be REAL Amity complaints (Google Form), never synthetic
