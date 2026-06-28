from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[UUID] = None
    roles: List[str] = []

# Base User Schema
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

# Sign Up Request
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role_names: List[str] = ["student"] # Default to student if not specified

# Login Request
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Profile Schema Data
class StudentProfileSchema(BaseModel):
    matriculation_number: Optional[str] = None
    profile_data: Optional[dict] = None

    class Config:
        from_attributes = True

class TutorProfileSchema(BaseModel):
    bio: Optional[str] = None
    department: Optional[str] = None
    max_workload: int = 5
    is_available: bool = True

    class Config:
        from_attributes = True

class AdminProfileSchema(BaseModel):
    department: Optional[str] = None

    class Config:
        from_attributes = True

# Role Schema for User Responses
class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

# User Response
class UserResponse(UserBase):
    id: UUID
    is_active: bool
    roles: List[RoleResponse] = []
    student_profile: Optional[StudentProfileSchema] = None
    tutor_profile: Optional[TutorProfileSchema] = None
    admin_profile: Optional[AdminProfileSchema] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Password Reset Request
class PasswordResetRequest(BaseModel):
    email: EmailStr

# Password Reset Confirm
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
