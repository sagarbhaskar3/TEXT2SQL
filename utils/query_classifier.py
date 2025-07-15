
# utils/query_classifier.py
from config.domain_knowledge import known_values
from config.schema import schema

def classify_query(query):
    """Classify query type and relevant tables."""
    query = query.lower()
    if "prescription" in query or "prescribe" in query or any(drug in query for drug in known_values["drugs"]):
        return "Prescription Analysis", ["Pharmacy_Claims_file", "KOL_Providers", "Provider_details_file"]
    elif "procedure" in query or "surgery" in query or any(proc in query for proc in known_values["procedures"]):
        return "Procedure Analysis", ["Referral_Patterns_file", "Diagnosis__Procedure_file", "Provider_details_file"]
    elif "payment" in query or "life science" in query:
        return "Payment Analysis", ["Payments_to_HCPs", "Provider_details_file"]
    elif "kol" in query or "opinion leader" in query:
        return "KOL Analysis", ["KOL_Providers", "KOL_Scores", "Condition_Directory_file"]
    elif "patient" in query or any(p in query for p in known_values["patients"]):
        return "Patient Analysis", ["Pharmacy_Claims_file"]
    else:
        return "Complex Multi-table", list(schema.keys())
