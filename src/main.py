from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from sqlalchemy import text

from src.config.settings import settings
from src.models.database import create_tables, engine
from src.api.routes import router as api_router
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting RAG Pipeline API with Groq and LangChain")
    try:
        create_tables()
        logger.info("Database tables created successfully")
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            logger.info(f"Database tables: {tables}")
            
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Pipeline API")

app = FastAPI(
    title="RAG Pipeline API",
    description="Retrieval-Augmented Generation Pipeline with Groq LLM and LangChain",
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

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Serve frontend files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    # Serve frontend files directly from root
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        frontend_file = os.path.join(frontend_path, path)
        if os.path.exists(frontend_file) and os.path.isfile(frontend_file):
            return FileResponse(frontend_file)
        # If file doesn't exist, serve index.html for client-side routing
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "message": "RAG Pipeline API with Groq and LangChain",
            "version": "1.0.0",
            "docs": "/docs",
            "frontend": "Frontend files not found. Please build the frontend."
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "RAG Pipeline API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)