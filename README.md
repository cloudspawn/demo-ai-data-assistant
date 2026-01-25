# AI-Powered Data Assistant

Multi-agent AI system for accelerating Data Engineering workflows.

## Status
🚧 In Development - Phase 1

## Stack
- Python 3.12
- FastAPI (API REST)
- LangGraph (multi-agent orchestration)
- Ollama + llama3.1 (local LLM)
- DuckDB (data warehouse)

## Features

### ✅ Implemented
- [x] SQL Query Generator (Agent 1)

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

# Edit .env if needed (default uses localhost:11434)
```

### Test SQL Generator Agent
```bash
# Run the agent directly
uv run python -m agents.sql_generator
```

## Project Structure
```
demo-ai-data-assistant/
├── agents/              # AI Agents
│   ├── sql_generator.py # Agent 1: SQL Generator
│   └── ...             # More agents coming
├── config/              # Configuration
│   └── settings.py     # Pydantic settings
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

## License
MIT