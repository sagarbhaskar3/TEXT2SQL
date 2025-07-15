# models/hybrid_sql_generator.py - Updated for Gemini 2.5
import google.generativeai as genai
import ollama
import os
import logging
import json
import re
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class HybridSQLGenerator:
    """
    Simplified SQL generator: Google Gemini 2.5 primary + Ollama fallback
    No caching or pattern matching for now
    """
    
    def __init__(self):
        # Initialize Gemini 2.5 (primary)
        self.gemini_client = None
        self._initialize_gemini()
        
        # Initialize Ollama (fallback)
        self.ollama_model = None
        self._initialize_ollama()
        
        # Simple performance tracking
        self.stats = {
            'gemini_calls': 0,
            'ollama_calls': 0,
            'total_queries': 0,
            'successful_queries': 0
        }
    
    def _initialize_gemini(self):
        """Initialize Google Gemini 2.5 client"""
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.warning("⚠️ GOOGLE_API_KEY not found in environment")
                return
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Initialize the model
            self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Test connection with minimal request
            test_response = self.gemini_client.generate_content("test", stream=False)
            
            logger.info("✅ Google Gemini 2.5 client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Gemini initialization failed: {e}")
            self.gemini_client = None
    
    def _initialize_ollama(self):
        """Initialize Ollama as fallback"""
        try:
            models = ollama.list()
            available_models = [model['name'] for model in models.get('models', [])]
            
            # Prefer lightweight, reliable models
            preferred_models = ['llama3:latest', 'mistral:latest', 'codellama:latest']
            
            for model in preferred_models:
                if model in available_models:
                    self.ollama_model = model
                    logger.info(f"✅ Ollama fallback ready: {model}")
                    break
            
            if not self.ollama_model:
                logger.warning("⚠️ No suitable Ollama model found for fallback")
                
        except Exception as e:
            logger.warning(f"⚠️ Ollama fallback initialization failed: {e}")
    
    def _generate_with_gemini(self, query: str, context: str, mappings: Dict) -> Optional[str]:
        """Generate SQL using Google Gemini 2.5"""
        
        if not self.gemini_client:
            logger.warning("Gemini client not available")
            return None
        
        try:
            # Build prompt using your context and mappings
            prompt = self._build_gemini_prompt(query, context, mappings)
            
            logger.info("🤖 Generating SQL with Google Gemini 2.5...")
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=500,
                top_p=0.8,
                top_k=40
            )
            
            # Configure safety settings to be less restrictive for code generation
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=False
            )
            
            raw_sql = response.text
            cleaned_sql = self._extract_and_clean_sql(raw_sql)
            
            if cleaned_sql:
                self.stats['gemini_calls'] += 1
                logger.info("✅ Gemini SQL generation successful")
                return cleaned_sql
            else:
                logger.warning("❌ Gemini returned invalid SQL")
                return None
                
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {e}")
            return None
    
    def _generate_with_ollama(self, query: str, context: str) -> Optional[str]:
        """Generate SQL using Ollama as fallback"""
        
        if not self.ollama_model:
            logger.warning("Ollama model not available")
            return None
        
        try:
            # Simplified prompt for Ollama
            prompt = f"""Generate a ClickHouse SQL query for: {query}

Context: {context[:500] if context else 'No context available'}

Focus on these tables:
- fct_pharmacy_clear_claim_allstatus_cluster_brand (prescriptions)
- as_providers_v1 (providers)
- as_lsf_v1 (payments)

Return only SQL, no explanations:"""

            logger.info(f"🔄 Fallback to Ollama ({self.ollama_model})...")
            
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'num_predict': 300,
                    'timeout': 15  # Increased timeout
                }
            )
            
            raw_sql = response.get('response', '')
            cleaned_sql = self._extract_and_clean_sql(raw_sql)
            
            if cleaned_sql:
                self.stats['ollama_calls'] += 1
                logger.info("✅ Ollama fallback successful")
                return cleaned_sql
            else:
                logger.warning("❌ Ollama returned invalid SQL")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ollama fallback failed: {e}")
            return None
    
    def _build_gemini_prompt(self, query: str, context: str, mappings: Dict) -> str:
        """Build optimized prompt for Gemini using your context and mappings"""
        
        # Extract entities from your mappings format
        entities_info = []
        for entity_type, entity_data in mappings.items():
            if isinstance(entity_data, dict) and 'values' in entity_data:
                values = entity_data['values']
                if values:
                    entities_info.append(f"{entity_type}: {', '.join(values)}")
        
        entities_str = "; ".join(entities_info) if entities_info else "None identified"
        
        prompt = f"""You are a healthcare data expert. Generate a precise ClickHouse SQL query for this healthcare question.

QUESTION: {query}

ENTITIES IDENTIFIED: {entities_str}

RETRIEVED CONTEXT:
{context[:1000] if context else 'No context available'}

KEY TABLES AND COLUMNS:
- fct_pharmacy_clear_claim_allstatus_cluster_brand: 
  * NDC_PREFERRED_BRAND_NM (drug names)
  * PRESCRIBER_NPI_NM (prescriber names)
  * PRESCRIBER_NPI_STATE_CD (state codes)
  
- as_providers_v1: 
  * type_1_npi, first_name, last_name
  * specialties (Array), states (Array)
  
- as_lsf_v1: 
  * type_1_npi, life_science_firm_name, amount, year

- mf_providers: 
  * npi, name, primaryOrgName, score

CLICKHOUSE REQUIREMENTS:
1. Arrays are 1-indexed: specialties[1], states[1]
2. Use ilike for case-insensitive matching
3. Include LIMIT 10 for top results
4. Proper JOINs on type_1_npi or npi fields
5. Return ONLY the SQL query, no explanations

Generate the SQL query:"""

        return prompt
    
    def _extract_and_clean_sql(self, raw_sql: str) -> str:
        """Extract and clean SQL from model response"""
        if not raw_sql:
            return ""
        
        # Remove markdown and code blocks
        sql = re.sub(r'```sql\s*', '', raw_sql)
        sql = re.sub(r'```\s*', '', sql)
        
        # Find SQL statements
        lines = sql.strip().split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip comments and explanations
            if line and not line.startswith('#') and not line.startswith('--') and not line.startswith('/*'):
                sql_lines.append(line)
        
        cleaned_sql = ' '.join(sql_lines).strip()
        
        # Basic validation - must start with SQL keyword
        sql_keywords = ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE']
        if not any(cleaned_sql.upper().startswith(keyword) for keyword in sql_keywords):
            return ""
        
        # Ensure semicolon
        if cleaned_sql and not cleaned_sql.endswith(';'):
            cleaned_sql += ';'
        
        return cleaned_sql
    
    def generate_sql_simple(self, query: str, context: str, mappings: Dict) -> Tuple[str, str, float]:
        """
        Simple SQL generation method without caching or patterns
        
        Args:
            query: User's natural language query
            context: Retrieved context from your Weaviate/RAG system
            mappings: Entity mappings from your entity_mapper
            
        Returns:
            Tuple of (sql, generation_source, confidence)
        """
        
        self.stats['total_queries'] += 1
        start_time = time.time()
        
        logger.info(f"🔍 Processing query: {query}")
        
        # Try Gemini first (primary method)
        if gemini_sql := self._generate_with_gemini(query, context, mappings):
            elapsed = time.time() - start_time
            self.stats['successful_queries'] += 1
            logger.info(f"🤖 Gemini generation successful! ({elapsed:.3f}s)")
            return gemini_sql, "gemini_generated", 0.85
        
        # Try Ollama fallback 
        if ollama_sql := self._generate_with_ollama(query, context):
            elapsed = time.time() - start_time
            self.stats['successful_queries'] += 1
            logger.info(f"🔄 Ollama fallback successful! ({elapsed:.3f}s)")
            return ollama_sql, "ollama_fallback", 0.70
        
        # All methods failed
        elapsed = time.time() - start_time
        logger.error(f"❌ All SQL generation methods failed ({elapsed:.3f}s)")
        return "", "failed", 0.0
    
    def process_query_complete(self, query: str, classification: Dict, schema_context: str = "") -> Dict:
        """
        Complete query processing that integrates with your existing architecture
        Simplified version without caching/patterns
        """
        
        logger.info(f"🔍 Processing: {query}")
        
        try:
            # Convert your classification format to mappings format for processing
            mappings = classification.get('entities', {})
            
            # Use schema_context if provided, otherwise use empty context
            context = schema_context or ""
            
            # Include HyDE examples in context if provided
            hyde_examples = classification.get('hyde_examples', [])
            if hyde_examples:
                hyde_context = "\n\nHyDE SQL Examples:\n" + "\n".join(hyde_examples)
                context += hyde_context
            
            # Generate SQL using simple approach
            sql, source, confidence = self.generate_sql_simple(query, context, mappings)
            
            if not sql:
                return {
                    'sql': '',
                    'confidence': 0.0,
                    'source': 'failed',
                    'success': False,
                    'error': 'SQL generation failed - both Gemini and Ollama failed'
                }
            
            return {
                'sql': sql,
                'confidence': confidence,
                'source': source,
                'query_type': classification.get('query_type'),
                'success': True,
                'stats': self.get_performance_stats()
            }
            
        except Exception as e:
            logger.error(f"❌ Complete processing failed: {e}")
            return {
                'sql': '',
                'confidence': 0.0,
                'source': 'error',
                'success': False,
                'error': str(e)
            }
    
    def get_performance_stats(self) -> Dict:
        """Get simple performance statistics"""
        total = self.stats['total_queries']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'success_rate': self.stats['successful_queries'] / total,
            'gemini_usage_rate': self.stats['gemini_calls'] / total,
            'ollama_usage_rate': self.stats['ollama_calls'] / total
        }
    
    # For backward compatibility, keep the openai_client property
    @property
    def openai_client(self):
        """Backward compatibility property - returns Gemini client"""
        return self.gemini_client