import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.db import init_db
from app.services.seed_data import seed_starter_knowledge
from app.routers import documents, facts, reconciliation, showcase, system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fact_knowledge_layer")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB exists and initialize seed knowledge
    logger.info("Initializing Fact Knowledge Layer database...")
    init_db()
    seed_starter_knowledge(force=False)
    logger.info("Startup complete. System is ready to accept queries and PDFs.")
    yield
    # Shutdown
    logger.info("Shutting down Fact Knowledge Layer.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Fact Extraction, Evidence Grounding, and Cross-Document Epistemological Reconciliation Engine",
    lifespan=lifespan
)

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(documents.router)
app.include_router(facts.router)
app.include_router(reconciliation.router)
app.include_router(showcase.router)
app.include_router(system.router)

@app.get("/api/info")
def get_api_info():
    """Returns JSON metadata about the Fact Knowledge Layer."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "showcase_url": "/api/showcase"
    }

# Mount frontend build if available
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root():
        return get_api_info()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
