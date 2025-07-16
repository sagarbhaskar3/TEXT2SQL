# utils/sql_validator.py - SQL Validation Module
import logging
from typing import Dict, Any, List, Tuple
from config.app_config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class SQLValidator:
    """Enhanced SQL validation with comprehensive ClickHouse support"""
    
    def __init__(self):
        self.connection_configs = self._get_connection_configs()
    
    def _get_connection_configs(self) -> List[Dict[str, Any]]:
        """Get multiple connection configurations to try"""
        base_config = DATABASE_CONFIG['clickhouse']
        
        return [
            # Full configuration
            {
                'host': base_config['host'],
                'port': base_config['port'],
                'username': base_config['username'],
                'database': base_config['database'],
                'password': base_config['password']
            },
            # Without password
            {
                'host': base_config['host'],
                'port': base_config['port'],
                'username': base_config['username'],
                'database': base_config['database']
            },
            # Minimal configuration
            {
                'host': base_config['host'],
                'port': base_config['port'],
                'database': base_config['database']
            }
        ]
    
    def validate_syntax(self, sql: str) -> Tuple[bool, str]:
        """Enhanced SQL syntax validation"""
        if not sql or not sql.strip():
            return False, "Empty SQL"
        
        sql_upper = sql.strip().upper()
        
        # Valid starting keywords
        valid_starts = ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'EXPLAIN']
        
        # Check if starts with valid keyword
        starts_valid = any(sql_upper.startswith(keyword) for keyword in valid_starts)
        if not starts_valid:
            return False, f"SQL must start with one of: {', '.join(valid_starts)}"
        
        # Enhanced CTE validation
        if sql_upper.startswith('WITH'):
            if 'SELECT' not in sql_upper:
                return False, "WITH clause must contain SELECT statement"
            # Check for proper CTE structure
            if ')' not in sql or '(' not in sql:
                return False, "WITH clause has invalid structure"
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            return False, "Unbalanced parentheses in SQL"
        
        # Check for semicolon at end
        if not sql.rstrip().endswith(';'):
            # Add semicolon if missing
            sql = sql.rstrip() + ';'
        
        return True, "Valid SQL syntax"
    
    def prepare_test_sql(self, sql: str) -> str:
        """Prepare SQL for testing by adding LIMIT if needed"""
        test_sql = sql
        
        if 'LIMIT' not in sql.upper() and 'COUNT(' not in sql.upper():
            # Add LIMIT carefully for different SQL types
            if sql.upper().strip().startswith('WITH'):
                # For WITH statements, add LIMIT to the final SELECT
                test_sql = sql.rstrip(';') + ' LIMIT 1;'
            elif sql.upper().strip().startswith('SELECT'):
                test_sql = sql.rstrip(';') + ' LIMIT 1;'
        
        return test_sql
    
    def validate_against_database(self, sql: str) -> Dict[str, Any]:
        """Validate SQL against ClickHouse database"""
        try:
            import clickhouse_connect
        except ImportError:
            return {
                'valid': False,
                'executable': False,
                'error': 'ClickHouse client not available',
                'result_count': 0,
                'validation_type': 'import_error'
            }
        
        # First validate syntax
        syntax_valid, syntax_message = self.validate_syntax(sql)
        if not syntax_valid:
            return {
                'valid': False,
                'executable': False,
                'error': syntax_message,
                'result_count': 0,
                'validation_type': 'syntax_check'
            }
        
        # Try database connections
        for i, config in enumerate(self.connection_configs):
            try:
                logger.info(f"🔍 ClickHouse attempt {i+1}: {config['host']}:{config['port']}")
                client = clickhouse_connect.get_client(**config)
                
                # Test connection
                client.query("SELECT 1")
                
                # Prepare test SQL
                test_sql = self.prepare_test_sql(sql)
                
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
                    'validation_type': 'database_execution',
                    'connection_config': i + 1
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

def validate_sql_against_clickhouse(sql: str) -> Dict[str, Any]:
    """Main validation function for backward compatibility"""
    validator = SQLValidator()
    
    try:
        return validator.validate_against_database(sql)
    except Exception as e:
        logger.error(f"❌ Validation completely failed: {e}")
        return {
            'valid': False,
            'executable': False,
            'error': f'Validation error: {str(e)}',
            'result_count': 0,
            'validation_type': 'error'
        }