"""POST /api/similar - find stored complaints about the same problem (supervisors only).

The results contain other students' complaint text, so only supervisors may search.
"""

from app.api.classify import classifier_dependency
from app.api.deps import require_supervisor
from app.db.session import get_db
from app.ml.classifier import ComplaintClassifier
from app.ml.similar import DUPLICATE_THRESHOLD, search
from app.schemas.similar import SimilarMatch, SimilarRequest, SimilarResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(tags=["Similar complaints"], dependencies=[Depends(require_supervisor)])


@router.post("/similar", response_model=SimilarResponse)
def similar(
    req: SimilarRequest,
    db: Session = Depends(get_db),
    clf: ComplaintClassifier = Depends(classifier_dependency),
):
    matches, searched = search(db, clf.encode, req.text, k=req.k, min_score=req.min_score)
    return SimilarResponse(
        searched=searched,
        possible_duplicate=bool(matches) and matches[0].score >= DUPLICATE_THRESHOLD,
        matches=[SimilarMatch(**m.__dict__) for m in matches],
    )
