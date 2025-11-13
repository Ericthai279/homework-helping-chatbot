from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# --- Interaction ---
class InteractionResponse(BaseModel):
    id: int
    ai_response: Optional[str] = None
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    suggested_exercise: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Exercise ---
class ExerciseResponse(BaseModel):
    id: int
    content: str
    status: str
    created_at: datetime
    interactions: List[InteractionResponse] = [] 

    class Config:
        from_attributes = True

# --- Data submitted by user ---
class SubmitAnswerRequest(BaseModel):
    answer: str # The user's answer