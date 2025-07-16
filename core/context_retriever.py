# core/context_retriever.py - Updated Context Retrieval Module
import logging
import json
from typing import Dict, List, Any, Optional
from config.app_config import PROCESSING_CONFIG

logger = logging.getLogger(__name__)

class ContextRetriever:
    """Handles enhanced context retrieval with rule-based enhancement"""
    
    def __init__(self, index):
        self.index = index
        self.max_documents = PROCESSING_CONFIG['max_context_documents']
    
    def retrieve_enhanced_context(self, query: str, query_type: str, 
                                relevant_tables: List[str], hyde_examples: List[str]) -> Dict[str, Any]:
        """Enhanced context retrieval with rule-based enhancement"""
        try:
            if not self.index:
                logger.warning("Index not available, returning empty context")
                return self._create_empty_context()
            
            # Build enhanced query string
            enhanced_query = self._build_enhanced_query(query, query_type, relevant_tables, hyde_examples)
            
            # Retrieve context
            context_result = self._retrieve_from_index(enhanced_query)
            
            # Enhance with metadata
            context_result['query_type'] = query_type
            context_result['relevant_tables'] = relevant_tables
            context_result['hyde_count'] = len(hyde_examples)
            
            logger.info(f"✅ Retrieved {len(context_result.get('documents', []))} context documents")
            return context_result
            
        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {e}")
            return self._create_error_context(str(e))
    
    def _build_enhanced_query(self, query: str, query_type: str, 
                            relevant_tables: List[str], hyde_examples: List[str]) -> str:
        """Build enhanced query string with HyDE examples and intent"""
        
        # Core query components
        intent_context = f"Intent: {query_type} analysis"
        table_context = f"Primary tables: {', '.join(relevant_tables)}"
        
        # HyDE SQL context
        hyde_sql_context = ""
        if hyde_examples:
            hyde_sql_context = "SQL patterns:\n" + "\n".join(hyde_examples[:2])  # Use first 2 examples
        
        # Combine all contexts
        enhanced_query = f"{query}\n\n{intent_context}\n{table_context}"
        if hyde_sql_context:
            enhanced_query += f"\n\n{hyde_sql_context}"
        
        return enhanced_query
    
    def _retrieve_from_index(self, enhanced_query: str) -> Dict[str, Any]:
        """Retrieve context from vector index"""
        try:
            query_engine = self.index.as_query_engine(similarity_top_k=self.max_documents)
            response = query_engine.query(enhanced_query)
            
            # Extract information from response
            documents = [str(doc) for doc in response.source_nodes]
            distances = [node.score for node in response.source_nodes]
            values = []
            
            # Extract metadata values
            for node in response.source_nodes:
                try:
                    metadata = node.metadata
                    values.append(json.loads(metadata.get("values", "{}")))
                except:
                    values.append({})
            
            return {
                'documents': documents,
                'distances': distances,
                'values': values,
                'response_text': str(response),
                'retrieval_successful': True
            }
            
        except Exception as e:
            logger.error(f"Index retrieval failed: {e}")
            return self._create_error_context(f"Index retrieval error: {e}")
    
    def _create_empty_context(self) -> Dict[str, Any]:
        """Create empty context structure"""
        return {
            'documents': [],
            'distances': [],
            'values': [],
            'response_text': '',
            'retrieval_successful': False,
            'error': 'No index available'
        }
    
    def _create_error_context(self, error: str) -> Dict[str, Any]:
        """Create error context structure"""
        return {
            'documents': [],
            'distances': [],
            'values': [],
            'response_text': '',
            'retrieval_successful': False,
            'error': error
        }
    
    def get_context_summary(self, context_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of context retrieval results"""
        return {
            'document_count': len(context_result.get('documents', [])),
            'average_similarity': sum(context_result.get('distances', [])) / max(len(context_result.get('distances', [])), 1),
            'retrieval_successful': context_result.get('retrieval_successful', False),
            'has_values': len(context_result.get('values', [])) > 0,
            'query_type': context_result.get('query_type', 'Unknown'),
            'relevant_tables': context_result.get('relevant_tables', []),
            'hyde_count': context_result.get('hyde_count', 0)
        }
    
    def filter_relevant_documents(self, context_result: Dict[str, Any], 
                                 similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """Filter documents based on similarity threshold"""
        if not context_result.get('retrieval_successful', False):
            return context_result
        
        documents = context_result.get('documents', [])
        distances = context_result.get('distances', [])
        values = context_result.get('values', [])
        
        # Filter based on similarity
        filtered_docs = []
        filtered_distances = []
        filtered_values = []
        
        for i, distance in enumerate(distances):
            # Note: lower distance = higher similarity in some systems
            # Adjust this logic based on your similarity scoring
            if distance >= similarity_threshold or len(filtered_docs) < 2:  # Keep at least 2 docs
                if i < len(documents):
                    filtered_docs.append(documents[i])
                    filtered_distances.append(distance)
                    if i < len(values):
                        filtered_values.append(values[i])
        
        # Update context result
        filtered_result = context_result.copy()
        filtered_result.update({
            'documents': filtered_docs,
            'distances': filtered_distances,
            'values': filtered_values,
            'filtered': True,
            'original_count': len(documents),
            'filtered_count': len(filtered_docs)
        })
        
        return filtered_result