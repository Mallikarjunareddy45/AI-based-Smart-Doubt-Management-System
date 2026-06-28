from typing import Generator, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import redis

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import SessionLocal
from app.models.user import User

# OAuth2 context configuration matching login route endpoint
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_db() -> Generator[Session, None, None]:
    """Database session generator utility. Ensures connections close cleanly."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    import uuid
    try:
        uuid_obj = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception
        
    user = db.query(User).filter(User.id == uuid_obj, User.deleted_at.is_(None)).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user profile"
        )
    return current_user


class RoleChecker:
    """Dependency validator to verify user matches specific access privileges."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, 
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        user_roles = [r.name for r in current_user.roles]
        
        # Superuser bypasses role checks
        if current_user.is_superuser:
            return current_user
            
        # Check if user roles overlap with allowed roles
        if not any(role in self.allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return current_user


class RateLimiter:
    """Redis-backed rate limiter for protecting endpoints from abuse/DDoS."""
    def __init__(self, requests_limit: int, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    def __call__(self, request: Request) -> None:
        import os
        if os.environ.get("TESTING") == "True":
            return
            
        try:
            # Connect to Redis broker
            r = redis.from_url(settings.REDIS_URL)
            client_ip = request.client.host if request.client else "unknown_ip"
            key = f"rate_limit:{client_ip}:{request.url.path}"
            
            current_requests = r.get(key)
            if current_requests and int(current_requests) >= self.requests_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
            
            # Atomic increment and expire settings
            pipe = r.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window_seconds)
            pipe.execute()
            
        except redis.RedisError:
            # Gracefully log warning and bypass check if Redis goes offline, maintaining endpoint availability
            pass
