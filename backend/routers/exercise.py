from fastapi import APIRouter, Depends, HTTPException, status, Request # <-- Import Request
from sqlalchemy.orm import Session
import base64

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
async def create_exercise(
    # --- THIS IS THE FIX ---
    # We no longer use the Pydantic model for the request.
    # We get the raw Request object.
    request: Request,
    # ---------------------
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """
    Create a new exercise (from text and/or base64 image).
    Returns the first hint.
    """
    # --- MANUALLY PARSE JSON ---
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    prompt = data.get("prompt", "")
    base64_image = data.get("base64_image")
    # -------------------------

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
                exercise_content = initial_guidance.split('\n')[0]
            except:
                exercise_content = "Exercise from image"
        
        db_exercise = exercise_model.Exercise(
            user_id=current_user.id,
            content=exercise_content,
            image_base64=base64_image
        )
        db.add(db_exercise)
        db.commit()

        # 3. Save the first interaction
        first_interaction = exercise_model.Interaction(
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
    # --- THIS IS THE FIX (Part 2) ---
    # We do the same for the answer endpoint.
    request: Request,
    # --------------------------
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """
    Submit an answer for an in-progress exercise.
    """
    # --- MANUALLY PARSE JSON ---
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    user_answer = data.get("answer")
    if not user_answer:
         raise HTTPException(status_code=422, detail="Missing 'answer' field")
    # -------------------------

    db_exercise = db.query(exercise_model.Exercise).filter(
        exercise_model.Exercise.id == exercise_id,
        exercise_model.Exercise.user_id == current_user.id
    ).first()

    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    if db_exercise.status == "completed":
        raise HTTPException(status_code=400, detail="Exercise is already completed")

    try:
        # 1. Call AI to check the answer
        check_response_text = await TutorService.check_user_answer(
            exercise_content=db_exercise.content,
            user_answer=user_answer # Use our manually parsed variable
        )
        
        # ... (rest of the function is the same) ...
        is_correct = "correct" in check_response_text.lower() or "great job" in check_response_text.lower()
        
        db_interaction = exercise_model.Interaction(
            exercise_id=db_exercise.id,
            user_answer=user_answer,
            ai_response=check_response_text,
            is_correct=is_correct
        )
        db.add(db_interaction)

        suggested_exercise_text = None
        if is_correct:
            db_exercise.status = "completed"
            
            suggested_exercise_text = await TutorService.get_similar_exercise(
                exercise_content=db_exercise.content
            )
            
            suggestion_interaction = exercise_model.Interaction(
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
        print(f"Error checking answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing: {str(e)}")