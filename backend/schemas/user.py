from typing import Optional, List
from pydantic import BaseModel, EmailStr

# --- User ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_premium: bool

    class Config:
        from_attributes = True

# --- User Profile (for premium users) ---
class UserProfile(BaseModel):
    profile_year: Optional[str] = None
    profile_skill_level: Optional[str] = None
    profile_common_mistakes: Optional[List[str]] = None

    class Config:
        from_attributes = True