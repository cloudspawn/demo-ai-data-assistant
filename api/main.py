"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx

from config.settings import load_settings
from api.routers import sql, quality
from api.models import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 AI Data Assistant API starting...")
    settings = load_settings()
    print(f"📡 Ollama URL: {settings.ollama_base_url}")
    print(f"🤖 Model: {settings.ollama_model}")
    print(f"💾 Database: {settings.duckdb_path}")
    
    yield
    
    # Shutdown
    print("👋 AI Data Assistant API shutting down...")


app = FastAPI(
    title="AI Data Assistant API",
    description="Multi-agent AI system for accelerating Data Engineering workflows",
    version="0.2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sql.router, prefix="/api")
app.include_router(quality.router, prefix="/api")


@app.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service status and Ollama connectivity
    """
    settings = load_settings()
    
    # Check Ollama connectivity
    ollama_connected = False
    try:
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
        ollama_connected = response.status_code == 200
    except Exception:
        ollama_connected = False
    
    return HealthResponse(
        status="healthy",
        version="0.2.0",
        ollama_connected=ollama_connected
    )


@app.get("/health")
async def simple_health():
    """Simple health check for monitoring."""
    return {"status": "ok"}