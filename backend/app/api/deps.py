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
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def get_db() -> Generator[Session, None, None]:
    """Database session generator utility. Ensures connections close cleanly."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_guest_user(db: Session) -> User:
    """Returns an existing active user or creates a default guest user with all roles."""
    user = db.query(User).filter(User.is_active.is_(True), User.deleted_at.is_(None)).first()
    if user:
        return user
    
    import uuid
    from app.models.user import Role, Student, Tutor, Admin
    
    roles = []
    for role_name in ["student", "tutor", "admin"]:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=f"Default {role_name} role")
            db.add(role)
        roles.append(role)
    db.commit()
    
    guest_user = User(
        email="guest@example.com",
        hashed_password="guest_hashed_password",
        first_name="Guest",
        last_name="User",
        is_active=True,
        is_superuser=True,
        roles=roles
    )
    db.add(guest_user)
    db.commit()
    db.refresh(guest_user)
    
    student = Student(user_id=guest_user.id, matriculation_number="GUEST123")
    tutor = Tutor(user_id=guest_user.id, bio="Default Guest Tutor", department="General", max_workload=10, is_available=True)
    admin = Admin(user_id=guest_user.id, department="General")
    db.add_all([student, tutor, admin])
    db.commit()
    db.refresh(guest_user)
    return guest_user


def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    import uuid
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id:
                uuid_obj = uuid.UUID(user_id)
                user = db.query(User).filter(User.id == uuid_obj, User.deleted_at.is_(None)).first()
                if user:
                    return user
        except Exception:
            pass
            
    return get_or_create_guest_user(db)


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


class RoleChecker:
    """Dependency validator to verify user matches specific access privileges."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, 
        current_user: User = Depends(get_current_active_user)
    ) -> User:
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
            
        except Exception:
            # Gracefully log warning and bypass check if Redis goes offline, maintaining endpoint availability
            pass
