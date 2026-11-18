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

## Labelling rules (category = which team fixes it)
- Geyser, water heater, water cooler, switches -> electrical
- Tap, pipe, flush, drain, no water supply, leaks -> water_plumbing
- Insects or hair IN the food, taste, stale food -> mess_food
- Insects or dirt on tables, floors, counters -> cleanliness
- Broken lock, missing guard, CCTV, strangers -> security
- Broken cupboard, door hinge, chair, bed -> furniture
- LAN port, router, portal, login -> internet_wifi
- Parking, transport, library hours, health centre staff -> other
- Two problems in one complaint -> the more urgent one
- Water cooler: not cooling -> electrical; no water or leaking -> water_plumbing; dirty or insects -> cleanliness

## Real test set (v1) - never used for training
- Source: anonymous Google Form, 108 responses (14-18 Nov 2026)
- Removed: 5 named a real person, 4 not a complaint, 1 exact duplicate -> 98 kept
- Privacy: personal names and room numbers removed; the raw file stays local and git-ignored
- 40 responses arrived one every ~20-30 s in the same polished style -> flagged `suspected_pasted`, scored separately
- 58 genuine responses; labels by our rules (`our_label`), students' own choice kept as `student_label`
- Human baseline: students agree with our rules on 84.5% of genuine responses
- TF-IDF word model: 96.8% on synthetic validation, 55.2% on genuine real, 85.0% on the pasted batch
- Main gap: real complaints about mess policy (token, rebate, menu voting), Hinglish, and new topics (drugs, monkeys) -> mostly predicted `other`
- Weakness: only 2 genuine water_plumbing examples, so treat per-class scores with care
