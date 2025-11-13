# In models/user.py

from sqlalchemy import Column, Integer, String, Boolean, JSON, Date # <-- Import Date
from sqlalchemy.orm import relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_premium = Column(Boolean, default=False)
    
    # --- NEW FIELDS ---
    # We make username unique, just like email
    username = Column(String, unique=True, index=True, nullable=True) 
    gender = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    school = Column(String, nullable=True)
    major = Column(String, nullable=True)
    # --- END NEW FIELDS ---

    # Profile data for premium users (the AI uses this)
    profile_year = Column(String, nullable=True) # e.g., "University Year 1"
    profile_skill_level = Column(String, nullable=True) # e.g., "Beginner"
    
    # Stores list of strings like "theory", "calculation"
    profile_common_mistakes = Column(JSON, nullable=True) 

    # Relationships
    exercises = relationship("Exercise", back_populates="user")
    roadmaps = relationship("RoadmapJob", back_populates="user")