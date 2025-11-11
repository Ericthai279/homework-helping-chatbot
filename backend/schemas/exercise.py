from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# --- Interaction ---
class InteractionBase(BaseModel):
    ai_response: Optional[str] = None
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    suggested_exercise: Optional[str] = None

class InteractionResponse(InteractionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Exercise ---
class CreateExerciseRequest(BaseModel):
    content: str # The text of the exercise

class ExerciseResponse(BaseModel):
    id: int
    content: str
    status: str
    created_at: datetime
    # Returns the first interaction (the initial guidance)
    interactions: List[InteractionResponse] = [] 

    class Config:
        from_attributes = True

# --- Answering ---
class SubmitAnswerRequest(BaseModel):
    answer: str # The user's answer

class CheckAnswerResponse(BaseModel):
    is_correct: bool
    explanation: str # The AI's reasoning
    suggested_exercise: Optional[str] = None # A new exercise if they were right