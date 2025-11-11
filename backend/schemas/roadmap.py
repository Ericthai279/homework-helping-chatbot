from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Json

# This schema is no longer used for a request, 
# as the "theme" (learning target) will be part of the
# roadmap creation endpoint.

class RoadmapJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    theme: str # The learning target
    
    # The roadmap_data will be returned by a different endpoint
    # once the job is "completed"
    roadmap_data: Optional[Any] = None 
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True # Replaced orm_mode

class CreateRoadmapRequest(BaseModel):
    learning_target: str