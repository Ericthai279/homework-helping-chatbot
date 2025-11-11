from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_premium = Column(Boolean, default=False)

    # Profile data for premium users (the AI uses this)
    profile_year = Column(String, nullable=True) # e.g., "University Year 1"
    profile_skill_level = Column(String, nullable=True) # e.g., "Beginner"
    
    # Stores list of strings like "theory", "calculation"
    profile_common_mistakes = Column(JSON, nullable=True) 

    # Relationships
    exercises = relationship("Exercise", back_populates="user")
    roadmaps = relationship("RoadmapJob", back_populates="user")