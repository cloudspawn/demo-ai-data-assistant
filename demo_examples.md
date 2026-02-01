# Demo Examples

## SQL Generator

### Simple queries
- "Show me all data"
- "Show me traffic in Paris"
- "What's the average traffic value?"

### Complex queries
- "Show me traffic trends in Paris for the last 30 days"
- "Compare average mobility between all cities"
- "Which city has the highest energy consumption?"

## Quality Checker

### Analytics Events Schema
```json
{
  "table_name": "analytics_events_daily",
  "table_schema": {
    "event_date": "DATE",
    "city": "VARCHAR",
    "category": "VARCHAR",
    "event_count": "INTEGER",
    "avg_value": "DOUBLE"
  }
}
```

### Users Schema
```json
{
  "table_name": "users",
  "table_schema": {
    "user_id": "INTEGER",
    "email": "VARCHAR",
    "created_at": "TIMESTAMP",
    "age": "INTEGER"
  }
}
```

## Pipeline Debugger

### PermissionError
```json
{
  "error_log": "PermissionError: [Errno 13] Permission denied: '/opt/airflow/data/raw/events.csv'",
  "dag_code": "with open('/opt/airflow/data/raw/events.csv', 'r') as f:\n    data = f.read()"
}
```

### ModuleNotFoundError
```json
{
  "error_log": "ModuleNotFoundError: No module named 'pandas'",
  "dag_code": "import pandas as pd"
}
```