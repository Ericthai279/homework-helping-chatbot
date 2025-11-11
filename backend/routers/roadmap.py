import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal
from models.roadmap import RoadmapJob
from models.user import User
from schemas.roadmap import RoadmapJobResponse
from schemas.roadmap import CreateRoadmapRequest # We need to create this schema
from core.tutor_service import RoadmapService
from routers.auth import get_current_user

router = APIRouter(
    prefix="/roadmaps",
    tags=["roadmaps"]
)

# --- Background Task ---
def generate_roadmap_task(job_id: str, user_id: int, learning_target: str):
    """
    This is the background task that calls the LLM.
    It runs separately from the API request.
    """
    db = SessionLocal() # Create a new session for the background task
    try:
        job = db.query(RoadmapJob).filter(RoadmapJob.job_id == job_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if not job or not user:
            return # Job or user was deleted, nothing to do

        job.status = "processing"
        db.commit()

        try:
            # This is the slow LLM call
            roadmap_data = RoadmapService.generate_roadmap(user, learning_target)
            
            job.roadmap_data = roadmap_data.model_dump() # Store as JSON
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
        
        db.commit()
    
    finally:
        db.close()
# --- End of Task ---


@router.post("/create", response_model=RoadmapJobResponse)
def create_roadmap(
    request: CreateRoadmapRequest, # Needs schema: schemas/roadmap.py
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new job to generate a premium learning roadmap.
    """
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is a premium feature."
        )

    job_id = str(uuid.uuid4())
    job = RoadmapJob(
        job_id=job_id,
        user_id=current_user.id,
        theme=request.learning_target, # Using 'theme' field from model
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Add the slow task to run in the background
    background_tasks.add_task(
        generate_roadmap_task,
        job_id=job_id,
        user_id=current_user.id,
        learning_target=request.learning_target
    )

    return job

@router.get("/{job_id}", response_model=RoadmapJobResponse)
def get_roadmap_job_status(
    job_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Checks the status of a roadmap generation job.
    """
    job = db.query(RoadmapJob).filter(RoadmapJob.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    return job