"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SQLGenerateRequest(BaseModel):
    """Request model for SQL generation."""
    
    question: str = Field(
        ...,
        description="Natural language question about the data",
        min_length=3,
        examples=["Show me traffic trends in Paris last week"]
    )


class SQLGenerateResponse(BaseModel):
    """Response model for SQL generation."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    question: str = Field(..., description="Original question")
    sql: str = Field(..., description="Generated SQL query")
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    row_count: int = Field(..., description="Number of rows returned")
    explanation: Optional[str] = Field(None, description="Plain English explanation of the query")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    ollama_connected: bool = Field(..., description="Whether Ollama is accessible")