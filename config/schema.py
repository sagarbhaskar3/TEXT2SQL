# config/schema.py - Updated with Actual Database Schema
schema = {
    "as_lsf_v1": [
        {"name": "type_1_npi", "type": "UInt64", "comment": "National Provider Identifier (NPI) for healthcare providers"},
        {"name": "life_science_firm_name", "type": "String", "comment": "Names of life science firms making payments"},
        {"name": "product_name", "type": "String", "comment": "Products associated with the payments"},
        {"name": "nature_of_payment", "type": "Nullable(String)", "comment": "Type of payment (Food and Beverage, Travel, Education, etc.)"},
        {"name": "year", "type": "UInt16", "comment": "Year when the payment was made"},
        {"name": "amount", "type": "Nullable(Float32)", "comment": "Monetary amount of the payment"}
    ],
    "as_providers_v1": [
        {"name": "type_1_npi", "type": "UInt64", "comment": "Primary NPI identifier"},
        {"name": "type_2_npi_names", "type": "Array(String)", "comment": "Array of Type 2 NPI names"},
        {"name": "type_2_npis", "type": "Array(UInt64)", "comment": "Array of Type 2 NPIs"},
        {"name": "first_name", "type": "String", "comment": "Provider first name"},
        {"name": "middle_name", "type": "String", "comment": "Provider middle name"},
        {"name": "last_name", "type": "String", "comment": "Provider last name"},
        {"name": "gender", "type": "Enum8('M' = 1, 'F' = 2, 'O' = 3, 'U' = 4, '' = 5)", "comment": "Provider gender"},
        {"name": "specialties", "type": "Array(String)", "comment": "Array of medical specialties"},
        {"name": "conditions_tags", "type": "Array(Tuple(String, String))", "comment": "Array of condition tags"},
        {"name": "conditions", "type": "Array(String)", "comment": "Array of medical conditions"},
        {"name": "cities", "type": "Array(String)", "comment": "Array of cities where provider practices"},
        {"name": "states", "type": "Array(String)", "comment": "Array of states where provider practices"},
        {"name": "counties", "type": "Array(String)", "comment": "Array of counties"},
        {"name": "city_states", "type": "Array(String)", "comment": "Array of city-state combinations"},
        {"name": "hospital_names", "type": "Array(String)", "comment": "Array of hospital names"},
        {"name": "system_names", "type": "Array(String)", "comment": "Array of health system names"},
        {"name": "affiliations", "type": "String", "comment": "Provider affiliations"},
        {"name": "best_type_2_npi", "type": "UInt64", "comment": "Best Type 2 NPI"},
        {"name": "best_hospital_name", "type": "String", "comment": "Best hospital name"},
        {"name": "best_system_name", "type": "String", "comment": "Best system name"},
        {"name": "phone", "type": "Nullable(String)", "comment": "Phone number"},
        {"name": "email", "type": "Nullable(String)", "comment": "Email address"},
        {"name": "linkedin", "type": "Nullable(String)", "comment": "LinkedIn profile"},
        {"name": "twitter", "type": "Nullable(String)", "comment": "Twitter handle"}
    ],
    "as_providers_referrals_v2": [
        {"name": "primary_type_2_npi", "type": "UInt64", "comment": "Primary Type 2 NPI"},
        {"name": "referring_type_2_npi", "type": "UInt64", "comment": "Referring Type 2 NPI"},
        {"name": "primary_type_2_npi_city", "type": "String", "comment": "Primary provider city"},
        {"name": "referring_type_2_npi_city", "type": "String", "comment": "Referring provider city"},
        {"name": "primary_type_2_npi_state", "type": "String", "comment": "Primary provider state"},
        {"name": "referring_type_2_npi_state", "type": "String", "comment": "Referring provider state"},
        {"name": "primary_type_2_npi_postal_code", "type": "String", "comment": "Primary provider postal code"},
        {"name": "referring_type_2_npi_postal_code", "type": "String", "comment": "Referring provider postal code"},
        {"name": "primary_type_2_npi_lat", "type": "Float64", "comment": "Primary provider latitude"},
        {"name": "referring_type_2_npi_lat", "type": "Float64", "comment": "Referring provider latitude"},
        {"name": "primary_type_2_npi_lng", "type": "Float64", "comment": "Primary provider longitude"},
        {"name": "referring_type_2_npi_lng", "type": "Float64", "comment": "Referring provider longitude"},
        {"name": "primary_type_2_npi_name", "type": "String", "comment": "Primary Type 2 NPI name"},
        {"name": "referring_type_2_npi_name", "type": "String", "comment": "Referring Type 2 NPI name"},
        {"name": "primary_hospital_name", "type": "String", "comment": "Primary hospital name"},
        {"name": "referring_hospital_name", "type": "String", "comment": "Referring hospital name"},
        {"name": "primary_type_1_npi", "type": "UInt64", "comment": "Primary Type 1 NPI"},
        {"name": "referring_type_1_npi", "type": "UInt64", "comment": "Referring Type 1 NPI"},
        {"name": "primary_type_1_npi_name", "type": "String", "comment": "Primary Type 1 NPI name"},
        {"name": "referring_type_1_npi_name", "type": "String", "comment": "Referring Type 1 NPI name"},
        {"name": "primary_specialty", "type": "String", "comment": "Primary provider specialty"},
        {"name": "referring_specialty", "type": "String", "comment": "Referring provider specialty"},
        {"name": "date", "type": "Date", "comment": "Referral date"},
        {"name": "diagnosis_code", "type": "String", "comment": "Diagnosis code"},
        {"name": "diagnosis_code_description", "type": "String", "comment": "Diagnosis description"},
        {"name": "procedure_code", "type": "String", "comment": "Procedure code"},
        {"name": "procedure_code_description", "type": "String", "comment": "Procedure description"},
        {"name": "total_claim_charge", "type": "Float64", "comment": "Total claim charge"},
        {"name": "total_claim_line_charge", "type": "Float64", "comment": "Total claim line charge"},
        {"name": "patient_count", "type": "UInt64", "comment": "Number of patients"}
    ],
    "fct_pharmacy_clear_claim_allstatus_cluster_brand": [
        {"name": "RX_ANCHOR_DD", "type": "Date32", "comment": "Prescription anchor date"},
        {"name": "RX_CLAIM_NBR", "type": "String", "comment": "Prescription claim number"},
        {"name": "PATIENT_ID", "type": "String", "comment": "Patient identifier"},
        {"name": "SERVICE_DATE_DD", "type": "Date32", "comment": "Service date"},
        {"name": "TRANSACTION_STATUS_NM", "type": "String", "comment": "Transaction status"},
        {"name": "REJECT_REASON_1_CD", "type": "String", "comment": "Rejection reason code"},
        {"name": "REJECT_REASON_1_DESC", "type": "String", "comment": "Rejection reason description"},
        {"name": "NDC", "type": "String", "comment": "National Drug Code"},
        {"name": "NDC_DESC", "type": "String", "comment": "NDC description"},
        {"name": "NDC_GENERIC_NM", "type": "String", "comment": "Generic drug name"},
        {"name": "NDC_PREFERRED_BRAND_NM", "type": "String", "comment": "Preferred brand name"},
        {"name": "NDC_DOSAGE_FORM_NM", "type": "String", "comment": "Dosage form"},
        {"name": "NDC_DRUG_FORM_NM", "type": "String", "comment": "Drug form"},
        {"name": "NDC_DRUG_NM", "type": "String", "comment": "Drug name"},
        {"name": "NDC_DRUG_SUBCLASS_NM", "type": "String", "comment": "Drug subclass"},
        {"name": "NDC_DRUG_CLASS_NM", "type": "String", "comment": "Drug class"},
        {"name": "NDC_DRUG_GROUP_NM", "type": "String", "comment": "Drug group"},
        {"name": "NDC_ISBRANDED_IND", "type": "String", "comment": "Branded indicator"},
        {"name": "PRESCRIBED_NDC", "type": "String", "comment": "Prescribed NDC"},
        {"name": "DIAGNOSIS_CD", "type": "String", "comment": "Diagnosis code"},
        {"name": "DAW_CD", "type": "Int64", "comment": "Dispense as written code"},
        {"name": "UNIT_OF_MEASUREMENT_CD", "type": "String", "comment": "Unit of measurement"},
        {"name": "PRESCRIBER_NBR_QUAL_CD", "type": "String", "comment": "Prescriber qualifier code"},
        {"name": "PRESCRIBER_NPI_NBR", "type": "String", "comment": "Prescriber NPI number"},
        {"name": "PRESCRIBER_NPI_NM", "type": "String", "comment": "Prescriber NPI name"},
        {"name": "PRESCRIBER_NPI_ENTITY_CD", "type": "Int64", "comment": "Prescriber entity code"},
        {"name": "PRESCRIBER_NPI_HCO_CLASS_OF_TRADE_DESC", "type": "String", "comment": "HCO class of trade"},
        {"name": "PRESCRIBER_NPI_HCP_SEGMENT_DESC", "type": "String", "comment": "HCP segment description"},
        {"name": "PRESCRIBER_NPI_STATE_CD", "type": "String", "comment": "Prescriber state code"},
        {"name": "PRESCRIBER_NPI_ZIP5_CD", "type": "String", "comment": "Prescriber ZIP code"},
        {"name": "PAYER_ID", "type": "Int64", "comment": "Payer identifier"},
        {"name": "PAYER_PAYER_NM", "type": "String", "comment": "Payer name"},
        {"name": "PAYER_COB_SEQ_VAL", "type": "Int64", "comment": "Coordination of benefits sequence"},
        {"name": "PAYER_PLAN_SUBCHANNEL_CD", "type": "String", "comment": "Payer plan subchannel code"},
        {"name": "PAYER_PLAN_SUBCHANNEL_NM", "type": "String", "comment": "Payer plan subchannel name"},
        {"name": "PAYER_PLAN_CHANNEL_CD", "type": "String", "comment": "Payer plan channel code"},
        {"name": "PAYER_PLAN_CHANNEL_NM", "type": "String", "comment": "Payer plan channel name"},
        {"name": "PAYER_COMPANY_NM", "type": "String", "comment": "Payer company name"},
        {"name": "PAYER_MCO_ISSUER_ID", "type": "String", "comment": "MCO issuer ID"},
        {"name": "PAYER_MCO_ISSUER_NM", "type": "String", "comment": "MCO issuer name"},
        {"name": "PAYER_BIN_NBR", "type": "String", "comment": "Payer BIN number"},
        {"name": "PAYER_PCN_NBR", "type": "String", "comment": "Payer PCN number"},
        {"name": "PAYER_GROUP_STR", "type": "String", "comment": "Payer group string"},
        {"name": "FILL_NUMBER_VAL", "type": "Int64", "comment": "Fill number"},
        {"name": "DISPENSED_QUANTITY_VAL", "type": "Decimal(38,9)", "comment": "Dispensed quantity"},
        {"name": "PRESCRIBED_QUANTITY_VAL", "type": "Decimal(38,9)", "comment": "Prescribed quantity"},
        {"name": "DAYS_SUPPLY_VAL", "type": "Decimal(38,9)", "comment": "Days supply"},
        {"name": "NUMBER_OF_REFILLS_AUTHORIZED_VAL", "type": "Int64", "comment": "Number of authorized refills"},
        {"name": "GROSS_DUE_AMT", "type": "Decimal(38,9)", "comment": "Gross amount due"},
        {"name": "TOTAL_PAID_AMT", "type": "Decimal(38,9)", "comment": "Total amount paid"},
        {"name": "PATIENT_TO_PAY_AMT", "type": "Decimal(38,9)", "comment": "Patient payment amount"},
        {"name": "AWP_UNIT_PRICE_AMT", "type": "Float64", "comment": "AWP unit price"},
        {"name": "AWP_CALC_AMT", "type": "Float64", "comment": "AWP calculated amount"}
    ],
    "mf_conditions": [
        {"name": "projectId", "type": "Int32", "comment": "Unique project identifier for the condition"},
        {"name": "display", "type": "Nullable(String)", "comment": "Human-readable condition name"},
        {"name": "codingType", "type": "Nullable(String)", "comment": "Type of coding (condition or procedure)"},
        {"name": "tcSize", "type": "Nullable(Int32)", "comment": "Clinical trial or dataset size"}
    ],
    "mf_providers": [
        {"name": "npi", "type": "Int32", "comment": "National Provider Identifier"},
        {"name": "docId", "type": "Nullable(String)", "comment": "Document identifier"},
        {"name": "personId", "type": "Nullable(Int32)", "comment": "Person identifier"},
        {"name": "name", "type": "Nullable(String)", "comment": "Provider full name"},
        {"name": "displayName", "type": "Nullable(String)", "comment": "Display name for provider"},
        {"name": "initials", "type": "Nullable(String)", "comment": "Provider initials"},
        {"name": "familyName", "type": "Nullable(String)", "comment": "Provider family name"},
        {"name": "score", "type": "Nullable(Float32)", "comment": "Provider performance score"},
        {"name": "phone", "type": "Nullable(String)", "comment": "Contact phone number"},
        {"name": "isUSPrescriber", "type": "Nullable(Bool)", "comment": "US prescriber authorization"},
        {"name": "sex", "type": "Nullable(String)", "comment": "Provider gender"},
        {"name": "image", "type": "Nullable(String)", "comment": "Provider image URL"},
        {"name": "primaryOrgName", "type": "Nullable(String)", "comment": "Primary organization name"},
        {"name": "primaryOrgWebsite", "type": "Nullable(String)", "comment": "Primary organization website"},
        {"name": "highlyRatedConditionsCount", "type": "Nullable(Int32)", "comment": "Count of highly rated conditions"},
        {"name": "orgLogo", "type": "Nullable(String)", "comment": "Organization logo URL"},
        {"name": "orgWebsite", "type": "Nullable(String)", "comment": "Organization website"},
        {"name": "healthSystem_website", "type": "Nullable(String)", "comment": "Health system website"},
        {"name": "healthSystem_name", "type": "Nullable(String)", "comment": "Health system name"},
        {"name": "codingCount", "type": "Nullable(Int32)", "comment": "Medical coding count"},
        {"name": "biography", "type": "Nullable(String)", "comment": "Provider biography"},
        {"name": "gradInstitution_year", "type": "Nullable(Int32)", "comment": "Graduation year"},
        {"name": "gradInstitution_gradYearNumber", "type": "Nullable(Int32)", "comment": "Graduation year number"},
        {"name": "gradInstitution_name", "type": "Nullable(String)", "comment": "Graduation institution name"},
        {"name": "trainingInstitution_year", "type": "Nullable(Int32)", "comment": "Training completion year"},
        {"name": "trainingInstitution_gradYearNumber", "type": "Nullable(Int32)", "comment": "Training year number"},
        {"name": "trainingInstitution_name", "type": "Nullable(String)", "comment": "Training institution name"}
    ],
    "mf_scores": [
        {"name": "id", "type": "Int32", "comment": "Unique score entry identifier"},
        {"name": "score", "type": "Nullable(Float32)", "comment": "Score value"},
        {"name": "mf_providers_npi", "type": "Nullable(Int32)", "comment": "Provider NPI from mf_providers"},
        {"name": "mf_conditions_projectId", "type": "Nullable(Int32)", "comment": "Project ID from mf_conditions"}
    ]
}

# Table name mappings for backward compatibility
TABLE_NAME_MAPPING = {
    "Payments_to_HCPs": "as_lsf_v1",
    "Provider_details_file": "as_providers_v1", 
    "Referral_Patterns_file": "as_providers_referrals_v2",
    "Diagnosis_Procedures_file": "as_providers_referrals_v2",  # Same table as referrals
    "Pharmacy_Claims_file": "fct_pharmacy_clear_claim_allstatus_cluster_brand",
    "Condition_Directory_file": "mf_conditions",
    "KOL_Providers": "mf_providers",
    "KOL_Scores": "mf_scores"
}

def get_table_columns(table_name: str) -> list:
    """Get column names for a table"""
    # Map old names to new names
    actual_table_name = TABLE_NAME_MAPPING.get(table_name, table_name)
    
    if actual_table_name in schema:
        return [col["name"] for col in schema[actual_table_name]]
    return []

def validate_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    columns = get_table_columns(table_name)
    return column_name in columns

def get_all_table_names() -> list:
    """Get all available table names"""
    return list(schema.keys())