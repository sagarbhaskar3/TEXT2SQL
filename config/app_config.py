# config/app_config.py - Updated Application Configuration
import os

# Application Configuration
APP_CONFIG = {
    'app_title': "DocNexus.ai Text2SQL - Healthcare Analytics",
    'app_icon': "🏥",
    'app_description': "Transform natural language into precise SQL queries for healthcare data analysis"
}

# Database Configuration
DATABASE_CONFIG = {
    'clickhouse': {
        'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
        'port': int(os.getenv('CLICKHOUSE_PORT', 8123)),
        'database': os.getenv('CLICKHOUSE_DATABASE', 'docnexus'),
        'username': os.getenv('CLICKHOUSE_USERNAME', 'default'),
        'password': os.getenv('CLICKHOUSE_PASSWORD', 'mysecret')
    },
    'weaviate': {
        'host': os.getenv('WEAVIATE_HOST', 'localhost'),
        'port': int(os.getenv('WEAVIATE_PORT', 8080)),
        'grpc_port': int(os.getenv('WEAVIATE_GRPC_PORT', 50051))
    }
}

# AI Model Configuration
AI_CONFIG = {
    'google_api_key': os.getenv('GOOGLE_API_KEY'),
    'preferred_ollama_models': ['llama3:latest', 'mistral:latest', 'codellama:latest'],
    'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2'
}

# Logging Configuration
LOGGING_CONFIG = {
    'log_file': 'text2sql.log',
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    'csv_log_file': 'evaluation.csv'
}

# Sample Queries for UI
SAMPLE_QUERIES = [
    "Who are the top 10 prescribers of Ozempic in New York?",
    "Find the top Ambulatory Surgical Centers for laparoscopic procedures in Texas",
    "Which pharmaceutical companies paid the most to doctors in 2023?",
    "Most prescribed diabetes medications by endocrinologists in California",
    "Top facilities for cardiac procedures with provider expertise analysis",
    "Show me providers who prescribed both Metformin and Lipitor in Texas"
]

# UI Configuration
UI_CONFIG = {
    'max_query_length': 500,
    'default_query_height': 100,
    'show_sample_results': False,
    'enable_detailed_analysis': True,
    'confidence_thresholds': {
        'excellent': 0.90,
        'very_good': 0.80,
        'good': 0.70,
        'fair': 0.60,
        'poor': 0.50
    }
}

# Data Processing Configuration
PROCESSING_CONFIG = {
    'max_hyde_examples': 3,
    'max_context_documents': 5,
    'default_sql_limit': 10,
    'max_sql_limit': 100,
    'query_timeout': 30  # seconds
}