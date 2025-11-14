from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import base64

from db.database import get_db
# FIX: Import models directly from their files, not through the __init__.py
from models.user import User as UserModel
from models.exercise import Exercise as ExerciseModel
from models.exercise import Interaction as InteractionModel 
from schemas import exercise as exercise_schema
from core.tutor_service import TutorService
from routers.auth import get_current_user

router = APIRouter(
    prefix="/exercises",
    tags=["exercises"]
)

@router.post("/", response_model=exercise_schema.ExerciseResponse)
async def create_exercise(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new exercise (from text and/or base64 image).
    Returns the first hint.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    prompt = data.get("prompt", "")
    base64_image = data.get("base64_image")

    if not prompt and not base64_image:
        raise HTTPException(status_code=400, detail="Must provide either text or an image")

    try:
        # 1. Call AI to get the first hint
        initial_guidance = await TutorService.get_initial_guidance(
            prompt=prompt,
            base64_image=base64_image
        )

        # 2. Create the exercise in the DB
        exercise_content = prompt
        
        if not prompt and base64_image:
            try:
                # Use the OCR output from the guidance as the exercise content
                exercise_content = initial_guidance.split('\n')[0]
            except:
                exercise_content = "Exercise from image"
        
        db_exercise = ExerciseModel(
            user_id=current_user.id,
            content=exercise_content,
            image_base64=base64_image
        )
        db.add(db_exercise)
        db.commit()

        # 3. Save the first interaction
        first_interaction = InteractionModel(
            exercise_id=db_exercise.id,
            ai_response=initial_guidance
        )
        db.add(first_interaction)
        db.commit()
        db.refresh(db_exercise)

        return db_exercise

    except Exception as e:
        print(f"Error creating exercise: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing: {str(e)}")


@router.post("/{exercise_id}/answer")
async def submit_answer(
    exercise_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Submit an answer for an in-progress exercise.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    user_answer = data.get("answer")
    if not user_answer:
        raise HTTPException(status_code=422, detail="Missing 'answer' field")

    db_exercise = db.query(ExerciseModel).filter(
        ExerciseModel.id == exercise_id,
        ExerciseModel.user_id == current_user.id
    ).first()

    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    if db_exercise.status == "completed":
        raise HTTPException(status_code=400, detail="Exercise is already completed")

    try:
        # 1. Call AI to check the answer (returns a Pydantic object: CheckAnswerLLM)
        check_response_obj = await TutorService.check_user_answer(
            exercise_content=db_exercise.content,
            user_answer=user_answer
        )
        
        # FIX: Get data directly from the object's structured fields
        is_correct = check_response_obj.is_correct
        check_response_text = check_response_obj.explanation # The text explanation
        
        # 2. Save the user's answer and the AI's check
        db_interaction = InteractionModel(
            exercise_id=db_exercise.id,
            user_answer=user_answer,
            ai_response=check_response_text, # FIX: Store the text explanation
            is_correct=is_correct
        )
        db.add(db_interaction)

        suggested_exercise_text = None
        if is_correct:
            db_exercise.status = "completed"
            
            # 3. If correct, get a similar exercise (returns a Pydantic object: SimilarExerciseLLM)
            suggested_exercise_obj = await TutorService.get_similar_exercise(
                exercise_content=db_exercise.content
            )
            suggested_exercise_text = suggested_exercise_obj.content # FIX: Access the content field
            
            # 4. Save the suggestion as a new interaction
            suggestion_interaction = InteractionModel(
                exercise_id=db_exercise.id,
                suggested_exercise=suggested_exercise_text
            )
            db.add(suggestion_interaction)
        
        db.commit()

        return {
            "check_response": check_response_text,
            "is_correct": is_correct,
            "suggested_exercise": suggested_exercise_text
        }

    except Exception as e:
        print(f"Error processing: {e}")
        # Re-raise the exception as an HTTP 500 error for the client
        raise HTTPException(status_code=500, detail=f"Error processing: {str(e)}")