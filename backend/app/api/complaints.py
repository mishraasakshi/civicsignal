"""Submit complaints and list them.

POST /api/complaints        - any logged-in user: classify with the AI and save
GET  /api/complaints        - supervisors: all; students: only their own
GET  /api/complaints/{id}   - supervisors: any; students: only their own
PATCH /api/complaints/{id}  - supervisors only: correct category and/or move status

The reporter's identity is stored but never returned, so students can complain without fear.
"""

from app.api.classify import classifier_dependency
from app.api.deps import get_current_user, require_supervisor
from app.db.session import get_db
from app.ml.classifier import ComplaintClassifier
from app.models.complaint import Complaint
from app.models.user import User
from app.schemas.complaint import (
    Category,
    ComplaintCreate,
    ComplaintList,
    ComplaintOut,
    ComplaintUpdate,
    Status,
)
from app.services.workflow import ALLOWED, can_move
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
def create_complaint(
    body: ComplaintCreate,
    db: Session = Depends(get_db),
    clf: ComplaintClassifier = Depends(classifier_dependency),
    user: User = Depends(get_current_user),
):
    vector = clf.encode([body.text])[0]  # the text's meaning, computed once
    p = clf.predict_vector(vector)
    complaint = Complaint(
        text=body.text,
        location=body.location,
        urgency_reported=body.urgency,
        predicted_category=p.category,
        confidence=p.confidence,
        needs_review=p.needs_review,
        category=p.category,  # starts as the AI's guess; a supervisor can change it later
        reporter_id=user.id,
        embedding=vector.astype("float32").tobytes(),  # kept for "similar complaints"
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
    user: User = Depends(get_current_user),
):
    query = select(Complaint)
    if user.role != "supervisor":
        query = query.where(Complaint.reporter_id == user.id)  # students see only their own
    if category is not None:
        query = query.where(Complaint.category == category)
    if status_ is not None:
        query = query.where(Complaint.status == status_)
    if needs_review is not None:
        query = query.where(Complaint.needs_review == needs_review)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(
        query.order_by(Complaint.created_at.desc(), Complaint.id.desc()).limit(limit).offset(offset)
    ).all()
    return ComplaintList(total=total or 0, items=rows)


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(
    complaint_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    complaint = db.get(Complaint, complaint_id)
    # someone else's complaint looks "not found" to a student (does not reveal that it exists)
    if complaint is None or (user.role != "supervisor" and complaint.reporter_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"complaint {complaint_id} not found")
    return complaint


@router.patch("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(
    complaint_id: int,
    body: ComplaintUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_supervisor),
):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"complaint {complaint_id} not found")

    if body.status is not None and not can_move(complaint.status, body.status):
        allowed = ", ".join(sorted(ALLOWED[complaint.status])) or "none (final)"
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"cannot move from '{complaint.status}' to '{body.status}'. Allowed: {allowed}",
        )

    if body.category is not None:
        complaint.category = (
            body.category
        )  # predicted_category is kept, so we can measure the AI later
        complaint.needs_review = False  # a human has looked at it
    if body.status is not None:
        complaint.status = body.status

    db.commit()
    db.refresh(complaint)
    return complaint
