"""POST /api/classify - suggest which team should handle a complaint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.ml.classifier import ComplaintClassifier, get_classifier
from app.schemas.classify import CategoryScore, ClassifyRequest, ClassifyResponse

router = APIRouter(tags=["Classification"])


def classifier_dependency() -> ComplaintClassifier:
    try:
        return get_classifier()
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e


@router.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest, clf: ComplaintClassifier = Depends(classifier_dependency)):
    p = clf.predict(req.text)
    return ClassifyResponse(
        category=p.category,
        confidence=p.confidence,
        needs_review=p.needs_review,
        top3=[CategoryScore(category=c, probability=s) for c, s in p.top3],
        model=clf.model_name,
    )
