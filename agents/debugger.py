"""
Pipeline Debugger Agent - Multi-agent system for debugging data pipelines.
Uses LangGraph for agent orchestration.
"""

import httpx
from typing import Dict, Any, List, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from config.settings import Settings


class DebuggerState(TypedDict):
    """State shared across all debugger agents."""
    
    messages: Annotated[List[BaseMessage], add_messages]
    error_log: str
    dag_code: str
    error_type: str
    root_cause: str
    solution: str
    commands: List[str]
    prevention: str


class PipelineDebuggerAgent:
    """Multi-agent system for debugging data pipeline errors."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the Pipeline Debugger Agent.
        
        Args:
            settings: Application settings with LLM configuration
        """
        self.settings = settings
        self.graph = self._build_graph()
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            LLM response
        """
        try:
            response = httpx.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={
                    "model": self.settings.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120.0
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        
        except Exception as e:
            raise Exception(f"Error calling Ollama: {str(e)}")
    
    def _log_analyzer_agent(self, state: DebuggerState) -> DebuggerState:
        """
        Agent 1: Analyze error logs to identify error type.
        
        Args:
            state: Current debugger state
            
        Returns:
            Updated state with error type
        """
        prompt = f"""You are a log analysis expert. Analyze this error log and identify the error type.

Error Log:
{state['error_log']}

Identify:
1. Error type (e.g., PermissionError, ImportError, ConnectionError, etc.)
2. The exact error message
3. Which component/file is failing

Respond in this format:
Error Type: [type]
Error Message: [message]
Failing Component: [component]

Analysis:"""
        
        response = self._call_ollama(prompt)
        
        # Extract error type (improved parsing)
        error_type = "Unknown"
        
        # Try multiple patterns
        for line in response.split('\n'):
            line_clean = line.strip()
            
            # Pattern 1: "Error Type: PermissionError"
            if 'error type:' in line_clean.lower():
                error_type = line_clean.split(':', 1)[1].strip()
                break
            
            # Pattern 2: Direct mention of known error types
            known_errors = ['PermissionError', 'ImportError', 'ConnectionError', 
                           'FileNotFoundError', 'ValueError', 'KeyError', 
                           'TypeError', 'AttributeError', 'ModuleNotFoundError']
            for err in known_errors:
                if err in line_clean:
                    error_type = err
                    break
            
            if error_type != "Unknown":
                break
        
        # Fallback: search in original log
        if error_type == "Unknown":
            for line in state['error_log'].split('\n'):
                for err in ['PermissionError', 'ImportError', 'ConnectionError', 
                           'FileNotFoundError', 'ValueError', 'KeyError']:
                    if err in line:
                        error_type = err
                        break
        
        state['error_type'] = error_type
        state['messages'].append(AIMessage(content=f"Log Analyzer: Identified {error_type}"))
        
        return state
    
    def _code_checker_agent(self, state: DebuggerState) -> DebuggerState:
        """
        Agent 2: Check DAG code for issues related to the error.
        
        Args:
            state: Current debugger state
            
        Returns:
            Updated state with root cause
        """
        prompt = f"""You are a code review expert. Given this error type and DAG code, identify the root cause.

Error Type: {state['error_type']}
Error Log: {state['error_log']}

DAG Code:
{state['dag_code']}

Analyze the code and identify:
1. What is causing this error?
2. Which line(s) of code are problematic?
3. Why is this happening?

Root Cause Analysis:"""
        
        response = self._call_ollama(prompt)
        
        state['root_cause'] = response.strip()
        state['messages'].append(AIMessage(content=f"Code Checker: {response[:100]}..."))
        
        return state
    
    def _solution_generator_agent(self, state: DebuggerState) -> DebuggerState:
        """
        Agent 3: Generate solution with commands and explanation.
        
        Args:
            state: Current debugger state
            
        Returns:
            Updated state with solution
        """
        prompt = f"""You are a DevOps/Data Engineering expert. Given this error analysis, provide a solution.

Error Type: {state['error_type']}
Root Cause: {state['root_cause']}
Error Log: {state['error_log']}

Provide:
1. Step-by-step solution
2. Exact commands to fix the issue
3. Explanation of why this fixes the problem
4. How to prevent this in the future

Format your response as:
SOLUTION:
[step by step]

COMMANDS:
[command 1]
[command 2]

EXPLANATION:
[why this works]

PREVENTION:
[how to avoid this]

Solution:"""
        
        response = self._call_ollama(prompt)
        
        # Parse response (simple extraction)
        solution = ""
        commands = []
        prevention = ""
        
        current_section = None
        for line in response.split('\n'):
            line_upper = line.strip().upper()
            
            if 'SOLUTION:' in line_upper:
                current_section = 'solution'
            elif 'COMMANDS:' in line_upper or 'COMMAND:' in line_upper:
                current_section = 'commands'
            elif 'PREVENTION:' in line_upper:
                current_section = 'prevention'
            elif line.strip():
                if current_section == 'solution':
                    solution += line + "\n"
                elif current_section == 'commands':
                    if line.strip().startswith(('-', '*', '`')):
                        cmd = line.strip().lstrip('-*`').strip()
                        if cmd:
                            commands.append(cmd)
                    elif not line.strip().upper().startswith(('EXPLANATION', 'WHY')):
                        commands.append(line.strip())
                elif current_section == 'prevention':
                    prevention += line + "\n"
        
        state['solution'] = solution.strip() if solution else response
        state['commands'] = commands if commands else ["# See solution above"]
        state['prevention'] = prevention.strip() if prevention else "Review code before deployment"
        state['messages'].append(AIMessage(content="Solution Generator: Generated fix"))
        
        return state
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for multi-agent debugging.
        
        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(DebuggerState)
        
        # Add nodes (agents)
        workflow.add_node("log_analyzer", self._log_analyzer_agent)
        workflow.add_node("code_checker", self._code_checker_agent)
        workflow.add_node("solution_generator", self._solution_generator_agent)
        
        # Define edges (workflow)
        workflow.set_entry_point("log_analyzer")
        workflow.add_edge("log_analyzer", "code_checker")
        workflow.add_edge("code_checker", "solution_generator")
        workflow.add_edge("solution_generator", END)
        
        # Compile
        return workflow.compile()
    
    def debug_pipeline(self, error_log: str, dag_code: str = "") -> Dict[str, Any]:
        """
        Debug a pipeline error using multi-agent workflow.
        
        Args:
            error_log: Error log from pipeline failure
            dag_code: Optional DAG code for analysis
            
        Returns:
            Dictionary containing diagnosis and solution
        """
        try:
            # Initialize state
            initial_state: DebuggerState = {
                "messages": [HumanMessage(content="Debug this pipeline error")],
                "error_log": error_log,
                "dag_code": dag_code or "# No DAG code provided",
                "error_type": "",
                "root_cause": "",
                "solution": "",
                "commands": [],
                "prevention": ""
            }
            
            # Run multi-agent workflow
            final_state = self.graph.invoke(initial_state)
            
            return {
                "success": True,
                "error_log": error_log,
                "diagnosis": {
                    "error_type": final_state.get("error_type", "Unknown"),
                    "root_cause": final_state.get("root_cause", "Unable to determine")
                },
                "solution": {
                    "steps": final_state.get("solution", ""),
                    "commands": final_state.get("commands", []),
                    "explanation": final_state.get("solution", "")
                },
                "prevention": final_state.get("prevention", ""),
                "agent_workflow": [msg.content for msg in final_state.get("messages", [])]
            }
        
        except Exception as e:
            return {
                "success": False,
                "error_log": error_log,
                "error": str(e),
                "diagnosis": {},
                "solution": {}
            }


def main():
    """Test the Pipeline Debugger Agent."""
    from config.settings import load_settings
    
    settings = load_settings()
    agent = PipelineDebuggerAgent(settings)
    
    # Test error log
    error_log = """
[2026-01-25 10:30:45] ERROR - Task 'extract_data' failed
Traceback (most recent call last):
  File "/opt/airflow/dags/etl_pipeline.py", line 45, in extract_data
    with open('/opt/airflow/data/raw/events.csv', 'r') as f:
PermissionError: [Errno 13] Permission denied: '/opt/airflow/data/raw/events.csv'
"""
    
    dag_code = """
from airflow import DAG
from airflow.operators.python import PythonOperator

def extract_data():
    with open('/opt/airflow/data/raw/events.csv', 'r') as f:
        data = f.read()
    return data

dag = DAG('etl_pipeline', schedule_interval='@daily')
task = PythonOperator(task_id='extract_data', python_callable=extract_data, dag=dag)
"""
    
    print("Debugging pipeline error...")
    print("-" * 80)
    
    result = agent.debug_pipeline(error_log, dag_code)
    
    if result["success"]:
        print(f"\n🔍 Diagnosis:")
        print(f"  Error Type: {result['diagnosis']['error_type']}")
        print(f"  Root Cause: {result['diagnosis']['root_cause'][:200]}...")
        
        print(f"\n✅ Solution:")
        print(f"  {result['solution']['steps'][:300]}...")
        
        print(f"\n💻 Commands:")
        for cmd in result['solution']['commands']:
            print(f"  - {cmd}")
        
        print(f"\n🛡️ Prevention:")
        print(f"  {result['prevention'][:200]}...")
        
        print(f"\n🤖 Agent Workflow:")
        for step in result['agent_workflow']:
            print(f"  - {step}")
    else:
        print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    main()