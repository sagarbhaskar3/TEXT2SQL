# main.py - Fixed version with proper HyDE, validation, and confidence calculation using Gemini 2.5
import json
import csv
import os
from datetime import datetime
import streamlit as st
import logging
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from utils.data_loader import create_clickhouse_tables, load_csv_to_clickhouse, setup_weaviate, load_data_to_weaviate, create_clickhouse_client
from utils.query_classifier import classify_query
from utils.entity_mapper import extract_entities
from utils.sql_evaluator import evaluate_sql
from utils.mock_results import mock_execution_results
from models.hybrid_sql_generator import HybridSQLGenerator
from llama_index.core import Settings

Settings.llm = None

# Configure logging
logging.basicConfig(
    filename="text2sql.log", 
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the hybrid SQL generator
@st.cache_resource
def initialize_hybrid_generator():
    """Initialize the hybrid SQL generator with caching"""
    try:
        generator = HybridSQLGenerator()
        logger.info("✅ Hybrid SQL generator initialized successfully")
        return generator
    except Exception as e:
        logger.error(f"❌ Failed to initialize hybrid generator: {e}")
        return None

# Initialize Data
@st.cache_resource
def initialize_data_systems():
    """Initialize all data systems with caching"""
    try:
        logger.info("🚀 Initializing data systems...")
        
        create_clickhouse_tables()
        load_csv_to_clickhouse()
        setup_weaviate()
        index, sample_values = load_data_to_weaviate()
        
        logger.info("✅ Data systems initialized successfully")
        return index, sample_values
        
    except Exception as e:
        logger.error(f"❌ Data system initialization failed: {e}")
        return None, None

def generate_hyde_sql_examples(query, hybrid_generator):
    """Generate actual SQL examples using HyDE approach with Gemini"""
    try:
        logger.info("🔄 Generating HyDE SQL examples...")
        
        # Use the hybrid generator to create hypothetical SQL examples
        hyde_prompt = f"""Generate 2-3 different SQL query examples for this healthcare question:
        
Question: "{query}"

Generate realistic ClickHouse SQL queries that could answer similar questions.
Focus on these healthcare tables:
- fct_pharmacy_clear_claim_allstatus_cluster_brand (prescriptions)
- as_providers_v1 (providers) 
- as_lsf_v1 (payments)

Return only SQL queries, one per line:"""

        # Generate HyDE examples using Gemini if available
        if hybrid_generator.gemini_client:
            try:
                response = hybrid_generator.gemini_client.generate_content(
                    f"You are a SQL expert. Generate only SQL queries, no explanations.\n\n{hyde_prompt}",
                    stream=False
                )
                
                hyde_response = response.text
                
                # Extract SQL queries from response
                hyde_examples = []
                for line in hyde_response.split('\n'):
                    line = line.strip()
                    if line and ('SELECT' in line.upper() or 'WITH' in line.upper()):
                        # Clean the SQL
                        cleaned = line.replace('```sql', '').replace('```', '').strip()
                        if cleaned and not cleaned.startswith('--'):
                            hyde_examples.append(cleaned)
                
                logger.info(f"✅ Generated {len(hyde_examples)} HyDE SQL examples")
                return hyde_examples[:3]  # Return max 3 examples
                
            except Exception as e:
                logger.warning(f"HyDE generation with Gemini failed: {e}")
        
        # Fallback: Generate simple template examples
        logger.info("Using fallback HyDE templates")
        return [
            "SELECT PRESCRIBER_NPI_NM, COUNT(*) FROM fct_pharmacy_clear_claim_allstatus_cluster_brand GROUP BY PRESCRIBER_NPI_NM;",
            "SELECT NDC_PREFERRED_BRAND_NM, COUNT(*) FROM fct_pharmacy_clear_claim_allstatus_cluster_brand GROUP BY NDC_PREFERRED_BRAND_NM;",
            "SELECT PRESCRIBER_NPI_STATE_CD, COUNT(*) FROM fct_pharmacy_clear_claim_allstatus_cluster_brand GROUP BY PRESCRIBER_NPI_STATE_CD;"
        ]
        
    except Exception as e:
        logger.error(f"❌ HyDE generation failed: {e}")
        return []

def retrieve_context(query, query_type, relevant_tables, hyde_examples, index):
    """Retrieve context from Weaviate using LlamaIndex with HyDE examples"""
    try:
        if not index:
            logger.warning("Index not available, returning empty context")
            return [], [], []
            
        query_engine = index.as_query_engine(similarity_top_k=5)
        
        # Build enhanced query string with HyDE examples
        hyde_sql_context = "\n".join(hyde_examples) if hyde_examples else ""
        query_str = f"{query}\n\nSimilar SQL patterns:\n{hyde_sql_context}"
        
        response = query_engine.query(query_str)
        
        documents = [str(doc) for doc in response.source_nodes]
        distances = [node.score for node in response.source_nodes]
        values = []
        
        for node in response.source_nodes:
            try:
                metadata = node.metadata
                values.append(json.loads(metadata.get("values", "{}")))
            except:
                values.append({})
        
        logger.info(f"✅ Retrieved {len(documents)} context documents with HyDE enhancement")
        return documents, distances, values
        
    except Exception as e:
        logger.error(f"❌ Context retrieval failed: {e}")
        return [], [], []

def validate_sql_against_clickhouse(sql):
    """Enhanced SQL validation supporting WITH clauses and better error handling"""
    try:
        import clickhouse_connect
        
        # Enhanced SQL syntax validation
        def is_valid_sql_syntax(sql_text):
            """Check if SQL has valid starting keywords and basic structure"""
            if not sql_text or not sql_text.strip():
                return False, "Empty SQL"
            
            sql_upper = sql_text.strip().upper()
            
            # Valid starting keywords
            valid_starts = ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
            
            # Check if starts with valid keyword
            starts_valid = any(sql_upper.startswith(keyword) for keyword in valid_starts)
            if not starts_valid:
                return False, f"SQL must start with one of: {', '.join(valid_starts)}"
            
            # For WITH statements, ensure they contain SELECT
            if sql_upper.startswith('WITH'):
                if 'SELECT' not in sql_upper:
                    return False, "WITH clause must contain SELECT statement"
            
            # Basic structure validation
            if sql_upper.startswith(('SELECT', 'WITH')):
                if 'FROM' not in sql_upper and sql_upper.startswith('SELECT'):
                    # Allow SELECT without FROM for simple expressions
                    if not any(func in sql_upper for func in ['NOW()', 'CURRENT_DATE', 'VERSION()', '1', '2', '3']):
                        return False, "SELECT statement should contain FROM clause"
            
            return True, "Valid SQL syntax"
        
        # First, check syntax
        syntax_valid, syntax_message = is_valid_sql_syntax(sql)
        if not syntax_valid:
            return {
                'valid': False,
                'executable': False,
                'error': syntax_message,
                'result_count': 0,
                'validation_type': 'syntax_check'
            }
        
        # Try multiple connection approaches
        connection_attempts = [
            {'host': 'localhost', 'port': 8123, 'username': 'default'},
            {'host': 'localhost', 'port': 8123, 'username': 'default', 'password': ''},
            {'host': 'localhost', 'port': 8123, 'username': 'default', 'database': 'docnexus'},
            {'host': '127.0.0.1', 'port': 8123, 'username': 'default'},
        ]
        
        for i, config in enumerate(connection_attempts):
            try:
                logger.info(f"🔍 ClickHouse attempt {i+1}: {config}")
                client = clickhouse_connect.get_client(**config)
                
                # Test connection
                client.query("SELECT 1")
                
                # Prepare test SQL with LIMIT to avoid large results
                test_sql = sql
                if 'LIMIT' not in sql.upper():
                    # Add LIMIT carefully for different SQL types
                    if sql.upper().strip().startswith('WITH'):
                        # For WITH statements, add LIMIT to the final SELECT
                        test_sql = sql.rstrip(';') + ' LIMIT 1;'
                    elif sql.upper().strip().startswith('SELECT'):
                        test_sql = sql.rstrip(';') + ' LIMIT 1;'
                
                logger.info(f"🔍 Testing SQL: {test_sql[:150]}...")
                
                # Execute the query
                result = client.query(test_sql)
                client.close()
                
                logger.info("✅ ClickHouse validation successful")
                return {
                    'valid': True,
                    'executable': True,
                    'error': None,
                    'result_count': len(result.result_rows) if hasattr(result, 'result_rows') else 0,
                    'validation_type': 'database_execution'
                }
                
            except Exception as e:
                logger.warning(f"❌ Attempt {i+1} failed: {e}")
                continue
        
        # If all ClickHouse connections failed, return syntax validation only
        logger.warning("⚠️ ClickHouse unavailable, using syntax-only validation")
        return {
            'valid': True,
            'executable': False,
            'error': 'ClickHouse connection failed, syntax validation passed',
            'result_count': 0,
            'validation_type': 'syntax_only'
        }
            
    except Exception as e:
        logger.error(f"❌ Validation completely failed: {e}")
        return {
            'valid': False,
            'executable': False,
            'error': f'Validation error: {str(e)}',
            'result_count': 0,
            'validation_type': 'error'
        }

def calculate_confidence_score(sql, generation_source, sql_evaluation, clickhouse_validation, entity_mappings):
    """Calculate comprehensive confidence score"""
    
    confidence = 0.0
    
    # 1. Generation source quality (25%)
    source_scores = {
        'gemini_generated': 0.25,  # Updated from openai_generated
        'ollama_fallback': 0.20,
        'template_match': 0.15,
        'cache_hit': 0.25,
        'failed': 0.0
    }
    confidence += source_scores.get(generation_source, 0.0)
    
    # 2. SQL syntax and structure (25%)
    if sql and sql.strip():
        # Basic SQL structure
        if sql.upper().startswith('SELECT'):
            confidence += 0.15
        if 'FROM' in sql.upper():
            confidence += 0.05
        if any(keyword in sql.upper() for keyword in ['WHERE', 'GROUP BY', 'ORDER BY']):
            confidence += 0.05
    
    # 3. ClickHouse validation (25%)
    if clickhouse_validation:
        if clickhouse_validation.get('valid', False):
            confidence += 0.15
        if clickhouse_validation.get('executable', False):
            confidence += 0.10
    
    # 4. Entity mapping quality (15%)
    if entity_mappings:
        mapped_entities = sum(1 for entity_data in entity_mappings.values() 
                            if isinstance(entity_data, dict) and entity_data.get('values'))
        total_entities = len(entity_mappings)
        if total_entities > 0:
            confidence += 0.15 * (mapped_entities / total_entities)
    
    # 5. SQL evaluation scores (10%)
    if sql_evaluation:
        avg_score = sum([
            sql_evaluation.get('syntax_score', 0),
            sql_evaluation.get('schema_score', 0),
            sql_evaluation.get('clickhouse_score', 0)
        ]) / 3
        confidence += 0.10 * avg_score
    
    return min(confidence, 1.0)  # Cap at 100%

# Add these imports to the top of main.py
from datetime import datetime

# Replace your enhanced_generate_sql function with this updated version:
def enhanced_generate_sql(query, hybrid_generator, context, values, mappings, hyde_examples):
    """Enhanced SQL generation with realistic confidence calculation"""
    try:
        logger.info(f"🔍 Starting SQL generation for: {query}")
        start_time = datetime.now()
        
        # Step 1: Use your existing classification
        query_type, relevant_tables = classify_query(query)
        logger.info(f"📋 Query classified as: {query_type}")
        
        # Step 2: Build classification dict for hybrid generator
        classification = {
            'query_type': query_type,
            'relevant_tables': relevant_tables,
            'entities': mappings,
            'hyde_examples': hyde_examples
        }
        
        # Step 3: Build schema context from your retrieved context
        schema_context = "\n".join(context) if context else ""
        
        # Step 4: Generate SQL using hybrid approach
        logger.info("🤖 Calling hybrid generator...")
        result = hybrid_generator.process_query_complete(
            query, classification, schema_context
        )
        
        if result.get('success', False):
            sql = result['sql']
            source = result.get('source', 'unknown')
            
            # Step 5: Validate SQL (now supports WITH statements)
            logger.info("🔍 Validating SQL...")
            clickhouse_validation = validate_sql_against_clickhouse(sql)
            
            # Step 6: Calculate realistic confidence score
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            logger.info("📊 Calculating realistic confidence score...")
            confidence, confidence_breakdown = calculate_realistic_confidence_score(
                sql=sql,
                generation_source=source,
                query=query,
                entity_mappings=mappings,
                hyde_examples=hyde_examples,
                clickhouse_validation=clickhouse_validation,
                processing_time=processing_time
            )
            
            logger.info(f"✅ SQL generated via {source} with confidence {confidence:.1%} ({confidence_breakdown['confidence_grade']})")
            
            return sql, source, confidence, clickhouse_validation, confidence_breakdown
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Hybrid SQL generation failed: {error_msg}")
            return "", "failed", 0.0, {'valid': False, 'error': error_msg}, {}
            
    except Exception as e:
        logger.error(f"❌ Enhanced SQL generation failed: {e}")
        return "", "error", 0.0, {'valid': False, 'error': str(e)}, {}


def log_results(query, sql, query_type, evaluation, results, mappings, hyde_examples, generation_source=None, clickhouse_validation=None):
    """Enhanced logging with all components"""
    try:
        csv_file = "evaluation.csv"
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow([
                    "timestamp", "query", "sql", "query_type", "confidence",
                    "syntax_score", "schema_score", "clickhouse_score", "entity_score",
                    "value_score", "mapping_score", "retrieval_score",
                    "syntax_message", "schema_message", "clickhouse_message",
                    "entity_message", "value_message", "mapping_message",
                    "performance_message", "mappings", "hyde_examples", "results",
                    "generation_source", "clickhouse_validation"
                ])
            
            writer.writerow([
                datetime.now().isoformat(),
                query,
                sql,
                query_type,
                evaluation.get("confidence", 0),
                evaluation.get("syntax_score", 0),
                evaluation.get("schema_score", 0),
                evaluation.get("clickhouse_score", 0),
                evaluation.get("entity_score", 0),
                evaluation.get("value_score", 0),
                evaluation.get("mapping_score", 0),
                evaluation.get("retrieval_score", 0),
                evaluation.get("syntax_message", ""),
                evaluation.get("schema_message", ""),
                evaluation.get("clickhouse_message", ""),
                evaluation.get("entity_message", ""),
                evaluation.get("value_message", ""),
                evaluation.get("mapping_message", ""),
                evaluation.get("performance_message", ""),
                json.dumps(mappings),
                json.dumps(hyde_examples),
                json.dumps(results),
                generation_source or "unknown",
                json.dumps(clickhouse_validation or {})
            ])
            
    except Exception as e:
        logger.error(f"❌ Logging failed: {e}")

# ADD THESE IMPORTS at the top of main.py (after your existing imports)
from utils.sql_evaluator import evaluate_sql, get_evaluation_summary_text

# ADD THESE TWO FUNCTIONS to main.py (before the run_streamlit function)

def display_enhanced_confidence_analysis(confidence_breakdown, st):
    """Display enhanced confidence analysis with SQL evaluation details"""
    
    st.subheader("🎯 Enhanced Confidence Analysis")
    
    # Overall score with grade
    col1, col2 = st.columns(2)
    with col1:
        confidence_pct = confidence_breakdown['total_confidence'] * 100
        st.metric("Overall Confidence", f"{confidence_pct:.1f}%")
    with col2:
        st.metric("Confidence Grade", confidence_breakdown['confidence_grade'])
    
    # SQL Quality Summary
    if 'sql_quality_summary' in confidence_breakdown:
        st.info(confidence_breakdown['sql_quality_summary'])
    
    # Component breakdown
    st.write("**📊 Confidence Component Breakdown:**")
    components = confidence_breakdown['components']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"🔧 **SQL Quality:** {components.get('sql_quality', 0)*100:.1f}%")
        st.write(f"🤖 **Generation Source:** {components.get('generation_source', 0)*100:.1f}%")
    with col2:
        st.write(f"🎯 **Entity Usage:** {components.get('entity_usage', 0)*100:.1f}%")
        st.write(f"🧠 **Query Understanding:** {components.get('query_understanding', 0)*100:.1f}%")
    with col3:
        st.write(f"✅ **Technical Validation:** {components.get('technical_validation', 0)*100:.1f}%")
        st.write(f"⚡ **Performance:** {components.get('performance', 0)*100:.1f}%")
    
    # Detailed SQL Evaluation
    if 'sql_evaluation' in confidence_breakdown:
        with st.expander("🔍 Detailed SQL Analysis", expanded=False):
            sql_eval = confidence_breakdown['sql_evaluation']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Syntax & Structure:**")
                st.write(f"- Syntax Score: {sql_eval.get('syntax_score', 0)*100:.1f}%")
                st.write(f"- Schema Score: {sql_eval.get('schema_score', 0)*100:.1f}%")
                st.write(f"- ClickHouse Score: {sql_eval.get('clickhouse_score', 0)*100:.1f}%")
                
                st.write("**Entity & Mapping:**")
                st.write(f"- Entity Score: {sql_eval.get('entity_score', 0)*100:.1f}%")
                st.write(f"- Mapping Score: {sql_eval.get('mapping_score', 0)*100:.1f}%")
            
            with col2:
                st.write("**Performance Analysis:**")
                perf_analysis = sql_eval.get('performance_analysis', {})
                issues = perf_analysis.get('issues', [])
                recommendations = perf_analysis.get('recommendations', [])
                
                if issues:
                    st.write("Issues:")
                    for issue in issues:
                        st.write(f"- ⚠️ {issue}")
                
                if recommendations:
                    st.write("Recommendations:")
                    for rec in recommendations:
                        st.write(f"- 💡 {rec}")
                
                if not issues:
                    st.write("✅ No performance issues detected")
            
            # Schema Details
            schema_details = sql_eval.get('schema_details', {})
            if schema_details.get('tables_found'):
                st.write("**Schema Usage:**")
                st.write(f"Tables: {', '.join(schema_details.get('tables_valid', []))}")
                if schema_details.get('invalid_elements'):
                    st.write("Issues:")
                    for issue in schema_details['invalid_elements'][:3]:  # Show first 3
                        st.write(f"- ⚠️ {issue}")
            
            # Entity Details
            entity_details = sql_eval.get('entity_details', {})
            if entity_details.get('found_entities'):
                st.write("**Entities in SQL:**")
                for entity in entity_details['found_entities'][:5]:  # Show first 5
                    st.write(f"- ✅ {entity}")
    
    # Performance metrics
    with st.expander("📋 Performance Metrics", expanded=False):
        details = confidence_breakdown.get('details', {})
        for key, value in details.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

def enhanced_generate_sql(query, hybrid_generator, context, values, mappings, hyde_examples):
    """Enhanced SQL generation with realistic confidence calculation and detailed evaluation"""
    try:
        logger.info(f"🔍 Starting SQL generation for: {query}")
        start_time = datetime.now()
        
        # Step 1: Use your existing classification
        query_type, relevant_tables = classify_query(query)
        logger.info(f"📋 Query classified as: {query_type}")
        
        # Step 2: Build classification dict for hybrid generator
        classification = {
            'query_type': query_type,
            'relevant_tables': relevant_tables,
            'entities': mappings,
            'hyde_examples': hyde_examples
        }
        
        # Step 3: Build schema context from your retrieved context
        schema_context = "\n".join(context) if context else ""
        
        # Step 4: Generate SQL using hybrid approach
        logger.info("🤖 Calling hybrid generator...")
        result = hybrid_generator.process_query_complete(
            query, classification, schema_context
        )
        
        if result.get('success', False):
            sql = result['sql']
            source = result.get('source', 'unknown')
            
            # Step 5: Validate SQL (now supports WITH statements)
            logger.info("🔍 Validating SQL...")
            clickhouse_validation = validate_sql_against_clickhouse(sql)
            
            # Step 6: Enhanced SQL Evaluation
            logger.info("📊 Performing detailed SQL evaluation...")
            try:
                # Use the enhanced evaluator - now returns much more detailed analysis
                sql_evaluation = evaluate_sql(
                    sql, query, query_type, [], entities, mappings, relevant_tables
                )
                
                # Extract key metrics for confidence calculation
                sql_quality_metrics = sql_evaluation.get('sql_quality_metrics', {})
                
            except Exception as e:
                logger.error(f"SQL evaluation failed: {e}")
                sql_evaluation = {
                    'syntax_score': 0.5,
                    'schema_score': 0.0,
                    'entity_score': 0.0,
                    'sql_quality_metrics': {}
                }
            
            # Step 7: Calculate realistic confidence score
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            logger.info("📊 Calculating realistic confidence score...")
            confidence, confidence_breakdown = calculate_realistic_confidence_score(
                sql=sql,
                generation_source=source,
                query=query,
                entity_mappings=mappings,
                hyde_examples=hyde_examples,
                clickhouse_validation=clickhouse_validation,
                processing_time=processing_time
            )
            
            # Step 8: Enhance confidence breakdown with SQL evaluation details
            confidence_breakdown['sql_evaluation'] = sql_evaluation
            confidence_breakdown['sql_quality_summary'] = get_evaluation_summary_text(sql_evaluation)
            
            logger.info(f"✅ SQL generated via {source} with confidence {confidence:.1%} ({confidence_breakdown['confidence_grade']})")
            
            return sql, source, confidence, clickhouse_validation, confidence_breakdown
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Hybrid SQL generation failed: {error_msg}")
            return "", "failed", 0.0, {'valid': False, 'error': error_msg}, {}
            
    except Exception as e:
        logger.error(f"❌ Enhanced SQL generation failed: {e}")
        return "", "error", 0.0, {'valid': False, 'error': str(e)}, {}

def run_streamlit():
    """Main Streamlit UI with proper HyDE, validation, and confidence calculation"""
    
    st.set_page_config(
        page_title="DocNexus.ai Text2SQL",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🏥 DocNexus.ai Text2SQL")
    st.write("Transform natural language into precise SQL queries for healthcare data")
    
    # Check Google API key status
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        masked_key = f"{google_key[:8]}...{google_key[-4:]}" if len(google_key) > 12 else "***configured***"
        st.success(f"🤖 Google API Key: {masked_key}")
    else:
        st.warning("⚠️ Google API key not found in .env file")
        st.info("💡 Add GOOGLE_API_KEY=your_key to your .env file for best performance")
    
    # Initialize systems
    with st.spinner("🚀 Initializing systems..."):
        hybrid_generator = initialize_hybrid_generator()
        if not hybrid_generator:
            st.error("❌ Failed to initialize SQL generator. Please check your setup.")
            st.stop()
        
        index, sample_values = initialize_data_systems()
        if not index:
            st.error("❌ Failed to initialize data systems. Please check ClickHouse and Weaviate.")
            st.stop()
    
    st.success("✅ All systems initialized successfully!")
    
    # Sidebar with system status and examples
    with st.sidebar:
        st.header("🔧 System Status")
        
        if hybrid_generator.gemini_client:
            st.success("🤖 Gemini 2.5: Connected")
        else:
            st.warning("⚠️ Gemini 2.5: Not available")
        
        if hybrid_generator.ollama_model:
            st.success(f"🔄 Ollama: {hybrid_generator.ollama_model}")
        else:
            st.warning("⚠️ Ollama: Not available")
        
        # Example queries
        st.header("📋 Example Queries")
        examples = [
            "Who are the top 10 prescribers of Ozempic in New York?",
            "Find the highest paid KOLs in oncology in California",
            "What are the most common procedures performed by cardiologists?",
            "Which pharmaceutical companies paid the most to doctors in 2023?",
            "Top 5 drugs prescribed by endocrinologists in Florida"
        ]
        
        for i, example in enumerate(examples):
            if st.button(f"Example {i+1}", key=f"ex_{i}"):
                st.session_state.example_query = example
    
    # Main query interface
    st.header("💬 Enter Your Query")
    
    # Query input with session state management
    if 'query_input' not in st.session_state:
        st.session_state.query_input = "Who are the top 10 prescribers of Ozempic in New York?"  # Default query for testing
    
    # Check for example query
    if 'example_query' in st.session_state:
        st.session_state.query_input = st.session_state.example_query
        del st.session_state.example_query
    
    query = st.text_area(
        "Enter your query:",
        value=st.session_state.query_input,
        height=100,
        placeholder="e.g., Who are the top prescribers of Humira in California?",
        key="query_text_area"
    )
    
    # Update session state when query changes
    if query != st.session_state.query_input:
        st.session_state.query_input = query
    
    # Control buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        generate_button = st.button("🔍 Generate SQL", type="primary")
    
    with col2:
        if st.button("🧹 Clear"):
            st.session_state.query_input = ""
            st.rerun()
    
    with col3:
        # Quick test button
        if st.button("🚀 Test Query"):
            st.session_state.query_input = "Who are the top 10 prescribers of Ozempic in New York?"
            st.rerun()
    
     # Process query section - REPLACE your existing query processing with this:
    if generate_button:
        if not query or not query.strip():
            st.error("Please enter a query")
            return
        
        with st.spinner("🤖 Processing your query..."):
            start_time = datetime.now()
            
            try:
                # Step 1: Query classification and entity extraction
                query_type, relevant_tables = classify_query(query)
                entities, mappings = extract_entities(query)
                
                # Step 2: Generate HyDE SQL examples
                hyde_examples = generate_hyde_sql_examples(query, hybrid_generator)
                
                # Step 3: Retrieve context with HyDE enhancement
                context, distances, values = retrieve_context(
                    query, query_type, relevant_tables, hyde_examples, index
                )
                
                # Step 4: Generate SQL with enhanced evaluation
                sql, generation_source, confidence, clickhouse_validation, confidence_breakdown = enhanced_generate_sql(
                    query, hybrid_generator, context, values, mappings, hyde_examples
                )
                
                # Step 5: Mock results
                results = mock_execution_results(sql, query_type)
                
                # Step 6: Logging (optional)
                try:
                    evaluation = {'confidence': confidence}  # Simplified for logging
                    log_results(
                        query, sql, query_type, evaluation, results, mappings, 
                        hyde_examples, generation_source, clickhouse_validation
                    )
                except Exception as e:
                    logger.warning(f"Logging failed: {e}")
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Display results
                if sql:
                    st.success("✅ Query processed successfully!")
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Query Type", query_type)
                    with col2:
                        confidence_grade = confidence_breakdown.get('confidence_grade', 'Unknown')
                        st.metric("Confidence", f"{confidence:.1%}")
                        st.caption(confidence_grade)
                    with col3:
                        source_emoji = {
                            'gemini_generated': '🤖',
                            'ollama_fallback': '🔄'
                        }.get(generation_source, '❓')
                        st.metric("Source", f"{source_emoji} {generation_source.replace('_', ' ').title()}")
                    with col4:
                        st.metric("Processing Time", f"{processing_time:.2f}s")
                    
                    # Validation status
                    validation_type = clickhouse_validation.get('validation_type', 'unknown')
                    if validation_type == 'database_execution':
                        st.success("✅ SQL validated and executed successfully against ClickHouse")
                    elif validation_type == 'syntax_only':
                        st.info("ℹ️ SQL syntax validated (ClickHouse connection unavailable)")
                    elif validation_type == 'syntax_check':
                        st.warning("⚠️ Basic syntax validation passed")
                    else:
                        st.error(f"❌ Validation issue: {clickhouse_validation.get('error', 'Unknown error')}")
                    
                    # Generated SQL
                    st.subheader("📝 Generated SQL")
                    st.code(sql, language='sql')
                    
                    # Download button
                    st.download_button(
                        "💾 Download SQL",
                        sql,
                        file_name=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                        mime="text/sql"
                    )
                    
                    # Enhanced confidence analysis - THIS IS THE KEY ADDITION
                    display_enhanced_confidence_analysis(confidence_breakdown, st)
                    
                    # Other detailed results in expander
                    with st.expander("🔍 Additional Analysis", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**HyDE SQL Examples:**")
                            for i, example in enumerate(hyde_examples, 1):
                                if example.strip():
                                    st.code(example, language='sql')
                            
                            st.write("**Entity Mappings:**")
                            st.json(mappings)
                        
                        with col2:
                            st.write("**Validation Details:**")
                            st.json(clickhouse_validation)
                    
                    # Sample results
                    st.subheader("📊 Sample Results")
                    st.info("💡 These are mock results for demonstration purposes")
                    st.json(results)
                
                else:
                    st.error("❌ SQL generation failed")
                    st.error(f"Source: {generation_source}")
                    if clickhouse_validation.get('error'):
                        st.error(f"Validation error: {clickhouse_validation['error']}")
                
            except Exception as e:
                st.error(f"❌ Query processing failed: {e}")
                logger.error(f"❌ Query processing error: {e}")
                import traceback
                st.error(traceback.format_exc())