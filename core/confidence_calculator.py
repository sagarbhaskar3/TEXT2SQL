# core/confidence_calculator.py - Updated Tiered Confidence System
import logging
import re
from typing import Dict, Any, Tuple, List
from config.app_config import UI_CONFIG

logger = logging.getLogger(__name__)

class ConfidenceCalculator:
    """Tiered confidence calculation system for healthcare SQL queries"""
    
    def __init__(self):
        self.tier_weights = {
            'tier_1': 0.40,  # Foundational Correctness
            'tier_2': 0.35,  # Semantic Accuracy  
            'tier_3': 0.25   # Practical Validation
        }
    
    def calculate_confidence(self, sql: str, generation_source: str, query: str,
                           entity_mappings: Dict, hyde_examples: List[str],
                           clickhouse_validation: Dict, intent_analysis: Dict,
                           processing_time: float = 0.0) -> Tuple[float, Dict]:
        """
        Calculate confidence using the new tiered mechanism
        
        Tier 1: Foundational Correctness (40%)
        - Syntax and Structure (20%)
        - Database Compatibility (20%)
        
        Tier 2: Semantic Accuracy (35%)
        - Intent Recognition (15%)
        - Entity Accuracy (20%)
        
        Tier 3: Practical Validation (25%)
        - Execution Success (15%)
        - Performance Efficiency (10%)
        """
        
        # Tier 1: Foundational Correctness (40%)
        tier_1_scores = self._calculate_tier_1(sql, clickhouse_validation)
        tier_1_total = sum(tier_1_scores.values())
        
        # Tier 2: Semantic Accuracy (35%)
        tier_2_scores = self._calculate_tier_2(query, intent_analysis, entity_mappings, sql)
        tier_2_total = sum(tier_2_scores.values())
        
        # Tier 3: Practical Validation (25%)
        tier_3_scores = self._calculate_tier_3(clickhouse_validation, processing_time, sql)
        tier_3_total = sum(tier_3_scores.values())
        
        # Apply tiered reduction logic
        tier_1_capped = self._apply_tier_cap(tier_1_total, 0.40, 0.70)
        tier_2_capped = self._apply_tier_cap(tier_2_total, 0.35, 0.70) if tier_1_total >= 0.28 else tier_2_total * 0.7
        tier_3_capped = self._apply_tier_cap(tier_3_total, 0.25, 0.70) if tier_2_total >= 0.245 else tier_3_total * 0.7
        
        # Base score
        base_score = tier_1_capped + tier_2_capped + tier_3_capped
        
        # Contextual boost
        complexity_boost = self._calculate_complexity_boost(sql)
        healthcare_boost = self._calculate_healthcare_boost(entity_mappings, sql)
        total_boost = min(complexity_boost + healthcare_boost, 0.10)  # Cap at 10%
        
        # Final score
        final_score = min(base_score * (1 + total_boost), 1.0)
        
        # Create detailed breakdown
        breakdown = {
            'final_confidence': final_score,
            'tier_scores': {
                'tier_1_foundational': {
                    'syntax_structure': tier_1_scores['syntax_structure'],
                    'database_compatibility': tier_1_scores['database_compatibility'],
                    'total': tier_1_total,
                    'capped': tier_1_capped
                },
                'tier_2_semantic': {
                    'intent_recognition': tier_2_scores['intent_recognition'],
                    'entity_accuracy': tier_2_scores['entity_accuracy'],
                    'total': tier_2_total,
                    'capped': tier_2_capped
                },
                'tier_3_practical': {
                    'execution_success': tier_3_scores['execution_success'],
                    'performance_efficiency': tier_3_scores['performance_efficiency'],
                    'total': tier_3_total,
                    'capped': tier_3_capped
                }
            },
            'base_score': base_score,
            'contextual_boost': {
                'complexity_boost': complexity_boost,
                'healthcare_boost': healthcare_boost,
                'total_boost': total_boost
            },
            'metadata': {
                'query': query,
                'sql_length': len(sql) if sql else 0,
                'generation_source': generation_source,
                'processing_time': processing_time,
                'validation_type': clickhouse_validation.get('validation_type', 'unknown'),
                'entity_count': len(entity_mappings) if entity_mappings else 0,
                'join_count': sql.upper().count('JOIN') if sql else 0
            }
        }
        
        return final_score, breakdown
    
    def _calculate_tier_1(self, sql: str, clickhouse_validation: Dict) -> Dict[str, float]:
        """Calculate Tier 1: Foundational Correctness scores"""
        scores = {
            'syntax_structure': 0.0,
            'database_compatibility': 0.0
        }
        
        if not sql or not sql.strip():
            return scores
        
        # Syntax and Structure (20%)
        syntax_score = self._evaluate_syntax_structure(sql)
        scores['syntax_structure'] = 0.20 * syntax_score
        
        # Database Compatibility (20%)
        compatibility_score = self._evaluate_database_compatibility(sql, clickhouse_validation)
        scores['database_compatibility'] = 0.20 * compatibility_score
        
        return scores
    
    def _calculate_tier_2(self, query: str, intent_analysis: Dict, entity_mappings: Dict, sql: str) -> Dict[str, float]:
        """Calculate Tier 2: Semantic Accuracy scores"""
        scores = {
            'intent_recognition': 0.0,
            'entity_accuracy': 0.0
        }
        
        # Intent Recognition (15%)
        intent_score = self._evaluate_intent_recognition(query, intent_analysis, sql)
        scores['intent_recognition'] = 0.15 * intent_score
        
        # Entity Accuracy (20%)
        entity_score = self._evaluate_entity_accuracy(entity_mappings, sql)
        scores['entity_accuracy'] = 0.20 * entity_score
        
        return scores
    
    def _calculate_tier_3(self, clickhouse_validation: Dict, processing_time: float, sql: str) -> Dict[str, float]:
        """Calculate Tier 3: Practical Validation scores"""
        scores = {
            'execution_success': 0.0,
            'performance_efficiency': 0.0
        }
        
        # Execution Success (15%)
        execution_score = self._evaluate_execution_success(clickhouse_validation)
        scores['execution_success'] = 0.15 * execution_score
        
        # Performance Efficiency (10%)
        performance_score = self._evaluate_performance_efficiency(processing_time, sql)
        scores['performance_efficiency'] = 0.10 * performance_score
        
        return scores
    
    def _evaluate_syntax_structure(self, sql: str) -> float:
        """Evaluate SQL syntax and structure (0-1 scale)"""
        score = 0.0
        sql_upper = sql.upper()
        
        # Valid start (25%)
        if any(sql_upper.startswith(keyword) for keyword in ['SELECT', 'WITH']):
            score += 0.25
        
        # Required clauses (25%)
        if 'FROM' in sql_upper:
            score += 0.125
        if 'SELECT' in sql_upper:
            score += 0.125
        
        # Proper joins (25%)
        if 'JOIN' in sql_upper:
            join_count = sql_upper.count('JOIN')
            if join_count <= 3:  # Reasonable number of joins
                score += 0.25
            else:
                score += 0.15  # Partial credit for many joins
        else:
            score += 0.10  # Some credit for single table queries
        
        # Good practices (25%)
        if 'ORDER BY' in sql_upper:
            score += 0.10
        if 'LIMIT' in sql_upper:
            score += 0.10
        if 'GROUP BY' in sql_upper:
            score += 0.05
        
        return min(score, 1.0)
    
    def _evaluate_database_compatibility(self, sql: str, clickhouse_validation: Dict) -> float:
        """Evaluate ClickHouse compatibility (0-1 scale)"""
        score = 0.0
        
        # Base compatibility from validation
        validation_type = clickhouse_validation.get('validation_type', 'unknown')
        if validation_type == 'database_execution':
            score += 0.50
        elif validation_type == 'syntax_only':
            score += 0.35
        elif validation_type == 'syntax_check':
            score += 0.25
        
        # ClickHouse specific features
        if 'ILIKE' in sql.upper():
            score += 0.10
        if 'toString(' in sql:
            score += 0.10
        if re.search(r'\[\d+\]', sql):  # Array indexing
            score += 0.10
        if 'EXTRACT(' in sql.upper():
            score += 0.10
        
        # Avoid common issues
        if 'LIKE' in sql.upper() and 'ILIKE' not in sql.upper():
            score -= 0.05  # Should use ILIKE for case-insensitive
        
        return min(score, 1.0)
    
    def _evaluate_intent_recognition(self, query: str, intent_analysis: Dict, sql: str) -> float:
        """Evaluate intent recognition accuracy (0-1 scale)"""
        score = 0.0
        query_lower = query.lower()
        sql_upper = sql.upper()
        
        # Ranking intent
        if any(word in query_lower for word in ['top', 'best', 'highest', 'most']):
            if 'ORDER BY' in sql_upper and 'DESC' in sql_upper:
                score += 0.30
            elif 'ORDER BY' in sql_upper:
                score += 0.20
        
        # Filtering intent
        if any(word in query_lower for word in ['in', 'from', 'where', 'with']):
            if 'WHERE' in sql_upper:
                score += 0.25
        
        # Aggregation intent
        if any(word in query_lower for word in ['count', 'total', 'sum', 'average']):
            if any(func in sql_upper for func in ['COUNT(', 'SUM(', 'AVG(']):
                score += 0.25
        
        # Grouping intent
        if any(word in query_lower for word in ['by', 'group', 'each']):
            if 'GROUP BY' in sql_upper:
                score += 0.20
        
        return min(score, 1.0)
    
    def _evaluate_entity_accuracy(self, entity_mappings: Dict, sql: str) -> float:
        """Evaluate entity detection and usage accuracy (0-1 scale)"""
        if not entity_mappings:
            return 0.5  # Neutral score for queries without entities
        
        total_entities = 0
        used_entities = 0
        
        for entity_type, entity_data in entity_mappings.items():
            if isinstance(entity_data, dict) and entity_data.get('values'):
                for value in entity_data['values']:
                    total_entities += 1
                    if str(value).upper() in sql.upper():
                        used_entities += 1
        
        if total_entities == 0:
            return 0.5
        
        usage_rate = used_entities / total_entities
        
        # Bonus for healthcare-specific entities
        healthcare_entities = ['drugs', 'procedures', 'specialties', 'states']
        healthcare_count = sum(1 for entity_type in healthcare_entities 
                              if entity_type in entity_mappings and entity_mappings[entity_type].get('values'))
        
        healthcare_bonus = min(healthcare_count * 0.1, 0.3)
        
        return min(usage_rate + healthcare_bonus, 1.0)
    
    def _evaluate_execution_success(self, clickhouse_validation: Dict) -> float:
        """Evaluate execution success (0-1 scale)"""
        validation_type = clickhouse_validation.get('validation_type', 'unknown')
        is_valid = clickhouse_validation.get('valid', False)
        
        if validation_type == 'database_execution' and is_valid:
            return 1.0
        elif validation_type == 'syntax_only' and is_valid:
            return 0.7
        elif validation_type == 'syntax_check' and is_valid:
            return 0.5
        else:
            return 0.2
    
    def _evaluate_performance_efficiency(self, processing_time: float, sql: str) -> float:
        """Evaluate performance efficiency (0-1 scale)"""
        score = 1.0
        
        # Processing time penalty
        if processing_time > 10:
            score -= 0.3
        elif processing_time > 5:
            score -= 0.1
        
        # SQL efficiency checks
        sql_upper = sql.upper()
        
        # Penalties
        if 'SELECT *' in sql_upper:
            score -= 0.2
        if sql_upper.count('JOIN') > 3:
            score -= 0.1
        if 'LIMIT' not in sql_upper and 'COUNT(' not in sql_upper:
            score -= 0.1
        
        return max(score, 0.0)
    
    def _calculate_complexity_boost(self, sql: str) -> float:
        """Calculate complexity boost (0-0.10 scale)"""
        sql_upper = sql.upper()
        
        join_count = sql_upper.count('JOIN')
        condition_count = sql_upper.count('WHERE') + sql_upper.count('AND') + sql_upper.count('OR')
        
        complexity_score = (join_count + condition_count) * 0.02
        return min(complexity_score, 0.10)
    
    def _calculate_healthcare_boost(self, entity_mappings: Dict, sql: str) -> float:
        """Calculate healthcare relevance boost (0-0.05 scale)"""
        if not entity_mappings:
            return 0.0
        
        critical_entities = ['drugs', 'procedures', 'specialties', 'states']
        healthcare_count = 0
        
        for entity_type in critical_entities:
            if entity_type in entity_mappings and entity_mappings[entity_type].get('values'):
                # Check if entity is actually used in SQL
                for value in entity_mappings[entity_type]['values']:
                    if str(value).upper() in sql.upper():
                        healthcare_count += 1
                        break
        
        return min(healthcare_count * 0.0125, 0.05)  # 1.25% per critical entity, max 5%
    
    def _apply_tier_cap(self, tier_score: float, max_weight: float, threshold: float) -> float:
        """Apply tiered reduction if tier score below threshold"""
        if tier_score < (max_weight * threshold):
            return max_weight * threshold
        return tier_score
    
    def get_confidence_grade(self, confidence: float) -> str:
        """Convert confidence score to descriptive grade"""
        if confidence >= 0.90:
            return "Excellent (90%+)"
        elif confidence >= 0.80:
            return "Very Good (80-89%)"
        elif confidence >= 0.70:
            return "Good (70-79%)"
        elif confidence >= 0.60:
            return "Fair (60-69%)"
        else:
            return "Poor (<60%)"
    
    def get_confidence_insights(self, breakdown: Dict) -> List[str]:
        """Get actionable insights from confidence breakdown"""
        insights = []
        
        tier_scores = breakdown.get('tier_scores', {})
        
        # Tier 1 insights
        tier_1 = tier_scores.get('tier_1_foundational', {})
        if tier_1.get('total', 0) < 0.28:  # Below 70% of 40%
            insights.append("🔧 Improve SQL syntax and ClickHouse compatibility")
        
        # Tier 2 insights
        tier_2 = tier_scores.get('tier_2_semantic', {})
        if tier_2.get('total', 0) < 0.245:  # Below 70% of 35%
            insights.append("🎯 Better entity detection and intent recognition needed")
        
        # Tier 3 insights
        tier_3 = tier_scores.get('tier_3_practical', {})
        if tier_3.get('total', 0) < 0.175:  # Below 70% of 25%
            insights.append("⚡ Optimize query performance and execution")
        
        return insights