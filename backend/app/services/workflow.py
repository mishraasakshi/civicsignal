"""Which status changes are allowed.

Submitted -> Under Review / Assigned / Needs More Information / Closed
Under Review -> Assigned / Needs More Information / Closed
Needs More Information -> Under Review / Closed
Assigned -> In Progress / Closed
In Progress -> Resolved / Assigned (hand back)
Resolved -> Closed / In Progress (reopen if the fix did not work)
Closed -> nothing (final)
"""

ALLOWED: dict[str, set[str]] = {
    "Submitted": {"Under Review", "Assigned", "Needs More Information", "Closed"},
    "Under Review": {"Assigned", "Needs More Information", "Closed"},
    "Needs More Information": {"Under Review", "Closed"},
    "Assigned": {"In Progress", "Closed"},
    "In Progress": {"Resolved", "Assigned"},
    "Resolved": {"Closed", "In Progress"},
    "Closed": set(),
}


def can_move(current: str, new: str) -> bool:
    return new == current or new in ALLOWED.get(current, set())
