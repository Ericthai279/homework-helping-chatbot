from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os # Import os

from core.config import settings
from db.database import create_tables
from routers import auth, exercise, roadmap

# payments 

# Create all database tables (if they don't exist)
create_tables()

app = FastAPI(
    title="EDUKIE AI Tutor API",
    description="API for the EDUKIE AI learning platform.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- API Routers ---
# All your API routes are prefixed with /api
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(exercise.router, prefix=settings.API_PREFIX)
app.include_router(roadmap.router, prefix=settings.API_PREFIX)
# app.include_router(payments.router, prefix=settings.API_PREFIX)

# --- Frontend Serving ---

# Define the path to the frontend folder
# It's one directory up ("..") from this file's directory ("backend")
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

# 1. Mount the 'frontend' folder as '/static'
# This serves app.js, style.css, etc.
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# 2. Serve the index.html file for the root path
@app.get("/")
async def read_index():
    index_path = os.path.join(frontend_dir, "index.html")
    return FileResponse(index_path)

# --- Middleware (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)