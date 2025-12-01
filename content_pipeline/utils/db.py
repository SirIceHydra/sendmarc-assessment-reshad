"""
Database Operations - SQLite wrapper for pipeline state management
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'pipeline.db')

@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """Initialize database with schema"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Pipelines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipelines (
                id TEXT PRIMARY KEY,
                source_url TEXT NOT NULL,
                current_stage INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                safety_decision TEXT,
                quality_score REAL
            )
        ''')
        
        # Stage outputs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stage_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id TEXT NOT NULL,
                stage INTEGER NOT NULL,
                output_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pipeline_id) REFERENCES pipelines(id)
            )
        ''')
        
        # Audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                reviewer TEXT,
                metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pipeline_id) REFERENCES pipelines(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pipeline_status ON pipelines(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stage_outputs_pipeline ON stage_outputs(pipeline_id, stage)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_log_pipeline ON audit_log(pipeline_id)')
        
        conn.commit()
        print(f"Database initialized at {DB_PATH}")


def create_pipeline(pipeline_id: str, source_url: str) -> None:
    """Create a new pipeline entry"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pipelines (id, source_url, current_stage, status)
            VALUES (?, ?, 0, 'running')
        ''', (pipeline_id, source_url))


def update_pipeline_stage(pipeline_id: str, stage: int) -> None:
    """Update the current stage of a pipeline"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE pipelines 
            SET current_stage = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (stage, pipeline_id))


def update_pipeline_status(
    pipeline_id: str, 
    status: str, 
    safety_decision: Optional[str] = None,
    quality_score: Optional[float] = None
) -> None:
    """Update pipeline status and optional fields"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        updates = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
        params = [status]
        
        if safety_decision is not None:
            updates.append('safety_decision = ?')
            params.append(safety_decision)
        
        if quality_score is not None:
            updates.append('quality_score = ?')
            params.append(quality_score)
        
        params.append(pipeline_id)
        
        query = f"UPDATE pipelines SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)


def save_stage_output(pipeline_id: str, stage: int, data: Dict[str, Any]) -> None:
    """Save output from a pipeline stage"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO stage_outputs (pipeline_id, stage, output_json)
            VALUES (?, ?, ?)
        ''', (pipeline_id, stage, json.dumps(data)))


def get_stage_output(pipeline_id: str, stage: int) -> Optional[Dict[str, Any]]:
    """Retrieve output from a specific stage"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT output_json FROM stage_outputs
            WHERE pipeline_id = ? AND stage = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (pipeline_id, stage))
        
        row = cursor.fetchone()
        if row:
            return json.loads(row['output_json'])
        return None


def get_all_stage_outputs(pipeline_id: str) -> Dict[int, Dict[str, Any]]:
    """Retrieve all stage outputs for a pipeline"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT stage, output_json FROM stage_outputs
            WHERE pipeline_id = ?
            ORDER BY stage, created_at DESC
        ''', (pipeline_id,))
        
        outputs = {}
        for row in cursor.fetchall():
            stage = row['stage']
            # Only keep the most recent output for each stage
            if stage not in outputs:
                outputs[stage] = json.loads(row['output_json'])
        
        return outputs


def get_pipeline_state(pipeline_id: str) -> Optional[Dict[str, Any]]:
    """Get complete pipeline state"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pipelines WHERE id = ?', (pipeline_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'id': row['id'],
            'source_url': row['source_url'],
            'current_stage': row['current_stage'],
            'status': row['status'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'safety_decision': row['safety_decision'],
            'quality_score': row['quality_score']
        }


def log_audit_event(
    pipeline_id: str, 
    event_type: str, 
    metadata: Optional[Dict[str, Any]] = None,
    reviewer: Optional[str] = None
) -> None:
    """Log an audit event"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_log (pipeline_id, event_type, reviewer, metadata)
            VALUES (?, ?, ?, ?)
        ''', (pipeline_id, event_type, reviewer, json.dumps(metadata) if metadata else None))


def get_audit_log(pipeline_id: str) -> List[Dict[str, Any]]:
    """Retrieve audit log for a pipeline"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM audit_log
            WHERE pipeline_id = ?
            ORDER BY timestamp ASC
        ''', (pipeline_id,))
        
        return [dict(row) for row in cursor.fetchall()]


def list_pipelines(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """List pipelines with optional status filter"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT * FROM pipelines
                WHERE status = ?
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT * FROM pipelines
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

