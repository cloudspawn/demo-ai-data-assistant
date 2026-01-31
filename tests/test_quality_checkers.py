"""
Tests for Quality Checker Agent.
"""

import pytest
from unittest.mock import Mock, patch
from agents.quality_checker import QualityCheckerAgent
from config.settings import Settings


class TestQualityCheckerAgent:
    """Test suite for Quality Checker Agent."""
    
    def test_init(self, test_settings):
        """Test agent initialization."""
        agent = QualityCheckerAgent(test_settings)
        assert agent.settings == test_settings
    
    def test_parse_checks_response_simple(self, test_settings):
        """Test parsing simple check response."""
        agent = QualityCheckerAgent(test_settings)
        
        response = """
- Check name: event_date_not_null
  Column: event_date
  Type: null_check
  Severity: critical
  Description: Date should not be null

- Check name: event_count_positive
  Column: event_count
  Type: range_check
  Severity: high
  Description: Count must be positive
"""
        
        checks = agent._parse_checks_response(response)
        
        assert len(checks) >= 1
        assert any("event_date" in str(c).lower() for c in checks)
    
    def test_parse_checks_response_empty(self, test_settings):
        """Test parsing empty response."""
        agent = QualityCheckerAgent(test_settings)
        
        response = "No specific checks suggested."
        checks = agent._parse_checks_response(response)
        
        assert len(checks) >= 1  # Should return at least one general check
    
    @patch.object(QualityCheckerAgent, '_call_ollama')
    def test_suggest_checks_success(self, mock_ollama, test_settings):
        """Test successful check generation."""
        agent = QualityCheckerAgent(test_settings)
        
        # Mock LLM response
        mock_ollama.return_value = """
- Check name: event_date_not_null
  Column: event_date
  Type: null_check
  Severity: critical
  Description: Date should not be null
  Python code: assert df['event_date'].notna().all()
"""
        
        schema = {
            "event_date": "DATE",
            "city": "VARCHAR",
            "event_count": "INTEGER"
        }
        
        result = agent.suggest_checks("test_table", schema)
        
        assert result["success"] is True
        assert result["table_name"] == "test_table"
        assert result["schema"] == schema
        assert len(result["checks"]) >= 1
        assert result["check_count"] >= 1
        
        # Verify check structure
        first_check = result["checks"][0]
        assert "check_id" in first_check
        assert "table_name" in first_check
        assert "check_name" in first_check
        assert "column" in first_check
        assert "check_type" in first_check
        assert "description" in first_check
        assert "severity" in first_check
        assert "python_code" in first_check
    
    @patch.object(QualityCheckerAgent, '_call_ollama')
    def test_suggest_checks_llm_error(self, mock_ollama, test_settings):
        """Test check generation with LLM error."""
        agent = QualityCheckerAgent(test_settings)
        
        mock_ollama.side_effect = Exception("Ollama connection error")
        
        schema = {"event_date": "DATE"}
        result = agent.suggest_checks("test_table", schema)
        
        assert result["success"] is False
        assert "error" in result
        assert result["checks"] == []
    
    @patch('agents.quality_checker.httpx.post')
    def test_call_ollama_success(self, mock_post, test_settings):
        """Test successful Ollama API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Check suggestions here"}
        mock_post.return_value = mock_response
        
        agent = QualityCheckerAgent(test_settings)
        result = agent._call_ollama("test prompt")
        
        assert result == "Check suggestions here"
        mock_post.assert_called_once()
    
    @patch('agents.quality_checker.httpx.post')
    def test_call_ollama_error(self, mock_post, test_settings):
        """Test Ollama API call with error."""
        mock_post.side_effect = Exception("Connection error")
        
        agent = QualityCheckerAgent(test_settings)
        
        with pytest.raises(Exception) as exc_info:
            agent._call_ollama("test prompt")
        
        assert "Error calling Ollama" in str(exc_info.value)
    
    def test_check_enhancement(self, test_settings):
        """Test that checks are enhanced with proper structure."""
        agent = QualityCheckerAgent(test_settings)
        
        # Simulate parsed checks
        raw_checks = [
            {"description": "Check 1"},
            {"check_name": "custom_check", "description": "Check 2"}
        ]
        
        # The enhancement happens in suggest_checks, so we test the structure
        schema = {"col1": "VARCHAR"}
        
        with patch.object(agent, '_call_ollama', return_value="- Check: test"):
            with patch.object(agent, '_parse_checks_response', return_value=raw_checks):
                result = agent.suggest_checks("test_table", schema)
        
        assert result["success"] is True
        for check in result["checks"]:
            assert check["table_name"] == "test_table"
            assert "check_id" in check
            assert check["check_id"].startswith("test_table_check_")