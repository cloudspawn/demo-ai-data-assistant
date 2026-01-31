# AI-Powered Data Assistant

Multi-agent AI system for accelerating Data Engineering workflows.

## Status
🚧 In Development - Phase 3 Complete (SQL + Quality + Multi-Agent Debugger)

## Stack
- Python 3.12
- FastAPI (API REST)
- LangGraph (multi-agent orchestration)
- Ollama + llama3.1 (local LLM)
- DuckDB (data warehouse)
- pytest (testing)

## Features

### ✅ Implemented
- [x] SQL Query Generator (Agent 1)
- [x] Quality Check Generator (Agent 2)
- [x] Pipeline Debugger (Agent 3 - Multi-agent with LangGraph)
- [x] FastAPI REST API
- [x] Health check endpoints
- [x] Auto-generated Swagger UI
- [x] Full test coverage (41 tests)

### 🚧 In Progress
- [ ] Documentation Generator (Agent 4 - optional)

## Quick Start

### Prerequisites
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull llama3.1 model
ollama pull llama3.1

# Start Ollama server
ollama serve
```

### Installation
```bash
# Clone repository
git clone <your-repo-url>
cd demo-ai-data-assistant

# Install dependencies with uv
uv sync --extra dev

# Copy environment template
cp .env.example .env

# Edit .env with your Ollama URL (default: localhost:11434)
# If VM → PC setup: OLLAMA_BASE_URL=http://192.168.x.x:11434
```

### Create Sample Data
```bash
# Create sample DuckDB database
uv run python scripts/create_sample_data.py
```

### Run API Server
```bash
# Start FastAPI server
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Test the API

**Option 1: Swagger UI (Recommended)**
```
Open: http://localhost:8000/docs
```

**Option 2: curl**
```bash
# Health check
curl http://localhost:8000/

# Generate SQL
curl -X POST http://localhost:8000/api/sql/generate \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me traffic trends in Paris"}'

# Suggest quality checks
curl -X POST http://localhost:8000/api/quality/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "analytics_events_daily",
    "table_schema": {
      "event_date": "DATE",
      "city": "VARCHAR",
      "event_count": "INTEGER"
    }
  }'

# Debug pipeline error
curl -X POST http://localhost:8000/api/debug/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "error_log": "PermissionError: Permission denied",
    "dag_code": "with open(\"/path/file\") as f: pass"
  }'
```

**Option 3: Direct agent test**
```bash
# Test SQL Generator
uv run python -m agents.sql_generator

# Test Quality Checker
uv run python -m agents.quality_checker

# Test Pipeline Debugger
uv run python -m agents.debugger
```

## Testing

### Run all tests
```bash
uv run pytest
```

### Run specific test file
```bash
uv run pytest tests/test_sql_generator.py
uv run pytest tests/test_quality_checker.py
uv run pytest tests/test_debugger.py
uv run pytest tests/test_api.py
```

## API Endpoints

### `GET /`
Health check with Ollama connectivity status

### `GET /health`
Simple health check

### `POST /api/sql/generate`
Generate and execute SQL from natural language

**Request:**
```json
{
  "question": "Show me traffic trends in Paris last week"
}
```

**Response:**
```json
{
  "success": true,
  "sql": "SELECT ...",
  "results": [...],
  "row_count": 3,
  "explanation": "This query..."
}
```

### `POST /api/quality/suggest`
Generate data quality check suggestions from table schema

**Request:**
```json
{
  "table_name": "analytics_events_daily",
  "table_schema": {
    "event_date": "DATE",
    "city": "VARCHAR",
    "event_count": "INTEGER",
    "avg_value": "DOUBLE"
  }
}
```

**Response:**
```json
{
  "success": true,
  "table_name": "analytics_events_daily",
  "checks": [
    {
      "check_name": "event_date_not_null",
      "column": "event_date",
      "check_type": "null_check",
      "severity": "critical",
      "description": "event_date should never be NULL",
      "python_code": "assert df['event_date'].notna().all()"
    }
  ],
  "check_count": 5
}
```

### `POST /api/debug/pipeline`
Debug data pipeline errors using multi-agent analysis (LangGraph)

**Request:**
```json
{
  "error_log": "[2026-01-25] ERROR - PermissionError: Permission denied: '/opt/airflow/data/raw/events.csv'",
  "dag_code": "from airflow import DAG\n\ndef extract_data():\n    with open('/opt/airflow/data/raw/events.csv', 'r') as f:\n        data = f.read()"
}
```

**Response:**
```json
{
  "success": true,
  "diagnosis": {
    "error_type": "PermissionError",
    "root_cause": "File permissions issue..."
  },
  "solution": {
    "steps": "1. Change ownership...",
    "commands": ["sudo chown airflow:airflow /opt/airflow/data/raw"],
    "explanation": "This fixes the permissions..."
  },
  "prevention": "Set correct permissions from start...",
  "agent_workflow": [
    "Log Analyzer: Identified PermissionError",
    "Code Checker: Analyzed code...",
    "Solution Generator: Generated fix"
  ]
}
```

## Architecture

### Multi-Agent System (Pipeline Debugger)

The Pipeline Debugger uses **LangGraph** to orchestrate 3 specialized agents:
```
Error Log + DAG Code
        ↓
┌─────────────────┐
│ Log Analyzer    │ → Identifies error type
└─────────────────┘
        ↓
┌─────────────────┐
│ Code Checker    │ → Analyzes root cause
└─────────────────┘
        ↓
┌─────────────────┐
│Solution Generator│ → Proposes fix + commands
└─────────────────┘
        ↓
  Diagnosis + Solution
```

Each agent specializes in one task, improving accuracy and quality of responses.

## Project Structure
```
demo-ai-data-assistant/
├── agents/              # AI Agents
│   ├── sql_generator.py # Agent 1: SQL Generator
│   ├── quality_checker.py # Agent 2: Quality Checker
│   └── debugger.py      # Agent 3: Pipeline Debugger (LangGraph)
├── api/                 # FastAPI application
│   ├── main.py         # App entry point
│   ├── models.py       # Pydantic models
│   └── routers/
│       ├── sql.py      # SQL endpoints
│       ├── quality.py  # Quality endpoints
│       └── debugger.py # Debugger endpoints
├── config/              # Configuration
│   └── settings.py     # Pydantic settings
├── tests/               # Test suite (41 tests)
│   ├── conftest.py     # Pytest fixtures
│   ├── test_sql_generator.py
│   ├── test_quality_checker.py
│   ├── test_debugger.py
│   └── test_api.py
├── scripts/             # Utility scripts
│   └── create_sample_data.py
├── data/                # Data files (gitignored)
├── .env.example        # Environment template
└── pyproject.toml      # Dependencies
```

## Configuration

### Ollama (Default - Local)
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

### Network Setup (VM → PC with GPU)
If running on VM and Ollama on separate PC:
```bash
OLLAMA_BASE_URL=http://192.168.x.x:11434  # Replace x.x with PC IP
```

## Development

### Run tests
```bash
uv run pytest
```

### Code formatting
```bash
uv run ruff check .
uv run ruff format .
```

## What I Learned

### Multi-Agent Orchestration
- Built a LangGraph-powered multi-agent system
- Each agent specializes in one task (separation of concerns)
- Agents share state and collaborate sequentially
- Better results than single large prompts

### LLM Integration
- Integrated Ollama for local, cost-free LLM inference
- Prompt engineering for structured outputs
- Parsing and validating LLM responses
- Error handling and fallback strategies

### API Design
- RESTful API with FastAPI
- Pydantic models for request/response validation
- Dependency injection for settings and agents
- Auto-generated OpenAPI documentation

### Testing Strategy
- Unit tests with mocked LLM calls
- Integration tests for end-to-end workflows
- Test fixtures for reusable test data
- 41 tests covering all agents and endpoints

## License
MIT