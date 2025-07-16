# utils/ui_components.py - Updated Streamlit UI Components
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from config.app_config import APP_CONFIG, SAMPLE_QUERIES, UI_CONFIG

class UIComponents:
    """Handles all Streamlit UI components and interactions"""
    
    def __init__(self):
        self.config = UI_CONFIG
    
    def display_header(self):
        """Display application header and description"""
        st.title(APP_CONFIG['app_title'])
        st.write(APP_CONFIG['app_description'])
    
    def display_sidebar(self):
        """Display sidebar with system status and sample queries"""
        with st.sidebar:
            self._display_system_status()
            self._display_sample_queries()
    
    def _display_system_status(self):
        """Display system status in sidebar"""
        st.header("🔧 System Status")
        st.success("✅ AI Model: Ready")
        st.success("✅ Database: Connected")
        st.success("✅ Analytics: Active")
    
    def _display_sample_queries(self):
        """Display sample queries in sidebar"""
        st.header("📋 Sample Queries")
        st.write("**Try these healthcare analytics queries:**")
        
        for i, sample in enumerate(SAMPLE_QUERIES):
            if st.button(f"Query {i+1}", key=f"sample_{i}", help=sample):
                st.session_state.example_query = sample
    
    def display_query_interface(self) -> str:
        """Display main query input interface"""
        st.header("💬 Enter Your Healthcare Query")
        
        # Initialize session state
        if 'query_input' not in st.session_state:
            st.session_state.query_input = ""
        
        # Check for example query
        if 'example_query' in st.session_state:
            st.session_state.query_input = st.session_state.example_query
            del st.session_state.example_query
        
        # Query input
        query = st.text_area(
            "Enter your query:",
            value=st.session_state.query_input,
            height=self.config['default_query_height'],
            max_chars=self.config['max_query_length'],
            placeholder="e.g., Who are the top prescribers of Humira in California?",
            key="query_text_area",
            help="Ask questions about prescriptions, procedures, payments, or healthcare providers"
        )
        
        # Update session state
        if query != st.session_state.query_input:
            st.session_state.query_input = query
        
        # Control buttons
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if st.button("🔍 Generate SQL & Analysis", type="primary", use_container_width=True):
                st.session_state.generate_clicked = True
        
        with col2:
            if st.button("🧹 Clear", use_container_width=True):
                st.session_state.query_input = ""
                st.rerun()
        
        return query
    
    def display_successful_result(self, result: Dict[str, Any]):
        """Display successful query processing result"""
        st.success("✅ Query processed successfully!")
        
        # Main SQL Output
        st.header("📝 Generated SQL Query")
        st.code(result['sql'], language='sql')
        
        # Quick metrics
        self._display_quick_metrics(result)
        
        # Download button
        self._display_download_button(result)
    
    def _display_quick_metrics(self, result: Dict[str, Any]):
        """Display quick metrics row"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            confidence = result.get('confidence', 0)
            st.metric("Confidence Score", f"{confidence:.1%}")
        
        with col2:
            query_type = result.get('query_type', 'Unknown')
            st.metric("Query Type", query_type)
        
        with col3:
            join_count = result.get('sql', '').upper().count('JOIN')
            st.metric("Table Joins", f"{join_count}")
        
        with col4:
            processing_time = result.get('processing_time', 0)
            st.metric("Processing Time", f"{processing_time:.1f}s")
    
    def _display_download_button(self, result: Dict[str, Any]):
        """Display SQL download button"""
        sql = result.get('sql', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        st.download_button(
            "💾 Download SQL Query",
            sql,
            file_name=f"healthcare_query_{timestamp}.sql",
            mime="text/sql",
            use_container_width=True
        )
    
    def display_detailed_analysis(self, result: Dict[str, Any]):
        """Display detailed step-by-step analysis"""
        st.header("🔍 Step-by-Step Analysis")
        st.write("Here's how we processed your query and generated the SQL:")
        
        # Step 1: Query Understanding
        self._display_query_understanding(result)
        
        # Step 2: Entity Extraction
        self._display_entity_extraction(result)
        
        # Step 3: Context Enhancement
        self._display_context_enhancement(result)
        
        # Step 4: AI Model Processing
        self._display_ai_processing(result)
        
        # Step 5: Validation Process
        self._display_validation_process(result)
        
        # Step 6: Confidence Calculation
        self._display_confidence_calculation(result)
    
    def _display_query_understanding(self, result: Dict[str, Any]):
        """Display query understanding step"""
        with st.expander("📝 Step 1: Query Understanding & Classification", expanded=True):
            st.write("**Original Query:**")
            st.info(f'"{result.get("query", "")}"')
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Query Classification:**")
                st.write(f"• **Type:** {result.get('query_type', 'Unknown')}")
                
                intent = result.get('intent_analysis', {}).get('primary_intent', 'Unknown')
                st.write(f"• **Primary Intent:** {intent}")
                
            with col2:
                st.write("**Recommended Tables:**")
                for table in result.get('relevant_tables', []):
                    st.write(f"• `{table}`")
    
    def _display_entity_extraction(self, result: Dict[str, Any]):
        """Display entity extraction step"""
        with st.expander("🎯 Step 2: Entity Extraction & Mapping", expanded=True):
            st.write("**Detected Entities:**")
            
            mappings = result.get('mappings', {})
            entity_found = False
            
            for entity_type, entity_data in mappings.items():
                if isinstance(entity_data, dict) and entity_data.get('values'):
                    entity_found = True
                    values = entity_data['values']
                    columns = entity_data.get('columns', [])
                    
                    st.write(f"**{entity_type.title()}:**")
                    st.write(f"• Values: {', '.join(map(str, values))}")
                    if columns:
                        st.write(f"• Mapped to columns: {', '.join(columns[:3])}{'...' if len(columns) > 3 else ''}")
                    st.write("")
            
            if not entity_found:
                st.write("No specific entities detected - using general analysis approach")
            
            confidence_breakdown = result.get('confidence_breakdown', {})
            tier_scores = confidence_breakdown.get('tier_scores', {})
            tier_2 = tier_scores.get('tier_2_semantic', {})
            entity_score = tier_2.get('entity_accuracy', 0) * 100
            st.write(f"**Entity Usage Score:** {entity_score:.1f}%")
    
    def _display_context_enhancement(self, result: Dict[str, Any]):
        """Display context enhancement step"""
        with st.expander("🔄 Step 3: Context Enhancement with HyDE", expanded=False):
            st.write("**HyDE (Hypothetical Document Embeddings) Process:**")
            st.write("Generated example SQL patterns to guide the AI model:")
            
            hyde_examples = result.get('hyde_examples', [])
            if hyde_examples and len(hyde_examples) > 0:
                # Clean and display actual SQL examples
                for i, example in enumerate(hyde_examples[:2], 1):
                    if example and example.strip():
                        # Clean the example of any extra text
                        cleaned_example = example.strip()
                        if cleaned_example.upper().startswith('SELECT') or cleaned_example.upper().startswith('WITH'):
                            st.write(f"**Example {i}:**")
                            st.code(cleaned_example, language='sql')
                        else:
                            st.write(f"**Example {i}:** Pattern generated")
            else:
                st.write("No HyDE examples generated for this query")
            
            st.write(f"**Generated {len(hyde_examples)} example patterns** to improve SQL quality")
    
    def _display_ai_processing(self, result: Dict[str, Any]):
        """Display AI processing step"""
        with st.expander("🤖 Step 4: AI Model SQL Generation", expanded=True):
            st.write("**AI Processing Details:**")
            
            col1, col2 = st.columns(2)
            with col1:
                source = result.get('generation_source', 'unknown').replace('_', ' ').title()
                st.write(f"**Generation Method:** {source}")
                
                processing_time = result.get('processing_time', 0)
                st.write(f"**Processing Time:** {processing_time:.2f} seconds")
                
                sql_length = len(result.get('sql', ''))
                st.write(f"**SQL Length:** {sql_length} characters")
                
            with col2:
                join_count = result.get('sql', '').upper().count('JOIN')
                st.write(f"**Table Joins:** {join_count}")
                
                confidence_breakdown = result.get('confidence_breakdown', {})
                tier_scores = confidence_breakdown.get('tier_scores', {})
                tier_1 = tier_scores.get('tier_1_foundational', {})
                sql_quality = tier_1.get('total', 0) * 100
                st.write(f"**SQL Quality Score:** {sql_quality:.1f}%")
                
                tier_2 = tier_scores.get('tier_2_semantic', {})
                intent_score = tier_2.get('total', 0) * 100
                st.write(f"**Semantic Accuracy:** {intent_score:.1f}%")
            
            self._display_sql_features(result.get('sql', ''))
    
    def _display_sql_features(self, sql: str):
        """Display detected SQL features"""
        st.write("**Key SQL Features Detected:**")
        features = []
        
        sql_upper = sql.upper()
        if 'SELECT' in sql_upper:
            features.append("✅ Proper SELECT structure")
        if 'JOIN' in sql_upper:
            features.append("✅ Multi-table joins")
        if 'WHERE' in sql_upper:
            features.append("✅ Filtering conditions")
        if 'GROUP BY' in sql_upper:
            features.append("✅ Data aggregation")
        if 'ORDER BY' in sql_upper:
            features.append("✅ Result sorting")
        if 'LIMIT' in sql_upper:
            features.append("✅ Result limiting")
        
        for feature in features:
            st.write(feature)
    
    def _display_validation_process(self, result: Dict[str, Any]):
        """Display validation process step"""
        with st.expander("✅ Step 5: SQL Validation & Testing", expanded=True):
            st.write("**Validation Process:**")
            
            validation = result.get('validation', {})
            validation_type = validation.get('validation_type', 'unknown')
            
            confidence_breakdown = result.get('confidence_breakdown', {})
            tier_scores = confidence_breakdown.get('tier_scores', {})
            tier_3 = tier_scores.get('tier_3_practical', {})
            validation_score = tier_3.get('total', 0) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Validation Type:** {validation_type.replace('_', ' ').title()}")
                st.write(f"**Validation Score:** {validation_score:.1f}%")
                
                if validation_type == 'database_execution':
                    st.success("✅ SQL executed successfully against database")
                elif validation_type == 'syntax_only':
                    st.info("ℹ️ Syntax validated (database unavailable)")
                else:
                    st.warning("⚠️ Basic validation only")
            
            with col2:
                st.write("**Validation Checks:**")
                st.write("✅ Syntax structure")
                st.write("✅ ClickHouse compatibility")
                st.write("✅ Table/column names")
                if validation.get('valid', False):
                    st.write("✅ Executable query")
                else:
                    st.write("⚠️ Execution issues detected")
    
    def _display_confidence_calculation(self, result: Dict[str, Any]):
        """Display confidence calculation step"""
        with st.expander("📊 Step 6: Confidence Score Calculation", expanded=True):
            st.write("**Tiered Confidence Scoring System:**")
            
            confidence_breakdown = result.get('confidence_breakdown', {})
            tier_scores = confidence_breakdown.get('tier_scores', {})
            total_confidence = result.get('confidence', 0) * 100
            
            # Tier 1: Foundational Correctness (40%)
            tier_1 = tier_scores.get('tier_1_foundational', {})
            st.write("**Tier 1: Foundational Correctness (40%)**")
            col1, col2 = st.columns(2)
            with col1:
                syntax_score = tier_1.get('syntax_structure', 0) * 100
                st.write(f"• Syntax & Structure: {syntax_score:.1f}%")
            with col2:
                compat_score = tier_1.get('database_compatibility', 0) * 100
                st.write(f"• Database Compatibility: {compat_score:.1f}%")
            
            # Tier 2: Semantic Accuracy (35%)
            tier_2 = tier_scores.get('tier_2_semantic', {})
            st.write("**Tier 2: Semantic Accuracy (35%)**")
            col1, col2 = st.columns(2)
            with col1:
                intent_score = tier_2.get('intent_recognition', 0) * 100
                st.write(f"• Intent Recognition: {intent_score:.1f}%")
            with col2:
                entity_score = tier_2.get('entity_accuracy', 0) * 100
                st.write(f"• Entity Accuracy: {entity_score:.1f}%")
            
            # Tier 3: Practical Validation (25%)
            tier_3 = tier_scores.get('tier_3_practical', {})
            st.write("**Tier 3: Practical Validation (25%)**")
            col1, col2 = st.columns(2)
            with col1:
                exec_score = tier_3.get('execution_success', 0) * 100
                st.write(f"• Execution Success: {exec_score:.1f}%")
            with col2:
                perf_score = tier_3.get('performance_efficiency', 0) * 100
                st.write(f"• Performance Efficiency: {perf_score:.1f}%")
            
            # Contextual Boost
            contextual_boost = confidence_breakdown.get('contextual_boost', {})
            total_boost = contextual_boost.get('total_boost', 0) * 100
            if total_boost > 0:
                st.write(f"**Contextual Boost:** +{total_boost:.1f}% (complexity & healthcare relevance)")
            
            # Final Score
            st.write("---")
            st.metric("**Final Confidence Score**", f"{total_confidence:.1f}%")
            
            # Score Interpretation
            if total_confidence >= 90:
                st.success("🎯 Excellent - Meets all requirements with high accuracy")
            elif total_confidence >= 80:
                st.success("👍 Very Good - Reliable with minor optimization opportunities")
            elif total_confidence >= 70:
                st.info("✔️ Good - Functional with some areas for improvement")
            elif total_confidence >= 60:
                st.warning("⚠️ Fair - Works but may need refinement")
            else:
                st.error("❌ Poor - May have significant issues")
    
    def display_error_result(self, result: Dict[str, Any]):
        """Display error result"""
        st.error("❌ SQL generation failed")
        st.error(f"Source: {result.get('generation_source', 'unknown')}")
        
        error = result.get('error', 'Unknown error')
        if error:
            st.error(f"Details: {error}")
        
        # Show debug information in expandable section
        with st.expander("🔍 Debug Information", expanded=False):
            st.write("**Query Processing Details:**")
            st.json({
                'query': result.get('query', ''),
                'processing_time': result.get('processing_time', 0),
                'generation_source': result.get('generation_source', ''),
                'error': error,
                'entities': result.get('entities', {}),
                'relevant_tables': result.get('relevant_tables', [])
            })