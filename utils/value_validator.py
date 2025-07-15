
# utils/value_validator.py
import logging
import clickhouse_connect
from config.schema import schema
from config.domain_knowledge import known_values

# Configure logging
logging.basicConfig(filename="text2sql.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# ClickHouse Client
clickhouse_client = clickhouse_connect.get_client(host='localhost', port=8123, database='docnexus', password='mysecret')

def validate_values(entities, mappings):
    """Validate query entities in ClickHouse database."""
    value_score = 0.0
    value_message = "Values validated"
    value_count = sum(len(v) for v in entities.values())
    valid_values = 0
    
    for entity_type, values in entities.items():
        for value in values:
            found = False
            for col in mappings.get(entity_type, {}).get("columns", []):
                for table in schema:
                    if col in [c["name"] for c in schema[table]]:
                        query = f"SELECT COUNT(*) FROM {table} WHERE {col} = %s"
                        try:
                            result = clickhouse_client.query(query, parameters=[value]).result_rows
                            if result and result[0][0] > 0:
                                found = True
                                valid_values += 1
                                break
                        except Exception as e:
                            logging.error(f"Error validating {value} in {table}.{col}: {str(e)}")
                if found:
                    break
            if not found and value in known_values.get(entity_type, []):
                valid_values += 1
                found = True
            if not found:
                value_message = f"Value not found in database or known values: {value}"
    
    value_score = valid_values / value_count if value_count > 0 else 0.0
    return value_score, value_message
