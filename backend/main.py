from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.database import create_tables
from routers import auth, exercise, roadmap

# Create all database tables (if they don't exist)
# This is from your original code and is good practice.
create_tables()

app = FastAPI(
    title="EDUKIE AI Tutor API",
    description="API for the EDUKIE AI learning platform.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the new routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(exercise.router, prefix=settings.API_PREFIX)
app.include_router(roadmap.router, prefix=settings.API_PREFIX)

@app.get("/")
def read_root():
    return {"message": "Welcome to the EDUKIE API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)