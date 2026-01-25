"""
Pytest configuration and fixtures.
"""

import pytest
from pathlib import Path
import duckdb
from config.settings import Settings


@pytest.fixture
def test_settings():
    """Create test settings with in-memory database."""
    settings = Settings(
        ollama_base_url="http://localhost:11434",
        ollama_model="llama3.1",
        duckdb_path=":memory:",  # In-memory database for tests
        api_host="0.0.0.0",
        api_port=8000
    )
    return settings


@pytest.fixture
def sample_db_path(tmp_path):
    """Create a temporary DuckDB database with sample data."""
    db_path = tmp_path / "test_warehouse.duckdb"
    
    conn = duckdb.connect(str(db_path))
    
    # Create test table
    conn.execute("""
        CREATE TABLE analytics_events_daily (
            event_date DATE,
            city VARCHAR,
            category VARCHAR,
            event_count INTEGER,
            avg_value DOUBLE
        )
    """)
    
    # Insert test data
    conn.execute("""
        INSERT INTO analytics_events_daily VALUES
        ('2026-01-18', 'Paris', 'traffic', 1500, 75.5),
        ('2026-01-19', 'Paris', 'traffic', 1600, 78.3),
        ('2026-01-20', 'Lyon', 'weather', 1200, 12.3)
    """)
    
    conn.close()
    
    return db_path