from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User, Role, UserSession, Student, Tutor, Admin
from app.schemas.auth import (
    Token, UserCreate, UserResponse, UserLogin
)

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.RateLimiter(5, 60))])
def register_user(user_in: UserCreate, db: Session = Depends(deps.get_db)) -> Any:
    """Register a new student user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered",
        )
    
    # Verify target roles are valid profiles (restricted to student/tutor)
    for role_name in user_in.role_names:
        if role_name not in ["student", "tutor"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration role '{role_name}' is not permitted"
            )

    # Hash the password
    hashed_pwd = security.get_password_hash(user_in.password)
    
    # Create the user base
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_active=True
    )
    
    # Assign Roles
    for role_name in user_in.role_names:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            # Auto-provision role if missing in base schema
            role = Role(name=role_name, description=f"Default {role_name} permissions")
            db.add(role)
            db.flush()
        new_user.roles.append(role)
        
    db.add(new_user)
    db.flush() # Generate ID for 1-to-1 profiles
    
    # Create specific profile records
    if "student" in user_in.role_names:
        student_profile = Student(user_id=new_user.id)
        db.add(student_profile)
    if "tutor" in user_in.role_names:
        tutor_profile = Tutor(user_id=new_user.id, max_workload=5, is_available=True)
        db.add(tutor_profile)
        
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token, dependencies=[Depends(deps.RateLimiter(10, 60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Standard OAuth2 compatible token login."""
    # Find user
    user = db.query(User).filter(User.email == form_data.username, User.deleted_at.is_(None)).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )
        
    # Get user role names
    roles = [r.name for r in user.roles]
    
    # Generate Tokens
    access_token = security.create_access_token(subject=user.id, roles=roles)
    refresh_token = security.create_refresh_token(subject=user.id)
    
    # Store user session
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        is_revoked=False,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(deps.get_db)) -> Any:
    """Validate refresh token and issue a new access token."""
    payload = security.verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
        
    user_id = payload.get("sub")
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.is_revoked == False,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or revoked"
        )
        
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active"
        )
        
    roles = [r.name for r in user.roles]
    new_access_token = security.create_access_token(subject=user.id, roles=roles)
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(refresh_token: str, db: Session = Depends(deps.get_db)) -> Any:
    """Log out a user by revoking their refresh token."""
    session = db.query(UserSession).filter(UserSession.refresh_token == refresh_token).first()
    if session:
        session.is_revoked = True
        db.commit()
    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve the current logged-in user profile details."""
    return current_user
