from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from models import user as user_model
from models import exercise as exercise_model
from schemas import exercise as exercise_schema
from core.tutor_service import TutorService
from routers.auth import get_current_user

router = APIRouter(
    prefix="/exercises",
    tags=["exercises"]
)

@router.post("/", response_model=exercise_schema.ExerciseResponse)
def create_exercise(
    request: exercise_schema.CreateExerciseRequest,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """
    Creates a new exercise from user input and gets the first AI hint.
    """
    # 1. Create the Exercise
    db_exercise = exercise_model.Exercise(
        user_id=current_user.id,
        content=request.content
    )
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)

    # 2. Get initial guidance from LLM
    try:
        guidance = TutorService.get_initial_guidance(request.content)
    except Exception as e:
        # If LLM fails, still return the exercise
        raise HTTPException(status_code=500, detail=f"Failed to get AI guidance: {str(e)}")

    # 3. Save the first interaction
    first_interaction = exercise_model.Interaction(
        exercise_id=db_exercise.id,
        ai_response=guidance
    )
    db.add(first_interaction)
    db.commit()
    db.refresh(db_exercise) # Refresh to get the new interaction

    return db_exercise

@router.post("/{exercise_id}/answer", response_model=exercise_schema.CheckAnswerResponse)
def submit_answer(
    exercise_id: int,
    request: exercise_schema.SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """
    Submits a user's answer to an exercise, checks it, 
    and returns a new hint or a similar exercise.
    """
    # 1. Get exercise and validate ownership
    db_exercise = db.query(exercise_model.Exercise).filter(
        exercise_model.Exercise.id == exercise_id
    ).first()

    if not db_exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    if db_exercise.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this exercise")
    
    if db_exercise.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This exercise is already completed")

    # 2. Check answer with LLM
    try:
        check_result = TutorService.check_user_answer(
            db_exercise.content,
            request.answer
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check answer: {str(e)}")

    # 3. Save this interaction
    new_interaction = exercise_model.Interaction(
        exercise_id=db_exercise.id,
        user_answer=request.answer,
        ai_response=check_result.explanation,
        is_correct=check_result.is_correct
    )

    # 4. If correct, update exercise and get a similar one
    similar_exercise_content = None
    if check_result.is_correct:
        db_exercise.status = "completed"
        try:
            similar_exercise = TutorService.get_similar_exercise(db_exercise.content)
            similar_exercise_content = similar_exercise.content
            new_interaction.suggested_exercise = similar_exercise_content
        except Exception as e:
            # This is not a critical error, so we just log it
            print(f"Failed to generate similar exercise: {e}")

    db.add(new_interaction)
    db.commit()

    return exercise_schema.CheckAnswerResponse(
        is_correct=check_result.is_correct,
        explanation=check_result.explanation,
        suggested_exercise=similar_exercise_content
    )