"""Phase 4: turn each complaint group into a short admin-ready summary with Groq (via LangChain).

Run from the project root (after cluster_complaints.py):
    backend/venv/bin/python ml/models/summarize_groups.py --dry-run   # show prompts, no API call
    backend/venv/bin/python ml/models/summarize_groups.py             # call Groq

What it does:
1. Reads the groups made by cluster_complaints.py (data/processed/real_clusters_v1.csv)
2. For each group, sends ONLY the anonymised complaint texts to the LLM
3. Asks for a strict JSON answer: title, summary, category, urgency, suggested action
4. Checks the answer with Pydantic (wrong shape -> one retry, then marked as failed)
5. Caches answers, so re-running costs no extra Groq requests
6. Saves the summaries to data/processed/ (git-ignored) and prints them
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

CATEGORIES = Literal["water_plumbing", "electrical", "cleanliness", "internet_wifi",
                     "furniture", "mess_food", "security", "other"]


class GroupSummary(BaseModel):
    title: str = Field(max_length=80, description="max 10 words, English")
    summary: str = Field(max_length=400, description="1-2 sentences, English")
    category: CATEGORIES
    urgency: Literal["low", "medium", "high"]
    suggested_action: str = Field(max_length=300, description="one concrete next step for the admin")


SYSTEM_PROMPT = """You help a university facilities office read student complaints.
You get several complaints that were grouped together because they look similar.
They may be in English, Hindi or Hinglish (Hindi written in English letters).

Reply with ONE JSON object and nothing else, with exactly these keys:
  "title": what the shared problem is, max 10 words, in English
  "summary": 1-2 sentences in English: what students report and how many
  "category": one of water_plumbing, electrical, cleanliness, internet_wifi, furniture, mess_food, security, other
  "urgency": one of low, medium, high (high = safety risk or many students blocked)
  "suggested_action": one concrete next step for the responsible team

Rules:
- Use only what the complaints say. Do not invent places, numbers or names.
- If the complaints are about different things, say so in the summary.
- Never include personal details."""

USER_TEMPLATE = "Number of complaints: {n}\n\nComplaints:\n{complaints}"


def build_messages(texts: list[str]) -> list[tuple[str, str]]:
    lines = "\n".join(f"{i}. {t}" for i, t in enumerate(texts, 1))
    return [("system", SYSTEM_PROMPT), ("human", USER_TEMPLATE.format(n=len(texts), complaints=lines))]


def parse_reply(content: str) -> GroupSummary:
    """Pull the JSON object out of the reply and validate it."""
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in reply")
    return GroupSummary.model_validate_json(content[start:end + 1])


def make_llm(model_name: str):
    from langchain_groq import ChatGroq

    return ChatGroq(model=model_name, temperature=0, max_retries=2)


def summarise(llm, texts: list[str]) -> GroupSummary:
    messages = build_messages(texts)
    last_error = None
    for attempt in range(2):  # one retry if the answer has the wrong shape
        reply = llm.invoke(messages)
        try:
            return parse_reply(str(reply.content))
        except (ValueError, ValidationError) as e:
            last_error = e
            messages = messages + [("ai", str(reply.content)),
                                   ("human", "That was not valid. Reply with only the JSON object.")]
    raise RuntimeError(f"invalid answer twice: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", default="data/processed/real_clusters_v1.csv")
    parser.add_argument("--out", default="data/processed/real_group_summaries_v1.json")
    parser.add_argument("--cache", default="data/processed/group_summary_cache.json")
    parser.add_argument("--model-name", default=None, help="default: GROQ_MODEL_NAME from .env")
    parser.add_argument("--max-per-group", type=int, default=15, help="send at most this many texts per group")
    parser.add_argument("--dry-run", action="store_true", help="print the prompts, do not call Groq")
    args = parser.parse_args()

    df = pd.read_csv(args.groups).fillna("")
    groups = df[df["group"] != -1].groupby("group")
    print(f"Loaded {len(df)} complaints, {groups.ngroups} groups from {args.groups}")

    if args.dry_run:
        g, members = next(iter(groups))
        print(f"\n--- DRY RUN: prompt for group {g} (nothing sent) ---")
        for role, text in build_messages(members["text"].tolist()[: args.max_per_group]):
            print(f"[{role}]\n{text}\n")
        print(f"Would make {groups.ngroups} Groq requests (fewer if cached).")
        return

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from dotenv import load_dotenv

    load_dotenv()
    if not os.getenv("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY is missing in .env")
    model_name = args.model_name or os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b")
    print(f"LLM: {model_name} (Groq)\n")

    cache_path = Path(args.cache)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    llm = None
    results, n_calls, n_failed = [], 0, 0

    for g, members in sorted(groups, key=lambda kv: -len(kv[1])):
        texts = members["text"].tolist()[: args.max_per_group]
        key = hashlib.sha1((model_name + "\n" + SYSTEM_PROMPT + "\n".join(texts)).encode()).hexdigest()[:16]

        if key in cache:
            s = GroupSummary(**cache[key])
        else:
            llm = llm or make_llm(model_name)
            try:
                s = summarise(llm, texts)
                n_calls += 1
            except Exception as e:  # keep going; report at the end
                n_failed += 1
                print(f"Group {g}: FAILED ({type(e).__name__}: {str(e)[:120]})\n")
                continue
            cache[key] = s.model_dump()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
            time.sleep(1)  # be gentle with the free tier

        main_label = members["our_label"].mode().iloc[0]
        results.append({
            "group": int(g),
            "size": int(len(members)),
            "genuine": int((members["source"] == "real").sum()),
            "cluster_main_label": main_label,
            "ids": members["id"].tolist(),
            **s.model_dump(),
        })
        flag = "" if s.category == main_label else f"  (LLM says {s.category}, labels say {main_label})"
        print(f"Group {g}  [{len(members)} complaints, {results[-1]['genuine']} genuine]  "
              f"{s.urgency.upper()}  {s.category}{flag}")
        print(f"  Title  : {s.title}")
        print(f"  Summary: {s.summary}")
        print(f"  Action : {s.suggested_action}\n")

    Path(args.out).write_text(json.dumps(results, indent=2, ensure_ascii=False))
    agree = sum(r["category"] == r["cluster_main_label"] for r in results)
    print("=" * 70)
    print(f"Summarised {len(results)} groups | Groq calls this run: {n_calls} | failed: {n_failed}")
    if results:
        print(f"LLM category agrees with the group's main label: {agree}/{len(results)}")
    print(f"Saved -> {args.out}  (git-ignored)")


if __name__ == "__main__":
    main()
