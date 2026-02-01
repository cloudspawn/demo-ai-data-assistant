"""
Create sample DuckDB database for testing.
"""

import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import random


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
    
    # Clear existing data
    conn.execute("DELETE FROM analytics_events_daily")
    
    # Generate richer dataset
    cities = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice']
    categories = ['traffic', 'weather', 'mobility', 'energy']
    
    # Generate 60 days of data
    start_date = datetime(2026, 1, 1)
    
    for day_offset in range(60):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        for city in cities:
            for category in categories:
                # Generate realistic values based on category
                if category == 'traffic':
                    base_value = 70 + random.randint(-10, 15)
                    event_count = random.randint(800, 2000)
                elif category == 'weather':
                    base_value = random.randint(5, 25)  # Temperature
                    event_count = random.randint(500, 1500)
                elif category == 'mobility':
                    base_value = random.randint(60, 90)
                    event_count = random.randint(1000, 3000)
                else:  # energy
                    base_value = random.randint(40, 80)
                    event_count = random.randint(600, 1800)
                
                conn.execute("""
                    INSERT INTO analytics_events_daily VALUES
                    (?, ?, ?, ?, ?)
                """, [date_str, city, category, event_count, base_value])
    
    # Verify data
    result = conn.execute("SELECT COUNT(*) as count FROM analytics_events_daily").fetchone()
    print(f"✅ Created sample_warehouse.duckdb with {result[0]} rows")
    
    # Show sample stats
    stats = conn.execute("""
        SELECT 
            COUNT(DISTINCT city) as cities,
            COUNT(DISTINCT category) as categories,
            MIN(event_date) as first_date,
            MAX(event_date) as last_date
        FROM analytics_events_daily
    """).fetchone()
    
    print(f"✅ Cities: {stats[0]}, Categories: {stats[1]}")
    print(f"✅ Date range: {stats[2]} to {stats[3]}")
    
    conn.close()


if __name__ == "__main__":
    create_sample_database()