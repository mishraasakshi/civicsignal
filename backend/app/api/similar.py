"""POST /api/similar - find past complaints about the same problem."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.ml.similar import DUPLICATE_THRESHOLD, SimilarIndex, get_similar_index
from app.schemas.similar import SimilarMatch, SimilarRequest, SimilarResponse

# Returns other students' complaint text, so only logged-in users may search
router = APIRouter(tags=["Similar complaints"], dependencies=[Depends(get_current_user)])


def index_dependency() -> SimilarIndex:
    try:
        return get_similar_index()
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e


@router.post("/similar", response_model=SimilarResponse)
def similar(req: SimilarRequest, index: SimilarIndex = Depends(index_dependency)):
    matches = index.search(req.text, k=req.k, min_score=req.min_score)
    return SimilarResponse(
        searched=len(index),
        possible_duplicate=bool(matches) and matches[0].score >= DUPLICATE_THRESHOLD,
        matches=[SimilarMatch(**m.__dict__) for m in matches],
    )
