import pydantic
from typing import List, Optional, Any
from pydantic import BaseModel, Field

class CheckAnswerLLM(BaseModel):
    """
    Pydantic model for the LLM to check a user's answer.
    """
    is_correct: bool = Field(description="Whether the user's answer is correct.")
    explanation: str = Field(description="The reasoning for why the answer is correct or incorrect, in a helpful, tutor-like tone.")

class SimilarExerciseLLM(BaseModel):
    """
    Pydantic model for the LLM to generate a similar exercise.
    """
    content: str = Field(description="The text of a new, similar exercise for the user to practice.")

class RoadmapStepLLM(BaseModel):
    """
    A single step in the generated learning roadmap.
    """
    title: str = Field(description="A concise title for this step or module (e.g., 'Reviewing Basic Algebra').")
    description: str = Field(description="A 1-2 sentence description of what this step covers.")
    topics_to_focus: List[str] = Field(description="A list of key topics or concepts to focus on.")
    common_pitfalls: List[str] = Field(description="What to watch out for, based on the user's common mistakes.")

class RoadmapLLM(BaseModel):
    """
    The complete, personalized learning roadmap.
    """
    title: str = Field(description="A high-level title for the entire learning roadmap (e.g., 'Calculus I Mastery Plan').")
    study_intensity: str = Field(description="A recommendation for study intensity (e.g., 'Moderate: 3-4 hours/week').")
    steps: List[RoadmapStepLLM] = Field(description="A list of the learning steps to follow.")