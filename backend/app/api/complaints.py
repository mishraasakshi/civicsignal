"""Submit complaints and list them.

POST /api/complaints        - classify with the AI and save
GET  /api/complaints        - newest first, with optional filters
GET  /api/complaints/{id}   - one complaint
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.classify import classifier_dependency
from app.db.session import get_db
from app.ml.classifier import ComplaintClassifier
from app.models.complaint import Complaint
from app.schemas.complaint import Category, ComplaintCreate, ComplaintList, ComplaintOut, Status

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
def create_complaint(
    body: ComplaintCreate,
    db: Session = Depends(get_db),
    clf: ComplaintClassifier = Depends(classifier_dependency),
):
    p = clf.predict(body.text)
    complaint = Complaint(
        text=body.text,
        location=body.location,
        urgency_reported=body.urgency,
        predicted_category=p.category,
        confidence=p.confidence,
        needs_review=p.needs_review,
        category=p.category,  # starts as the AI's guess; a supervisor can change it later
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)  # load id, status and timestamps filled in by the database
    return complaint


@router.get("", response_model=ComplaintList)
def list_complaints(
    category: Category | None = None,
    status_: Status | None = Query(default=None, alias="status"),
    needs_review: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Complaint)
    if category is not None:
        query = query.where(Complaint.category == category)
    if status_ is not None:
        query = query.where(Complaint.status == status_)
    if needs_review is not None:
        query = query.where(Complaint.needs_review == needs_review)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Complaint.created_at.desc(), Complaint.id.desc())
                      .limit(limit).offset(offset)).all()
    return ComplaintList(total=total or 0, items=rows)


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"complaint {complaint_id} not found")
    return complaint
