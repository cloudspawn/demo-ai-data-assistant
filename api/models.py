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


class QualityCheckSuggestRequest(BaseModel):
    """Request model for quality check suggestions."""
    
    table_name: str = Field(
        ...,
        description="Name of the table to check",
        min_length=1,
        examples=["analytics_events_daily"]
    )
    table_schema: Dict[str, str] = Field(
        ...,
        description="Table schema as column_name: data_type mapping",
        examples=[{
            "event_date": "DATE",
            "city": "VARCHAR",
            "event_count": "INTEGER"
        }]
    )


class QualityCheck(BaseModel):
    """Individual quality check suggestion."""
    
    check_id: str = Field(..., description="Unique check identifier")
    table_name: str = Field(..., description="Table name")
    check_name: str = Field(..., description="Name of the check")
    column: str = Field(..., description="Column being checked")
    check_type: str = Field(..., description="Type of check (null_check, range_check, etc)")
    description: str = Field(..., description="What the check validates")
    severity: str = Field(..., description="Severity level (critical, high, medium, low)")
    python_code: str = Field(..., description="Example Python code for the check")
    raw_suggestion: Dict[str, Any] = Field(..., description="Raw parsed suggestion from LLM")


class QualityCheckSuggestResponse(BaseModel):
    """Response model for quality check suggestions."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    table_name: str = Field(..., description="Table name")
    table_schema: Dict[str, str] = Field(..., description="Table schema")
    checks: List[QualityCheck] = Field(..., description="List of suggested quality checks")
    check_count: int = Field(..., description="Number of checks generated")
    raw_response: Optional[str] = Field(None, description="Raw LLM response")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    ollama_connected: bool = Field(..., description="Whether Ollama is accessible")