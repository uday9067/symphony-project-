from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import os

from app.routes import projects, tasks
from core.database import create_db_and_tables
from core.models import ProjectCreate
from core.orchestrator import ProjectOrchestrator
from utils.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Project Symphony API")
    await create_db_and_tables()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Project Symphony API")

# Create FastAPI app
app = FastAPI(
    title="Project Symphony API",
    description="Multi-Agent AI Project Builder with Free APIs",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve web interface"""
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Project Symphony API</h1><p>Go to /docs for API documentation</p>")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "project_symphony"}

@app.post("/api/process-project")
async def process_project(project: ProjectCreate):
    """Main endpoint to process a project through all phases"""
    try:
        orchestrator = ProjectOrchestrator()
        result = await orchestrator.process_project(project.description)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error processing project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )