from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import date

# --- User ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
    # --- NEW FIELDS ---
    username: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None # Pydantic will auto-convert "YYYY-MM-DD" string
    school: Optional[str] = None
    major: Optional[str] = None
    # --- END NEW FIELDS ---

class User(UserBase):
    id: int
    is_premium: bool
    username: str # <-- Add username to the response
    

    class Config:
        from_attributes = True

# --- User Profile (for premium users) ---
class UserProfile(BaseModel):
    profile_year: Optional[str] = None
    profile_skill_level: Optional[str] = None
    profile_common_mistakes: Optional[List[str]] = None

    class Config:
        from_attributes = True