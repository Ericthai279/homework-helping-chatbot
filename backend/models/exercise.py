from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime

# This table stores the original exercise
class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Exercise content (from text or OCR)
    content = Column(Text, nullable=False)
    # Original image (optional) - stored as base64
    image_base64 = Column(Text, nullable=True) 
    
    status = Column(String, default="in_progress") # in_progress, completed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="exercises")
    interactions = relationship("Interaction", back_populates="exercise", cascade="all, delete-orphan")

# This table stores each turn (AI hint, user answer)
class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    
    # AI's message (hint, check)
    ai_response = Column(Text, nullable=True)
    
    # User's answer
    user_answer = Column(Text, nullable=True)
    
    # AI check correct/incorrect
    is_correct = Column(Boolean, nullable=True)
    
    # AI suggested new exercise
    suggested_exercise = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exercise = relationship("Exercise", back_populates="interactions")