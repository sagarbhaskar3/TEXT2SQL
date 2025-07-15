# DocNexus.ai Text2SQL Prototype

## Overview
A prototype for translating natural language queries into ClickHouse-compliant SQL for healthcare claims data. Uses LlamaIndex with Llama 3 8B for HyDE, `NumbersStation/nsql-350M` for SQL generation, ClickHouse for full data storage (~80,000 rows), and Weaviate for context retrieval. Streamlit provides the UI for commercial teams.

## Setup
1. Install: `pip install -r requirements.txt`
2. Run ClickHouse: `docker run -d -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server:latest`
3. Run Weaviate: `docker run -d -p 8080:8080 semitechnologies/weaviate:latest`
4. Authenticate Hugging Face: `huggingface-cli login` (for Llama 3 8B)
5. Place CSV files (8 tables, ~10,000 rows each) in `data/` and `nsql_finetuned_lora` and `balanced_finetune_data.jsonl` in `docnexus-text2sql/`.
6. Run: `streamlit run main.py`

## Assumptions
- ~80,000 rows stored in ClickHouse for value validation.
- Weaviate stores schema, ~280 query-SQL examples, and ~1,000 sample rows.
- No query execution; uses `sqlglot` and mock results.
- SQL is ClickHouse-compliant (`arrayJoin`, `Enum8`, `Date32`).

## Features
- **LlamaIndex HyDE**: Uses Llama 3 8B for hypothetical SQL snippets.
- **Full Data Storage**: ~80,000 rows in ClickHouse for validation.
- **Query Classification**: Identifies query type and tables.
- **Term Mapping**: Maps terms (e.g., “drug” → `NDC_PREFERRED_BRAND_NM`).
- **Evaluation**: `sqlglot` validates syntax, schema, ClickHouse types; ClickHouse validates values.
- **Streamlit UI**: Displays SQL, mappings, evaluation, and mock results.

## Limitations
- Weaviate stores ~1,000 sample rows for context; full data in ClickHouse.
- Limited fine-tuning dataset (~280 examples) may affect complex queries.
- Llama 3 8B requires ~8GB VRAM, `nsql-350M` ~700MB.

## Directory Structure