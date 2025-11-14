import pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os # Need os for path joining

from core.config import settings
from db.database import create_tables
# FIX: Only import active routers
from routers import auth, exercise, roadmap 

# Create all database tables (if they don't exist)
create_tables()

app = FastAPI(
    title="EDUKIE AI Tutor API",
    description="API for the EDUKIE AI learning platform.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- FIX: Define Base Directories Robustly ---
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# --- API Routers ---
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(exercise.router, prefix=settings.API_PREFIX)
app.include_router(roadmap.router, prefix=settings.API_PREFIX)

# --- Frontend Serving ---

# 1. Mount the frontend assets (CSS, JS) under /static
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# 2. Serve the main index.html file for the root path
@app.get("/")
async def read_index():
    index_path = FRONTEND_DIR / "index.html"
    # This check is vital for local and deployed safety
    if not index_path.exists():
        return {"message": "Frontend index.html not found on server."} 
    return FileResponse(index_path)

# --- Middleware (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)