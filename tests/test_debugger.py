"""
Tests for Pipeline Debugger Agent.
"""

import pytest
from unittest.mock import Mock, patch
from agents.debugger import PipelineDebuggerAgent
from config.settings import Settings


class TestPipelineDebuggerAgent:
    """Test suite for Pipeline Debugger Agent."""
    
    def test_init(self, test_settings):
        """Test agent initialization."""
        agent = PipelineDebuggerAgent(test_settings)
        assert agent.settings == test_settings
        assert agent.graph is not None
    
    @patch('agents.debugger.httpx.post')
    def test_call_ollama_success(self, mock_post, test_settings):
        """Test successful Ollama API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Analysis result"}
        mock_post.return_value = mock_response
        
        agent = PipelineDebuggerAgent(test_settings)
        result = agent._call_ollama("test prompt")
        
        assert result == "Analysis result"
        mock_post.assert_called_once()
    
    @patch('agents.debugger.httpx.post')
    def test_call_ollama_error(self, mock_post, test_settings):
        """Test Ollama API call with error."""
        mock_post.side_effect = Exception("Connection error")
        
        agent = PipelineDebuggerAgent(test_settings)
        
        with pytest.raises(Exception) as exc_info:
            agent._call_ollama("test prompt")
        
        assert "Error calling Ollama" in str(exc_info.value)
    
    @patch.object(PipelineDebuggerAgent, '_call_ollama')
    def test_debug_pipeline_success(self, mock_ollama, test_settings):
        """Test successful pipeline debugging."""
        agent = PipelineDebuggerAgent(test_settings)
        
        # Mock LLM responses for each agent
        mock_ollama.side_effect = [
            "Error Type: PermissionError\nError Message: Permission denied\nFailing Component: file access",
            "Root Cause: The file permissions are incorrect.",
            "SOLUTION:\nChange file ownership\n\nCOMMANDS:\nsudo chown airflow file\n\nPREVENTION:\nSet correct permissions"
        ]
        
        error_log = "PermissionError: [Errno 13] Permission denied"
        dag_code = "with open('/path/file', 'r') as f: pass"
        
        result = agent.debug_pipeline(error_log, dag_code)
        
        assert result["success"] is True
        assert "diagnosis" in result
        assert result["diagnosis"]["error_type"] == "PermissionError"
        assert "solution" in result
        assert len(result["solution"]["commands"]) > 0
        assert "prevention" in result
        assert len(result["agent_workflow"]) > 0
    
    @patch.object(PipelineDebuggerAgent, '_call_ollama')
    def test_debug_pipeline_llm_error(self, mock_ollama, test_settings):
        """Test pipeline debugging with LLM error."""
        agent = PipelineDebuggerAgent(test_settings)
        
        mock_ollama.side_effect = Exception("Ollama connection error")
        
        error_log = "Some error"
        result = agent.debug_pipeline(error_log)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_log_analyzer_agent(self, test_settings):
        """Test log analyzer agent."""
        agent = PipelineDebuggerAgent(test_settings)
        
        state = {
            "messages": [],
            "error_log": "PermissionError: Permission denied",
            "dag_code": "",
            "error_type": "",
            "root_cause": "",
            "solution": "",
            "commands": [],
            "prevention": ""
        }
        
        with patch.object(agent, '_call_ollama', return_value="Error Type: PermissionError"):
            result = agent._log_analyzer_agent(state)
        
        assert result["error_type"] == "PermissionError"
        assert len(result["messages"]) > 0
    
    def test_code_checker_agent(self, test_settings):
        """Test code checker agent."""
        agent = PipelineDebuggerAgent(test_settings)
        
        state = {
            "messages": [],
            "error_log": "Error",
            "dag_code": "code",
            "error_type": "PermissionError",
            "root_cause": "",
            "solution": "",
            "commands": [],
            "prevention": ""
        }
        
        with patch.object(agent, '_call_ollama', return_value="File permissions issue"):
            result = agent._code_checker_agent(state)
        
        assert "File permissions" in result["root_cause"]
        assert len(result["messages"]) > 0
    
    def test_solution_generator_agent(self, test_settings):
        """Test solution generator agent."""
        agent = PipelineDebuggerAgent(test_settings)
        
        state = {
            "messages": [],
            "error_log": "Error",
            "dag_code": "code",
            "error_type": "PermissionError",
            "root_cause": "Wrong permissions",
            "solution": "",
            "commands": [],
            "prevention": ""
        }
        
        mock_response = """
SOLUTION:
Change file ownership

COMMANDS:
sudo chown airflow file

PREVENTION:
Set proper permissions
"""
        
        with patch.object(agent, '_call_ollama', return_value=mock_response):
            result = agent._solution_generator_agent(state)
        
        assert result["solution"] != ""
        assert len(result["commands"]) > 0
        assert result["prevention"] != ""