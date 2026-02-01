"""
Quality Checker Agent - Generates data quality check suggestions.
"""

import httpx
from typing import Dict, Any, List
from config.settings import Settings


class QualityCheckerAgent:
    """Agent that generates data quality check suggestions from table schemas."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the Quality Checker Agent.
        
        Args:
            settings: Application settings with LLM configuration
        """
        self.settings = settings
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API to generate quality checks.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Generated quality check suggestions
        """
        try:
            response = httpx.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={
                    "model": self.settings.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60.0
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        
        except Exception as e:
            raise Exception(f"Error calling Ollama: {str(e)}")
    
    def _parse_checks_response_v2(self, response: str) -> List[Dict[str, Any]]:
        """
        Improved parser for LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            List of quality check suggestions
        """
        checks = []
        lines = response.strip().split('\n')
        
        current_check = {}
        in_code_block = False
        code_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines between checks
            if not line:
                if current_check and 'description' in current_check:
                    # Save accumulated code
                    if code_lines:
                        current_check['python_code'] = '\n'.join(code_lines).strip()
                    checks.append(current_check)
                    current_check = {}
                    code_lines = []
                    in_code_block = False
                continue
            
            # New check marker
            if line.upper().startswith('CHECK'):
                if current_check and 'description' in current_check:
                    if code_lines:
                        current_check['python_code'] = '\n'.join(code_lines).strip()
                    checks.append(current_check)
                    current_check = {}
                    code_lines = []
                    in_code_block = False
                continue
            
            # Parse fields
            if ':' in line:
                parts = line.split(':', 1)
                key = parts[0].strip().lower()
                value = parts[1].strip()
                
                if 'check name' in key or 'name' in key:
                    current_check['check_name'] = value
                    in_code_block = False
                elif 'column' in key:
                    current_check['column'] = value
                    in_code_block = False
                elif 'type' in key:
                    current_check['type'] = value
                    in_code_block = False
                elif 'severity' in key:
                    current_check['severity'] = value.lower()
                    in_code_block = False
                elif 'description' in key:
                    current_check['description'] = value
                    in_code_block = False
                elif 'python code' in key or 'code' in key:
                    in_code_block = True
                    if value and value != ':':
                        code_lines.append(value)
            
            # Collect code lines
            elif in_code_block:
                # Skip markdown code blocks
                if line.startswith('```'):
                    continue
                # Add actual code lines
                if line and not line.startswith('#'):
                    code_lines.append(line)
        
        # Don't forget last check
        if current_check and 'description' in current_check:
            if code_lines:
                current_check['python_code'] = '\n'.join(code_lines).strip()
            checks.append(current_check)
        
        return checks if checks else [{"description": response, "type": "general"}]
    
    def suggest_checks(self, table_name: str, table_schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate quality check suggestions for a table schema.
        
        Args:
            table_name: Name of the table
            table_schema: Dictionary mapping column names to data types
            
        Returns:
            Dictionary containing quality check suggestions
        """
        # Build schema description
        schema_description = f"Table: {table_name}\nColumns:\n"
        for col_name, col_type in table_schema.items():
            schema_description += f"  - {col_name}: {col_type}\n"
        
        # Build prompt - SIMPLIFIÉ et PLUS CLAIR
        prompt = f"""You are a data quality expert. Analyze this table schema and suggest quality checks.

{schema_description}

For each column, suggest specific quality checks with Python code.

Return your suggestions in this EXACT format (one check per block):

CHECK 1:
Check name: event_date_not_null
Column: event_date
Type: null_check
Severity: critical
Description: Event date should never be NULL
Python code: assert df['event_date'].notna().all()

CHECK 2:
Check name: event_count_positive
Column: event_count
Type: range_check
Severity: high
Description: Event count must be greater than 0
Python code: assert (df['event_count'] > 0).all()

Now generate quality checks for this table:"""
        
        try:
            # Call LLM
            llm_response = self._call_ollama(prompt)
            
            # Parse response with improved parser
            checks = self._parse_checks_response_v2(llm_response)
            
            # Enhance checks with default structure
            enhanced_checks = []
            for i, check in enumerate(checks):
                enhanced_check = {
                    "check_id": f"{table_name}_check_{i+1}",
                    "table_name": table_name,
                    "check_name": check.get("check_name", f"check_{i+1}"),
                    "column": check.get("column", "multiple"),
                    "check_type": check.get("type", "general"),
                    "description": check.get("description", "Quality check"),
                    "severity": check.get("severity", "medium"),
                    "python_code": check.get("python_code", "# Check implementation needed"),
                    "raw_suggestion": check
                }
                enhanced_checks.append(enhanced_check)
            
            return {
                "success": True,
                "table_name": table_name,
                "table_schema": table_schema,
                "checks": enhanced_checks,
                "check_count": len(enhanced_checks),
                "raw_response": llm_response
            }
        
        except Exception as e:
            return {
                "success": False,
                "table_name": table_name,
                "table_schema": table_schema,
                "error": str(e),
                "checks": []
            }


def main():
    """Test the Quality Checker Agent."""
    from config.settings import load_settings
    
    settings = load_settings()
    agent = QualityCheckerAgent(settings)
    
    # Test schema
    table_name = "analytics_events_daily"
    table_schema = {
        "event_date": "DATE",
        "city": "VARCHAR",
        "category": "VARCHAR",
        "event_count": "INTEGER",
        "avg_value": "DOUBLE"
    }
    
    print(f"Generating quality checks for: {table_name}")
    print("-" * 80)
    
    result = agent.suggest_checks(table_name, table_schema)
    
    if result["success"]:
        print(f"\n✅ Generated {result['check_count']} quality checks:\n")
        for check in result["checks"]:
            print(f"Check: {check['check_name']}")
            print(f"  Column: {check['column']}")
            print(f"  Type: {check['check_type']}")
            print(f"  Severity: {check['severity']}")
            print(f"  Description: {check['description']}")
            print(f"  Python code: {check['python_code']}")
            print()
    else:
        print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    main()