"""
Quality Checker API router.
"""

from fastapi import APIRouter, HTTPException, Depends
from agents.quality_checker import QualityCheckerAgent
from api.models import QualityCheckSuggestRequest, QualityCheckSuggestResponse
from config.settings import Settings, load_settings


router = APIRouter(prefix="/quality", tags=["Quality Checker"])


def get_settings() -> Settings:
    """Dependency to get application settings."""
    return load_settings()


def get_quality_agent(settings: Settings = Depends(get_settings)) -> QualityCheckerAgent:
    """Dependency to get Quality Checker agent."""
    return QualityCheckerAgent(settings)


@router.post("/suggest", response_model=QualityCheckSuggestResponse)
async def suggest_quality_checks(
    request: QualityCheckSuggestRequest,
    agent: QualityCheckerAgent = Depends(get_quality_agent)
):
    """
    Generate data quality check suggestions for a table schema.
    
    Args:
        request: Table name and schema
        agent: Quality Checker agent instance
        
    Returns:
        List of suggested quality checks with descriptions and code examples
    """
    try:
        result = agent.suggest_checks(request.table_name, request.table_schema)
        return QualityCheckSuggestResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating quality checks: {str(e)}"
        )