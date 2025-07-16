🏥 Text2SQL Healthcare Analytics System
Transform natural language into precise SQL queries for healthcare data using AI.

📘 Project Overview
The Text2SQL Healthcare Analytics System is an AI-powered platform designed to translate natural language questions into optimized SQL queries for analyzing healthcare data stored in ClickHouse databases. This tool empowers commercial teams, data analysts, and healthcare professionals to query complex datasets in plain English without requiring SQL expertise.

🛠️ Methods Used
1. HyDE (Hypothetical Document Embeddings)
The system employs HyDE to enhance the accuracy of SQL generation. For each natural language query, the AI generates three hypothetical SQL examples that represent ideal responses. These examples are used to guide the final query generation, reducing hallucinations and improving alignment with the user's intent. This approach leverages structural context to refine the output, making it particularly effective for complex healthcare queries.

2. Tiered Confidence Scoring
A three-tier evaluation system assesses the quality of generated SQL queries, focusing on syntax, entity accuracy, and executability. This method ensures robust validation and provides a confidence score to gauge reliability.

3. Healthcare Entity Recognition
Advanced entity detection identifies critical healthcare elements (e.g., drugs, procedures) using domain-specific mappings, enhancing query precision.

4. Vector Context Retrieval
The system integrates Weaviate, a vector database, to retrieve semantically relevant context, improving the interpretation of natural language inputs.

🎯 Key Features
🧠 Natural Language to SQL: Convert English queries into accurate SQL using advanced AI models.
🏥 Healthcare-Specific Entity Recognition: Identify and extract drugs, procedures, specialties, locations, and conditions.
🤖 Multi-Model AI Integration: Supports Google Gemini and local Ollama models (with Ollama as a fallback for private execution).
📊 HyDE SQL Examples: Enhance output accuracy with hypothetical document embeddings.
✅ Real-time Schema Validation: Ensure generated SQL aligns with ClickHouse table schemas.
📈 Tiered Confidence Scoring: Evaluate query accuracy across three tiers.
🔍 Vector Context Retrieval: Leverage Weaviate for semantic context enhancement.
🏗️ Architecture
text

Collapse

Wrap

Copy
text2sql-healthcare/
├── main.py                          # Streamlit frontend
├── core/
│   ├── system_initializer.py        # System initialization
│   ├── query_processor.py           # Text2SQL pipeline
│   ├── hyde_generator.py            # HyDE example generation
│   ├── context_retriever.py         # Weaviate-based context search
│   └── confidence_calculator.py     # Tiered confidence scoring
├── models/
│   └── hybrid_sql_generator.py      # Multi-model generation logic
├── utils/
│   ├── ui_components.py             # UI elements
│   ├── logging_utils.py             # Logging utilities
│   ├── entity_mapper.py             # Domain-aware entity detection
│   ├── query_classifier.py          # Query intent classification
│   ├── schema_validator.py          # SQL schema verification
│   └── sql_evaluator.py             # SQL quality evaluation
├── config/
│   ├── app_config.py                # Application configuration
│   ├── schema.py                    # Database schema definitions
│   ├── domain_knowledge.py          # Healthcare domain knowledge
│   └── prompts.py                   # Prompt templates
└── requirements.txt                 # Project dependencies
🚀 Setup & Installation
Prerequisites
Python 3.8+
ClickHouse Database
Weaviate Vector Database
API key for Google Gemini or Ollama model
Steps
Clone the repository:
bash

Collapse

Wrap

Run

Copy
git clone <repository-url>
cd text2sql-healthcare
Install dependencies:
bash

Collapse

Wrap

Run

Copy
pip install -r requirements.txt
Create a .env file with the following configuration:
text

Collapse

Wrap

Copy
# Model Keys
GOOGLE_API_KEY=your_google_key
OLLAMA_MODEL=llama3:8b

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=docnexus
CLICKHOUSE_PASSWORD=your_password

# Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your_weaviate_key
Run the application:
bash

Collapse

Wrap

Run

Copy
streamlit run main.py
📊 Methodology
1. HyDE (Hypothetical Document Embeddings)
AI generates 3 SQL examples per query to reduce hallucinations and improve accuracy.
2. Tiered Confidence Scoring

Tier	Category	Weight
1	SQL Syntax & ClickHouse Compatibility	40%
2	Entity Accuracy & Query Intent	35%
3	Executability & Runtime Performance	25%
3. Healthcare Entity Recognition
Supports detection of:

🧪 Drugs: e.g., Ozempic, Trulicity
⚕️ Procedures: e.g., CPT codes
🩺 Providers: e.g., NPIs, specialties
📍 Locations: e.g., CA, TX
🦠 Conditions: e.g., ICD codes
4. Multi-Model AI Integration

Model	Use Case
Gemini	Complex healthcare reasoning
Ollama	Private, offline model execution (fallback)
🗄️ Database Schema

Table	Description
as_lsf_v1	HCP Payments
fct_pharmacy_clear_claim_allstatus_cluster_brand	Claims
as_providers_v1	Provider Details
as_providers_referrals_v2	Referrals
kol_providers_v1	Opinion Leaders
kol_scores_v1	KOL Scores
📈 Example Queries
sql

Collapse

Wrap

Copy
"Top prescribers of Ozempic in California"
"Compare prescribing trends between cardiologists and endocrinologists"
"Find cardiologists in Texas with high pharma payments and referral volumes"
🔧 Configuration
Modify settings in config/app_config.py:
Model priority: gemini > ollama
Prompt tuning
Timeout settings
📝 Assumptions
Consistent use of NPI IDs across datasets.
ClickHouse schema adheres to the defined format.
Weaviate vector DB is populated with relevant data.
Models are stateless and respect data privacy.
🚧 Limitations
Weaviate Capacity: Free version limited to 1,000 records.
Open-Source Models: No fine-tuning capabilities, affecting precision.
Single-DB Support: Only ClickHouse currently supported.
Temporal Analysis: Basic date-based filtering.
Streaming Not Supported: No real-time ingestion or live query processing.
Data Visualization: Tabular only; no charts/graphs yet.
🔮 Future Enhancements
🔁 Architectural Improvements:
✅ Model-Agnostic Pipeline: Dynamic LLM switching based on query type and load.
🛠️ MCP Tools & Pipelines: Incorporate MLOps for monitoring, retraining, and versioning.
🧠 Agentic Framework Integration: Enable autonomous query decomposition with LangGraph or AutoGen.
🧩 Context Engineering Feedback Loop: Implement human-in-the-loop corrections.
🌐 Multi-DB Support: Add PostgreSQL, MySQL, and Snowflake.
🔒 Security & Compliance: Ensure HIPAA compliance, no PHI exposure, API key security, and optional rate limiting.
🐛 Troubleshooting

Issue	Resolution
Model Timeout	Verify .env keys and network
Weaviate Errors	Ensure schema and index exist
Low Confidence	Tune prompts or improve entity mappings
SQL Errors	Check for schema mismatch in ClickHouse
📚 Dependencies
text

Collapse

Wrap

Copy
streamlit
clickhouse-connect
weaviate-client
google-generativeai
ollama
sqlglot
pandas
numpy
python-dotenv


