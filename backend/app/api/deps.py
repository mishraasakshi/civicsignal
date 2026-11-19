"""Who is calling? Reusable checks for protected endpoints."""

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# tokenUrl makes the "Authorize" button in /docs work
# auto_error=False: if there is no Authorization header we still check the session cookie
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    request: Request, token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    # Browsers send the httpOnly session cookie; API clients and /docs send "Authorization: Bearer ..."
    token = token or request.cookies.get(settings.SESSION_COOKIE_NAME)
    user_id = decode_access_token(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="not logged in or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_supervisor(user: User = Depends(get_current_user)) -> User:
    if user.role != "supervisor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="supervisors only")
    return user
