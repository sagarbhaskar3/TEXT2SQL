# config/domain_knowledge.py - Updated with Correct Schema Mappings

# Term mappings for entity extraction - maps conceptual terms to actual database columns
term_mappings = {
    "drug": [
        "NDC_PREFERRED_BRAND_NM", 
        "NDC_DRUG_NM", 
        "NDC_GENERIC_NM",
        "NDC_DESC",
        "product_name"
    ],
    "drugs": [
        "NDC_PREFERRED_BRAND_NM", 
        "NDC_DRUG_NM", 
        "NDC_GENERIC_NM",
        "NDC_DESC",
        "product_name"
    ],
    "state": [
        "PRESCRIBER_NPI_STATE_CD", 
        "states[1]",  # Array column - 1-indexed
        "primary_type_2_npi_state", 
        "referring_type_2_npi_state"
    ],
    "states": [
        "PRESCRIBER_NPI_STATE_CD", 
        "states[1]",
        "primary_type_2_npi_state", 
        "referring_type_2_npi_state"
    ],
    "cities": [
        "cities[1]",  # Array column - 1-indexed
        "primary_type_2_npi_city",
        "referring_type_2_npi_city"
    ],
    "procedure": [
        "procedure_code_description",
        "procedure_code",
        "diagnosis_code_description",
        "diagnosis_code"
    ],
    "procedures": [
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
    "payments": [
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
    "conditions": [
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
    "providers": [
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
    "years": [
        "year", 
        "SERVICE_DATE_DD", 
        "date",
        "RX_ANCHOR_DD"
    ],
    "patient": [
        "PATIENT_ID"
    ],
    "patients": [
        "PATIENT_ID"
    ],
    "specialty": [
        "specialties[1]",  # Array column - 1-indexed
        "primary_specialty",
        "referring_specialty"
    ],
    "specialties": [
        "specialties[1]",
        "primary_specialty",
        "referring_specialty"
    ],
    "company": [
        "life_science_firm_name",
        "primaryOrgName",
        "PAYER_COMPANY_NM"
    ],
    "companies": [
        "life_science_firm_name",
        "primaryOrgName",
        "PAYER_COMPANY_NM"
    ],
    "facility": [
        "primary_hospital_name",
        "referring_hospital_name",
        "primaryOrgName",
        "best_hospital_name"
    ],
    "facilities": [
        "primary_hospital_name",
        "referring_hospital_name",
        "primaryOrgName",
        "best_hospital_name"
    ],
    "numbers": [
        "COUNT(*)",
        "SUM(amount)",
        "AVG(score)"
    ],
    "payment_types": [
        "nature_of_payment"
    ]
}

# Enhanced known values for validation and entity recognition
known_values = {
    "drugs": [
        # Diabetes medications
        "Ozempic", "Mounjaro", "Wegovy", "Rybelsus", "Trulicity", "Victoza", 
        "Lantus", "Humalog", "Novolog", "Levemir", "Tresiba", "Basaglar", "Metformin",
        
        # Cancer medications
        "Keytruda", "Opdivo", "Tecentriq", "Yervoy", "Imfinzi", "Bavencio",
        
        # Cardiovascular medications
        "Atorvastatin", "Rosuvastatin", "Simvastatin", "Crestor", "Lipitor",
        
        # Other common medications
        "Humira", "Enbrel", "Remicade", "Stelara", "Cosentyx",
        "JARDIANCE", "EYLEA HD", "Lyrica", "Gabapentin",
        
        # Eye medications
        "Eylea", "Lucentis", "Avastin", "Beovu"
    ],
    
    "states": [
        # State codes
        "NY", "CA", "TX", "FL", "PA", "IL", "OH", "GA", "NC", "MI", 
        "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
        "CO", "MN", "SC", "AL", "LA", "KY", "OR", "OK", "CT", "UT",
        
        # Full state names
        "New York", "California", "Texas", "Florida", "Pennsylvania", 
        "Illinois", "Ohio", "Georgia", "North Carolina", "Michigan",
        "New Jersey", "Virginia", "Washington", "Arizona", "Massachusetts",
        "Tennessee", "Indiana", "Missouri", "Maryland", "Wisconsin",
        "Colorado", "Minnesota", "South Carolina", "Alabama", "Louisiana",
        "Kentucky", "Oregon", "Oklahoma", "Connecticut", "Utah"
    ],
    
    "procedures": [
        # Surgical procedures
        "laparoscopic", "knee arthroplasty", "hip replacement", "hip arthroplasty",
        "coronary angioplasty", "cardiac catheterization", "cataract surgery", 
        "hernia repair", "appendectomy", "cholecystectomy", "tonsillectomy",
        
        # Diagnostic procedures
        "colonoscopy", "endoscopy", "bronchoscopy", "arthroscopy",
        "angiography", "echocardiography", "mammography",
        
        # Therapeutic procedures
        "chemotherapy", "radiation therapy", "physical therapy",
        "dialysis", "blood transfusion", "vaccination"
    ],
    
    "payment_types": [
        "Food and Beverage", "Travel and Lodging", "Education", "Research",
        "Consulting Fee", "Speaker Fee", "Grant", "Honoraria", "Gift",
        "Compensation", "Royalty", "License", "Investment Interest",
        "Debt Forgiveness", "Charity", "Entertainment", "Current Research"
    ],
    
    "conditions": [
        # Common chronic conditions
        "diabetes", "hypertension", "heart disease", "cancer", "obesity",
        "depression", "anxiety", "arthritis", "asthma", "COPD",
        
        # Specific conditions
        "Type 2 Diabetes", "Cardiovascular Disease", "Breast Cancer",
        "Lung Cancer", "Prostate Cancer", "Alzheimer's Disease",
        "Parkinson's Disease", "Multiple Sclerosis", "Rheumatoid Arthritis",
        
        # Eye conditions
        "Macular Degeneration", "Diabetic Retinopathy", "Glaucoma"
    ],
    
    "genders": ["M", "F", "O", "U", ""],
    
    "specialties": [
        # Primary specialties
        "cardiology", "oncology", "endocrinology", "neurology", "psychiatry",
        "orthopedics", "dermatology", "gastroenterology", "pulmonology",
        "rheumatology", "urology", "ophthalmology", "otolaryngology",
        
        # Additional specialties
        "anesthesiology", "radiology", "pathology", "emergency medicine",
        "family medicine", "internal medicine", "pediatrics", "obstetrics",
        "gynecology", "surgery", "plastic surgery", "cardiac surgery",
        "neurosurgery", "orthopedic surgery", "vascular surgery",
        
        # Subspecialties
        "interventional cardiology", "medical oncology", "surgical oncology",
        "pediatric cardiology", "pediatric oncology", "geriatric medicine"
    ],
    
    "companies": [
        # Top pharmaceutical companies
        "Pfizer", "Johnson & Johnson", "Roche", "Novartis", "Merck",
        "AbbVie", "Bristol Myers Squibb", "Amgen", "Gilead", "Eli Lilly",
        "Sanofi", "GSK", "AstraZeneca", "Biogen", "Regeneron",
        "Moderna", "BioNTech", "Vertex", "Alexion", "Celgene",
        
        # From schema samples
        "TEVA PHARMACEUTICALS USA, INC.", "ABBVIE, INC.", "AMGEN INC.",
        
        # Include variations
        "J&J", "BMS", "BMY", "LLY", "PFE", "GILD", "AMGN", "BIIB"
    ],
    
    "patients": [],
    "numbers": ["1", "2", "3", "4", "5", "10", "15", "20", "25", "50", "100"],
    
    "cities": [
        # Major US cities
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
        "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
        "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
        "Seattle", "Denver", "Washington", "Boston", "Nashville", "Baltimore",
        "Oklahoma City", "Louisville", "Portland", "Las Vegas", "Milwaukee",
        "Albuquerque", "Tucson", "Fresno", "Sacramento", "Mesa", "Kansas City",
        "Atlanta", "Long Beach", "Omaha", "Raleigh", "Miami", "Virginia Beach",
        "Oakland", "Minneapolis", "Tulsa", "Tampa", "Arlington", "New Orleans"
    ],
    
    "facilities": [
        "ambulatory surgical center", "ASC", "hospital", "medical center",
        "clinic", "health system", "surgery center", "outpatient center",
        "imaging center", "dialysis center", "cancer center", "heart center"
    ]
}

# Healthcare-specific terminology mappings for better entity recognition
healthcare_synonyms = {
    "doctor": ["physician", "provider", "prescriber", "clinician", "hcp", "healthcare professional"],
    "medicine": ["drug", "medication", "pharmaceutical", "prescription", "therapy"],
    "hospital": ["medical center", "health system", "clinic", "facility", "healthcare facility"],
    "treatment": ["therapy", "procedure", "intervention", "care", "management"],
    "disease": ["condition", "illness", "disorder", "diagnosis", "syndrome"],
    "payment": ["reimbursement", "compensation", "fee", "amount", "financial support"],
    "surgery": ["operation", "procedure", "surgical intervention", "surgical procedure"],
    "analysis": ["study", "review", "assessment", "evaluation", "examination"],
    "top": ["best", "highest", "leading", "most", "greatest", "primary"],
    "facility": ["center", "institution", "organization", "establishment"]
}

# Table relationship mappings for better SQL generation (Updated with actual table names)
table_relationships = {
    "as_lsf_v1": {  # Payments to HCPs
        "primary_key": "type_1_npi",
        "description": "Life science firm payments to healthcare providers",
        "foreign_keys": {
            "as_providers_v1": "type_1_npi"
        },
        "key_columns": ["life_science_firm_name", "product_name", "amount", "year", "nature_of_payment"],
        "common_joins": ["as_providers_v1"]
    },
    
    "as_providers_v1": {  # Provider details
        "primary_key": "type_1_npi", 
        "description": "Healthcare provider demographic and professional information",
        "foreign_keys": {},
        "key_columns": ["first_name", "last_name", "specialties", "states", "cities"],
        "array_columns": ["specialties", "states", "cities", "hospital_names", "system_names"],
        "common_joins": ["fct_pharmacy_clear_claim_allstatus_cluster_brand", "as_lsf_v1", "as_providers_referrals_v2"]
    },
    
    "fct_pharmacy_clear_claim_allstatus_cluster_brand": {  # Pharmacy claims
        "primary_key": "PATIENT_ID",
        "description": "Prescription claims and pharmacy data",
        "foreign_keys": {
            "as_providers_v1": "PRESCRIBER_NPI_NBR"
        },
        "key_columns": ["NDC_PREFERRED_BRAND_NM", "PRESCRIBER_NPI_NM", "PRESCRIBER_NPI_STATE_CD", "SERVICE_DATE_DD"],
        "common_joins": ["as_providers_v1"]
    },
    
    "as_providers_referrals_v2": {  # Referral patterns and procedures
        "primary_key": ["primary_type_1_npi", "referring_type_1_npi"],
        "description": "Provider referral patterns and procedure data",
        "foreign_keys": {
            "as_providers_v1": ["primary_type_1_npi", "referring_type_1_npi"]
        },
        "key_columns": ["primary_hospital_name", "procedure_code_description", "diagnosis_code_description", "date"],
        "common_joins": ["as_providers_v1"]
    },
    
    "mf_providers": {  # KOL providers
        "primary_key": "npi",
        "description": "Key Opinion Leader provider information",
        "foreign_keys": {
            "mf_scores": "npi"
        },
        "key_columns": ["displayName", "score", "primaryOrgName", "sex"],
        "common_joins": ["mf_scores", "mf_conditions"]
    },
    
    "mf_scores": {  # KOL scores
        "primary_key": "id",
        "description": "KOL provider scoring data",
        "foreign_keys": {
            "mf_providers": "mf_providers_npi",
            "mf_conditions": "mf_conditions_projectId"
        },
        "key_columns": ["score", "mf_providers_npi"],
        "common_joins": ["mf_providers", "mf_conditions"]
    },
    
    "mf_conditions": {  # Medical conditions
        "primary_key": "projectId",
        "description": "Medical conditions directory",
        "foreign_keys": {},
        "key_columns": ["display", "codingType", "tcSize"],
        "common_joins": ["mf_scores"]
    }
}

# Query intent patterns for rule-based SQL generation (Updated with actual table names)
query_intent_patterns = {
    "prescription_analysis": {
        "keywords": ["prescrib", "drug", "medication", "pharmacy", "dispens"],
        "primary_tables": ["fct_pharmacy_clear_claim_allstatus_cluster_brand", "as_providers_v1"],
        "typical_columns": ["NDC_PREFERRED_BRAND_NM", "PRESCRIBER_NPI_NM", "PRESCRIBER_NPI_STATE_CD"],
        "common_aggregations": ["COUNT(*)", "SUM(DISPENSED_QUANTITY_VAL)", "COUNT(DISTINCT PATIENT_ID)"]
    },
    
    "procedure_analysis": {
        "keywords": ["procedure", "surgery", "operation", "perform", "treatment"],
        "primary_tables": ["as_providers_referrals_v2", "as_providers_v1"],
        "typical_columns": ["procedure_code_description", "primary_hospital_name", "primary_type_1_npi_name"],
        "common_aggregations": ["COUNT(*)", "SUM(total_claim_charge)", "COUNT(DISTINCT primary_type_1_npi)"]
    },
    
    "payment_analysis": {
        "keywords": ["payment", "paid", "compensation", "financial", "money"],
        "primary_tables": ["as_lsf_v1", "as_providers_v1"],
        "typical_columns": ["life_science_firm_name", "amount", "nature_of_payment", "year"],
        "common_aggregations": ["SUM(amount)", "COUNT(*)", "AVG(amount)"]
    },
    
    "facility_analysis": {
        "keywords": ["hospital", "facility", "center", "asc", "ambulatory"],
        "primary_tables": ["as_providers_referrals_v2", "as_providers_v1"],
        "typical_columns": ["primary_hospital_name", "primary_type_2_npi_city", "primary_type_2_npi_state"],
        "common_aggregations": ["COUNT(*)", "COUNT(DISTINCT primary_type_1_npi)", "SUM(total_claim_charge)"]
    },
    
    "kol_analysis": {
        "keywords": ["kol", "key opinion leader", "influential", "expert", "leader"],
        "primary_tables": ["mf_providers", "mf_scores", "mf_conditions"],
        "typical_columns": ["displayName", "score", "primaryOrgName"],
        "common_aggregations": ["AVG(score)", "COUNT(*)", "MAX(score)"]
    },
    
    "provider_analysis": {
        "keywords": ["provider", "doctor", "physician", "hcp", "prescriber"],
        "primary_tables": ["as_providers_v1"],
        "typical_columns": ["first_name", "last_name", "specialties", "states"],
        "common_aggregations": ["COUNT(*)", "COUNT(DISTINCT type_1_npi)"]
    }
}

# Multi-constraint query patterns for complex analysis
multi_constraint_patterns = {
    "geographic_temporal": {
        "pattern": r"(state|city|location).*(year|month|date|time)",
        "constraints": ["location", "temporal"],
        "complexity_level": 2
    },
    
    "specialty_geographic": {
        "pattern": r"(specialty|cardiology|oncology).*(state|city|location)",
        "constraints": ["specialty", "location"],
        "complexity_level": 2
    },
    
    "drug_specialty_geographic": {
        "pattern": r"(drug|medication).*(specialty|cardiology|oncology).*(state|city|location)",
        "constraints": ["drug", "specialty", "location"],
        "complexity_level": 3
    },
    
    "procedure_geographic_temporal": {
        "pattern": r"(procedure|surgery|operation).*(state|city|location).*(year|month|date)",
        "constraints": ["procedure", "location", "temporal"],
        "complexity_level": 3
    },
    
    "comprehensive_analysis": {
        "pattern": r"(comprehensive|detailed|analysis|performance|compare)",
        "constraints": ["multiple"],
        "complexity_level": 4
    }
}

# ClickHouse-specific rules for SQL generation
clickhouse_rules = {
    "array_handling": {
        "arrays_are_1_indexed": True,
        "array_columns": ["specialties", "states", "cities", "hospital_names", "system_names", "conditions"],
        "array_access_pattern": "column_name[1]",
        "array_functions": ["arrayJoin", "has", "length", "arrayMap"]
    },
    
    "data_type_conversions": {
        "npi_joins": "toString(type_1_npi) = PRESCRIBER_NPI_NBR",
        "date_extractions": "EXTRACT(YEAR FROM date_column)",
        "string_matching": "ILIKE for case-insensitive"
    },
    
    "performance_optimizations": {
        "always_use_limit": True,
        "default_limit": 10,
        "max_limit": 100,
        "prefer_specific_columns": True,
        "avoid_select_star": True
    },
    
    "join_optimization": {
        "prefer_inner_joins": True,
        "use_table_aliases": True,
        "alias_mapping": {
            "as_providers_v1": "prov",
            "fct_pharmacy_clear_claim_allstatus_cluster_brand": "p",
            "as_lsf_v1": "pay",
            "as_providers_referrals_v2": "r",
            "mf_providers": "k",
            "mf_scores": "s",
            "mf_conditions": "c"
        }
    }
}

# Common SQL patterns for healthcare queries (Updated with actual table names)
sql_patterns = {
    "top_prescribers": {
        "template": """
SELECT 
    {prescriber_columns},
    COUNT(*) as prescription_count,
    COUNT(DISTINCT PATIENT_ID) as unique_patients
FROM fct_pharmacy_clear_claim_allstatus_cluster_brand p
INNER JOIN as_providers_v1 prov ON toString(prov.type_1_npi) = p.PRESCRIBER_NPI_NBR
WHERE {filters}
GROUP BY {group_columns}
ORDER BY prescription_count DESC
LIMIT {limit};
        """,
        "required_filters": ["drug_filter", "state_filter"],
        "optional_filters": ["specialty_filter", "date_filter"]
    },
    
    "top_facilities": {
        "template": """
SELECT 
    {facility_columns},
    COUNT(*) as procedure_count,
    COUNT(DISTINCT primary_type_1_npi) as unique_providers
FROM as_providers_referrals_v2 r
INNER JOIN as_providers_v1 prov ON r.primary_type_1_npi = prov.type_1_npi
WHERE {filters}
GROUP BY {group_columns}
ORDER BY procedure_count DESC
LIMIT {limit};
        """,
        "required_filters": ["procedure_filter", "location_filter"],
        "optional_filters": ["date_filter", "specialty_filter"]
    },
    
    "payment_analysis": {
        "template": """
SELECT 
    {payment_columns},
    SUM(amount) as total_payment,
    COUNT(*) as payment_count,
    AVG(amount) as avg_payment
FROM as_lsf_v1 pay
INNER JOIN as_providers_v1 prov ON pay.type_1_npi = prov.type_1_npi
WHERE {filters}
GROUP BY {group_columns}
ORDER BY total_payment DESC
LIMIT {limit};
        """,
        "required_filters": ["year_filter"],
        "optional_filters": ["company_filter", "specialty_filter", "state_filter"]
    }
}

# Validation rules for entity extraction
validation_rules = {
    "drug_validation": {
        "min_length": 3,
        "max_length": 50,
        "exclude_patterns": [r'\b(the|and|for|with|are|was|were)\b'],
        "common_suffixes": ["mg", "mcg", "ml", "tablet", "capsule", "injection"]
    },
    
    "state_validation": {
        "valid_codes": known_values["states"][:50],  # First 50 are state codes
        "valid_names": known_values["states"][50:],   # Remaining are full names
        "case_insensitive": True
    },
    
    "specialty_validation": {
        "valid_specialties": known_values["specialties"],
        "common_variations": {
            "cardiologist": "cardiology",
            "oncologist": "oncology",
            "endocrinologist": "endocrinology"
        }
    }
}

# Schema-aware filtering rules
schema_aware_filters = {
    "diabetes_drugs": {
        "description": "Filter for diabetes medications using actual drug names",
        "filter_sql": """(
            p.NDC_PREFERRED_BRAND_NM IN ('Ozempic', 'Mounjaro', 'Lantus', 'Humalog', 'Metformin', 'Trulicity', 'Victoza', 'Rybelsus')
            OR p.NDC_GENERIC_NM ILIKE '%metformin%'
            OR p.NDC_PREFERRED_BRAND_NM ILIKE '%insulin%'
            OR p.NDC_DRUG_CLASS_NM ILIKE '%diabetes%'
        )"""
    },
    
    "asc_facilities": {
        "description": "Filter for Ambulatory Surgical Centers using hospital name patterns",
        "filter_sql": """(
            r.primary_hospital_name ILIKE '%ambulatory%' 
            OR r.primary_hospital_name ILIKE '%surgical center%'
            OR r.primary_hospital_name ILIKE '%ASC%'
            OR r.primary_hospital_name ILIKE '%surgery center%'
        )"""
    },
    
    "cardiac_procedures": {
        "description": "Filter for cardiac procedures",
        "filter_sql": """(
            r.procedure_code_description ILIKE '%cardiac%'
            OR r.procedure_code_description ILIKE '%heart%'
            OR r.procedure_code_description ILIKE '%angioplasty%'
            OR r.procedure_code_description ILIKE '%catheterization%'
        )"""
    }
}

# Assignment-specific configurations (Updated with actual table names)
assignment_requirements = {
    "top_prescribers_query": {
        "example": "Who are the top prescribers of Ozempic in New York?",
        "required_elements": ["ranking", "drug", "provider", "location"],
        "expected_tables": ["fct_pharmacy_clear_claim_allstatus_cluster_brand", "as_providers_v1"],
        "expected_joins": ["prescription to provider"],
        "expected_filters": ["drug name", "state"]
    },
    
    "facility_procedures_query": {
        "example": "Find me the top Ambulatory Surgical Centers (ASCs) for laparoscopic procedures in Austin, Texas",
        "required_elements": ["ranking", "facility type", "procedure", "location"],
        "expected_tables": ["as_providers_referrals_v2", "as_providers_v1"],
        "expected_joins": ["referral to provider"],
        "expected_filters": ["procedure type", "city/state", "facility type"]
    },
    
    "hcp_procedures_query": {
        "example": "Which HCPs performed the most knee arthroplasties in 2023 in California?",
        "required_elements": ["ranking", "provider", "procedure", "temporal", "location"],
        "expected_tables": ["as_providers_referrals_v2", "as_providers_v1"],
        "expected_joins": ["procedure to provider"],
        "expected_filters": ["procedure name", "year", "state"]
    }
}