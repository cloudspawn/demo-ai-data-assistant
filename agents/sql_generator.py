"""
SQL Generator Agent - Converts natural language questions to SQL queries.
"""

import duckdb
import httpx
from pathlib import Path
from typing import Dict, Any, List
from config.settings import Settings


class SQLGeneratorAgent:
    """Agent that generates SQL queries from natural language questions."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the SQL Generator Agent.
        
        Args:
            settings: Application settings with LLM and database configuration
        """
        self.settings = settings
        self.db_path = settings.project_root / settings.duckdb_path
        
    def _get_database_schema(self) -> str:
        """
        Extract schema information from DuckDB database.
        
        Returns:
            Formatted schema description as string
        """
        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            
            # Get all tables
            tables = conn.execute("SHOW TABLES").fetchall()
            
            schema_info = []
            for table in tables:
                table_name = table[0]
                
                # Get columns for each table
                columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                
                column_info = []
                for col in columns:
                    col_name, col_type = col[0], col[1]
                    column_info.append(f"  - {col_name}: {col_type}")
                
                schema_info.append(f"Table: {table_name}\n" + "\n".join(column_info))
            
            conn.close()
            
            return "\n\n".join(schema_info)
        
        except Exception as e:
            return f"Error reading schema: {str(e)}"
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API to generate SQL.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Generated SQL query
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
    
    def _extract_sql_from_response(self, response: str) -> str:
        """
        Extract SQL query from LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned SQL query
        """
        # Remove markdown code blocks if present
        sql = response.strip()
        
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0]
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0]
        
        return sql.strip()
    
    def _execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query on DuckDB database.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Query results as list of dictionaries
        """
        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            result = conn.execute(sql).fetchall()
            columns = [desc[0] for desc in conn.description]
            conn.close()
            
            # Convert to list of dicts
            return [dict(zip(columns, row)) for row in result]
        
        except Exception as e:
            raise Exception(f"Error executing SQL: {str(e)}")
    
    def generate_and_execute(self, question: str) -> Dict[str, Any]:
        """
        Generate SQL from natural language question and execute it.
        
        Args:
            question: Natural language question about the data
            
        Returns:
            Dictionary containing SQL, results, and explanation
        """
        # Step 1: Get database schema
        schema = self._get_database_schema()
        
        # Step 2: Build prompt for LLM
        prompt = f"""You are a SQL expert. Given the following database schema, generate a valid DuckDB SQL query to answer the user's question.

Database Schema:
{schema}

User Question: {question}

Requirements:
- Generate ONLY the SQL query, no explanation
- Use DuckDB syntax
- Ensure the query is valid and safe (read-only)
- Do not use DELETE, DROP, or INSERT statements

SQL Query:"""
        
        # Step 3: Call LLM to generate SQL
        llm_response = self._call_ollama(prompt)
        sql = self._extract_sql_from_response(llm_response)
        
        # Step 4: Execute SQL
        try:
            results = self._execute_sql(sql)
            
            # Step 5: Generate explanation
            explanation_prompt = f"""Explain this SQL query in simple terms:

{sql}

Provide a brief 1-2 sentence explanation of what this query does."""
            
            explanation = self._call_ollama(explanation_prompt)
            
            return {
                "success": True,
                "question": question,
                "sql": sql,
                "results": results,
                "row_count": len(results),
                "explanation": explanation.strip()
            }
        
        except Exception as e:
            return {
                "success": False,
                "question": question,
                "sql": sql,
                "error": str(e),
                "results": []
            }


def main():
    """Test the SQL Generator Agent."""
    from config.settings import load_settings
    
    settings = load_settings()
    agent = SQLGeneratorAgent(settings)
    
    # Test question
    question = "Show me all tables in the database"
    
    print(f"Question: {question}")
    print("-" * 80)
    
    result = agent.generate_and_execute(question)
    
    if result["success"]:
        print(f"\nGenerated SQL:\n{result['sql']}\n")
        print(f"Results ({result['row_count']} rows):")
        for row in result["results"][:5]:  # Show first 5 rows
            print(row)
        print(f"\nExplanation: {result['explanation']}")
    else:
        print(f"\nError: {result['error']}")
        print(f"Generated SQL:\n{result['sql']}")


if __name__ == "__main__":
    main()