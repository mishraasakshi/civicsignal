"""Sign up (students only), log in, and who-am-I.

Supervisors cannot sign up here - create them with backend/scripts/create_supervisor.py.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
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
def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    remember: bool = Form(default=False, description="keep me logged in for 30 days"),
    db: Session = Depends(get_db),
):
    """Log in with email (in the 'username' field) and password.

    Sets an httpOnly session cookie for the browser (JavaScript cannot read it) and also
    returns the token in the body for API clients and the /docs Authorize button.
    remember=true -> the cookie lasts REMEMBER_ME_DAYS; otherwise it ends when the browser closes.
    """
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    ok = verify_password(form.password, user.hashed_password if user else DUMMY_HASH)
    if user is None or not ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="wrong email or password",  # same message either way: don't reveal which
            headers={"WWW-Authenticate": "Bearer"},
        )
    lifetime = timedelta(days=settings.REMEMBER_ME_DAYS) if remember else None
    token = create_access_token(user.id, user.role, lifetime)
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        token,
        max_age=int(lifetime.total_seconds()) if lifetime else None,  # None = session cookie
        httponly=True,  # not readable by JavaScript (protects against XSS token theft)
        samesite="lax",  # not sent on cross-site POSTs (CSRF protection)
        secure=settings.ENVIRONMENT != "development",  # HTTPS only outside local development
        path="/",
    )
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """Forget the browser session (clears the httpOnly cookie)."""
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/", httponly=True, samesite="lax")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
