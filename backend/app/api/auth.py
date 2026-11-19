"""Sign up (students only), log in, and who-am-I.

Supervisors cannot sign up here - create them with backend/scripts/create_supervisor.py.
"""

from datetime import timedelta

from app.api.deps import get_current_user
from app.core import rate_limit
from app.core.config import settings
from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterIn, Token, UserOut
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Auth"])


def client_ip(request: Request) -> str:
    """The caller's IP address. (Behind a proxy in production this needs the proxy's forwarded
    address instead - to be configured at deployment.)"""
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    wait = rate_limit.signups_per_ip.check_and_hit(client_ip(request))
    if wait:
        raise rate_limit.too_many(wait, "sign-ups from this network")
    if db.scalar(select(User).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email already registered")
    user = User(email=body.email, hashed_password=hash_password(body.password), role="reporter")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
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
    email = form.username.strip().lower()

    # 1) one network trying many logins
    wait = rate_limit.logins_per_ip.check_and_hit(client_ip(request))
    if wait:
        raise rate_limit.too_many(wait, "login attempts from this network")
    # 2) this account had too many wrong passwords recently: locked, even if this password is right
    wait = rate_limit.failed_logins_per_email.retry_after(email)
    if wait:
        raise rate_limit.too_many(wait, "failed login attempts for this account")

    user = db.scalar(select(User).where(User.email == email))
    ok = verify_password(form.password, user.hashed_password if user else DUMMY_HASH)
    if user is None or not ok:
        rate_limit.failed_logins_per_email.hit(email)  # counted for unknown emails too (no hint)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="wrong email or password",  # same message either way: don't reveal which
            headers={"WWW-Authenticate": "Bearer"},
        )
    rate_limit.failed_logins_per_email.reset(email)  # success clears the failure count
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
