
import pandas as pd
import json
import logging
import weaviate
from llama_index.core import VectorStoreIndex, Document
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
import clickhouse_connect
from config.schema import schema

# Configure logging
logging.basicConfig(filename="text2sql.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def create_clickhouse_client():
    """Create a new ClickHouse client instance."""
    return clickhouse_connect.get_client(
        host='localhost',
        port=8123,
        database='docnexus',
        username='default',
        password='mysecret'
    )

def create_clickhouse_tables():
    """Create ClickHouse tables for all CSV data."""
    client = create_clickhouse_client()
    try:
        type_mapping = {
            "UInt64": "UInt64",
            "String": "String",
            "Nullable(String)": "Nullable(String)",
            "UInt16": "UInt16",
            "Nullable(Float32)": "Nullable(Float32)",
            "Array(String)": "Array(String)",
            "Enum8('M' = 1, 'F' = 2, 'O' = 3, 'U' = 4, '' = 5)": "Enum8('M' = 1, 'F' = 2, 'O' = 3, 'U' = 4, '' = 5)",
            "Array(Tuple(String, String))": "Array(Tuple(String, String))",
            "Array(UInt64)": "Array(UInt64)",
            "Date": "Date",
            "Float64": "Float64",
            "Date32": "Date32",
            "Int64": "Int64",
            "Decimal(38,9)": "Decimal(38,9)",
            "Int32": "Int32",
            "Nullable(Int32)": "Nullable(Int32)",
            "Nullable(Bool)": "Nullable(UInt8)"
        }

        for table, columns in schema.items():
            columns_def = ", ".join([f"{col['name']} {type_mapping[col['type']]}" for col in columns])
            query = f"CREATE TABLE IF NOT EXISTS {table} ({columns_def}) ENGINE = MergeTree() ORDER BY tuple()"
            client.command(query)
            logging.info(f"Created table {table}")
    finally:
        client.close()

def load_csv_to_clickhouse():
    """Load all rows from CSVs into ClickHouse."""
    csv_files = [
        "data/csv_files/Payments_to_HCPs.csv",
        "data/csv_files/Provider_details_file.csv",
        "data/csv_files/Referral_Patterns_file.csv",
        "data/csv_files/Diagnosis_Procedures_file.csv",
        "data/csv_files/Pharmacy_Claims_file.csv",
        "data/csv_files/Condition_Directory_file.csv",
        "data/csv_files/KOL_Providers.csv",
        "data/csv_files/KOL_Scores.csv"
    ]
    for file in csv_files:
        client = create_clickhouse_client()
        try:
            table_name = file.split("/")[-1].split(".")[0]
            df = pd.read_csv(file)
            # Convert to appropriate types based on schema
            for col in df.columns:
                if col in [c["name"] for c in schema.get(table_name, [])]:
                    col_schema = next((c for c in schema.get(table_name, []) if c["name"] == col), {})
                    if col_schema.get("type") == "String":
                        df[col] = df[col].astype(str).fillna("")
                    elif col_schema.get("type") in ["Int64", "UInt64", "Int32", "UInt16", "Float64", "Nullable(Float32)", "Decimal(38,9)"]:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    elif col_schema.get("type") in ["Date", "Date32"]:
                        df[col] = pd.to_datetime(df[col], errors='coerce').fillna(pd.NaT)
                    else:
                        df[col] = df[col].where(pd.notna(df[col]), None)
            # Drop PATIENT_ID if not in schema
            if "PATIENT_ID" in df.columns and "PATIENT_ID" not in [c["name"] for c in schema.get(table_name, [])]:
                df = df.drop(columns=["PATIENT_ID"])
            client.insert_df(table_name, df)
            logging.info(f"Loaded {len(df)} rows into {table_name}")
        except Exception as e:
            logging.error(f"Error loading {file} into ClickHouse: {str(e)}")
        finally:
            client.close()

# Weaviate Setup
weaviate_client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    grpc_port=50051,
    skip_init_checks=True
)

embedder = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = WeaviateVectorStore(weaviate_client=weaviate_client, class_name="SchemaAndExamples")

def setup_weaviate():
    """Setup Weaviate schema."""
    if weaviate_client.collections.exists("SchemaAndExamples"):
        weaviate_client.collections.delete("SchemaAndExamples")

def load_data_to_weaviate():
    """Load schema, query-SQL examples, and sample data into Weaviate."""
    documents = []

    # Schema Documents
    for table, columns in schema.items():
        columns_str = ", ".join([f"{col['name']} ({col['type']})" for col in columns])
        documents.append(Document(
            text=f"Table: {table}\nColumns: {columns_str}",
            metadata={"type": "schema", "table": table, "values": ""}
        ))

    # Example Query-SQL Pairs
    dataset_path = "data/balanced_finetune_data.jsonl"
    try:
        examples = []
        with open(dataset_path, "r") as f:
            for line in f:
                examples.append(json.loads(line.strip()))
        for example in examples:
            documents.append(Document(
                text=f"Query: {example['query']}\nSQL: {example['sql']}\nTables: {', '.join(example['tables'])}",
                metadata={"type": "example", "table": ",".join(example['tables']), "values": ""}
            ))
    except FileNotFoundError:
        logging.warning("Fine-tuning dataset not found. Skipping example queries.")

    # Sample Data (~1,000 rows total, ~125 per table)
    csv_files = [
        "data/csv_files/Payments_to_HCPs.csv",
        "data/csv_files/Provider_details_file.csv",
        "data/csv_files/Referral_Patterns_file.csv",
        "data/csv_files/Diagnosis_Procedures_file.csv",
        "data/csv_files/Pharmacy_Claims_file.csv",
        "data/csv_files/Condition_Directory_file.csv",
        "data/csv_files/KOL_Providers.csv",
        "data/csv_files/KOL_Scores.csv"
    ]
    sample_values = {}
    for file in csv_files:
        try:
            table_name = file.split("/")[-1].split(".")[0]
            df = pd.read_csv(file, nrows=125)
            samples = df.head(5).to_dict(orient="records")
            sample_doc = f"Table: {table_name}\nSample Data: {json.dumps(samples, indent=2)}"
            values = {}
            for col in df.columns:
                if col in [c["name"] for c in schema.get(table_name, [])]:
                    unique_vals = df[col].dropna().astype(str).unique().tolist()[:10]
                    values[col] = unique_vals

            # Truncate values string if too long
            values_str = json.dumps(values)
            if len(values_str) > 500:
                values_str = values_str[:480] + "... (truncated)"

            documents.append(Document(
                text=sample_doc,
                metadata={"type": "sample_data", "table": table_name, "values": values_str}
            ))

            sample_values[table_name] = values
        except Exception as e:
            logging.error(f"Error loading {file} samples: {str(e)}")

    # Create VectorStoreIndex with larger chunk size
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=embedder,
        vector_store=vector_store,
        transformations=[SentenceSplitter(chunk_size=2048)]
    )
    logging.info("Weaviate data loaded")
    return index, sample_values

# Entry Point
if __name__ == "__main__":
    try:
        setup_weaviate()
        index, sample_values = load_data_to_weaviate()
    finally:
        weaviate_client.close()