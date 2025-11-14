import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
import asyncio 

from db.database import get_db, SessionLocal
# FIX: Import models directly from their files, not through the __init__.py
from models.roadmap import RoadmapJob as RoadmapJobModel
from models.user import User as UserModel
from schemas.roadmap import RoadmapJobResponse, CreateRoadmapRequest
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
    """
    db = SessionLocal() 
    
    async def _run_async_job():
        # FIX: Reference models by their new name
        job = db.query(RoadmapJobModel).filter(RoadmapJobModel.job_id == job_id).first()
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not job or not user:
            return

        job.status = "processing"
        db.commit()

        try:
            roadmap_object = await RoadmapService.generate_roadmap(user, learning_target)
            
            job.roadmap_data = roadmap_object.model_dump() 
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
        
        db.commit()
    
    try:
        asyncio.run(_run_async_job())
    finally:
        db.close()
# --- End of Task ---


@router.post("/create", response_model=RoadmapJobResponse)
def create_roadmap(
    request: CreateRoadmapRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Creates a new job to generate a premium learning roadmap.
    """
    # --- TEMPORARY FIX FOR TESTING (BYPASS PREMIUM CHECK) ---
    # if not current_user.is_premium:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="This is a premium feature."
    #     )
    # --- REMOVE ABOVE LINES IN PRODUCTION ---

    job_id = str(uuid.uuid4())
    job = RoadmapJobModel(
        job_id=job_id,
        user_id=current_user.id,
        theme=request.learning_target,
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
    current_user: UserModel = Depends(get_current_user)
):
    """
    Checks the status of a roadmap generation job.
    """
    job = db.query(RoadmapJobModel).filter(RoadmapJobModel.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this job")

    return job