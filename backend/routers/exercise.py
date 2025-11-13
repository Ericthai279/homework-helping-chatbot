from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
import base64

from db.database import get_db
from models import user as user_model
# --- ADD BACK ---
from models import exercise as exercise_model 
from schemas import exercise as exercise_schema
# -----------------
from core.tutor_service import TutorService # Renamed service
from routers.auth import get_current_user

router = APIRouter(
    prefix="/exercises",
    tags=["exercises"]
)

@router.post("/", response_model=exercise_schema.ExerciseResponse)
async def create_exercise(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
    prompt: str = Form(""), # Prompt can be empty if there's only an image
    image: UploadFile = File(None)
):
    """
    Create a new exercise (from text or image).
    Returns the first hint.
    """
    if not prompt and not image:
        raise HTTPException(status_code=400, detail="Must provide either text or an image")

    base64_image_data = None
    if image:
        image_bytes = await image.read()
        base64_image_data = base64.b64encode(image_bytes).decode('utf-8')

    try:
        # 1. Call AI to get the first hint (and OCR if applicable)
        # AI will return (A) OCR + Hint, or (B) Hint
        initial_guidance = TutorService.get_initial_guidance(
            prompt=prompt,
            base64_image=base64_image_data
        )

        # 2. Create the exercise in the DB
        # Exercise content: if image, it should be the OCR. If not, it's the prompt.
        # We need to improve this, but for now just use the prompt.
        exercise_content = prompt if prompt else "Exercise from image"
        
        db_exercise = exercise_model.Exercise(
            user_id=current_user.id,
            content=exercise_content, # TODO: Save the OCR content here
            image_base64=base64_image_data
        )
        db.add(db_exercise)
        db.commit()

        # 3. Save the first interaction (the AI's hint)
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
    request: exercise_schema.SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """
    Submit an answer for an in-progress exercise.
    The AI will check if it's correct or incorrect.
    """
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
        check_response_text = TutorService.check_user_answer(
            exercise_content=db_exercise.content,
            user_answer=request.answer
        )
        
        # 2. Analyze AI response (simple logic)
        is_correct = "correct" in check_response_text.lower() or "great job" in check_response_text.lower()
        
        # 3. Save this interaction
        db_interaction = exercise_model.Interaction(
            exercise_id=db_exercise.id,
            user_answer=request.answer,
            ai_response=check_response_text,
            is_correct=is_correct
        )
        db.add(db_interaction)

        suggested_exercise_text = None
        if is_correct:
            db_exercise.status = "completed"
            
            # 4. If correct, get a similar exercise
            suggested_exercise_text = TutorService.get_similar_exercise(
                exercise_content=db_exercise.content
            )
            # Save this new suggestion in the DB
            suggestion_interaction = exercise_model.Interaction(
                exercise_id=db_exercise.id,
                suggested_exercise=suggested_exercise_text
            )
            db.add(suggestion_interaction)
        
        db.commit()

        # Return all data for this check
        return {
            "check_response": check_response_text,
            "is_correct": is_correct,
            "suggested_exercise": suggested_exercise_text
        }

    except Exception as e:
        print(f"Error checking answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing: {str(e)}")