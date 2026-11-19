"""Serve the built website (frontend/dist) from FastAPI.

- /api/... and /health stay API routes (registered before this).
- Real files (JS, CSS, icons) are served as they are; hashed /assets files are cached for a year.
- Every other path returns index.html, so the React app handles it.
- Paths can never escape the dist folder.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

NO_CACHE = {"Cache-Control": "no-cache"}
LONG_CACHE = {"Cache-Control": "public, max-age=31536000, immutable"}


def mount_frontend(app: FastAPI, dist_dir: str) -> None:
    dist = Path(dist_dir).resolve()
    index = dist / "index.html"
    if not index.is_file():
        raise RuntimeError(
            f"FRONTEND_DIST={dist_dir!r} has no index.html - build the frontend first"
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    def website(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(
                404, detail="not found"
            )  # unknown API path: JSON 404, not the website
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(dist):
            headers = LONG_CACHE if full_path.startswith("assets/") else NO_CACHE
            return FileResponse(candidate, headers=headers)
        return FileResponse(index, headers=NO_CACHE)
