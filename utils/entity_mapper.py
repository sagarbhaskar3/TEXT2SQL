# utils/entity_mapper.py - Fixed version
import re
import logging

logger = logging.getLogger(__name__)

# Define term mappings locally to avoid import issues
term_mappings = {
    "drug": [
        "NDC_PREFERRED_BRAND_NM", 
        "NDC_DRUG_NM", 
        "NDC_GENERIC_NM",
        "NDC_DESC",
        "product_name"
    ],
    "state": [
        "PRESCRIBER_NPI_STATE_CD", 
        "states", 
        "primary_type_2_npi_state", 
        "referring_type_2_npi_state"
    ],
    "procedure": [
        "procedure_code_description",
        "procedure_code",
        "diagnosis_code_description",
        "diagnosis_code"
    ],
    "payment": [
        "nature_of_payment", 
        "amount",
        "TOTAL_PAID_AMT",
        "GROSS_DUE_AMT"
    ],
    "condition": [
        "conditions", 
        "display", 
        "diagnosis_code_description",
        "DIAGNOSIS_CD"
    ],
    "prescriber": [
        "displayName", 
        "first_name", 
        "last_name", 
        "PRESCRIBER_NPI_NBR",
        "PRESCRIBER_NPI_NM",
        "name"
    ],
    "year": [
        "year", 
        "SERVICE_DATE_DD", 
        "date",
        "RX_ANCHOR_DD"
    ],
    "patient": [
        "PATIENT_ID"
    ],
    "specialty": [
        "specialties",
        "primary_specialty",
        "referring_specialty"
    ],
    "company": [
        "life_science_firm_name",
        "primaryOrgName",
        "PAYER_COMPANY_NM"
    ]
}

# Define known values locally
known_values = {
    "drugs": [
        "JARDIANCE", "EYLEA HD", "Humira", "Keytruda", "Ozempic", "Mounjaro", 
        "Wegovy", "Rybelsus", "Trulicity", "Victoza", "Lantus", "Humalog",
        "Novolog", "Levemir", "Tresiba", "Basaglar", "Lyrica", "Gabapentin",
        "Atorvastatin", "Rosuvastatin", "Simvastatin", "Metformin"
    ],
    "states": [
        "NY", "CA", "TX", "FL", "PA", "IL", "OH", "GA", "NC", "MI",
        "New York", "California", "Texas", "Florida", "Pennsylvania", 
        "Illinois", "Ohio", "Georgia", "North Carolina", "Michigan"
    ],
    "procedures": [
        "laparoscopic", "knee arthroplasty", "hip replacement", "coronary angioplasty",
        "cataract surgery", "colonoscopy", "endoscopy", "cardiac catheterization",
        "appendectomy", "cholecystectomy", "hernia repair", "tonsillectomy"
    ],
    "payment_types": [
        "Food and Beverage", "Travel and Lodging", "Education", "Research",
        "Consulting Fee", "Speaker Fee", "Grant", "Honoraria", "Gift"
    ],
    "conditions": [
        "diabetes", "hypertension", "heart disease", "cancer", "obesity",
        "depression", "anxiety", "arthritis", "asthma", "COPD"
    ],
    "genders": ["M", "F", "O", "U", ""],
    "specialties": [
        "cardiology", "oncology", "endocrinology", "neurology", "psychiatry",
        "orthopedics", "dermatology", "gastroenterology", "pulmonology",
        "rheumatology", "urology", "ophthalmology", "otolaryngology"
    ],
    "companies": [
        "Pfizer", "Johnson & Johnson", "Roche", "Novartis", "Merck",
        "AbbVie", "Bristol Myers Squibb", "Amgen", "Gilead", "Eli Lilly"
    ],
    "patients": []  # Initialize as empty list
}

def extract_entities(query):
    """Extract entities and map to schema columns with improved error handling."""
    try:
        query_lower = query.lower()
        logger.info(f"🔍 Extracting entities from query: {query}")
        
        # Extract years with improved pattern
        years = re.findall(r'\b(20\d{2})\b', query)
        
        # Extract numbers for top N queries
        numbers = re.findall(r'\btop\s+(\d+)\b', query_lower)
        if not numbers:
            numbers = re.findall(r'\b(\d+)\s+(?:most|highest|top|largest)\b', query_lower)
        
        # Initialize entities dictionary with safe defaults
        entities = {
            "drugs": [],
            "states": [],
            "procedures": [],
            "years": years,
            "payment_types": [],
            "conditions": [],
            "patient": [],  # Note: singular to match term_mappings
            "specialties": [],
            "companies": [],
            "numbers": numbers
        }
        
        # Enhanced drug detection
        for drug in known_values.get("drugs", []):
            if drug.lower() in query_lower:
                entities["drugs"].append(drug)
                logger.info(f"✅ Found drug: {drug}")
        
        # Enhanced state detection
        for state in known_values.get("states", []):
            if state.lower() in query_lower:
                entities["states"].append(state)
                logger.info(f"✅ Found state: {state}")
        
        # Enhanced specialty detection
        for specialty in known_values.get("specialties", []):
            if specialty in query_lower:
                entities["specialties"].append(specialty)
                logger.info(f"✅ Found specialty: {specialty}")
            # Check for specialty variations
            elif specialty == "cardiology" and ("heart" in query_lower or "cardiac" in query_lower):
                entities["specialties"].append(specialty)
            elif specialty == "oncology" and "cancer" in query_lower:
                entities["specialties"].append(specialty)
            elif specialty == "endocrinology" and ("diabetes" in query_lower or "hormone" in query_lower):
                entities["specialties"].append(specialty)
        
        # Enhanced procedure detection
        for procedure in known_values.get("procedures", []):
            if procedure.lower() in query_lower:
                entities["procedures"].append(procedure)
                logger.info(f"✅ Found procedure: {procedure}")
        
        # Enhanced payment type detection
        for payment_type in known_values.get("payment_types", []):
            if payment_type.lower() in query_lower:
                entities["payment_types"].append(payment_type)
                logger.info(f"✅ Found payment type: {payment_type}")
        
        # Enhanced condition detection
        for condition in known_values.get("conditions", []):
            if condition.lower() in query_lower:
                entities["conditions"].append(condition)
                logger.info(f"✅ Found condition: {condition}")
        
        # Enhanced company detection
        for company in known_values.get("companies", []):
            if company.lower() in query_lower:
                entities["companies"].append(company)
                logger.info(f"✅ Found company: {company}")
        
        # Patient detection
        if any(term in query_lower for term in ["patient", "member", "individual"]):
            entities["patient"] = ["PATIENT_ID"]
            logger.info("✅ Found patient reference")
        
        # Create mappings with proper error handling
        mappings = {}
        for entity_type, values in entities.items():
            if values:
                # Use .get() to safely access term_mappings
                columns = term_mappings.get(entity_type, [])
                mappings[entity_type] = {
                    "values": values,
                    "columns": columns
                }
                logger.info(f"✅ Mapped {entity_type}: {len(values)} values, {len(columns)} columns")
        
        logger.info(f"✅ Entity extraction completed. Found {len(mappings)} entity types")
        return entities, mappings
        
    except Exception as e:
        logger.error(f"❌ Entity extraction failed: {e}")
        # Return safe defaults
        return {
            "drugs": [],
            "states": [],
            "procedures": [],
            "years": [],
            "payment_types": [],
            "conditions": [],
            "patient": [],
            "specialties": [],
            "companies": [],
            "numbers": []
        }, {}

def expand_query_with_synonyms(query):
    """Expand query with healthcare synonyms for better entity detection."""
    try:
        healthcare_synonyms = {
            "doctor": ["physician", "provider", "prescriber", "clinician"],
            "medicine": ["drug", "medication", "pharmaceutical", "prescription"],
            "hospital": ["medical center", "health system", "clinic", "facility"],
            "treatment": ["therapy", "procedure", "intervention", "care"],
            "disease": ["condition", "illness", "disorder", "diagnosis"],
            "payment": ["reimbursement", "compensation", "fee", "amount"]
        }
        
        expanded_terms = []
        query_lower = query.lower()
        
        for term, synonyms in healthcare_synonyms.items():
            if term in query_lower:
                expanded_terms.extend(synonyms)
        
        return expanded_terms
        
    except Exception as e:
        logger.error(f"❌ Synonym expansion failed: {e}")
        return []

def get_relevant_tables_for_entities(entities):
    """Determine most relevant tables based on detected entities."""
    try:
        table_scores = {}
        
        # Score tables based on entity types
        if entities.get("drugs") or entities.get("patient"):
            table_scores["Pharmacy_Claims_file"] = table_scores.get("Pharmacy_Claims_file", 0) + 2
        
        if entities.get("payment_types") or entities.get("companies"):
            table_scores["Payments_to_HCPs"] = table_scores.get("Payments_to_HCPs", 0) + 2
        
        if entities.get("specialties") or entities.get("states"):
            table_scores["Provider_details_file"] = table_scores.get("Provider_details_file", 0) + 2
            table_scores["KOL_Providers"] = table_scores.get("KOL_Providers", 0) + 1
        
        if entities.get("procedures"):
            table_scores["Referral_Patterns_file"] = table_scores.get("Referral_Patterns_file", 0) + 2
            table_scores["Diagnosis_Procedures_file"] = table_scores.get("Diagnosis_Procedures_file", 0) + 2
        
        # Return tables sorted by relevance score
        return sorted(table_scores.keys(), key=lambda x: table_scores[x], reverse=True)
        
    except Exception as e:
        logger.error(f"❌ Table relevance calculation failed: {e}")
        return ["Pharmacy_Claims_file", "Provider_details_file", "Payments_to_HCPs"]  # Safe defaults