from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False) # The exercise text
    status = Column(String, default="in_progress") # in_progress, completed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="exercises")
    interactions = relationship("Interaction", back_populates="exercise", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    
    # The user's answer for this step
    user_answer = Column(Text, nullable=True)
    
    # The AI's guidance or check
    ai_response = Column(Text, nullable=True)
    
    # Was the user's answer correct for this step?
    is_correct = Column(Boolean, nullable=True)
    
    # A suggested new exercise (if this was the final, correct answer)
    suggested_exercise = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    exercise = relationship("Exercise", back_populates="interactions")