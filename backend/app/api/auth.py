"""Sign up (students only), log in, and who-am-I.

Supervisors cannot sign up here - create them with backend/scripts/create_supervisor.py.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterIn, Token, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email already registered")
    user = User(email=body.email, hashed_password=hash_password(body.password), role="reporter")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Log in with email (in the 'username' field) and password; returns a token."""
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    ok = verify_password(form.password, user.hashed_password if user else DUMMY_HASH)
    if user is None or not ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="wrong email or password",  # same message either way: don't reveal which
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id, user.role))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
