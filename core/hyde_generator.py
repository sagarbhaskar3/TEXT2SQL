# core/hyde_generator.py - Updated HyDE SQL Example Generator
import logging
from typing import List, Optional
from config.prompts import PromptBuilder
from config.app_config import PROCESSING_CONFIG

logger = logging.getLogger(__name__)

class HydeGenerator:
    """Generates HyDE (Hypothetical Document Embeddings) SQL examples"""
    
    def __init__(self, hybrid_generator):
        self.hybrid_generator = hybrid_generator
        self.prompt_builder = PromptBuilder()
        self.max_examples = PROCESSING_CONFIG['max_hyde_examples']
    
    def generate_hyde_examples(self, query: str, query_type: str, relevant_tables: List[str]) -> List[str]:
        """Generate HyDE SQL examples using enhanced rule-based approach"""
        try:
            logger.info("🔄 Generating HyDE SQL examples...")
            
            # Try advanced generation with Gemini if available
            if self.hybrid_generator.gemini_client:
                examples = self._generate_with_gemini(query, query_type, relevant_tables)
                if examples:
                    logger.info(f"✅ Generated {len(examples)} HyDE SQL examples via Gemini")
                    return examples
            
            # Fallback to enhanced templates
            logger.info("Using enhanced HyDE templates")
            examples = self._generate_template_examples(query, query_type, relevant_tables)
            
            logger.info(f"✅ Generated {len(examples)} HyDE template examples")
            return examples
            
        except Exception as e:
            logger.error(f"❌ HyDE generation failed: {e}")
            return []
    
    def _generate_with_gemini(self, query: str, query_type: str, relevant_tables: List[str]) -> List[str]:
        """Generate HyDE examples using Gemini"""
        try:
            # Build enhanced prompt
            prompt = self.prompt_builder.build_hyde_prompt(query, query_type, relevant_tables)
            
            # Generate with Gemini
            response = self.hybrid_generator.gemini_client.generate_content(
                prompt,
                stream=False
            )
            
            hyde_response = response.text
            
            # Extract SQL queries from response
            return self._extract_sql_from_response(hyde_response)
            
        except Exception as e:
            logger.warning(f"HyDE generation with Gemini failed: {e}")
            return []
    
    def _extract_sql_from_response(self, response: str) -> List[str]:
        """Extract SQL queries from AI response"""
        hyde_examples = []
        
        # Split by lines and look for SQL statements
        lines = response.split('\n')
        current_sql = []
        in_sql_block = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#') or line.startswith('--'):
                continue
                
            # Check if this is a SQL statement start
            if any(line.upper().startswith(keyword) for keyword in ['SELECT', 'WITH']):
                # If we were building a SQL statement, save it
                if current_sql:
                    sql_statement = ' '.join(current_sql).strip()
                    if sql_statement and not sql_statement.startswith('Here'):
                        hyde_examples.append(sql_statement)
                    current_sql = []
                
                # Start new SQL statement
                current_sql = [line]
                in_sql_block = True
            elif in_sql_block and line:
                # Continue building the SQL statement
                if line.endswith(';'):
                    current_sql.append(line)
                    sql_statement = ' '.join(current_sql).strip()
                    if sql_statement and not sql_statement.startswith('Here'):
                        hyde_examples.append(sql_statement)
                    current_sql = []
                    in_sql_block = False
                else:
                    current_sql.append(line)
        
        # Handle any remaining SQL
        if current_sql:
            sql_statement = ' '.join(current_sql).strip()
            if sql_statement and not sql_statement.startswith('Here'):
                # Add semicolon if missing
                if not sql_statement.endswith(';'):
                    sql_statement += ';'
                hyde_examples.append(sql_statement)
        
        return hyde_examples[:self.max_examples]
    
    def _generate_template_examples(self, query: str, query_type: str, relevant_tables: List[str]) -> List[str]:
        """Generate enhanced template examples based on query analysis"""
        
        query_lower = query.lower()
        
        # Prescription-focused templates
        if any(word in query_lower for word in ["prescrib", "drug", "medication"]):
            return [
                "SELECT p.PRESCRIBER_NPI_NM, COUNT(*) as prescription_count FROM fct_pharmacy_clear_claim_allstatus_cluster_brand p GROUP BY p.PRESCRIBER_NPI_NM ORDER BY prescription_count DESC LIMIT 10;",
                "SELECT p.NDC_PREFERRED_BRAND_NM, COUNT(*) as drug_count FROM fct_pharmacy_clear_claim_allstatus_cluster_brand p GROUP BY p.NDC_PREFERRED_BRAND_NM ORDER BY drug_count DESC LIMIT 10;",
                "SELECT prov.specialties[1], COUNT(*) as specialty_count FROM as_providers_v1 prov INNER JOIN fct_pharmacy_clear_claim_allstatus_cluster_brand p ON toString(prov.type_1_npi) = p.PRESCRIBER_NPI_NBR GROUP BY prov.specialties[1] ORDER BY specialty_count DESC LIMIT 10;"
            ]
        
        # Procedure-focused templates
        elif any(word in query_lower for word in ["procedure", "surgery", "operation"]):
            return [
                "SELECT r.procedure_code_description, COUNT(*) as procedure_count FROM as_providers_referrals_v2 r GROUP BY r.procedure_code_description ORDER BY procedure_count DESC LIMIT 10;",
                "SELECT r.primary_hospital_name, COUNT(*) as hospital_count FROM as_providers_referrals_v2 r GROUP BY r.primary_hospital_name ORDER BY hospital_count DESC LIMIT 10;",
                "SELECT r.primary_type_2_npi_state, COUNT(*) as state_count FROM as_providers_referrals_v2 r GROUP BY r.primary_type_2_npi_state ORDER BY state_count DESC LIMIT 10;"
            ]
        
        # Payment-focused templates
        elif any(word in query_lower for word in ["payment", "paid", "financial"]):
            return [
                "SELECT pay.life_science_firm_name, SUM(pay.amount) as total_payment FROM as_lsf_v1 pay GROUP BY pay.life_science_firm_name ORDER BY total_payment DESC LIMIT 10;",
                "SELECT pay.nature_of_payment, COUNT(*) as payment_count FROM as_lsf_v1 pay GROUP BY pay.nature_of_payment ORDER BY payment_count DESC LIMIT 10;",
                "SELECT pay.year, SUM(pay.amount) as yearly_total FROM as_lsf_v1 pay GROUP BY pay.year ORDER BY yearly_total DESC LIMIT 10;"
            ]
        
        # KOL-focused templates
        elif any(word in query_lower for word in ["kol", "opinion leader", "expert"]):
            return [
                "SELECT k.displayName, k.score FROM mf_providers k ORDER BY k.score DESC LIMIT 10;",
                "SELECT k.primaryOrgName, AVG(k.score) as avg_score FROM mf_providers k GROUP BY k.primaryOrgName ORDER BY avg_score DESC LIMIT 10;",
                "SELECT c.display, COUNT(*) as condition_count FROM mf_conditions c INNER JOIN mf_scores s ON c.projectId = s.mf_conditions_projectId GROUP BY c.display ORDER BY condition_count DESC LIMIT 10;"
            ]
        
        # Facility-focused templates
        elif any(word in query_lower for word in ["facility", "hospital", "asc", "ambulatory"]):
            return [
                "SELECT r.primary_hospital_name, COUNT(DISTINCT r.primary_type_1_npi) as provider_count FROM as_providers_referrals_v2 r GROUP BY r.primary_hospital_name ORDER BY provider_count DESC LIMIT 10;",
                "SELECT prov.hospital_names[1], COUNT(*) as facility_count FROM as_providers_v1 prov WHERE prov.hospital_names[1] != '' GROUP BY prov.hospital_names[1] ORDER BY facility_count DESC LIMIT 10;",
                "SELECT k.primaryOrgName, COUNT(*) as kol_count FROM mf_providers k GROUP BY k.primaryOrgName ORDER BY kol_count DESC LIMIT 10;"
            ]
        
        # Default general templates
        else:
            return [
                "SELECT prov.first_name, prov.last_name, prov.specialties[1] FROM as_providers_v1 prov LIMIT 10;",
                "SELECT k.displayName, k.score FROM mf_providers k ORDER BY k.score DESC LIMIT 10;",
                "SELECT DISTINCT prov.states[1] as state FROM as_providers_v1 prov WHERE prov.states[1] != '' ORDER BY state LIMIT 10;"
            ]
    
    def _get_query_intent_keywords(self) -> dict:
        """Get keyword mappings for different query intents"""
        return {
            'prescription': ["prescrib", "drug", "medication", "pharmacy", "dispens"],
            'procedure': ["procedure", "surgery", "operation", "treatment", "perform"],
            'payment': ["payment", "paid", "compensation", "financial", "money"],
            'facility': ["hospital", "facility", "center", "asc", "ambulatory"],
            'kol': ["kol", "key opinion leader", "influential", "expert", "leader"],
            'provider': ["provider", "doctor", "physician", "hcp", "prescriber"]
        }
    
    def analyze_query_intent(self, query: str) -> str:
        """Analyze query to determine primary intent"""
        query_lower = query.lower()
        intent_keywords = self._get_query_intent_keywords()
        
        intent_scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        else:
            return 'general'