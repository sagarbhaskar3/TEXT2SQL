
# utils/mock_results.py
def mock_execution_results(sql, query_type):
    """Simulate query results for commercial teams."""
    if query_type == "Prescription Analysis":
        return [
            {"PRESCRIBER_NPI_NM": "Dr. John Doe", "prescription_count": 150},
            {"PRESCRIBER_NPI_NM": "Dr. Jane Smith", "prescription_count": 120}
        ]
    elif query_type == "Procedure Analysis":
        return [
            {"primary_hospital_name": "Austin Surgical Center", "procedure_count": 200},
            {"referring_hospital_name": "Texas Health ASC", "procedure_count": 180}
        ]
    elif query_type == "KOL Analysis":
        return [
            {"displayName": "Dr. Anna Morgan", "score": 41.36},
            {"displayName": "Dr. Rashid Khalil", "score": 37.84}
        ]
    elif query_type == "Payment Analysis":
        return [
            {"first_name": "John", "last_name": "Doe", "amount": 5000.0},
            {"first_name": "Jane", "last_name": "Smith", "amount": 3000.0}
        ]
    elif query_type == "Patient Analysis":
        return [
            {"PATIENT_ID": "PAT123", "age": 45, "PRESCRIBER_NPI_STATE_CD": "NY"},
            {"PATIENT_ID": "PAT456", "age": 60, "PRESCRIBER_NPI_STATE_CD": "CA"}
        ]
    return []
