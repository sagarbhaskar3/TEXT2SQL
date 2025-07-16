# utils/query_classifier.py - Updated with Actual Table Names
import logging
from typing import Tuple, List
from config.domain_knowledge import known_values, query_intent_patterns
from config.schema import schema, TABLE_NAME_MAPPING

logger = logging.getLogger(__name__)

def classify_query(query: str) -> Tuple[str, List[str]]:
    """
    Classify query type and determine relevant tables using actual schema
    
    Args:
        query: Natural language query string
        
    Returns:
        Tuple of (query_type, actual_table_names)
    """
    try:
        query_lower = query.lower()
        logger.info(f"Classifying query: {query}")
        
        # Check for prescription-related queries
        if _check_prescription_intent(query_lower):
            return "Prescription Analysis", ["fct_pharmacy_clear_claim_allstatus_cluster_brand", "as_providers_v1"]
        
        # Check for procedure-related queries
        elif _check_procedure_intent(query_lower):
            return "Procedure Analysis", ["as_providers_referrals_v2", "as_providers_v1"]
        
        # Check for payment-related queries
        elif _check_payment_intent(query_lower):
            return "Payment Analysis", ["as_lsf_v1", "as_providers_v1"]
        
        # Check for KOL-related queries
        elif _check_kol_intent(query_lower):
            return "KOL Analysis", ["mf_providers", "mf_scores", "mf_conditions"]
        
        # Check for facility-related queries
        elif _check_facility_intent(query_lower):
            return "Facility Analysis", ["as_providers_referrals_v2", "as_providers_v1"]
        
        # Check for provider-specific queries
        elif _check_provider_intent(query_lower):
            return "Provider Analysis", ["as_providers_v1"]
        
        # Default to complex multi-table analysis with actual table names
        else:
            return "Complex Multi-table", list(schema.keys())
            
    except Exception as e:
        logger.error(f"Query classification failed: {e}")
        # Return safe defaults with actual table names
        return "Complex Multi-table", ["as_providers_v1"]

def _check_prescription_intent(query: str) -> bool:
    """Check if query is about prescriptions/medications"""
    prescription_keywords = ["prescription", "prescribe", "prescriber", "drug", "medication", "pharmacy", "dispense"]
    
    # Check for explicit keywords
    if any(keyword in query for keyword in prescription_keywords):
        return True
    
    # Check for known drug names
    try:
        if any(drug.lower() in query for drug in known_values.get("drugs", [])):
            return True
    except Exception:
        pass
    
    return False

def _check_procedure_intent(query: str) -> bool:
    """Check if query is about medical procedures"""
    procedure_keywords = ["procedure", "surgery", "operation", "perform", "treatment", "surgical"]
    
    # Check for explicit keywords
    if any(keyword in query for keyword in procedure_keywords):
        return True
    
    # Check for known procedures
    try:
        if any(proc.lower() in query for proc in known_values.get("procedures", [])):
            return True
    except Exception:
        pass
    
    return False

def _check_payment_intent(query: str) -> bool:
    """Check if query is about payments/financial transactions"""
    payment_keywords = ["payment", "paid", "pay", "compensation", "financial", "money", "amount", "life science"]
    
    # Check for explicit keywords
    if any(keyword in query for keyword in payment_keywords):
        return True
    
    # Check for pharmaceutical companies
    try:
        if any(company.lower() in query for company in known_values.get("companies", [])):
            return True
    except Exception:
        pass
    
    return False

def _check_kol_intent(query: str) -> bool:
    """Check if query is about Key Opinion Leaders"""
    kol_keywords = ["kol", "key opinion leader", "opinion leader", "influential", "expert", "leader", "score"]
    
    return any(keyword in query for keyword in kol_keywords)

def _check_facility_intent(query: str) -> bool:
    """Check if query is about healthcare facilities"""
    facility_keywords = ["hospital", "facility", "clinic", "center", "asc", "ambulatory", "surgical center"]
    
    # Check for explicit keywords
    if any(keyword in query for keyword in facility_keywords):
        return True
    
    # Check for known facilities
    try:
        if any(facility.lower() in query for facility in known_values.get("facilities", [])):
            return True
    except Exception:
        pass
    
    return False

def _check_provider_intent(query: str) -> bool:
    """Check if query is about healthcare providers"""
    provider_keywords = ["provider", "doctor", "physician", "hcp", "prescriber", "clinician"]
    
    return any(keyword in query for keyword in provider_keywords)

def get_query_complexity(query: str) -> int:
    """
    Determine query complexity level (1-5)
    
    Args:
        query: Natural language query
        
    Returns:
        Complexity level from 1 (simple) to 5 (very complex)
    """
    try:
        query_lower = query.lower()
        complexity = 1
        
        # Check for multiple constraints
        constraint_keywords = {
            'location': ['state', 'city', 'location', 'area'],
            'temporal': ['year', 'month', 'date', 'time', '2023', '2024'],
            'specialty': ['specialty', 'cardiology', 'oncology', 'endocrinology'],
            'ranking': ['top', 'best', 'highest', 'most', 'leading'],
            'comparison': ['compare', 'versus', 'vs', 'difference']
        }
        
        found_constraints = 0
        for constraint_type, keywords in constraint_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_constraints += 1
        
        # Increase complexity based on number of constraints
        complexity += min(found_constraints, 3)
        
        # Check for complex analysis terms
        complex_terms = ['comprehensive', 'detailed', 'analysis', 'performance', 'trends']
        if any(term in query_lower for term in complex_terms):
            complexity += 1
        
        return min(complexity, 5)
        
    except Exception as e:
        logger.error(f"Complexity calculation failed: {e}")
        return 2  # Default medium complexity

def get_intent_confidence(query: str, classified_type: str) -> float:
    """
    Calculate confidence score for query classification
    
    Args:
        query: Natural language query
        classified_type: The classified query type
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    try:
        query_lower = query.lower()
        confidence = 0.5  # Base confidence
        
        # Get relevant pattern for classified type
        type_mapping = {
            "Prescription Analysis": "prescription_analysis",
            "Procedure Analysis": "procedure_analysis", 
            "Payment Analysis": "payment_analysis",
            "KOL Analysis": "kol_analysis",
            "Facility Analysis": "facility_analysis",
            "Provider Analysis": "provider_analysis"
        }
        
        pattern_key = type_mapping.get(classified_type)
        if pattern_key and pattern_key in query_intent_patterns:
            pattern = query_intent_patterns[pattern_key]
            
            # Check keyword matches
            keyword_matches = sum(1 for keyword in pattern["keywords"] if keyword in query_lower)
            if keyword_matches > 0:
                confidence += min(keyword_matches * 0.15, 0.45)
            
            # Check for entity matches
            entity_matches = 0
            try:
                for entity_type in ["drugs", "procedures", "companies", "specialties"]:
                    if any(entity.lower() in query_lower for entity in known_values.get(entity_type, [])):
                        entity_matches += 1
                
                if entity_matches > 0:
                    confidence += min(entity_matches * 0.05, 0.2)
            except Exception:
                pass
        
        return min(confidence, 1.0)
        
    except Exception as e:
        logger.error(f"Confidence calculation failed: {e}")
        return 0.5

def classify_query_detailed(query: str) -> dict:
    """
    Detailed query classification with metadata using actual table names
    
    Args:
        query: Natural language query
        
    Returns:
        Dictionary with classification details
    """
    try:
        query_type, relevant_tables = classify_query(query)
        complexity = get_query_complexity(query)
        confidence = get_intent_confidence(query, query_type)
        
        return {
            'query': query,
            'query_type': query_type,
            'relevant_tables': relevant_tables,  # These are now actual table names
            'complexity_level': complexity,
            'confidence': confidence,
            'timestamp': None,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Detailed classification failed: {e}")
        return {
            'query': query,
            'query_type': 'Unknown',
            'relevant_tables': [],
            'complexity_level': 1,
            'confidence': 0.0,
            'error': str(e),
            'success': False
        }

def validate_table_names(table_names: List[str]) -> List[str]:
    """
    Validate and convert table names to actual schema names
    
    Args:
        table_names: List of table names (may include old names)
        
    Returns:
        List of validated actual table names
    """
    validated_tables = []
    
    for table_name in table_names:
        # Check if it's already an actual table name
        if table_name in schema:
            validated_tables.append(table_name)
        # Check if it's an old name that needs mapping
        elif table_name in TABLE_NAME_MAPPING:
            validated_tables.append(TABLE_NAME_MAPPING[table_name])
        else:
            logger.warning(f"Unknown table name: {table_name}")
    
    return validated_tables

def get_schema_aware_recommendations(query_type: str) -> dict:
    """
    Get schema-aware recommendations for different query types
    
    Args:
        query_type: The classified query type
        
    Returns:
        Dictionary with schema-aware recommendations
    """
    recommendations = {
        "Prescription Analysis": {
            "primary_table": "fct_pharmacy_clear_claim_allstatus_cluster_brand",
            "join_table": "as_providers_v1",
            "key_columns": ["NDC_PREFERRED_BRAND_NM", "PRESCRIBER_NPI_NM", "PATIENT_ID"],
            "join_condition": "toString(prov.type_1_npi) = p.PRESCRIBER_NPI_NBR",
            "common_filters": ["drug names", "provider states", "specialties"]
        },
        
        "Procedure Analysis": {
            "primary_table": "as_providers_referrals_v2",
            "join_table": "as_providers_v1", 
            "key_columns": ["procedure_code_description", "primary_hospital_name", "date"],
            "join_condition": "prov.type_1_npi = r.primary_type_1_npi",
            "common_filters": ["procedure types", "hospital names", "dates"]
        },
        
        "Payment Analysis": {
            "primary_table": "as_lsf_v1",
            "join_table": "as_providers_v1",
            "key_columns": ["life_science_firm_name", "amount", "year", "nature_of_payment"],
            "join_condition": "prov.type_1_npi = pay.type_1_npi",
            "common_filters": ["company names", "payment years", "payment types"]
        },
        
        "KOL Analysis": {
            "primary_table": "mf_providers",
            "join_table": "mf_scores",
            "key_columns": ["displayName", "score", "primaryOrgName"],
            "join_condition": "k.npi = s.mf_providers_npi",
            "common_filters": ["provider scores", "organization names"]
        }
    }
    
    return recommendations.get(query_type, {})