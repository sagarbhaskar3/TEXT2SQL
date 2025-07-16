# models/hybrid_sql_generator.py - Updated with Prompt Integration
import google.generativeai as genai
import ollama
import os
import logging
import re
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

from config.prompts import PromptBuilder
from config.app_config import AI_CONFIG

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class HybridSQLGenerator:
    """
    Enhanced SQL generator with rule-based system for healthcare queries
    Supports multi-table joins, multi-constraint queries, and accurate intent understanding
    """
    
    def __init__(self):
        # Initialize Gemini 2.5 (primary)
        self.gemini_client = None
        self._initialize_gemini()
        
        # Initialize Ollama (fallback)
        self.ollama_model = None
        self._initialize_ollama()
        
        # Initialize prompt builder
        self.prompt_builder = PromptBuilder()
        
        # Initialize healthcare-specific rules
        self.healthcare_rules = self._initialize_healthcare_rules()
        self.table_relationships = self._initialize_table_relationships()
        
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
            api_key = AI_CONFIG['google_api_key']
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
            preferred_models = AI_CONFIG['preferred_ollama_models']
            
            for model in preferred_models:
                if model in available_models:
                    self.ollama_model = model
                    logger.info(f"✅ Ollama fallback ready: {model}")
                    break
            
            if not self.ollama_model:
                logger.warning("⚠️ No suitable Ollama model found for fallback")
                
        except Exception as e:
            logger.warning(f"⚠️ Ollama fallback initialization failed: {e}")
    
    def _initialize_healthcare_rules(self) -> Dict:
        """Initialize healthcare-specific SQL generation rules"""
        return {
            "table_priorities": {
                "prescription_queries": ["fct_pharmacy_clear_claim_allstatus_cluster_brand", "as_providers_v1"],
                "procedure_queries": ["as_providers_referrals_v2", "as_providers_v1"],
                "payment_queries": ["as_lsf_v1", "as_providers_v1"],
                "kol_queries": ["mf_providers", "mf_scores", "mf_conditions"],
                "facility_queries": ["as_providers_referrals_v2", "as_providers_v1"],
                "complex_queries": ["as_providers_v1", "fct_pharmacy_clear_claim_allstatus_cluster_brand", "as_lsf_v1", "as_providers_referrals_v2"]
            },
            "intent_patterns": {
                "top_ranking": ["top", "best", "highest", "most", "leading"],
                "procedure_focus": ["procedure", "surgery", "operation", "treatment", "performed"],
                "prescription_focus": ["prescrib", "drug", "medication", "pharmaceutical"],
                "payment_focus": ["payment", "paid", "compensation", "financial"],
                "facility_focus": ["asc", "ambulatory", "surgical center", "hospital", "facility", "clinic"],
                "provider_focus": ["hcp", "doctor", "physician", "provider", "prescriber"],
                "analysis_focus": ["analysis", "comprehensive", "detailed", "performance", "compare"]
            },
            "constraint_types": {
                "location": ["state", "city", "region", "area"],
                "temporal": ["year", "month", "date", "time", "period"],
                "specialty": ["specialty", "specialization", "department"],
                "volume": ["volume", "count", "number", "quantity"],
                "financial": ["amount", "cost", "payment", "charge", "revenue"]
            }
        }
    
    def _initialize_table_relationships(self) -> Dict:
        """Initialize table relationships for proper joins"""
        return {
            "as_providers_v1": {
                "primary_key": "type_1_npi",
                "joins": {
                    "fct_pharmacy_clear_claim_allstatus_cluster_brand": "toString(type_1_npi) = PRESCRIBER_NPI_NBR",
                    "as_lsf_v1": "type_1_npi = type_1_npi",
                    "as_providers_referrals_v2": "type_1_npi = primary_type_1_npi"
                },
                "key_columns": ["first_name", "last_name", "specialties[1]", "states[1]", "cities[1]"],
                "array_columns": ["specialties", "states", "cities", "hospital_names"]
            },
            "fct_pharmacy_clear_claim_allstatus_cluster_brand": {
                "primary_key": "PATIENT_ID",
                "joins": {
                    "as_providers_v1": "PRESCRIBER_NPI_NBR = toString(type_1_npi)"
                },
                "key_columns": ["NDC_PREFERRED_BRAND_NM", "PRESCRIBER_NPI_NM", "PRESCRIBER_NPI_STATE_CD", "SERVICE_DATE_DD"],
                "array_columns": []
            },
            "as_lsf_v1": {
                "primary_key": "type_1_npi",
                "joins": {
                    "as_providers_v1": "type_1_npi = type_1_npi"
                },
                "key_columns": ["life_science_firm_name", "product_name", "amount", "year", "nature_of_payment"],
                "array_columns": []
            },
            "as_providers_referrals_v2": {
                "primary_key": "primary_type_1_npi",
                "joins": {
                    "as_providers_v1": "primary_type_1_npi = type_1_npi"
                },
                "key_columns": ["primary_hospital_name", "procedure_code_description", "diagnosis_code_description", "primary_type_2_npi_state", "date"],
                "array_columns": []
            },
            "mf_providers": {
                "primary_key": "npi",
                "joins": {
                    "mf_scores": "npi = mf_providers_npi"
                },
                "key_columns": ["displayName", "score", "primaryOrgName", "sex"],
                "array_columns": []
            }
        }
    
    def _analyze_query_intent(self, query: str, entities: Dict) -> Dict:
        """Analyze query intent and determine appropriate SQL generation strategy"""
        query_lower = query.lower()
        
        # Determine primary intent
        intent_scores = {}
        for intent, patterns in self.healthcare_rules["intent_patterns"].items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "general"
        
        # Determine query type based on intent and entities
        if primary_intent in ["prescription_focus"] or any("drug" in str(entities.get(k, {})) for k in entities):
            query_type = "prescription_queries"
        elif primary_intent in ["procedure_focus"] or any("procedure" in str(entities.get(k, {})) for k in entities):
            query_type = "procedure_queries"
        elif primary_intent in ["payment_focus"]:
            query_type = "payment_queries"
        elif primary_intent in ["facility_focus"]:
            query_type = "facility_queries"
        elif "kol" in query_lower or "opinion leader" in query_lower:
            query_type = "kol_queries"
        elif primary_intent in ["analysis_focus"] or len(entities) > 2:
            query_type = "complex_queries"
        else:
            query_type = "complex_queries"
        
        # Identify constraints
        constraints = []
        for constraint_type, patterns in self.healthcare_rules["constraint_types"].items():
            if any(pattern in query_lower for pattern in patterns):
                constraints.append(constraint_type)
        
        # Determine if ranking is needed
        needs_ranking = any(pattern in query_lower for pattern in self.healthcare_rules["intent_patterns"]["top_ranking"])
        
        return {
            "primary_intent": primary_intent,
            "query_type": query_type,
            "constraints": constraints,
            "needs_ranking": needs_ranking,
            "complexity_level": len(constraints) + (2 if needs_ranking else 0),
            "recommended_tables": self.healthcare_rules["table_priorities"].get(query_type, [])
        }
    
    def _generate_with_gemini(self, query: str, context: str, mappings: Dict) -> Optional[str]:
        """Generate SQL using Google Gemini 2.5 with enhanced prompting"""
        
        if not self.gemini_client:
            logger.warning("Gemini client not available")
            return None
        
        try:
            # Analyze query intent
            intent_analysis = self._analyze_query_intent(query, mappings)
            
            # Build enhanced prompt using PromptBuilder
            prompt = self.prompt_builder.build_sql_generation_prompt(query, mappings, context, intent_analysis)
            
            logger.info(f"🤖 Generating SQL with Gemini (Intent: {intent_analysis['primary_intent']}, Complexity: {intent_analysis['complexity_level']})")
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Lower for more consistent SQL
                max_output_tokens=800,  # Increased for complex queries
                top_p=0.8,
                top_k=40
            )
            
            # Configure safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
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
    
    def _generate_with_ollama(self, query: str, context: str, mappings: Dict) -> Optional[str]:
        """Generate SQL using Ollama with enhanced prompting"""
        
        if not self.ollama_model:
            logger.warning("Ollama model not available")
            return None
        
        try:
            # Analyze query intent for Ollama
            intent_analysis = self._analyze_query_intent(query, mappings)
            
            # Build simplified prompt using PromptBuilder
            prompt = self.prompt_builder.build_ollama_prompt(query, mappings, intent_analysis)
            
            logger.info(f"🔄 Fallback to Ollama ({self.ollama_model})...")
            
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                options={
                    'temperature': 0.2,
                    'num_predict': 400,
                    'timeout': 20
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
    
    def _extract_and_clean_sql(self, raw_sql: str) -> str:
        """Extract and clean SQL from model response"""
        if not raw_sql:
            return ""
        
        # Remove markdown and code blocks
        sql = re.sub(r'```sql\s*', '', raw_sql)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove common prefixes
        sql = re.sub(r'^(Here\'s|Here is|The SQL query is:?)\s*', '', sql, flags=re.IGNORECASE)
        
        # Find SQL statements
        lines = sql.strip().split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip comments and explanations
            if line and not line.startswith('#') and not line.startswith('--') and not line.startswith('/*'):
                # Stop at explanation text
                if any(phrase in line.lower() for phrase in ['this query', 'explanation', 'note:', 'the above']):
                    break
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
        """Enhanced SQL generation with rule-based analysis"""
        
        self.stats['total_queries'] += 1
        start_time = time.time()
        
        logger.info(f"🔍 Processing query: {query}")
        
        # Analyze query intent for confidence scoring
        intent_analysis = self._analyze_query_intent(query, mappings)
        
        # Try Gemini first with enhanced prompting
        if gemini_sql := self._generate_with_gemini(query, context, mappings):
            elapsed = time.time() - start_time
            self.stats['successful_queries'] += 1
            
            # Calculate confidence based on intent analysis
            base_confidence = 0.85
            complexity_bonus = min(intent_analysis['complexity_level'] * 0.02, 0.10)
            entity_bonus = min(len(mappings) * 0.01, 0.05)
            
            confidence = base_confidence + complexity_bonus + entity_bonus
            
            logger.info(f"🤖 Gemini generation successful! ({elapsed:.3f}s, confidence: {confidence:.2f})")
            return gemini_sql, "gemini_generated", confidence
        
        # Try Ollama fallback with enhanced prompting
        if ollama_sql := self._generate_with_ollama(query, context, mappings):
            elapsed = time.time() - start_time
            self.stats['successful_queries'] += 1
            
            # Lower confidence for fallback
            base_confidence = 0.70
            complexity_bonus = min(intent_analysis['complexity_level'] * 0.01, 0.05)
            
            confidence = base_confidence + complexity_bonus
            
            logger.info(f"🔄 Ollama fallback successful! ({elapsed:.3f}s, confidence: {confidence:.2f})")
            return ollama_sql, "ollama_fallback", confidence
        
        # All methods failed
        elapsed = time.time() - start_time
        logger.error(f"❌ All SQL generation methods failed ({elapsed:.3f}s)")
        return "", "failed", 0.0
    
    def process_query_complete(self, query: str, classification: Dict, schema_context: str = "") -> Dict:
        """Complete query processing with enhanced rule-based analysis"""
        
        logger.info(f"🔍 Processing: {query}")
        
        try:
            # Convert classification format to mappings
            mappings = classification.get('entities', {})
            
            # Analyze query intent
            intent_analysis = self._analyze_query_intent(query, mappings)
            
            # Use schema_context if provided
            context = schema_context or ""
            
            # Include HyDE examples in context
            hyde_examples = classification.get('hyde_examples', [])
            if hyde_examples:
                hyde_context = "\n\nHyDE SQL Examples:\n" + "\n".join(hyde_examples)
                context += hyde_context
            
            # Generate SQL using enhanced approach
            sql, source, confidence = self.generate_sql_simple(query, context, mappings)
            
            if not sql:
                return {
                    'sql': '',
                    'confidence': 0.0,
                    'source': 'failed',
                    'success': False,
                    'error': 'SQL generation failed - both Gemini and Ollama failed',
                    'intent_analysis': intent_analysis
                }
            
            return {
                'sql': sql,
                'confidence': confidence,
                'source': source,
                'query_type': classification.get('query_type'),
                'success': True,
                'stats': self.get_performance_stats(),
                'intent_analysis': intent_analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Complete processing failed: {e}")
            return {
                'sql': '',
                'confidence': 0.0,
                'source': 'error',
                'success': False,
                'error': str(e),
                'intent_analysis': {}
            }
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        total = self.stats['total_queries']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'success_rate': self.stats['successful_queries'] / total,
            'gemini_usage_rate': self.stats['gemini_calls'] / total,
            'ollama_usage_rate': self.stats['ollama_calls'] / total
        }
    
    # For backward compatibility
    @property
    def openai_client(self):
        """Backward compatibility property - returns Gemini client"""
        return self.gemini_client