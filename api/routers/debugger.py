"""
Pipeline Debugger API router.
"""

from fastapi import APIRouter, HTTPException, Depends
from agents.debugger import PipelineDebuggerAgent
from api.models import DebugPipelineRequest, DebugPipelineResponse, Diagnosis, Solution
from config.settings import Settings, load_settings


router = APIRouter(prefix="/debug", tags=["Pipeline Debugger"])


def get_settings() -> Settings:
    """Dependency to get application settings."""
    return load_settings()


def get_debugger_agent(settings: Settings = Depends(get_settings)) -> PipelineDebuggerAgent:
    """Dependency to get Pipeline Debugger agent."""
    return PipelineDebuggerAgent(settings)


@router.post("/pipeline", response_model=DebugPipelineResponse)
async def debug_pipeline(
    request: DebugPipelineRequest,
    agent: PipelineDebuggerAgent = Depends(get_debugger_agent)
):
    """
    Debug a data pipeline error using multi-agent analysis.
    
    This endpoint uses a LangGraph-powered multi-agent system:
    1. Log Analyzer: Identifies error type
    2. Code Checker: Analyzes code for root cause
    3. Solution Generator: Proposes fix with commands
    
    Args:
        request: Error log and optional DAG code
        agent: Pipeline Debugger agent instance
        
    Returns:
        Diagnosis, solution, and prevention recommendations
    """
    try:
        result = agent.debug_pipeline(request.error_log, request.dag_code)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error during debugging")
            )
        
        return DebugPipelineResponse(
            success=result["success"],
            error_log=result["error_log"],
            diagnosis=Diagnosis(**result["diagnosis"]),
            solution=Solution(**result["solution"]),
            prevention=result["prevention"],
            agent_workflow=result["agent_workflow"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error debugging pipeline: {str(e)}"
        )