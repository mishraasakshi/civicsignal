import collections
import csv
import re
import sys

SRC, OUT = sys.argv[1], sys.argv[2]

STUDENT_MAP = {
    "Water / Plumbing": "water_plumbing",
    "Electrical (fan, light, AC, geyser)": "electrical",
    "Cleanliness": "cleanliness",
    "Internet / WiFi": "internet_wifi",
    "Furniture": "furniture",
    "Mess / Food": "mess_food",
    "Security": "security",
    "Other": "other",
}
URGENCY = {"Low": "low", "Medium": "medium", "High": "high"}

DROP_NAMES = {12, 32, 33, 36, 105}  # name real people / insults
DROP_JUNK = {1, 98, 100, 102}  # not a campus complaint
DROP_DUP = {49}  # exact duplicate of 48

# one response every ~20-30 s in the same polished style, 12:58-1:17 am on 14 Nov
SUSPECTED_PASTED = {
    2,
    5,
    7,
    8,
    9,
    10,
    11,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    29,
    30,
    34,
    35,
    37,
    38,
    40,
    41,
    43,
    44,
    45,
    46,
    47,
    48,
    50,
    51,
    52,
    53,
}

OUR = {
    2: "internet_wifi",
    3: "internet_wifi",
    4: "mess_food",
    5: "water_plumbing",
    6: "mess_food",
    7: "electrical",
    8: "cleanliness",
    9: "mess_food",
    10: "electrical",
    11: "electrical",
    13: "internet_wifi",
    14: "mess_food",
    15: "water_plumbing",
    16: "electrical",
    17: "furniture",
    18: "cleanliness",
    19: "internet_wifi",
    20: "electrical",
    21: "mess_food",
    22: "electrical",
    23: "furniture",
    24: "electrical",
    25: "cleanliness",
    26: "internet_wifi",
    27: "water_plumbing",
    28: "mess_food",
    29: "mess_food",
    30: "electrical",
    31: "internet_wifi",
    34: "cleanliness",
    35: "furniture",
    37: "water_plumbing",
    38: "internet_wifi",
    39: "cleanliness",
    40: "electrical",
    41: "mess_food",
    42: "water_plumbing",
    43: "mess_food",
    44: "furniture",
    45: "water_plumbing",
    46: "water_plumbing",
    47: "water_plumbing",
    48: "electrical",
    50: "cleanliness",
    51: "mess_food",
    52: "internet_wifi",
    53: "water_plumbing",
    54: "electrical",
    55: "cleanliness",
    56: "electrical",
    57: "furniture",
    58: "other",
    59: "electrical",
    60: "electrical",
    61: "other",
    62: "mess_food",
    63: "other",
    64: "security",
    65: "other",
    66: "mess_food",
    67: "mess_food",
    68: "mess_food",
    69: "mess_food",
    70: "mess_food",
    71: "mess_food",
    72: "electrical",
    73: "mess_food",
    74: "other",
    75: "mess_food",
    76: "other",
    77: "mess_food",
    78: "cleanliness",
    79: "furniture",
    80: "water_plumbing",
    81: "security",
    82: "furniture",
    83: "mess_food",
    84: "security",
    85: "electrical",
    86: "cleanliness",
    87: "other",
    88: "internet_wifi",
    89: "electrical",
    90: "furniture",
    91: "other",
    92: "security",
    93: "other",
    94: "cleanliness",
    95: "mess_food",
    96: "other",
    97: "internet_wifi",
    99: "other",
    101: "cleanliness",
    103: "other",
    104: "mess_food",
    106: "electrical",
    107: "cleanliness",
    108: "mess_food",
}

NOTES = {
    3: "vague: only names the category",
    10: "rule says water cooler = electrical; students think water",
    22: "rule says water cooler = electrical; students think water",
    27: "flush = plumber (rule)",
    39: "washroom not cleaned = housekeeping",
    41: "ambiguous: plate washing is done by mess staff",
    56: "broken fan = electrician, even though it is a safety risk",
    58: "warden behaviour = other",
    62: "vague",
    64: "ambiguous: face-ID gate could be security or IT",
    69: "vague",
    70: "two problems (mess + wifi)",
    73: "student picked wifi by mistake",
    74: "lift: not covered by any team in our rules",
    75: "location field held a second complaint (library hours) - removed",
    77: "several problems (hygiene, mess, wifi)",
    78: "plates left on tables = housekeeping (rule)",
    80: "blocked drains = plumber (rule)",
    88: "LMS/portal = IT (rule)",
    91: "lift: not covered by any team in our rules",
    94: "ambiguous: hostel sink hygiene",
    99: "warden behaviour = other",
    101: "ambiguous: lizard in water cooler = hygiene",
    108: "vague: mess policy",
}
NEEDS_REVIEW = {3, 10, 22, 41, 64, 70, 74, 77, 91, 94, 101}

ROOM_RE = re.compile(r"\b(room\s*(no\.?)?\s*)?\d{3}\s*-?\s*[a-z]?\b", re.I)


def clean_location(loc: str) -> str:
    loc = " ".join(loc.split())
    loc = re.sub(r",?\s*room\s*\d+\w*", "", loc, flags=re.I)
    loc = ROOM_RE.sub("", loc).strip(" ,-")
    return loc


def clean_text(text: str) -> str:
    text = re.sub(r"room\s*no\.?\s*\d+\s*-?\s*[a-z]?\b\.?", "", text, flags=re.I)
    text = re.sub(r"^\s*>\s*", "", text, flags=re.M)  # quote markers
    return " ".join(text.split())


rows = list(csv.reader(open(SRC, encoding="utf-8")))[1:]
out, dropped = [], collections.Counter()
for i, r in enumerate(rows, 1):
    if i in DROP_NAMES:
        dropped["names a real person"] += 1
        continue
    if i in DROP_JUNK:
        dropped["not a complaint"] += 1
        continue
    if i in DROP_DUP:
        dropped["exact duplicate"] += 1
        continue
    student = STUDENT_MAP[r[2]]
    ours = OUR[i]
    loc = "" if i == 75 else clean_location(r[3])
    out.append(
        {
            "id": f"real_{i:03d}",
            "submitted_at": r[0].replace(" GMT+5:30", ""),
            "text": clean_text(r[1]),
            "student_label": student,
            "our_label": ours,
            "labels_agree": "yes" if student == ours else "no",
            "needs_review": "yes" if i in NEEDS_REVIEW else "",
            "source": "suspected_pasted" if i in SUSPECTED_PASTED else "real",
            "location": loc,
            "urgency": URGENCY[r[4].split()[0]],
            "note": NOTES.get(i, ""),
        }
    )

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

print(f"Input responses : {len(rows)}")
for k, v in dropped.items():
    print(f"  removed ({k}): {v}")
print(f"Kept            : {len(out)}")
print("By source       :", dict(collections.Counter(o["source"] for o in out)))
real = [o for o in out if o["source"] == "real"]
print("Real by label   :", dict(collections.Counter(o["our_label"] for o in real).most_common()))
agree = sum(o["labels_agree"] == "yes" for o in out)
print(f"Student vs rule agreement: {agree}/{len(out)} = {agree/len(out):.0%}")
print("Needs review    :", sum(o["needs_review"] == "yes" for o in out))
