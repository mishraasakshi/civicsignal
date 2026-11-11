# CivicSignal REST API Specifications

All endpoints return JSON responses with standard HTTP status codes.
Consistent error response format:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Complaint #42 does not exist."
  }
}
```

---

## Endpoint Catalog (Section 11)

| # | Method | Path | Allowed Role | Purpose |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `POST` | `/api/auth/login` | Any | Authenticate and obtain JWT token |
| 2 | `POST` | `/api/complaints` | `reporter` | Create a complaint (runs extraction + classification) |
| 3 | `GET` | `/api/complaints` | `reporter`, `supervisor` | List complaints (reporters see only their own; paginated) |
| 4 | `GET` | `/api/complaints/{id}` | `reporter`, `supervisor` | Fetch complaint details and timeline |
| 5 | `GET` | `/api/complaints/{id}/similar` | `supervisor` | Ranked possible duplicate matches with explainable reasons |
| 6 | `PATCH` | `/api/complaints/{id}/status` | `supervisor` | Change status; records an immutable `status_history` event |
| 7 | `POST` | `/api/ai/classify` | `supervisor` | Classify arbitrary text (testing / sandbox) |
| 8 | `POST` | `/api/groups` | `supervisor` | Create an issue group from selected complaints |
| 9 | `PATCH` | `/api/groups/{id}/review` | `supervisor` | Accept or reject suggested group members |
| 10 | `POST` | `/api/groups/{id}/summary` | `supervisor` | Generate or refresh LLM 1-2 sentence group summary |
| 11 | `POST` | `/api/assignments` | `supervisor` | Assign a group or complaint to a person/team |
| 12 | `GET` | `/api/analytics/overview` | `supervisor` | Dashboard aggregates and workload stats |
| 13 | `GET` | `/api/analytics/hotspots` | `supervisor` | Map-ready DBSCAN geospatial clusters |
| 14 | `POST` | `/api/analytics/ask` | `supervisor` | Natural language question &rarr; Read-only SQL query + answer |
