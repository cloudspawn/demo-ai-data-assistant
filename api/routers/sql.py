"""
SQL Generator API router.
"""

from fastapi import APIRouter, HTTPException, Depends
from agents.sql_generator import SQLGeneratorAgent
from api.models import SQLGenerateRequest, SQLGenerateResponse
from config.settings import Settings, load_settings


router = APIRouter(prefix="/sql", tags=["SQL Generator"])


def get_settings() -> Settings:
    """Dependency to get application settings."""
    return load_settings()


def get_sql_agent(settings: Settings = Depends(get_settings)) -> SQLGeneratorAgent:
    """Dependency to get SQL Generator agent."""
    return SQLGeneratorAgent(settings)


@router.post("/generate", response_model=SQLGenerateResponse)
async def generate_sql(
    request: SQLGenerateRequest,
    agent: SQLGeneratorAgent = Depends(get_sql_agent)
):
    """
    Generate and execute SQL query from natural language question.
    
    Args:
        request: Question to convert to SQL
        agent: SQL Generator agent instance
        
    Returns:
        Generated SQL, results, and explanation
    """
    try:
        result = agent.generate_and_execute(request.question)
        return SQLGenerateResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating SQL: {str(e)}"
        )