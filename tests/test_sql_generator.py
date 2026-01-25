"""
Tests for SQL Generator Agent.
"""

import pytest
from unittest.mock import Mock, patch
from agents.sql_generator import SQLGeneratorAgent
from config.settings import Settings


class TestSQLGeneratorAgent:
    """Test suite for SQL Generator Agent."""
    
    def test_init(self, test_settings):
        """Test agent initialization."""
        agent = SQLGeneratorAgent(test_settings)
        assert agent.settings == test_settings
        assert agent.db_path is not None
    
    def test_get_database_schema(self, test_settings, sample_db_path):
        """Test schema extraction from DuckDB."""
        test_settings.duckdb_path = str(sample_db_path)
        agent = SQLGeneratorAgent(test_settings)
        
        schema = agent._get_database_schema()
        
        assert "analytics_events_daily" in schema
        assert "event_date" in schema
        assert "city" in schema
        assert "VARCHAR" in schema or "DATE" in schema
    
    def test_extract_sql_from_response(self, test_settings):
        """Test SQL extraction from LLM response."""
        agent = SQLGeneratorAgent(test_settings)
        
        # Test with markdown
        response = "```sql\nSELECT * FROM table\n```"
        sql = agent._extract_sql_from_response(response)
        assert sql == "SELECT * FROM table"
        
        # Test without markdown
        response = "SELECT * FROM table"
        sql = agent._extract_sql_from_response(response)
        assert sql == "SELECT * FROM table"
        
        # Test with generic code block
        response = "```\nSELECT * FROM table\n```"
        sql = agent._extract_sql_from_response(response)
        assert sql == "SELECT * FROM table"
    
    def test_execute_sql(self, test_settings, sample_db_path):
        """Test SQL execution on DuckDB."""
        test_settings.duckdb_path = str(sample_db_path)
        agent = SQLGeneratorAgent(test_settings)
        
        sql = "SELECT COUNT(*) as count FROM analytics_events_daily"
        results = agent._execute_sql(sql)
        
        assert len(results) == 1
        assert results[0]["count"] == 3
    
    def test_execute_sql_error(self, test_settings, sample_db_path):
        """Test SQL execution with invalid query."""
        test_settings.duckdb_path = str(sample_db_path)
        agent = SQLGeneratorAgent(test_settings)
        
        sql = "SELECT * FROM nonexistent_table"
        
        with pytest.raises(Exception) as exc_info:
            agent._execute_sql(sql)
        
        assert "Error executing SQL" in str(exc_info.value)
    
    @patch('agents.sql_generator.httpx.post')
    def test_call_ollama_success(self, mock_post, test_settings):
        """Test successful Ollama API call."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "SELECT * FROM table"}
        mock_post.return_value = mock_response
        
        agent = SQLGeneratorAgent(test_settings)
        result = agent._call_ollama("test prompt")
        
        assert result == "SELECT * FROM table"
        mock_post.assert_called_once()
    
    @patch('agents.sql_generator.httpx.post')
    def test_call_ollama_error(self, mock_post, test_settings):
        """Test Ollama API call with error."""
        mock_post.side_effect = Exception("Connection error")
        
        agent = SQLGeneratorAgent(test_settings)
        
        with pytest.raises(Exception) as exc_info:
            agent._call_ollama("test prompt")
        
        assert "Error calling Ollama" in str(exc_info.value)
    
    @patch.object(SQLGeneratorAgent, '_call_ollama')
    def test_generate_and_execute_success(self, mock_ollama, test_settings, sample_db_path):
        """Test full generate and execute flow."""
        test_settings.duckdb_path = str(sample_db_path)
        agent = SQLGeneratorAgent(test_settings)
        
        # Mock LLM responses
        mock_ollama.side_effect = [
            "SELECT * FROM analytics_events_daily WHERE city = 'Paris'",
            "This query selects all events for Paris."
        ]
        
        result = agent.generate_and_execute("Show me events in Paris")
        
        assert result["success"] is True
        assert "SELECT" in result["sql"]
        assert len(result["results"]) == 2  # 2 Paris rows in sample data
        assert result["row_count"] == 2
        assert "explanation" in result
    
    @patch.object(SQLGeneratorAgent, '_call_ollama')
    def test_generate_and_execute_sql_error(self, mock_ollama, test_settings, sample_db_path):
        """Test generate and execute with invalid SQL."""
        test_settings.duckdb_path = str(sample_db_path)
        agent = SQLGeneratorAgent(test_settings)
        
        # Mock LLM to return invalid SQL
        mock_ollama.return_value = "SELECT * FROM nonexistent_table"
        
        result = agent.generate_and_execute("Show me data")
        
        assert result["success"] is False
        assert "error" in result
        assert result["results"] == []