# core/system_initializer.py - Updated System Components Initializer
import logging
from typing import Dict, Optional, Any
from models.hybrid_sql_generator import HybridSQLGenerator
from utils.data_loader import (
    create_clickhouse_tables, 
    load_csv_to_clickhouse, 
    setup_weaviate, 
    load_data_to_weaviate
)

logger = logging.getLogger(__name__)

class SystemInitializer:
    """Handles initialization of all system components"""
    
    def __init__(self):
        self.hybrid_generator = None
        self.index = None
        self.sample_values = None
    
    def initialize_hybrid_generator(self) -> Optional[HybridSQLGenerator]:
        """Initialize the hybrid SQL generator"""
        try:
            logger.info("🤖 Initializing hybrid SQL generator...")
            generator = HybridSQLGenerator()
            logger.info("✅ Hybrid SQL generator initialized successfully")
            return generator
        except Exception as e:
            logger.error(f"❌ Failed to initialize hybrid generator: {e}")
            return None
    
    def initialize_data_systems(self) -> tuple:
        """Initialize ClickHouse and Weaviate data systems"""
        try:
            logger.info("💾 Initializing data systems...")
            
            # Initialize ClickHouse
            logger.info("📊 Setting up ClickHouse tables...")
            create_clickhouse_tables()
            load_csv_to_clickhouse()
            logger.info("✅ ClickHouse initialized")
            
            # Initialize Weaviate
            logger.info("🔍 Setting up Weaviate vector store...")
            setup_weaviate()
            index, sample_values = load_data_to_weaviate()
            logger.info("✅ Weaviate initialized")
            
            logger.info("✅ All data systems initialized successfully")
            return index, sample_values
            
        except Exception as e:
            logger.error(f"❌ Data system initialization failed: {e}")
            return None, None
    
    def validate_systems(self) -> Dict[str, Any]:
        """Validate that all systems are working correctly"""
        validation_results = {
            'hybrid_generator': False,
            'data_systems': False,
            'overall': False
        }
        
        try:
            # Validate hybrid generator
            if self.hybrid_generator:
                # Simple validation - check if both models are available
                has_gemini = self.hybrid_generator.gemini_client is not None
                has_ollama = self.hybrid_generator.ollama_model is not None
                validation_results['hybrid_generator'] = has_gemini or has_ollama
                logger.info(f"🤖 Generator validation: Gemini={has_gemini}, Ollama={has_ollama}")
            
            # Validate data systems
            if self.index and self.sample_values:
                validation_results['data_systems'] = True
                logger.info("💾 Data systems validation: ✅")
            
            # Overall validation
            validation_results['overall'] = (
                validation_results['hybrid_generator'] and 
                validation_results['data_systems']
            )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ System validation failed: {e}")
            return validation_results
    
    def initialize_all(self) -> Dict[str, Any]:
        """Initialize all system components and return status"""
        result = {
            'success': False,
            'hybrid_generator': None,
            'index': None,
            'sample_values': None,
            'error': None,
            'validation': {}
        }
        
        try:
            # Initialize hybrid generator
            self.hybrid_generator = self.initialize_hybrid_generator()
            if not self.hybrid_generator:
                result['error'] = "Failed to initialize SQL generator"
                return result
            
            # Initialize data systems
            self.index, self.sample_values = self.initialize_data_systems()
            if not self.index:
                result['error'] = "Failed to initialize data systems"
                return result
            
            # Validate systems
            validation = self.validate_systems()
            
            if not validation['overall']:
                result['error'] = f"System validation failed: {validation}"
                return result
            
            # Success
            result.update({
                'success': True,
                'hybrid_generator': self.hybrid_generator,
                'index': self.index,
                'sample_values': self.sample_values,
                'validation': validation
            })
            
            logger.info("🎉 All systems initialized and validated successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            result['error'] = str(e)
            return result
    
    def get_system_status(self) -> Dict[str, str]:
        """Get current status of all systems"""
        status = {
            'AI Model': '❌ Not Ready',
            'Database': '❌ Not Connected',
            'Vector Store': '❌ Not Ready',
            'Overall': '❌ Not Ready'
        }
        
        try:
            if self.hybrid_generator:
                if self.hybrid_generator.gemini_client:
                    status['AI Model'] = '✅ Gemini Ready'
                elif self.hybrid_generator.ollama_model:
                    status['AI Model'] = '✅ Ollama Ready'
                else:
                    status['AI Model'] = '⚠️ Limited Functionality'
            
            if self.index and self.sample_values:
                status['Database'] = '✅ Connected'
                status['Vector Store'] = '✅ Ready'
                status['Overall'] = '✅ All Systems Ready'
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
        
        return status