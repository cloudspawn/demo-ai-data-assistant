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
    
    def _parse_checks_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response to extract quality checks.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            List of quality check suggestions
        """
        # Simple parsing - in production, use structured output
        checks = []
        lines = response.strip().split('\n')
        
        current_check = {}
        for line in lines:
            line = line.strip()
            
            if line.startswith('- ') or line.startswith('* '):
                # New check item
                if current_check:
                    checks.append(current_check)
                current_check = {"description": line[2:].strip()}
            
            elif ':' in line and current_check:
                # Property of current check
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                current_check[key] = value.strip()
        
        # Add last check
        if current_check:
            checks.append(current_check)
        
        return checks if checks else [{"description": response, "type": "general"}]
    
    def suggest_checks(self, table_name: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate quality check suggestions for a table schema.
        
        Args:
            table_name: Name of the table
            schema: Dictionary mapping column names to data types
            
        Returns:
            Dictionary containing quality check suggestions
        """
        # Build schema description
        schema_description = f"Table: {table_name}\nColumns:\n"
        for col_name, col_type in schema.items():
            schema_description += f"  - {col_name}: {col_type}\n"
        
        # Build prompt
        prompt = f"""You are a data quality expert. Given the following database table schema, suggest data quality checks.

{schema_description}

For each column, suggest:
1. Null checks (should it allow nulls?)
2. Value range checks (min/max, allowed values)
3. Format checks (patterns, constraints)
4. Relationship checks (foreign keys, uniqueness)

Provide practical, actionable quality checks. Format each check as:
- Check name: [name]
  Column: [column_name]
  Type: [null_check, range_check, format_check, uniqueness_check]
  Description: [what to check]
  Severity: [critical, high, medium, low]
  Python code: [example assertion or check]

Generate quality checks:"""
        
        try:
            # Call LLM
            llm_response = self._call_ollama(prompt)
            
            # Parse response
            checks = self._parse_checks_response(llm_response)
            
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
                "schema": schema,
                "checks": enhanced_checks,
                "check_count": len(enhanced_checks),
                "raw_response": llm_response
            }
        
        except Exception as e:
            return {
                "success": False,
                "table_name": table_name,
                "schema": schema,
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
    schema = {
        "event_date": "DATE",
        "city": "VARCHAR",
        "category": "VARCHAR",
        "event_count": "INTEGER",
        "avg_value": "DOUBLE"
    }
    
    print(f"Generating quality checks for: {table_name}")
    print("-" * 80)
    
    result = agent.suggest_checks(table_name, schema)
    
    if result["success"]:
        print(f"\n✅ Generated {result['check_count']} quality checks:\n")
        for check in result["checks"]:
            print(f"Check: {check['check_name']}")
            print(f"  Column: {check['column']}")
            print(f"  Type: {check['check_type']}")
            print(f"  Severity: {check['severity']}")
            print(f"  Description: {check['description']}")
            print()
    else:
        print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    main()