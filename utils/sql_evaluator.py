# utils/sql_evaluator.py - Updated for realistic confidence framework
from sqlglot import parse_one, exp
import re
import numpy as np
import logging
from config.schema import schema
from config.domain_knowledge import known_values

logger = logging.getLogger(__name__)

def evaluate_sql(sql, query, query_type, distances, entities, mappings, tables=None):
    """
    Enhanced SQL evaluation that integrates with the realistic confidence framework.
    Now focuses on detailed analysis rather than overall confidence calculation.
    """
    
    evaluation_results = {}
    
    # 1. Enhanced Syntax Validation (supports WITH statements)
    try:
        # Support multiple SQL starting patterns
        sql_upper = sql.strip().upper()
        valid_starts = ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        if any(sql_upper.startswith(keyword) for keyword in valid_starts):
            try:
                parsed = parse_one(sql, dialect="clickhouse")
                syntax_score = 1.0
                syntax_message = f"Valid ClickHouse SQL syntax (starts with {sql_upper.split()[0]})"
            except Exception as parse_error:
                # If parsing fails but starts correctly, give partial credit
                syntax_score = 0.7
                syntax_message = f"Valid SQL start but parsing issues: {str(parse_error)[:100]}"
        else:
            syntax_score = 0.0
            syntax_message = f"Invalid SQL start. Must begin with: {', '.join(valid_starts)}"
            
    except Exception as e:
        syntax_score = 0.0
        syntax_message = f"Syntax validation error: {str(e)}"
    
    evaluation_results.update({
        "syntax_score": syntax_score,
        "syntax_message": syntax_message
    })
    
    # 2. Enhanced Schema Compliance
    schema_score = 0.0
    schema_message = "Schema validation"
    schema_details = {
        "tables_found": [],
        "tables_valid": [],
        "columns_found": [],
        "columns_valid": [],
        "invalid_elements": []
    }
    
    try:
        # Extract tables and columns from SQL text if parsing fails
        if 'parsed' in locals() and parsed:
            tables = tables or [t.name for t in parsed.find_all(exp.Table)]
            columns = [c.name for c in parsed.find_all(exp.Column)]
        else:
            # Fallback: regex extraction
            tables = re.findall(r'\bFROM\s+(\w+)', sql.upper())
            tables += re.findall(r'\bJOIN\s+(\w+)', sql.upper())
            # Simple column extraction (this is basic, could be improved)
            columns = re.findall(r'SELECT\s+.*?FROM', sql.upper(), re.DOTALL)
            columns = [] if not columns else re.findall(r'\b(\w+)\b', columns[0])
        
        schema_details["tables_found"] = tables
        schema_details["columns_found"] = columns
        
        total_elements = len(tables) + len(columns)
        valid_elements = 0
        
        # Validate tables
        for table in tables:
            if table in schema:
                valid_elements += 1
                schema_details["tables_valid"].append(table)
            else:
                schema_details["invalid_elements"].append(f"Invalid table: {table}")
        
        # Validate columns
        for column in columns:
            found = False
            for table_name in schema:
                if any(col["name"] == column for col in schema[table_name]):
                    valid_elements += 1
                    schema_details["columns_valid"].append(column)
                    found = True
                    break
            if not found and column not in ['*', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN']:  # Ignore common SQL functions
                schema_details["invalid_elements"].append(f"Invalid column: {column}")
        
        schema_score = valid_elements / total_elements if total_elements > 0 else 0.0
        
        if schema_score == 1.0:
            schema_message = f"All {total_elements} schema elements valid"
        elif schema_score > 0.5:
            schema_message = f"{valid_elements}/{total_elements} schema elements valid"
        else:
            schema_message = f"Poor schema compliance: {valid_elements}/{total_elements} valid"
            
    except Exception as e:
        schema_score = 0.0
        schema_message = f"Schema validation failed: {str(e)}"
        logger.error(f"Schema validation error: {e}")
    
    evaluation_results.update({
        "schema_score": schema_score,
        "schema_message": schema_message,
        "schema_details": schema_details
    })
    
    # 3. Enhanced ClickHouse Compliance
    clickhouse_score = 1.0
    clickhouse_message = "ClickHouse compatibility checked"
    clickhouse_warnings = []
    
    try:
        tables_to_check = schema_details.get("tables_valid", [])
        
        for table in tables_to_check:
            for col in schema.get(table, []):
                col_name = col["name"]
                col_type = col["type"]
                
                if col_name in sql:
                    # Array type handling
                    if col_type.startswith("Array"):
                        if "arrayJoin" not in sql and "ANY(" not in sql and "has(" not in sql:
                            clickhouse_warnings.append(f"Array column {col_name} may need arrayJoin/ANY/has")
                            clickhouse_score *= 0.9
                    
                    # Enum8 handling
                    elif col_type.startswith("Enum8"):
                        if col_name == "gender" and not any(g in sql for g in known_values.get("genders", [])):
                            clickhouse_warnings.append(f"Enum8 column {col_name} may have invalid values")
                            clickhouse_score *= 0.9
                    
                    # Date handling
                    elif col_type in ["Date", "Date32"]:
                        if not re.search(r"\d{4}-\d{2}-\d{2}", sql):
                            clickhouse_warnings.append(f"Date column {col_name} may need proper date format")
                            clickhouse_score *= 0.95
        
        if clickhouse_warnings:
            clickhouse_message = f"ClickHouse compatibility with {len(clickhouse_warnings)} warnings"
        else:
            clickhouse_message = "Good ClickHouse compatibility"
            
    except Exception as e:
        clickhouse_score = 0.5
        clickhouse_message = f"ClickHouse validation error: {str(e)}"
        logger.error(f"ClickHouse validation error: {e}")
    
    evaluation_results.update({
        "clickhouse_score": clickhouse_score,
        "clickhouse_message": clickhouse_message,
        "clickhouse_warnings": clickhouse_warnings
    })
    
    # 4. Enhanced Entity Alignment
    entity_score = 0.0
    entity_message = "Entity analysis"
    entity_details = {
        "total_entities": 0,
        "entities_in_sql": 0,
        "missing_entities": [],
        "found_entities": []
    }
    
    try:
        if entities:
            total_entity_values = 0
            matched_entities = 0
            
            for entity_type, values in entities.items():
                if isinstance(values, list):
                    for value in values:
                        total_entity_values += 1
                        if str(value).lower() in sql.lower():
                            matched_entities += 1
                            entity_details["found_entities"].append(f"{entity_type}: {value}")
                        else:
                            entity_details["missing_entities"].append(f"{entity_type}: {value}")
            
            entity_details["total_entities"] = total_entity_values
            entity_details["entities_in_sql"] = matched_entities
            
            entity_score = matched_entities / total_entity_values if total_entity_values > 0 else 0.0
            
            if entity_score == 1.0:
                entity_message = f"All {total_entity_values} entities found in SQL"
            elif entity_score > 0.5:
                entity_message = f"{matched_entities}/{total_entity_values} entities found in SQL"
            else:
                entity_message = f"Poor entity usage: {matched_entities}/{total_entity_values} found"
        else:
            entity_message = "No entities detected to validate"
            
    except Exception as e:
        entity_score = 0.0
        entity_message = f"Entity validation error: {str(e)}"
        logger.error(f"Entity validation error: {e}")
    
    evaluation_results.update({
        "entity_score": entity_score,
        "entity_message": entity_message,
        "entity_details": entity_details
    })
    
    # 5. Enhanced Mapping Validation
    mapping_score = 0.0
    mapping_message = "Column mapping analysis"
    mapping_details = {
        "total_mappings": 0,
        "used_mappings": 0,
        "unused_columns": [],
        "used_columns": []
    }
    
    try:
        if mappings:
            total_mapped_columns = 0
            used_mapped_columns = 0
            
            for entity_type, mapping_info in mappings.items():
                if isinstance(mapping_info, dict) and "columns" in mapping_info:
                    columns = mapping_info["columns"]
                    for col in columns:
                        total_mapped_columns += 1
                        if col in sql:
                            used_mapped_columns += 1
                            mapping_details["used_columns"].append(f"{entity_type}: {col}")
                        else:
                            mapping_details["unused_columns"].append(f"{entity_type}: {col}")
            
            mapping_details["total_mappings"] = total_mapped_columns
            mapping_details["used_mappings"] = used_mapped_columns
            
            mapping_score = used_mapped_columns / total_mapped_columns if total_mapped_columns > 0 else 0.0
            
            if mapping_score > 0.8:
                mapping_message = f"Excellent column mapping: {used_mapped_columns}/{total_mapped_columns} used"
            elif mapping_score > 0.5:
                mapping_message = f"Good column mapping: {used_mapped_columns}/{total_mapped_columns} used"
            else:
                mapping_message = f"Poor column mapping: {used_mapped_columns}/{total_mapped_columns} used"
        else:
            mapping_message = "No column mappings to validate"
            
    except Exception as e:
        mapping_score = 0.0
        mapping_message = f"Mapping validation error: {str(e)}"
        logger.error(f"Mapping validation error: {e}")
    
    evaluation_results.update({
        "mapping_score": mapping_score,
        "mapping_message": mapping_message,
        "mapping_details": mapping_details
    })
    
    # 6. Value Validation (with error handling)
    try:
        from utils.value_validator import validate_values
        value_score, value_message = validate_values(entities, mappings)
    except ImportError:
        value_score, value_message = 0.0, "Value validator not available"
    except Exception as e:
        value_score, value_message = 0.0, f"Value validation error: {str(e)}"
    
    evaluation_results.update({
        "value_score": value_score,
        "value_message": value_message
    })
    
    # 7. Retrieval Relevance
    retrieval_score = 1.0 - np.mean(distances) / 2.0 if distances else 0.5
    retrieval_score = max(0.0, min(1.0, retrieval_score))  # Clamp between 0 and 1
    
    evaluation_results.update({
        "retrieval_score": round(retrieval_score, 3)
    })
    
    # 8. Legacy Confidence Score (for backward compatibility)
    # This is now just one component, not the main confidence score
    legacy_confidence = (
        0.20 * retrieval_score +
        0.25 * syntax_score +
        0.20 * schema_score +
        0.15 * clickhouse_score +
        0.10 * entity_score +
        0.05 * value_score +
        0.05 * mapping_score
    )
    
    evaluation_results["legacy_confidence"] = round(legacy_confidence, 3)
    
    # 9. Enhanced Performance Analysis
    performance_analysis = {
        "issues": [],
        "recommendations": [],
        "score": 1.0
    }
    
    try:
        sql_upper = sql.upper()
        
        # Check for SELECT *
        if "SELECT *" in sql_upper:
            performance_analysis["issues"].append("Uses SELECT * which may be inefficient")
            performance_analysis["recommendations"].append("Specify only needed columns")
            performance_analysis["score"] *= 0.8
        
        # Check for multiple joins
        join_count = len(re.findall(r'\bJOIN\b', sql_upper))
        if join_count > 3:
            performance_analysis["issues"].append(f"Many joins ({join_count}) may impact performance")
            performance_analysis["recommendations"].append("Consider query optimization")
            performance_analysis["score"] *= 0.9
        
        # Check for LIMIT clause
        if "LIMIT" not in sql_upper:
            performance_analysis["issues"].append("No LIMIT clause - may return large result sets")
            performance_analysis["recommendations"].append("Add LIMIT clause for better performance")
            performance_analysis["score"] *= 0.95
        
        # Check for WHERE clause
        if "WHERE" not in sql_upper and "FROM" in sql_upper:
            performance_analysis["issues"].append("No WHERE clause - may scan entire table")
            performance_analysis["recommendations"].append("Add WHERE clause to filter data")
            performance_analysis["score"] *= 0.9
        
        if not performance_analysis["issues"]:
            performance_message = "Good SQL performance characteristics"
        else:
            performance_message = f"{len(performance_analysis['issues'])} performance considerations"
            
    except Exception as e:
        performance_message = f"Performance analysis error: {str(e)}"
        performance_analysis["score"] = 0.5
    
    evaluation_results.update({
        "performance_message": performance_message,
        "performance_analysis": performance_analysis
    })
    
    # 10. SQL Quality Metrics (for integration with realistic confidence)
    sql_quality_metrics = {
        "has_valid_structure": syntax_score > 0.5,
        "uses_appropriate_tables": schema_score > 0.7,
        "handles_clickhouse_types": clickhouse_score > 0.8,
        "incorporates_entities": entity_score > 0.5,
        "follows_best_practices": performance_analysis["score"] > 0.8,
        "complexity_appropriate": True  # Could be enhanced based on query complexity
    }
    
    evaluation_results.update({
        "sql_quality_metrics": sql_quality_metrics
    })
    
    # Summary
    evaluation_results.update({
        "evaluation_summary": {
            "total_checks": 9,
            "passed_checks": sum([
                sql_quality_metrics["has_valid_structure"],
                sql_quality_metrics["uses_appropriate_tables"],
                sql_quality_metrics["handles_clickhouse_types"],
                sql_quality_metrics["incorporates_entities"],
                sql_quality_metrics["follows_best_practices"]
            ]),
            "overall_quality": "good" if legacy_confidence > 0.7 else "fair" if legacy_confidence > 0.5 else "poor"
        }
    })
    
    logger.info(f"SQL evaluation completed: {evaluation_results['evaluation_summary']}")
    
    return evaluation_results

def get_evaluation_summary_text(evaluation_results):
    """Generate a human-readable summary of the evaluation results"""
    
    summary = evaluation_results.get("evaluation_summary", {})
    passed = summary.get("passed_checks", 0)
    total = summary.get("total_checks", 0)
    quality = summary.get("overall_quality", "unknown")
    
    text = f"SQL Evaluation: {passed}/{total} checks passed ({quality} quality)\n"
    
    # Add key findings
    if evaluation_results.get("syntax_score", 0) < 0.5:
        text += "⚠️ Syntax issues detected\n"
    
    if evaluation_results.get("schema_score", 0) < 0.5:
        text += "⚠️ Schema compliance issues\n"
    
    if evaluation_results.get("entity_score", 0) < 0.5:
        text += "⚠️ Entity incorporation issues\n"
    
    performance_issues = evaluation_results.get("performance_analysis", {}).get("issues", [])
    if performance_issues:
        text += f"⚠️ {len(performance_issues)} performance considerations\n"
    
    return text.strip()