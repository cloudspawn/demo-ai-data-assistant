"""
Tests for FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    def test_root_health_check(self):
        """Test root health check endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.2.0"
        assert "ollama_connected" in data
    
    def test_simple_health_check(self):
        """Test simple health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestSQLEndpoints:
    """Test suite for SQL Generator endpoints."""
    
    @patch('api.routers.sql.SQLGeneratorAgent')
    def test_generate_sql_success(self, mock_agent_class):
        """Test successful SQL generation."""
        # Mock agent
        mock_agent = Mock()
        mock_agent.generate_and_execute.return_value = {
            "success": True,
            "question": "Show me data",
            "sql": "SELECT * FROM table",
            "results": [{"id": 1}],
            "row_count": 1,
            "explanation": "This query selects all data."
        }
        mock_agent_class.return_value = mock_agent
        
        response = client.post(
            "/api/sql/generate",
            json={"question": "Show me data"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["sql"] == "SELECT * FROM table"
        assert data["row_count"] == 1
    
    def test_generate_sql_invalid_request(self):
        """Test SQL generation with invalid request."""
        response = client.post(
            "/api/sql/generate",
            json={"question": ""}  # Empty question
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_sql_missing_question(self):
        """Test SQL generation with missing question field."""
        response = client.post(
            "/api/sql/generate",
            json={}
        )
        
        assert response.status_code == 422
    
    @patch('api.routers.sql.SQLGeneratorAgent')
    def test_generate_sql_agent_error(self, mock_agent_class):
        """Test SQL generation when agent raises error."""
        mock_agent = Mock()
        mock_agent.generate_and_execute.side_effect = Exception("Agent error")
        mock_agent_class.return_value = mock_agent
        
        response = client.post(
            "/api/sql/generate",
            json={"question": "Show me data"}
        )
        
        assert response.status_code == 500
        assert "Error generating SQL" in response.json()["detail"]


class TestAPIDocumentation:
    """Test suite for API documentation."""
    
    def test_openapi_schema(self):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "AI Data Assistant API"
    
    def test_swagger_ui(self):
        """Test Swagger UI is accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

class TestQualityEndpoints:
    """Test suite for Quality Checker endpoints."""
    
    @patch('api.routers.quality.QualityCheckerAgent')
    def test_suggest_checks_success(self, mock_agent_class):
        """Test successful quality check suggestions."""
        mock_agent = Mock()
        mock_agent.suggest_checks.return_value = {
            "success": True,
            "table_name": "test_table",
            "table_schema": {"col1": "VARCHAR"},
            "checks": [
                {
                    "check_id": "test_table_check_1",
                    "table_name": "test_table",
                    "check_name": "col1_not_null",
                    "column": "col1",
                    "check_type": "null_check",
                    "description": "Column should not be null",
                    "severity": "critical",
                    "python_code": "assert df['col1'].notna().all()",
                    "raw_suggestion": {}
                }
            ],
            "check_count": 1,
            "raw_response": "Check suggestions"
        }
        mock_agent_class.return_value = mock_agent
        
        response = client.post(
            "/api/quality/suggest",
            json={
                "table_name": "test_table",
                "table_schema": {"col1": "VARCHAR"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["table_name"] == "test_table"
        assert data["check_count"] == 1
        assert len(data["checks"]) == 1
    
    def test_suggest_checks_invalid_request(self):
        """Test quality check suggestions with invalid request."""
        response = client.post(
            "/api/quality/suggest",
            json={"table_name": ""}  # Empty table name
        )
        
        assert response.status_code == 422
    
    def test_suggest_checks_missing_schema(self):
        """Test quality check suggestions with missing schema."""
        response = client.post(
            "/api/quality/suggest",
            json={"table_name": "test"}  # Missing schema
        )
        
        assert response.status_code == 422
    
    @patch('api.routers.quality.QualityCheckerAgent')
    def test_suggest_checks_agent_error(self, mock_agent_class):
        """Test quality check suggestions when agent raises error."""
        mock_agent = Mock()
        mock_agent.suggest_checks.side_effect = Exception("Agent error")
        mock_agent_class.return_value = mock_agent
        
        response = client.post(
            "/api/quality/suggest",
            json={
                "table_name": "test_table",
                "table_schema": {"col1": "VARCHAR"}
            }
        )
        
        assert response.status_code == 500
        assert "Error generating quality checks" in response.json()["detail"]