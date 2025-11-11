from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base


class RoadmapJob(Base):
    __tablename__ = "roadmap_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, index=True, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    theme = Column(String) # This is the "learning target"
    status = Column(String, default="pending") # pending, processing, completed, failed
    
    # This column will store the final JSON roadmap
    roadmap_data = Column(JSON, nullable=True) 
    
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    user = relationship("User", back_populates="roadmaps")