# src/sql_generator.py
import requests
import os
from typing import Optional, Dict, Any
import time

from rag_system import HealthcareRAGSystem

class DefogSQLGenerator:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        self.model_url = "https://api-inference.huggingface.co/models/defog/sqlcoder-7b"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
    
    def generate_sql(self, enhanced_prompt: str) -> str:
        """Generate SQL using defog/sqlcoder-7b"""
        
        payload = {
            "inputs": enhanced_prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.1,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(
                self.model_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract generated SQL
                if isinstance(result, list) and len(result) > 0:
                    generated_sql = result[0].get("generated_text", "")
                else:
                    generated_sql = str(result)
                
                # Clean up SQL
                sql = self._clean_sql(generated_sql)
                return sql
            
            elif response.status_code == 503:
                return "-- Model is loading, please try again in a few minutes"
            else:
                return f"-- Error: {response.status_code}"
                
        except Exception as e:
            return f"-- Error: {str(e)}"
    
    def _clean_sql(self, raw_sql: str) -> str:
        """Clean and format generated SQL"""
        
        sql = raw_sql.strip()
        
        # Remove markdown if present
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0]
        elif "```" in sql:
            sql = sql.split("```")[1]
        
        # Basic cleanup
        sql = sql.strip()
        if not sql.endswith(";"):
            sql += ";"
        
        return sql

class HealthcareSQLSystem:
    def __init__(self, chroma_directory: str = "./knowledge_base"):
        self.rag_system = HealthcareRAGSystem(chroma_directory)
        self.sql_generator = DefogSQLGenerator()
    
    def process_query(self, user_query: str) -> dict[str, any]:
        """Complete pipeline: Query -> RAG -> Enhanced Prompt -> SQL"""
        
        print(f"🔍 Processing: {user_query}")
        
        # Step 1: Retrieve context using RAG
        print("📚 Retrieving context...")
        context = self.rag_system.retrieve_context(user_query)
        
        # Step 2: Build enhanced prompt
        print("🔨 Building enhanced prompt...")
        enhanced_prompt = self.rag_system.build_context_prompt(user_query, context)
        
        # Step 3: Generate SQL
        print("🤖 Generating SQL...")
        sql = self.sql_generator.generate_sql(enhanced_prompt)
        
        return {
            "user_query": user_query,
            "sql": sql,
            "context": context,
            "enhanced_prompt": enhanced_prompt
        }