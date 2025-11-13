from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel

class RoadmapJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    theme: str # The learning target
    
    roadmap_data: Optional[Any] = None 
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True

class CreateRoadmapRequest(BaseModel):
    learning_target: str