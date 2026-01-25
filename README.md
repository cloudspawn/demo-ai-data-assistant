# AI-Powered Data Assistant

Multi-agent AI system for accelerating Data Engineering workflows.

## Status
🚧 In Development - Phase 1 Complete (SQL Generator + API + Tests)

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
- [x] FastAPI REST API
- [x] Health check endpoints
- [x] Auto-generated Swagger UI
- [x] Unit and integration tests
- [x] Test fixtures and mocks

### 🚧 In Progress
- [ ] Quality Check Generator (Agent 2)
- [ ] Pipeline Debugger (Agent 3 - multi-agent)
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
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your Ollama URL (default: localhost:11434)
# If VM → PC setup: OLLAMA_BASE_URL=http://192.168.1.10:11434
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
```

**Option 3: Direct agent test**
```bash
uv run python -m agents.sql_generator
```

## Testing

### Run all tests
```bash
uv run pytest
```

### Run specific test file
```bash
uv run pytest tests/test_sql_generator.py
uv run pytest tests/test_api.py
```

### Run with coverage
```bash
uv run pytest --cov=agents --cov=api
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
  "question": "Show me traffic trends in Paris last week",
  "sql": "SELECT event_date, city, avg_value FROM analytics_events_daily WHERE city = 'Paris' AND category = 'traffic' ORDER BY event_date",
  "results": [...],
  "row_count": 3,
  "explanation": "This query retrieves traffic trends for Paris..."
}
```

## Project Structure
```
demo-ai-data-assistant/
├── agents/              # AI Agents
│   └── sql_generator.py # Agent 1: SQL Generator
├── api/                 # FastAPI application
│   ├── main.py         # App entry point
│   ├── models.py       # Pydantic models
│   └── routers/
│       └── sql.py      # SQL endpoints
├── config/              # Configuration
│   └── settings.py     # Pydantic settings
├── tests/               # Test suite
│   ├── conftest.py     # Pytest fixtures
│   ├── test_sql_generator.py
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
OLLAMA_BASE_URL=http://192.168.x.x:11434  # Replace with PC IP
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

## License
MIT