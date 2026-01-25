"""
Create sample DuckDB database for testing.
"""

import duckdb
from pathlib import Path


def create_sample_database():
    """Create a sample DuckDB database with test data."""
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "sample_warehouse.duckdb"
    
    # Connect and create tables
    conn = duckdb.connect(str(db_path))
    
    # Create analytics_events_daily table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events_daily (
            event_date DATE,
            city VARCHAR,
            category VARCHAR,
            event_count INTEGER,
            avg_value DOUBLE
        )
    """)
    
    # Insert sample data
    conn.execute("""
        INSERT INTO analytics_events_daily VALUES
        ('2026-01-18', 'Paris', 'traffic', 1500, 75.5),
        ('2026-01-18', 'Lyon', 'traffic', 800, 68.2),
        ('2026-01-19', 'Paris', 'traffic', 1600, 78.3),
        ('2026-01-19', 'Lyon', 'traffic', 850, 70.1),
        ('2026-01-20', 'Paris', 'weather', 2000, 15.5),
        ('2026-01-20', 'Lyon', 'weather', 1200, 12.3),
        ('2026-01-21', 'Paris', 'traffic', 1550, 76.8),
        ('2026-01-21', 'Lyon', 'traffic', 820, 69.5)
    """)
    
    # Verify data
    result = conn.execute("SELECT COUNT(*) as count FROM analytics_events_daily").fetchone()
    print(f"✅ Created sample_warehouse.duckdb with {result[0]} rows")
    
    # Show tables
    tables = conn.execute("SHOW TABLES").fetchall()
    print(f"✅ Tables: {[t[0] for t in tables]}")
    
    conn.close()


if __name__ == "__main__":
    create_sample_database()