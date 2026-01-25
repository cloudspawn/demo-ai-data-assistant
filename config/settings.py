from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # LLM Provider (optional: "ollama" or "anthropic")
    llm_provider: Literal["ollama", "anthropic"] = "ollama"
    
    # Ollama Configuration (default - local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    
    # Anthropic Configuration (alternative - optional)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    
    # Database
    duckdb_path: str = "data/sample_warehouse.duckdb"
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Project paths
    project_root: Path = Path(__file__).parent.parent
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_settings() -> Settings:
    """Load and return application settings."""
    return Settings()