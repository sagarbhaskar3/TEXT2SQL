# utils/logging_utils.py - Logging Utilities
import logging
import csv
import os
import json
from datetime import datetime
from typing import Dict, Any
from config.app_config import LOGGING_CONFIG

def setup_logging():
    """Setup application logging configuration"""
    logging.basicConfig(
        filename=LOGGING_CONFIG['log_file'],
        level=getattr(logging, LOGGING_CONFIG['log_level']),
        format=LOGGING_CONFIG['log_format'],
        filemode='a'
    )
    
    # Also log to console for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add console handler to root logger
    root_logger = logging.getLogger()
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(console_handler)

def log_query_result(query: str, result: Dict[str, Any]):
    """Log query processing result to CSV file"""
    try:
        csv_file = LOGGING_CONFIG['csv_log_file']
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow([
                    "timestamp", "query", "sql", "query_type", "confidence",
                    "generation_source", "validation_status", "entity_count", 
                    "join_count", "processing_time", "success", "error"
                ])
            
            # Extract metrics
            sql = result.get('sql', '')
            entity_count = len(result.get('mappings', {}))
            join_count = sql.upper().count('JOIN') if sql else 0
            validation = result.get('validation', {})
            
            writer.writerow([
                datetime.now().isoformat(),
                query,
                sql,
                result.get('query_type', 'Unknown'),
                result.get('confidence', 0.0),
                result.get('generation_source', 'unknown'),
                validation.get('validation_type', 'none'),
                entity_count,
                join_count,
                result.get('processing_time', 0.0),
                result.get('success', False),
                result.get('error', '')
            ])
            
        logging.info(f"Query result logged: confidence={result.get('confidence', 0):.2f}")
        
    except Exception as e:
        logging.error(f"Failed to log query result: {e}")

def log_system_performance(stats: Dict[str, Any]):
    """Log system performance metrics"""
    try:
        logging.info(f"System performance: {json.dumps(stats, indent=2)}")
    except Exception as e:
        logging.error(f"Failed to log system performance: {e}")

def log_error_with_context(error: Exception, context: Dict[str, Any]):
    """Log error with additional context"""
    try:
        context_str = json.dumps(context, indent=2, default=str)
        logging.error(f"Error: {error}\nContext: {context_str}")
    except Exception as e:
        logging.error(f"Failed to log error with context: {e}")
        logging.error(f"Original error: {error}")

class QueryLogger:
    """Specialized logger for query processing"""
    
    def __init__(self, query: str):
        self.query = query
        self.logger = logging.getLogger(f"query_processor_{id(self)}")
        self.start_time = datetime.now()
        self.steps = []
    
    def log_step(self, step_name: str, step_result: Dict[str, Any]):
        """Log a processing step"""
        step_time = datetime.now()
        elapsed = (step_time - self.start_time).total_seconds()
        
        step_info = {
            'step': step_name,
            'elapsed_time': elapsed,
            'timestamp': step_time.isoformat(),
            'result_summary': self._summarize_step_result(step_result)
        }
        
        self.steps.append(step_info)
        self.logger.info(f"Step {step_name} completed in {elapsed:.2f}s")
    
    def _summarize_step_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of step result for logging"""
        summary = {}
        
        if 'sql' in result:
            summary['sql_length'] = len(result['sql'])
            summary['has_sql'] = bool(result['sql'])
        
        if 'entities' in result:
            summary['entity_count'] = len(result['entities'])
        
        if 'confidence' in result:
            summary['confidence'] = result['confidence']
        
        if 'success' in result:
            summary['success'] = result['success']
        
        if 'error' in result:
            summary['has_error'] = bool(result['error'])
        
        return summary
    
    def finalize(self, final_result: Dict[str, Any]):
        """Finalize logging with complete result"""
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        self.logger.info(f"Query processing completed in {total_time:.2f}s")
        self.logger.info(f"Final confidence: {final_result.get('confidence', 0):.2f}")
        self.logger.info(f"Success: {final_result.get('success', False)}")
        
        # Log step summary
        for step in self.steps:
            self.logger.debug(f"Step summary: {step}")

def get_log_statistics() -> Dict[str, Any]:
    """Get statistics from log files"""
    stats = {
        'total_queries': 0,
        'successful_queries': 0,
        'average_confidence': 0.0,
        'average_processing_time': 0.0,
        'query_types': {},
        'generation_sources': {}
    }
    
    try:
        csv_file = LOGGING_CONFIG['csv_log_file']
        if not os.path.exists(csv_file):
            return stats
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            confidences = []
            processing_times = []
            
            for row in reader:
                stats['total_queries'] += 1
                
                # Success tracking
                if row.get('success', '').lower() == 'true':
                    stats['successful_queries'] += 1
                
                # Confidence tracking
                try:
                    confidence = float(row.get('confidence', 0))
                    confidences.append(confidence)
                except:
                    pass
                
                # Processing time tracking
                try:
                    proc_time = float(row.get('processing_time', 0))
                    processing_times.append(proc_time)
                except:
                    pass
                
                # Query type tracking
                query_type = row.get('query_type', 'Unknown')
                stats['query_types'][query_type] = stats['query_types'].get(query_type, 0) + 1
                
                # Generation source tracking
                gen_source = row.get('generation_source', 'unknown')
                stats['generation_sources'][gen_source] = stats['generation_sources'].get(gen_source, 0) + 1
            
            # Calculate averages
            if confidences:
                stats['average_confidence'] = sum(confidences) / len(confidences)
            
            if processing_times:
                stats['average_processing_time'] = sum(processing_times) / len(processing_times)
        
        return stats
        
    except Exception as e:
        logging.error(f"Failed to get log statistics: {e}")
        return stats