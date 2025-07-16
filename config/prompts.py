# config/prompts.py - Updated with Schema-Aware Prompts

class PromptTemplates:
    """Centralized prompts for AI model interactions with schema awareness"""
    
    @staticmethod
    def get_enhanced_sql_prompt(query: str, entities: dict, context: str, intent_analysis: dict) -> str:
        """Enhanced prompt for SQL generation with actual schema validation"""
        
        # Get table information for recommended tables
        table_info = ""
        for table in intent_analysis.get("recommended_tables", []):
            if table == "fct_pharmacy_clear_claim_allstatus_cluster_brand":
                table_info += """
- fct_pharmacy_clear_claim_allstatus_cluster_brand: Pharmacy prescription claims
  Key columns: NDC_PREFERRED_BRAND_NM, PRESCRIBER_NPI_NBR, PRESCRIBER_NPI_STATE_CD, PATIENT_ID
  Join: toString(prov.type_1_npi) = p.PRESCRIBER_NPI_NBR
"""
            elif table == "as_providers_v1":
                table_info += """
- as_providers_v1: Healthcare provider details
  Key columns: type_1_npi, first_name, last_name, specialties[1], states[1], cities[1]
  Arrays: specialties, states, cities, hospital_names (1-indexed)
"""
            elif table == "as_lsf_v1":
                table_info += """
- as_lsf_v1: Life science firm payments to providers
  Key columns: type_1_npi, life_science_firm_name, amount, year, nature_of_payment
  Join: prov.type_1_npi = pay.type_1_npi
"""
            elif table == "as_providers_referrals_v2":
                table_info += """
- as_providers_referrals_v2: Provider referrals and procedures
  Key columns: primary_type_1_npi, procedure_code_description, primary_hospital_name, date
  Join: prov.type_1_npi = r.primary_type_1_npi
"""
            elif table == "mf_providers":
                table_info += """
- mf_providers: KOL provider information
  Key columns: npi, displayName, score, primaryOrgName
  Join: k.npi = s.mf_providers_npi
"""
        
        # Build constraint-specific instructions with schema awareness
        constraint_instructions = ""
        for constraint in intent_analysis.get("constraints", []):
            if constraint == "location":
                constraint_instructions += """
LOCATION CONSTRAINTS (Schema-Validated):
- Use states[1] for as_providers_v1 array column (1-indexed)
- Use PRESCRIBER_NPI_STATE_CD for pharmacy claims table
- Use primary_type_2_npi_state for referrals table
- Handle both state codes (CA, NY) and full names (California, New York)
"""
            elif constraint == "temporal":
                constraint_instructions += """
TEMPORAL CONSTRAINTS (Schema-Validated):
- Use EXTRACT(YEAR FROM date) for as_providers_referrals_v2 date column
- Use EXTRACT(YEAR FROM SERVICE_DATE_DD) for pharmacy claims
- Use year column directly in as_lsf_v1 payments table
- Available years typically 2016-2023
"""
            elif constraint == "specialty":
                constraint_instructions += """
SPECIALTY CONSTRAINTS (Schema-Validated):
- Use specialties[1] for primary specialty from as_providers_v1 (array is 1-indexed)
- Use primary_specialty for as_providers_referrals_v2
- Use ILIKE for case-insensitive specialty matching
- Common specialties: endocrinology, cardiology, oncology
"""
        
        # Build ranking instructions
        ranking_instructions = ""
        if intent_analysis.get("needs_ranking"):
            ranking_instructions = """
RANKING REQUIREMENTS (Schema-Validated):
- Use COUNT(*) for volume-based ranking of prescriptions/procedures
- Use SUM(amount) for financial ranking from as_lsf_v1
- Always include ORDER BY with DESC for top queries
- Include appropriate LIMIT (10-20 for top queries)
- Use proper GROUP BY with selected columns
"""
        
        # Build schema-aware filtering instructions
        filtering_instructions = """
SCHEMA-AWARE FILTERING:
For diabetes drugs, use actual drug names:
  p.NDC_PREFERRED_BRAND_NM IN ('Ozempic', 'Mounjaro', 'Lantus', 'Humalog', 'Metformin', 'Trulicity')
  OR p.NDC_DRUG_CLASS_NM ILIKE '%diabetes%'

For ASC facilities, use hospital name patterns:
  r.primary_hospital_name ILIKE '%ambulatory%' OR r.primary_hospital_name ILIKE '%surgical center%'

For cardiac procedures:
  r.procedure_code_description ILIKE '%cardiac%' OR r.procedure_code_description ILIKE '%heart%'
"""
        
        # Format entities for prompt
        entity_constraints = ""
        for entity_type, entity_data in entities.items():
            if isinstance(entity_data, dict) and entity_data.get("values"):
                values = entity_data["values"]
                entity_constraints += f"{entity_type.upper()}: {', '.join(map(str, values))}\n"
        
        return f"""You are an expert ClickHouse SQL generator for healthcare data. Generate ONLY the SQL query, no explanations.

QUERY: "{query}"

INTENT ANALYSIS:
- Primary Intent: {intent_analysis.get('primary_intent', 'general')}
- Query Type: {intent_analysis.get('query_type', 'general')}
- Complexity Level: {intent_analysis.get('complexity_level', 0)}/5
- Needs Ranking: {intent_analysis.get('needs_ranking', False)}
- Constraints: {', '.join(intent_analysis.get('constraints', []))}

ENTITY CONSTRAINTS:
{entity_constraints}

VALIDATED SCHEMA TABLES:
{table_info}

{constraint_instructions}

{ranking_instructions}

{filtering_instructions}

CRITICAL JOIN PATTERNS (Schema-Validated):
- Pharmacy to Provider: toString(prov.type_1_npi) = p.PRESCRIBER_NPI_NBR
- Provider to Payments: prov.type_1_npi = pay.type_1_npi  
- Provider to Referrals: prov.type_1_npi = r.primary_type_1_npi
- KOL Providers to Scores: k.npi = s.mf_providers_npi
- Use aliases: p, prov, pay, r, k, s, c

CLICKHOUSE SPECIFIC RULES (Schema-Validated):
1. Arrays are 1-indexed: specialties[1], states[1], cities[1]
2. Use ILIKE for case-insensitive text matching
3. Use toString() for NPI type conversions: toString(type_1_npi)
4. Date functions: EXTRACT(YEAR FROM date_column)
5. Handle Nullable columns appropriately
6. Use LIMIT for performance optimization

HEALTHCARE DOMAIN RULES (Schema-Validated):
1. Prescription queries: Use NDC_PREFERRED_BRAND_NM, PRESCRIBER_NPI_NM, PATIENT_ID
2. Procedure queries: Use procedure_code_description, primary_hospital_name
3. Payment queries: Use life_science_firm_name, amount, nature_of_payment, year
4. Provider queries: Use first_name, last_name, specialties[1], states[1]
5. Facility queries: Use primary_hospital_name, referring_hospital_name
6. KOL queries: Use displayName, score, primaryOrgName

NO INVALID COLUMNS: 
- Do NOT use DISEASE_NM (doesn't exist)
- Do NOT use facility_type (doesn't exist)
- Use actual schema columns only

CONTEXT FROM RETRIEVAL:
{context[:800] if context else 'No additional context'}

CRITICAL: Generate only the ClickHouse SQL query. No markdown, no explanations, no comments.
"""

    @staticmethod
    def get_hyde_generation_prompt(query: str, query_type: str, relevant_tables: list) -> str:
        """Prompt for generating HyDE SQL examples with schema awareness"""
        
        # Map to actual table names
        table_mapping = {
            "Pharmacy_Claims_file": "fct_pharmacy_clear_claim_allstatus_cluster_brand",
            "Provider_details_file": "as_providers_v1", 
            "Payments_to_HCPs": "as_lsf_v1",
            "Referral_Patterns_file": "as_providers_referrals_v2",
            "KOL_Providers": "mf_providers",
            "KOL_Scores": "mf_scores"
        }
        
        actual_tables = [table_mapping.get(table, table) for table in relevant_tables]
        tables_info = "\n".join([f"- {table}" for table in actual_tables])
        
        return f"""Generate 3 different ClickHouse SQL query examples for this healthcare question:
        
Question: "{query}"
Query Type: {query_type}

Use these ACTUAL healthcare tables with proper ClickHouse syntax:
{tables_info}

SCHEMA-VALIDATED Table Details:
- fct_pharmacy_clear_claim_allstatus_cluster_brand: NDC_PREFERRED_BRAND_NM, PRESCRIBER_NPI_NBR, PATIENT_ID
- as_providers_v1: type_1_npi, first_name, last_name, specialties[1], states[1] (arrays 1-indexed)
- as_lsf_v1: type_1_npi, life_science_firm_name, amount, year, nature_of_payment
- as_providers_referrals_v2: primary_type_1_npi, procedure_code_description, primary_hospital_name
- mf_providers: npi, displayName, score, primaryOrgName

CRITICAL ClickHouse Rules:
- Arrays are 1-indexed: specialties[1], states[1]
- Use toString() for NPI joins: toString(type_1_npi) = PRESCRIBER_NPI_NBR
- Use ILIKE for case-insensitive matching
- Include proper table aliases (p, prov, pay, r, k)
- NO invalid columns like DISEASE_NM or facility_type

Return 3 different SQL approaches as separate queries:"""

    @staticmethod
    def get_ollama_simple_prompt(query: str, entities: dict, intent_analysis: dict) -> str:
        """Simplified prompt for Ollama fallback with schema awareness"""
        
        entity_info = ""
        for entity_type, entity_data in entities.items():
            if isinstance(entity_data, dict) and entity_data.get("values"):
                values = entity_data["values"]
                entity_info += f"{entity_type}: {', '.join(map(str, values))}\n"
        
        # Map recommended tables to actual names
        table_mapping = {
            "Pharmacy_Claims_file": "fct_pharmacy_clear_claim_allstatus_cluster_brand",
            "Provider_details_file": "as_providers_v1",
            "Payments_to_HCPs": "as_lsf_v1",
            "Referral_Patterns_file": "as_providers_referrals_v2"
        }
        
        actual_tables = []
        for table in intent_analysis.get('recommended_tables', []):
            actual_tables.append(table_mapping.get(table, table))
        
        return f"""Generate ClickHouse SQL for healthcare query: {query}

ACTUAL Tables to use: {', '.join(actual_tables)}
Entities: {entity_info}

SCHEMA Rules:
- Arrays are 1-indexed: specialties[1], states[1]
- Use ILIKE for text matching
- Join as_providers_v1 with other tables using type_1_npi
- For prescriptions: fct_pharmacy_clear_claim_allstatus_cluster_brand
- For procedures: as_providers_referrals_v2
- For payments: as_lsf_v1
- Use toString(type_1_npi) = PRESCRIBER_NPI_NBR for pharmacy joins
- Include TOP queries with ORDER BY DESC LIMIT 10

CRITICAL: Use only actual column names from schema.

Return only SQL:"""

    @staticmethod
    def get_query_classification_prompt(query: str) -> str:
        """Prompt for query classification with actual table names"""
        
        return f"""Classify this healthcare query and identify the primary intent:

Query: "{query}"

Classify into one of these categories:
1. Prescription Analysis - queries about medications, prescriptions, drugs
2. Procedure Analysis - queries about medical procedures, surgeries, operations
3. Payment Analysis - queries about payments, financial transactions, compensation
4. KOL Analysis - queries about key opinion leaders, influential providers
5. Facility Analysis - queries about hospitals, clinics, ambulatory surgical centers
6. Provider Analysis - queries about healthcare providers, doctors, specialists
7. Complex Multi-table - queries requiring multiple tables or complex analysis

ACTUAL Table Names to Use:
- fct_pharmacy_clear_claim_allstatus_cluster_brand (pharmacy claims)
- as_providers_v1 (provider details)
- as_lsf_v1 (payments to providers)
- as_providers_referrals_v2 (referrals and procedures)
- mf_providers (KOL providers)
- mf_scores (KOL scores)
- mf_conditions (medical conditions)

Also identify:
- Primary entities (drugs, locations, specialties, years, etc.)
- Complexity level (1-5)
- Required tables from actual schema
- Whether ranking/top results are needed

Format response as JSON:
{{
    "primary_intent": "category",
    "query_type": "Analysis Type", 
    "complexity_level": 1-5,
    "needs_ranking": true/false,
    "entities_detected": ["entity1", "entity2"],
    "recommended_tables": ["actual_table1", "actual_table2"]
}}"""

    @staticmethod
    def get_entity_extraction_prompt(query: str) -> str:
        """Prompt for entity extraction with schema validation"""
        
        return f"""Extract healthcare entities from this query using actual schema knowledge:

Query: "{query}"

Extract these entity types with schema validation:
- drugs/medications (check against NDC_PREFERRED_BRAND_NM, NDC_GENERIC_NM)
- states/locations (use with PRESCRIBER_NPI_STATE_CD, states[1])
- medical specialties (use with specialties[1], primary_specialty)
- procedures (use with procedure_code_description)
- years/dates (use with year, date, SERVICE_DATE_DD)
- companies (use with life_science_firm_name, PAYER_COMPANY_NM)
- facilities (use with primary_hospital_name, primaryOrgName)
- numbers (for "top N" queries with LIMIT)

Return as JSON:
{{
    "drugs": ["drug1", "drug2"],
    "states": ["state1", "state2"],
    "specialties": ["specialty1"],
    "procedures": ["procedure1"],
    "years": ["year1"],
    "companies": ["company1"],
    "facilities": ["facility1"],
    "numbers": ["number1"]
}}"""

class PromptBuilder:
    """Dynamic prompt builder for different contexts with schema awareness"""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_sql_generation_prompt(self, query: str, entities: dict, context: str, intent_analysis: dict) -> str:
        """Build enhanced SQL generation prompt with schema validation"""
        return self.templates.get_enhanced_sql_prompt(query, entities, context, intent_analysis)
    
    def build_hyde_prompt(self, query: str, query_type: str, relevant_tables: list) -> str:
        """Build HyDE generation prompt with actual table names"""
        return self.templates.get_hyde_generation_prompt(query, query_type, relevant_tables)
    
    def build_ollama_prompt(self, query: str, entities: dict, intent_analysis: dict) -> str:
        """Build simplified prompt for Ollama with schema awareness"""
        return self.templates.get_ollama_simple_prompt(query, entities, intent_analysis)
    
    def build_classification_prompt(self, query: str) -> str:
        """Build query classification prompt with actual table names"""
        return self.templates.get_query_classification_prompt(query)
    
    def build_entity_extraction_prompt(self, query: str) -> str:
        """Build entity extraction prompt with schema validation"""
        return self.templates.get_entity_extraction_prompt(query)