# core/query_processor.py - Main Query Processing Logic
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from utils.query_classifier import classify_query
from utils.entity_mapper import extract_entities
from utils.sql_evaluator import evaluate_sql
from utils.sql_validator import validate_sql_against_clickhouse
from core.hyde_generator import HydeGenerator
from core.context_retriever import ContextRetriever
from core.confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)

class QueryProcessor:
    """Main query processing orchestrator"""
    
    def __init__(self, hybrid_generator, index, sample_values):
        self.hybrid_generator = hybrid_generator
        self.index = index
        self.sample_values = sample_values
        
        # Initialize specialized components
        self.hyde_generator = HydeGenerator(hybrid_generator)
        self.context_retriever = ContextRetriever(index)
        self.confidence_calculator = ConfidenceCalculator()
    
    def process_complete_query(self, query: str) -> Dict[str, Any]:
        """
        Complete query processing pipeline
        
        Args:
            query: Natural language query
            
        Returns:
            Complete processing result with all metadata
        """
        start_time = datetime.now()
        logger.info(f"🔍 Starting complete query processing: {query}")
        
        try:
            # Step 1: Query Classification and Entity Extraction
            step1_result = self._step1_classify_and_extract(query)
            
            # Step 2: Generate HyDE Examples
            step2_result = self._step2_generate_hyde(query, step1_result)
            
            # Step 3: Retrieve Context
            step3_result = self._step3_retrieve_context(query, step1_result, step2_result)
            
            # Step 4: Generate SQL
            step4_result = self._step4_generate_sql(query, step1_result, step2_result, step3_result)
            
            # Step 5: Validate SQL
            step5_result = self._step5_validate_sql(step4_result['sql'])
            
            # Step 6: Evaluate SQL Quality
            step6_result = self._step6_evaluate_sql(
                step4_result['sql'], query, step1_result, step5_result
            )
            
            # Step 7: Calculate Confidence
            step7_result = self._step7_calculate_confidence(
                query, step1_result, step2_result, step4_result, step5_result, step6_result
            )
            
            # Compile final result
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result = self._compile_final_result(
                query, processing_time, step1_result, step2_result, step3_result,
                step4_result, step5_result, step6_result, step7_result
            )
            
            logger.info(f"✅ Query processing completed in {processing_time:.2f}s with confidence {result['confidence']:.1%}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            return self._create_error_result(query, str(e), start_time)
    
    def _step1_classify_and_extract(self, query: str) -> Dict[str, Any]:
        """Step 1: Query classification and entity extraction"""
        logger.info("📋 Step 1: Classifying query and extracting entities")
        
        # Classify query
        query_type, relevant_tables = classify_query(query)
        
        # Extract entities
        entities, mappings = extract_entities(query)
        
        return {
            'query_type': query_type,
            'relevant_tables': relevant_tables,
            'entities': entities,
            'mappings': mappings
        }
    
    def _step2_generate_hyde(self, query: str, step1_result: Dict) -> Dict[str, Any]:
        """Step 2: Generate HyDE SQL examples"""
        logger.info("🔄 Step 2: Generating HyDE SQL examples")
        
        hyde_examples = self.hyde_generator.generate_hyde_examples(
            query, step1_result['query_type'], step1_result['relevant_tables']
        )
        
        return {
            'hyde_examples': hyde_examples,
            'hyde_count': len(hyde_examples)
        }
    
    def _step3_retrieve_context(self, query: str, step1_result: Dict, step2_result: Dict) -> Dict[str, Any]:
        """Step 3: Retrieve relevant context"""
        logger.info("🔍 Step 3: Retrieving context")
        
        context_result = self.context_retriever.retrieve_enhanced_context(
            query, 
            step1_result['query_type'], 
            step1_result['relevant_tables'],
            step2_result['hyde_examples']
        )
        
        return context_result
    
    def _step4_generate_sql(self, query: str, step1_result: Dict, step2_result: Dict, step3_result: Dict) -> Dict[str, Any]:
        """Step 4: Generate SQL using hybrid approach"""
        logger.info("🤖 Step 4: Generating SQL")
        
        # Build classification for hybrid generator
        classification = {
            'query_type': step1_result['query_type'],
            'relevant_tables': step1_result['relevant_tables'],
            'entities': step1_result['mappings'],
            'hyde_examples': step2_result['hyde_examples']
        }
        
        # Build schema context
        schema_context = "\n".join(step3_result.get('documents', []))
        
        # Generate SQL
        generation_result = self.hybrid_generator.process_query_complete(
            query, classification, schema_context
        )
        
        return {
            'sql': generation_result.get('sql', ''),
            'generation_source': generation_result.get('source', 'unknown'),
            'success': generation_result.get('success', False),
            'intent_analysis': generation_result.get('intent_analysis', {}),
            'error': generation_result.get('error', None)
        }
    
    def _step5_validate_sql(self, sql: str) -> Dict[str, Any]:
        """Step 5: Validate SQL against ClickHouse"""
        logger.info("✅ Step 5: Validating SQL")
        
        validation_result = validate_sql_against_clickhouse(sql)
        
        return {
            'validation': validation_result,
            'is_valid': validation_result.get('valid', False),
            'is_executable': validation_result.get('executable', False)
        }
    
    def _step6_evaluate_sql(self, sql: str, query: str, step1_result: Dict, step5_result: Dict) -> Dict[str, Any]:
        """Step 6: Evaluate SQL quality"""
        logger.info("📊 Step 6: Evaluating SQL quality")
        
        try:
            evaluation = evaluate_sql(
                sql, 
                query, 
                step1_result['query_type'], 
                [],  # distances - not used in current implementation
                step1_result['entities'], 
                step1_result['mappings'], 
                step1_result['relevant_tables']
            )
            
            return {
                'evaluation': evaluation,
                'quality_score': evaluation.get('legacy_confidence', 0.0)
            }
            
        except Exception as e:
            logger.error(f"SQL evaluation failed: {e}")
            return {
                'evaluation': {},
                'quality_score': 0.5,
                'error': str(e)
            }
    
    def _step7_calculate_confidence(self, query: str, step1_result: Dict, step2_result: Dict, 
                                   step4_result: Dict, step5_result: Dict, step6_result: Dict) -> Dict[str, Any]:
        """Step 7: Calculate final confidence score"""
        logger.info("📊 Step 7: Calculating confidence score")
        
        confidence, breakdown = self.confidence_calculator.calculate_confidence(
            sql=step4_result['sql'],
            generation_source=step4_result['generation_source'],
            query=query,
            entity_mappings=step1_result['mappings'],
            hyde_examples=step2_result['hyde_examples'],
            clickhouse_validation=step5_result['validation'],
            intent_analysis=step4_result['intent_analysis']
        )
        
        return {
            'confidence': confidence,
            'confidence_breakdown': breakdown,
            'confidence_grade': self._get_confidence_grade(confidence)
        }
    
    def _compile_final_result(self, query: str, processing_time: float, *step_results) -> Dict[str, Any]:
        """Compile all step results into final result"""
        step1, step2, step3, step4, step5, step6, step7 = step_results
        
        return {
            'success': step4['success'],
            'query': query,
            'processing_time': processing_time,
            
            # Core results
            'sql': step4['sql'],
            'query_type': step1['query_type'],
            'confidence': step7['confidence'],
            'confidence_grade': step7['confidence_grade'],
            
            # Classification and extraction
            'relevant_tables': step1['relevant_tables'],
            'entities': step1['entities'],
            'mappings': step1['mappings'],
            
            # Generation details
            'generation_source': step4['generation_source'],
            'intent_analysis': step4['intent_analysis'],
            'hyde_examples': step2['hyde_examples'],
            
            # Validation and evaluation
            'validation': step5['validation'],
            'is_valid': step5['is_valid'],
            'is_executable': step5['is_executable'],
            'evaluation': step6['evaluation'],
            'quality_score': step6['quality_score'],
            
            # Confidence details
            'confidence_breakdown': step7['confidence_breakdown'],
            
            # Context
            'context': step3,
            
            # Error information
            'error': step4.get('error', None)
        }
    
    def _create_error_result(self, query: str, error: str, start_time: datetime) -> Dict[str, Any]:
        """Create error result structure"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': False,
            'query': query,
            'processing_time': processing_time,
            'sql': '',
            'confidence': 0.0,
            'confidence_grade': 'F (Failed)',
            'error': error,
            'query_type': 'Unknown',
            'generation_source': 'error',
            'is_valid': False,
            'is_executable': False,
            'entities': {},
            'mappings': {},
            'relevant_tables': [],
            'hyde_examples': [],
            'validation': {'valid': False, 'error': error},
            'evaluation': {},
            'confidence_breakdown': {}
        }
    
    def _get_confidence_grade(self, confidence: float) -> str:
        """Convert confidence score to letter grade"""
        if confidence >= 0.90:
            return "A+ (Excellent)"
        elif confidence >= 0.80:
            return "A (Very Good)"
        elif confidence >= 0.70:
            return "B (Good)"
        elif confidence >= 0.60:
            return "C (Fair)"
        elif confidence >= 0.50:
            return "D (Poor)"
        else:
            return "F (Failed)"