from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.db import get_db_connection, init_db
from app.services.seed_data import seed_starter_knowledge
from app.services.llm_client import shared_llm_client
from app.models import StatsResponse
from app.config import settings

router = APIRouter(prefix="/api/system", tags=["System"])

llm_client = shared_llm_client

class KeyUpdateRequest(BaseModel):
    groq_api_key: str

@router.get("/stats", response_model=StatsResponse)
def get_system_stats():
    """Returns high-level statistics across the knowledge layer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(page_count) FROM documents")
    total_pages = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM facts")
    total_facts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM relationships")
    total_rels = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE relationship_type = 'corroboration'")
    corroborations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE relationship_type = 'genuine_contradiction'")
    contradictions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE relationship_type = 'contextual_reconciliation'")
    contextual = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM facts WHERE is_failure_example = 1")
    failures = cursor.fetchone()[0]
    
    conn.close()
    
    return StatsResponse(
        total_documents=total_docs,
        total_pages=total_pages,
        total_facts=total_facts,
        total_relationships=total_rels,
        corroborations_count=corroborations,
        contradictions_count=contradictions,
        contextual_reconciliations_count=contextual,
        failures_cataloged_count=failures
    )

@router.post("/key")
def update_api_key(req: KeyUpdateRequest):
    """Dynamically updates the Groq API key at runtime."""
    settings.GROQ_API_KEY = req.groq_api_key.strip()
    llm_client.set_api_key(settings.GROQ_API_KEY)
    return {
        "status": "success",
        "message": "Groq API key updated successfully.",
        "is_available": llm_client.is_available()
    }

@router.get("/status")
def get_status():
    """Returns server and LLM availability status."""
    return {
        "status": "online",
        "llm_available": llm_client.is_available(),
        "model": settings.DEFAULT_MODEL,
        "database_path": str(settings.DB_PATH)
    }

@router.post("/reseed")
def reseed_database():
    """Reseeds database with curated starter knowledge and 4 required cases."""
    seed_starter_knowledge(force=True)
    return {"message": "Database reseeded successfully."}
