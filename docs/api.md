# REST API

Base path: `/api`. All responses are JSON. Authentication is an httpOnly session cookie set by
`POST /api/auth/login` (an `Authorization: Bearer` header is also accepted, for the interactive
docs at `/docs` in development).

Errors always have the same shape:

```json
{ "error": { "code": "UNAUTHORIZED", "message": "not logged in or token expired" } }
```

Validation errors (422) list the invalid fields but never echo the submitted values.

## Endpoints

| Method | Path | Who | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | anyone | Create a student account (rate limited: 10 per IP per hour) |
| `POST` | `/auth/login` | anyone | Form fields `username` (email), `password`, optional `remember`; sets the session cookie (rate limited per email and per IP) |
| `POST` | `/auth/logout` | anyone | Clears the session cookie |
| `GET` | `/auth/me` | logged in | The current user (email, role) |
| `POST` | `/complaints` | logged in | Submit a complaint: `text`, optional `location`, `urgency` (`low`/`medium`/`high`); returns the AI category, confidence and `needs_review` |
| `GET` | `/complaints` | logged in | List complaints - students get only their own; filters `category`, `status`, `needs_review`, paging `limit` (max 200) / `offset` |
| `GET` | `/complaints/{id}` | logged in | One complaint; another student's complaint returns 404 (does not reveal that it exists) |
| `PATCH` | `/complaints/{id}` | supervisor | Correct the `category` and/or change the `status` (only allowed transitions) |
| `POST` | `/classify` | anyone | Classify a text without saving it: category, confidence, top 3, `needs_review` |
| `POST` | `/similar` | supervisor | Most similar stored complaints for a text (`k` 1-20, `min_score` 0-1) |
| `GET` | `/insights/groups` | supervisor | Repeated-problem groups with AI summaries (503 until summaries are imported) |
| `GET` | `/health` (no `/api`) | anyone | Liveness check |

## Status workflow

Main path: `Submitted -> Under Review -> Assigned -> In Progress -> Resolved -> Closed`.
Allowed moves (enforced in `backend/app/services/workflow.py`):

| From | To |
| :--- | :--- |
| Submitted | Under Review, Assigned, Needs More Information, Closed |
| Under Review | Assigned, Needs More Information, Closed |
| Needs More Information | Under Review, Closed |
| Assigned | In Progress, Closed |
| In Progress | Resolved, Assigned |
| Resolved | Closed, In Progress |
| Closed | - (final) |

## Categories

`water_plumbing`, `electrical`, `cleanliness`, `internet_wifi`, `furniture`, `mess_food`,
`security`, `other`.
