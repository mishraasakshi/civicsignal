#!/usr/bin/env python3
"""
Phase 1: Synthetic Complaint Generator using Groq API via LangChain
Generates multilingual (English, Hinglish, typos, short, angry) campus complaints
and labelled duplicate pairs for Amity University Lucknow.

Key design decisions:
- Resumable: each batch is appended to cache immediately so a rate-limit crash loses at most one batch.
- Idempotent: re-running with the same --seed and --count is free (served from cache).
- Category-aware location sampling: mess complaints go to mess/hostels, not management blocks, etc.
- "other" is tightly scoped and auto-corrected if model mis-labels a 7-category issue.
- Styles are deliberately messy: lowercase, missing punctuation, Hinglish fragments, WhatsApp tone.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta
from typing import Any

# Project root on sys.path so dotenv / backend imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

from langchain_core.prompts import ChatPromptTemplate  # noqa: E402  (after load_dotenv on purpose)
from langchain_groq import ChatGroq  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402, F401 – used for Pydantic models if needed later

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
CATEGORIES = [
    "water_plumbing",
    "electrical",
    "cleanliness",
    "internet_wifi",
    "furniture",
    "mess_food",
    "security",
    "other",
]

# Keyword hints used at validation/auto-correct time (not sent to model)
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "electrical": [
        "ac",
        "air condition",
        "light",
        "fan",
        "switch",
        "plug",
        "socket",
        "wire",
        "bulb",
        "tube",
        "power",
        "electricity",
        "inverter",
        "mcb",
        "heater",
        "geyser",
        "electric",
    ],
    "water_plumbing": [
        "water",
        "tap",
        "pipe",
        "drain",
        "leak",
        "flood",
        "washroom",
        "toilet",
        "bathroom",
        "overflow",
        "clog",
        "plumb",
        "sewage",
    ],
    "internet_wifi": [
        "wifi",
        "wi-fi",
        "internet",
        "net",
        "network",
        "broadband",
        "lan",
        "portal",
        "connection",
        "speed",
        "bandwidth",
    ],
    "cleanliness": [
        "dirty",
        "clean",
        "dust",
        "garbage",
        "trash",
        "mess",
        "litter",
        "hygiene",
        "smell",
        "rat",
        "cockroach",
        "pest",
        "mop",
        "sweep",
    ],
    "furniture": [
        "chair",
        "table",
        "bench",
        "desk",
        "board",
        "cupboard",
        "almirah",
        "shelf",
        "broken",
        "crack",
        "leg",
        "seat",
        "locker",
    ],
    "mess_food": [
        "food",
        "mess",
        "canteen",
        "meal",
        "lunch",
        "dinner",
        "breakfast",
        "khana",
        "roti",
        "dal",
        "rice",
        "quality",
        "taste",
        "menu",
        "cook",
        "expired",
    ],
    "security": [
        "guard",
        "security",
        "cctv",
        "camera",
        "door",
        "lock",
        "gate",
        "unauthorized",
        "theft",
        "stolen",
        "safe",
        "entry",
        "visitor",
    ],
}

CAMPUS_LOCATIONS = [
    {"label": "Hostel A - Boys (Malhar)", "latitude": 26.8580, "longitude": 80.9990},
    {"label": "Hostel B - Boys", "latitude": 26.8584, "longitude": 80.9995},
    {"label": "Hostel C - Girls", "latitude": 26.8572, "longitude": 80.9982},
    {"label": "Hostel D - Girls", "latitude": 26.8576, "longitude": 80.9986},
    {"label": "Main Campus Gate", "latitude": 26.8565, "longitude": 80.9975},
    {"label": "Central Library", "latitude": 26.8590, "longitude": 81.0002},
    {"label": "Main Canteen & Food Court", "latitude": 26.8582, "longitude": 81.0008},
    {"label": "Academic Block 1 (Engineering)", "latitude": 26.8595, "longitude": 81.0010},
    {"label": "Academic Block 2 (Management)", "latitude": 26.8598, "longitude": 81.0015},
    {"label": "Academic Block 3 (Law & Humanities)", "latitude": 26.8602, "longitude": 81.0020},
    {"label": "Academic Block 4", "latitude": 26.8605, "longitude": 81.0025},
    {"label": "Sports Ground & Pavilion", "latitude": 26.8568, "longitude": 81.0018},
    {"label": "Student Parking Lot", "latitude": 26.8562, "longitude": 80.9980},
    {"label": "Auditorium Complex", "latitude": 26.8588, "longitude": 81.0012},
    {"label": "Health Center & Clinic", "latitude": 26.8578, "longitude": 80.9978},
]

# Category → list of *plausible* location labels (subset of CAMPUS_LOCATIONS)
CATEGORY_LOCATION_MAP: dict[str, list[str]] = {
    "water_plumbing": [
        "Hostel A - Boys (Malhar)",
        "Hostel B - Boys",
        "Hostel C - Girls",
        "Hostel D - Girls",
        "Academic Block 1 (Engineering)",
        "Academic Block 2 (Management)",
        "Academic Block 3 (Law & Humanities)",
        "Academic Block 4",
        "Main Canteen & Food Court",
        "Health Center & Clinic",
    ],
    "electrical": [
        "Hostel A - Boys (Malhar)",
        "Hostel B - Boys",
        "Hostel C - Girls",
        "Hostel D - Girls",
        "Central Library",
        "Academic Block 1 (Engineering)",
        "Academic Block 2 (Management)",
        "Academic Block 3 (Law & Humanities)",
        "Academic Block 4",
        "Auditorium Complex",
    ],
    "cleanliness": [
        "Hostel A - Boys (Malhar)",
        "Hostel B - Boys",
        "Hostel C - Girls",
        "Hostel D - Girls",
        "Main Canteen & Food Court",
        "Sports Ground & Pavilion",
        "Student Parking Lot",
        "Academic Block 1 (Engineering)",
        "Central Library",
    ],
    "internet_wifi": [
        "Central Library",
        "Hostel A - Boys (Malhar)",
        "Hostel B - Boys",
        "Hostel C - Girls",
        "Hostel D - Girls",
        "Academic Block 1 (Engineering)",
        "Academic Block 2 (Management)",
        "Academic Block 3 (Law & Humanities)",
        "Academic Block 4",
    ],
    "furniture": [
        "Central Library",
        "Academic Block 1 (Engineering)",
        "Academic Block 2 (Management)",
        "Academic Block 3 (Law & Humanities)",
        "Academic Block 4",
        "Hostel A - Boys (Malhar)",
        "Hostel B - Boys",
        "Hostel C - Girls",
        "Hostel D - Girls",
        "Auditorium Complex",
    ],
    "mess_food": [
        "Main Canteen & Food Court",
        "Hostel A - Boys (Malhar)",
        "Hostel B - Boys",
        "Hostel C - Girls",
        "Hostel D - Girls",
    ],
    "security": [
        "Main Campus Gate",
        "Hostel A - Boys (Malhar)",
        "Hostel B - Boys",
        "Hostel C - Girls",
        "Hostel D - Girls",
        "Student Parking Lot",
        "Academic Block 1 (Engineering)",
    ],
    "other": [
        # other = seating, noise, transport, admin — anywhere is plausible
        "Main Campus Gate",
        "Sports Ground & Pavilion",
        "Auditorium Complex",
        "Academic Block 1 (Engineering)",
        "Academic Block 2 (Management)",
        "Academic Block 3 (Law & Humanities)",
        "Academic Block 4",
        "Student Parking Lot",
        "Health Center & Clinic",
    ],
}

STYLES = [
    "formal_english",
    "casual_english",
    "hinglish",
    "typos",
    "very_short",
    "angry",
    "vague_location",
]

# ---------------------------------------------------------------------------
# System + user prompts
# Note: curly braces that are NOT LangChain template variables are doubled {{}}
# so LangChain does not try to substitute them.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are a data-generation assistant creating training data for an AI complaint classifier at Amity University Lucknow.
Simulate realistic student messages — raw, unfiltered, exactly how students type on WhatsApp or Google Forms.

══════════════════════════════════════════════════════
 STYLE GUIDE — apply the requested style faithfully
══════════════════════════════════════════════════════
• formal_english   → polite, full sentences, correct grammar.
• casual_english   → relaxed but readable; minor shortcuts ("isn't", "can't").
• hinglish         → heavy Roman-script Hindi mixed with English; e.g.
    "bhai hostel A ke neeche paani bhar gaya hai koi nahi aa raha dekhne",
    "mess ka khana aaj bhi kharab tha daal me keede the yaar",
    "wifi chal hi nahi raha ek ghante se portal nahi khul raha help karo",
    "room me light nahi aa rahi se subah se andhere me baitha hoon".
• typos            → keyboard mistakes, missing spaces, wrong letters; e.g.
    "continuos leek outsde blcok A washrom", "flikring tubeliight 3rd flor".
• very_short       → 2-7 words, no punctuation; e.g.
    "wifi down again", "tap broken hostel b", "no light room 204".
• angry            → ALL CAPS words, exclamation marks, repetition, frustration; e.g.
    "3rd time complain kar raha hoon KUCH NHI HUA disgusting!!",
    "This is UNACCEPTABLE. 2 days no water and nobody cares!!!".
• vague_location   → use ONLY vague relative references, NEVER exact location names; e.g.
    "near the canteen stairs", "2nd floor washroom", "behind the library",
    "one of the hostels", "near the main gate area", "that block near parking".

══════════════════════════════════════════════════════
 CATEGORY DEFINITIONS — be strict
══════════════════════════════════════════════════════
water_plumbing  → taps, pipes, leaks, drains, floods, toilets, sewage.
electrical      → lights, fans, ACs, switches, power cuts, sockets, geysers, inverters.
cleanliness     → dirt, garbage, pests, bad smell, unswept floors, dustbins overflowing.
internet_wifi   → WiFi speed, portal not loading, LAN down, network outage.
furniture       → broken chairs, missing desks, damaged almirahs/lockers, benches.
mess_food       → food quality, canteen hygiene, expired items, meal timings.
security        → unauthorized access, missing CCTV, broken locks, theft, guard absence.
other           → ONLY use this for issues that do NOT fit any of the 7 categories above.
                  Valid "other" issues: shuttle / bus / transport problems, noisy neighbours,
                  seating shortage in common areas, event-related noise, admin paperwork delays,
                  exam hall booking issues, sports equipment damage.
                  ⚠ ACs, geysers → electrical. Leaking pipes → water_plumbing.
                  ⚠ If in doubt between "other" and a real category, pick the real category.

══════════════════════════════════════════════════════
 OUTPUT FORMAT — respond with ONLY valid JSON, no markdown fences
══════════════════════════════════════════════════════
{{"complaints": [
  {{
    "text": "<the raw student message>",
    "category": "<one of the 8 categories>",
    "location_label": "<exact campus location label from the list you are given>",
    "style": "<style name>",
    "urgency": "low" | "medium" | "high",
    "clean_summary_en": "<one concise English sentence describing the issue>"
  }}
]}}
"""

USER_PROMPT_TEMPLATE = """\
Generate exactly {batch_size} unique, realistic student complaints.

Allowed campus locations (use the exact label string):
{location_list}

Requested specifications (one complaint per line):
{specifications}

Rules:
1. Each complaint MUST match the category, location, and style requested.
2. The "text" field should sound like it was typed on a phone — casual, imperfect, authentic.
3. For vague_location style: the "text" must NOT contain the exact location label; use relative/vague references only.
4. For "other" category: the issue must NOT be solvable by water_plumbing, electrical, cleanliness, internet_wifi, furniture, mess_food, or security teams.
5. Vary sentence length: some very short (5 words), some medium (20 words), some longer (40+ words).
6. Output ONLY valid JSON with the "complaints" array. No extra text.
"""


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------


def init_llm(model_name: str | None = None) -> ChatGroq:
    """Create and return a ChatGroq instance using env-configured credentials."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in environment or .env file.")

    selected_model = model_name or os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b")
    print(f"[LLM] Using model: {selected_model}")
    return ChatGroq(
        model_name=selected_model,
        groq_api_key=api_key,
        temperature=0.85,  # slightly higher for more variety
        max_retries=5,
    )


def _clean_json_response(raw: str) -> str:
    """Strip markdown fences that some models add despite instructions."""
    content = raw.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def _auto_correct_category(item: dict[str, Any]) -> dict[str, Any]:
    """
    Post-generation correction: if an item is labelled 'other' but its text
    contains strong keywords from a real category, relabel it.
    Also fixes the reverse: if a 7-category item clearly belongs elsewhere.
    Returns the item (possibly mutated).
    """
    if item.get("category") != "other":
        return item  # only auto-fix mis-labelled "other"

    text_lower = item.get("text", "").lower() + " " + item.get("clean_summary_en", "").lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            old = item["category"]
            item["category"] = cat
            item["_autocorrected"] = f"{old} → {cat}"
            break
    return item


def generate_batch_with_retry(
    llm: ChatGroq,
    specifications_str: str,
    batch_size: int,
    location_list_str: str,
) -> list[dict[str, Any]]:
    """
    Call Groq with exponential backoff.
    Returns a list of validated complaint dicts.
    """
    # Double all curly braces in the static parts so LangChain won't misinterpret them.
    # The SYSTEM_PROMPT already has {{ }} around JSON examples.
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT_TEMPLATE),
        ]
    )
    chain = prompt | llm

    max_attempts = 6
    delay = 3.0

    for attempt in range(max_attempts):
        try:
            response = chain.invoke(
                {
                    "batch_size": batch_size,
                    "specifications": specifications_str,
                    "location_list": location_list_str,
                }
            )
            content = _clean_json_response(response.content)
            data = json.loads(content)
            items: list[dict[str, Any]] = data.get("complaints", [])
            if not items:
                raise ValueError("Empty 'complaints' array returned by model.")

            # Apply auto-correction for misclassified "other"
            pass  # auto-correct disabled: substring matching mislabelled items
            return items

        except Exception as exc:
            err = str(exc)
            # Auth errors are fatal — don't retry
            if "401" in err or "invalid_api_key" in err:
                raise
            if attempt < max_attempts - 1:
                wait = delay * (2**attempt)
                print(
                    f"  [Retry {attempt+1}/{max_attempts}] Error: {err[:80]} — waiting {wait:.1f}s..."
                )
                time.sleep(wait)
            else:
                raise RuntimeError(f"Batch failed after {max_attempts} attempts: {exc}") from exc

    return []  # unreachable but keeps type checker happy


# ---------------------------------------------------------------------------
# Cache / resumability helpers
# ---------------------------------------------------------------------------


def _load_cache(cache_path: str) -> dict[str, Any]:
    """Load existing cache or return empty structure."""
    if os.path.exists(cache_path):
        try:
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            print(f"[Cache] Warning: could not read cache ({exc}). Starting fresh.")
    return {"complaints": [], "batches_completed": [], "metadata": {}}


def _save_cache(cache_path: str, data: dict[str, Any]) -> None:
    """Write cache atomically (write to temp then rename)."""
    tmp_path = cache_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, cache_path)


# ---------------------------------------------------------------------------
# Main generation function
# ---------------------------------------------------------------------------


def generate_synthetic_complaints(
    target_count: int = 50,
    batch_size: int = 10,
    seed: int = 42,
    cache_path: str = "data/raw/synthetic_complaints_cache.json",
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Generate `target_count` synthetic complaints, batching Groq requests.

    Resumability design:
    - After every batch succeeds, the cache file is updated immediately.
    - On restart (without --force-refresh), already-completed batches are
      skipped; generation continues from where it stopped.
    - Batches are identified by a stable key: (batch_index, seed).

    Returns a dict with keys: complaints, requests_made, model_used,
    generated_at, duration_seconds, total_count.
    """
    random.seed(seed)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    llm = init_llm()
    model_name = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b")
    start_time = time.time()
    now = datetime.utcnow()

    # --- Load or init cache ---
    if force_refresh:
        cache = {"complaints": [], "batches_completed": [], "metadata": {}}
        print("[Cache] --force-refresh: ignoring existing cache.")
    else:
        cache = _load_cache(cache_path)
        already_have = len(cache.get("complaints", []))
        if already_have >= target_count:
            print(
                f"[Cache] Already have {already_have} complaints (need {target_count}). Serving from cache."
            )
            return {
                "complaints": cache["complaints"][:target_count],
                "requests_made": 0,
                "cache_hit": True,
                "model_used": cache.get("metadata", {}).get("model_used", "cached"),
                "generated_at": cache.get("metadata", {}).get("generated_at"),
                "duration_seconds": 0,
                "total_count": already_have,
            }
        if already_have > 0:
            print(
                f"[Cache] Resuming: {already_have} complaints already in cache, need {target_count - already_have} more."
            )

    completed_batch_keys = set(cache.get("batches_completed", []))
    all_complaints: list[dict[str, Any]] = cache.get("complaints", [])
    requests_made = 0

    # --- Build a deterministic per-category balanced plan ---
    # Distribute target_count across 8 categories roughly evenly.
    total_batches = (target_count + batch_size - 1) // batch_size

    # Pre-plan all (category, style, location) specs deterministically from seed
    rng = random.Random(seed)

    # Cycle categories and styles so each batch is diverse
    plan: list[dict[str, str]] = []
    for i in range(target_count):
        cat = CATEGORIES[i % len(CATEGORIES)]
        style = STYLES[i % len(STYLES)]
        allowed_locs = CATEGORY_LOCATION_MAP.get(cat, [loc["label"] for loc in CAMPUS_LOCATIONS])
        loc = rng.choice(allowed_locs)
        plan.append({"category": cat, "style": style, "location": loc})

    # Shuffle plan (deterministically) so category/style distribution is spread across batches
    rng.shuffle(plan)

    # Location list string sent to model in every request
    location_list_str = "\n".join(f"- {loc['label']}" for loc in CAMPUS_LOCATIONS)

    print(
        f"Generating {target_count} complaints across {total_batches} batch(es) of ~{batch_size}..."
    )

    for b_idx in range(total_batches):
        batch_key = f"b{b_idx}_s{seed}"
        if batch_key in completed_batch_keys:
            print(f"  [Batch {b_idx+1}/{total_batches}] Already done (cached). Skipping.")
            continue

        # Slice the plan for this batch
        start = b_idx * batch_size
        end = min(start + batch_size, target_count)
        batch_plan = plan[start:end]
        cur_batch_size = len(batch_plan)

        specs = []
        for i, spec in enumerate(batch_plan, 1):
            specs.append(
                f"{i}. Category: '{spec['category']}', "
                f"Location: '{spec['location']}', "
                f"Style: '{spec['style']}'"
            )
        spec_str = "\n".join(specs)

        print(
            f"  -> Batch {b_idx+1}/{total_batches}: {cur_batch_size} complaints (request #{requests_made+1})..."
        )

        items = generate_batch_with_retry(llm, spec_str, cur_batch_size, location_list_str)
        requests_made += 1

        # Enrich with coordinates and synthetic timestamps
        for item in items:
            # Match location label → coordinates
            loc_label = item.get("location_label", "")
            loc_match = next(
                (loc for loc in CAMPUS_LOCATIONS if loc["label"].lower() == str(loc_label).lower()),
                None,
            )
            if not loc_match:
                # Fallback: use the planned location for this spec slot
                planned_label = (
                    batch_plan[0]["location"] if batch_plan else CAMPUS_LOCATIONS[0]["label"]
                )
                loc_match = next(
                    (loc for loc in CAMPUS_LOCATIONS if loc["label"] == planned_label),
                    CAMPUS_LOCATIONS[0],
                )
                item["location_label"] = loc_match["label"]
                item["_location_fallback"] = True

            item["latitude"] = loc_match["latitude"]
            item["longitude"] = loc_match["longitude"]

            # Synthetic timestamp spread over last 30 days
            offset_hours = rng.randint(1, 30 * 24)
            item["created_at"] = (now - timedelta(hours=offset_hours)).isoformat()
            item["id"] = len(all_complaints) + 1
            all_complaints.append(item)

        # Mark batch complete and persist cache immediately (resumability)
        cache["complaints"] = all_complaints
        cache.setdefault("batches_completed", []).append(batch_key)
        cache["metadata"] = {
            "model_used": model_name,
            "generated_at": datetime.utcnow().isoformat(),
            "seed": seed,
            "target_count": target_count,
        }
        _save_cache(cache_path, cache)
        print(
            f"     ✓ {len(items)} complaints added (total: {len(all_complaints)}). Cache updated."
        )

        # Rate-limit safety pause between batches
        if b_idx < total_batches - 1:
            time.sleep(1.5)

    duration = round(time.time() - start_time, 2)
    print(
        f"\n[Done] {len(all_complaints)} complaints in cache. {requests_made} new Groq requests. ({duration}s)"
    )

    return {
        "complaints": all_complaints[:target_count],
        "requests_made": requests_made,
        "cache_hit": False,
        "model_used": model_name,
        "generated_at": datetime.utcnow().isoformat(),
        "duration_seconds": duration,
        "total_count": len(all_complaints),
    }


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------


def print_summary_and_samples(data: dict[str, Any], num_samples: int = 10) -> None:
    complaints = data.get("complaints", [])
    print("\n" + "=" * 70)
    print("PHASE 1 — SYNTHETIC DATA GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Complaints in Cache : {data.get('total_count', len(complaints))}")
    print(f"Returned this run         : {len(complaints)}")
    print(f"Groq API Requests Used    : {data.get('requests_made', 0)}")
    print(f"Cache Hit (no API calls)  : {data.get('cache_hit', False)}")
    print(f"Model Used                : {data.get('model_used')}")
    print(f"Duration                  : {data.get('duration_seconds', 0)}s")
    print("Cache Path                : data/raw/synthetic_complaints_cache.json")

    # Category distribution
    cat_counts: dict[str, int] = dict.fromkeys(CATEGORIES, 0)
    for c in complaints:
        cat = c.get("category", "unknown")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    print("\nCategory Distribution:")
    print("-" * 45)
    for cat in CATEGORIES:
        cnt = cat_counts.get(cat, 0)
        bar = "█" * cnt
        print(f"  {cat:<22} : {cnt:>3}  {bar}")

    # Style distribution
    style_counts: dict[str, int] = {}
    for c in complaints:
        sty = c.get("style", "unknown")
        style_counts[sty] = style_counts.get(sty, 0) + 1

    print("\nStyle Distribution:")
    print("-" * 45)
    for sty in STYLES:
        cnt = style_counts.get(sty, 0)
        print(f"  {sty:<22} : {cnt:>3}")

    # Auto-correction stats
    corrected = [c for c in complaints if c.get("_autocorrected")]
    if corrected:
        print(f"\n⚠  Auto-corrections applied: {len(corrected)}")
        for c in corrected[:5]:
            print(
                f"   ID #{c.get('id')}: {c.get('_autocorrected')} → text: \"{c.get('text', '')[:60]}\""
            )

    # Random samples
    print("\n" + "=" * 70)
    print(f"RANDOM SAMPLE OF {num_samples} COMPLAINTS FOR QUALITY REVIEW")
    print("=" * 70)
    sample_items = random.sample(complaints, min(num_samples, len(complaints)))
    for idx, c in enumerate(sample_items, 1):
        autocorrect_note = (
            f" ← AUTO-CORRECTED: {c['_autocorrected']}" if c.get("_autocorrected") else ""
        )
        print(f"\n[Sample {idx}/{num_samples}]  ID #{c.get('id')}{autocorrect_note}")
        print(f"  Category  : {c.get('category')}")
        print(f"  Style     : {c.get('style')}")
        print(
            f"  Location  : {c.get('location_label')} ({c.get('latitude')}, {c.get('longitude')})"
        )
        print(f"  Urgency   : {c.get('urgency')}")
        print(f"  Text      : \"{c.get('text')}\"")
        print(f"  Summary   : {c.get('clean_summary_en')}")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate synthetic complaints for CivicSignal via Groq API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick 50-complaint test (uses cache if present):
  python ml/data_gen/generate.py --count 50 --batch-size 10 --seed 42 --samples 10

  # Fresh 50-complaint test (ignores cache):
  python ml/data_gen/generate.py --count 50 --batch-size 10 --seed 42 --force-refresh --samples 10

  # Full generation (resumable — safe to Ctrl+C and re-run):
  python ml/data_gen/generate.py --count 4000 --batch-size 25 --seed 42
        """,
    )
    parser.add_argument("--count", type=int, default=50, help="Total complaints to generate")
    parser.add_argument(
        "--batch-size", type=int, default=10, help="Complaints per Groq API request"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--force-refresh", action="store_true", help="Ignore disk cache and regenerate"
    )
    parser.add_argument("--samples", type=int, default=10, help="Random samples to print for QA")
    parser.add_argument(
        "--cache-path",
        type=str,
        default="data/raw/synthetic_complaints_cache.json",
        help="Path to cache file (default: data/raw/synthetic_complaints_cache.json)",
    )
    args = parser.parse_args()

    data = generate_synthetic_complaints(
        target_count=args.count,
        batch_size=args.batch_size,
        seed=args.seed,
        cache_path=args.cache_path,
        force_refresh=args.force_refresh,
    )
    print_summary_and_samples(data, num_samples=args.samples)
