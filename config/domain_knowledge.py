# config/domain_knowledge.py - Fixed version with proper patient handling

# Term mappings for entity extraction - maps conceptual terms to database columns
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
    "patient": [  # Changed from "patients" to "patient"
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

# Known values for validation and entity recognition
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
    "patient": [],  # Changed from "patients" to "patient" to match term_mappings
    "numbers": []   # Added for top N queries
}

# Healthcare-specific terminology mappings
healthcare_synonyms = {
    "doctor": ["physician", "provider", "prescriber", "clinician"],
    "medicine": ["drug", "medication", "pharmaceutical", "prescription"],
    "hospital": ["medical center", "health system", "clinic", "facility"],
    "treatment": ["therapy", "procedure", "intervention", "care"],
    "disease": ["condition", "illness", "disorder", "diagnosis"],
    "payment": ["reimbursement", "compensation", "fee", "amount"]
}

# Table relationship mappings for better SQL generation
table_relationships = {
    "Payments_to_HCPs": {
        "primary_key": "type_1_npi",
        "foreign_keys": {
            "Provider_details_file": "type_1_npi"
        }
    },
    "Provider_details_file": {
        "primary_key": "type_1_npi", 
        "foreign_keys": {}
    },
    "Pharmacy_Claims_file": {
        "primary_key": "PATIENT_ID",
        "foreign_keys": {
            "Provider_details_file": "PRESCRIBER_NPI_NBR"
        }
    },
    "KOL_Providers": {
        "primary_key": "npi",
        "foreign_keys": {
            "KOL_Scores": "mf_providers_npi"
        }
    },
    "Referral_Patterns_file": {
        "primary_key": ["primary_type_1_npi", "referring_type_1_npi"],
        "foreign_keys": {
            "Provider_details_file": ["primary_type_1_npi", "referring_type_1_npi"]
        }
    }
}