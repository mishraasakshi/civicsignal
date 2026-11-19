"""Who is calling? Reusable checks for protected endpoints."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# tokenUrl makes the "Authorize" button in /docs work
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user_id = decode_access_token(token)
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
