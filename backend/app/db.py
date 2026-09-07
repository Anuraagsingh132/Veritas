import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database with Row factory enabled."""
    conn = sqlite3.connect(settings.DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes database tables and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        filesize INTEGER DEFAULT 0,
        page_count INTEGER DEFAULT 0,
        dataset_tag TEXT DEFAULT 'uploaded',
        status TEXT DEFAULT 'uploaded',
        summary TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_pages (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        page_number INTEGER NOT NULL,
        text_content TEXT NOT NULL,
        char_count INTEGER DEFAULT 0,
        table_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facts (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        page_number INTEGER NOT NULL,
        category TEXT NOT NULL,
        subject TEXT NOT NULL,
        predicate TEXT NOT NULL,
        value TEXT NOT NULL,
        unit TEXT DEFAULT '',
        temporal_context TEXT DEFAULT '',
        scope_context TEXT DEFAULT '',
        exact_quote TEXT NOT NULL,
        char_offset_start INTEGER DEFAULT 0,
        char_offset_end INTEGER DEFAULT 0,
        confidence REAL DEFAULT 1.0,
        is_failure_example INTEGER DEFAULT 0,
        failure_notes TEXT DEFAULT '',
        bbox TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relationships (
        id TEXT PRIMARY KEY,
        fact_id_1 TEXT NOT NULL,
        fact_id_2 TEXT NOT NULL,
        doc_id_1 TEXT NOT NULL,
        doc_id_2 TEXT NOT NULL,
        relationship_type TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        reasoning TEXT NOT NULL,
        context_difference TEXT DEFAULT '',
        case_category TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (fact_id_1) REFERENCES facts (id) ON DELETE CASCADE,
        FOREIGN KEY (fact_id_2) REFERENCES facts (id) ON DELETE CASCADE,
        FOREIGN KEY (doc_id_1) REFERENCES documents (id) ON DELETE CASCADE,
        FOREIGN KEY (doc_id_2) REFERENCES documents (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metadata (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create indexes for fast filtering
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_pages_doc ON document_pages(document_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_doc ON facts(document_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_facts ON relationships(fact_id_1, fact_id_2);")
    # Check and migrate bbox column if missing in existing database
    try:
        cursor.execute("SELECT bbox FROM facts LIMIT 1;")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE facts ADD COLUMN bbox TEXT DEFAULT '[]';")
            logger.info("Migrated facts table: added bbox column.")
        except Exception as e:
            logger.debug(f"Column migration skipped: {e}")

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully at %s", settings.DB_PATH)

if __name__ == "__main__":
    init_db()
