# src/csv_processor.py
import pandas as pd
import os
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json

class CSVToKnowledgeBase:
    def __init__(self, csv_directory: str = "./data/csv_files", 
                 chroma_directory: str = "./knowledge_base"):
        
        self.csv_directory = Path(csv_directory)
        self.chroma_directory = Path(chroma_directory)
        
        # Create directories
        self.csv_directory.mkdir(parents=True, exist_ok=True)
        self.chroma_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_directory))
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collections for different types of knowledge
        self.collections = {
            "schema_info": self.chroma_client.get_or_create_collection("schema_info"),
            "sample_data": self.chroma_client.get_or_create_collection("sample_data"),
            "column_relationships": self.chroma_client.get_or_create_collection("column_relationships"),
            "data_patterns": self.chroma_client.get_or_create_collection("data_patterns")
        }
    
    def process_all_csv_files(self):
        """Process all CSV files in the directory"""
        
        csv_files = list(self.csv_directory.glob("*.csv"))
        
        if not csv_files:
            print(f"❌ No CSV files found in {self.csv_directory}")
            print("📋 Please upload your CSV files to the data/csv_files/ directory")
            return False
        
        print(f"📁 Found {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            print(f"\n🔄 Processing {csv_file.name}...")
            self.process_single_csv(csv_file)
        
        print(f"\n✅ Processed all CSV files into ChromaDB knowledge base!")
        return True
    
    def process_single_csv(self, csv_file: Path):
        """Process a single CSV file and extract knowledge"""
        
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            table_name = csv_file.stem
            
            print(f"   📊 Loaded {len(df)} rows, {len(df.columns)} columns")
            
            # Extract different types of knowledge
            self._extract_schema_info(df, table_name)
            self._extract_sample_data(df, table_name)
            self._extract_column_relationships(df, table_name)
            self._extract_data_patterns(df, table_name)
            
        except Exception as e:
            print(f"   ❌ Error processing {csv_file.name}: {e}")
    
    def _extract_schema_info(self, df: pd.DataFrame, table_name: str):
        """Extract schema information from DataFrame"""
        
        schema_docs = []
        
        # Table overview
        table_overview = f"Table {table_name} has {len(df)} rows and {len(df.columns)} columns. "
        table_overview += f"Columns: {', '.join(df.columns.tolist())}."
        
        schema_docs.append({
            "content": table_overview,
            "metadata": {"type": "table_overview", "table": table_name},
            "id": f"{table_name}_overview"
        })
        
        # Column details
        for col in df.columns:
            col_info = f"Column {col} in table {table_name}: "
            col_info += f"Data type: {df[col].dtype}, "
            col_info += f"Non-null values: {df[col].count()}, "
            col_info += f"Unique values: {df[col].nunique()}"
            
            # Add sample values for categorical/text columns
            if df[col].dtype == 'object' and df[col].nunique() < 50:
                unique_vals = df[col].dropna().unique()[:10]
                col_info += f", Sample values: {', '.join(map(str, unique_vals))}"
            
            schema_docs.append({
                "content": col_info,
                "metadata": {"type": "column_info", "table": table_name, "column": col},
                "id": f"{table_name}_{col}_info"
            })
        
        # Add to ChromaDB
        self._add_to_collection("schema_info", schema_docs)
    
    def _extract_sample_data(self, df: pd.DataFrame, table_name: str):
        """Extract sample data patterns"""
        
        sample_docs = []
        
        # Sample rows as examples
        sample_rows = df.head(5).to_dict('records')
        
        for i, row in enumerate(sample_rows):
            row_content = f"Sample row from {table_name}: "
            row_content += ", ".join([f"{k}={v}" for k, v in row.items() if pd.notna(v)])
            
            sample_docs.append({
                "content": row_content,
                "metadata": {"type": "sample_row", "table": table_name, "row_index": i},
                "id": f"{table_name}_sample_{i}"
            })
        
        self._add_to_collection("sample_data", sample_docs)
    
    def _extract_column_relationships(self, df: pd.DataFrame, table_name: str):
        """Extract potential column relationships"""
        
        relationship_docs = []
        
        # Look for potential ID columns
        id_columns = [col for col in df.columns if 'id' in col.lower() or 'npi' in col.lower()]
        
        for col in id_columns:
            rel_content = f"Column {col} in {table_name} appears to be an identifier. "
            rel_content += f"Has {df[col].nunique()} unique values out of {len(df)} rows."
            
            # Check if it could be a foreign key
            if df[col].nunique() < len(df) * 0.9:
                rel_content += " May be used for joining with other tables."
            
            relationship_docs.append({
                "content": rel_content,
                "metadata": {"type": "relationship", "table": table_name, "column": col},
                "id": f"{table_name}_{col}_relationship"
            })
        
        self._add_to_collection("column_relationships", relationship_docs)
    
    def _extract_data_patterns(self, df: pd.DataFrame, table_name: str):
        """Extract data patterns for SQL generation"""
        
        pattern_docs = []
        
        # Common query patterns based on data
        
        # If there are date columns
        date_columns = df.select_dtypes(include=['datetime64', 'object']).columns
        date_columns = [col for col in date_columns if 'date' in col.lower() or 'year' in col.lower()]
        
        if date_columns:
            pattern_content = f"Table {table_name} has time-based columns: {', '.join(date_columns)}. "
            pattern_content += "Useful for time-series analysis and filtering by date ranges."
            
            pattern_docs.append({
                "content": pattern_content,
                "metadata": {"type": "query_pattern", "table": table_name, "pattern": "temporal"},
                "id": f"{table_name}_temporal_pattern"
            })
        
        # If there are amount/numeric columns
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        amount_columns = [col for col in numeric_columns if any(word in col.lower() 
                         for word in ['amount', 'price', 'cost', 'total', 'count'])]
        
        if amount_columns:
            pattern_content = f"Table {table_name} has numeric columns for aggregation: {', '.join(amount_columns)}. "
            pattern_content += "Useful for SUM, AVG, COUNT operations and ranking queries."
            
            pattern_docs.append({
                "content": pattern_content,
                "metadata": {"type": "query_pattern", "table": table_name, "pattern": "aggregation"},
                "id": f"{table_name}_aggregation_pattern"
            })
        
        self._add_to_collection("data_patterns", pattern_docs)
    
    def _add_to_collection(self, collection_name: str, docs: List[dict]):
        """Add documents to ChromaDB collection"""
        
        if not docs:
            return
        
        collection = self.collections[collection_name]
        
        # Prepare data for ChromaDB
        contents = [doc["content"] for doc in docs]
        metadatas = [doc["metadata"] for doc in docs]
        ids = [doc["id"] for doc in docs]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(contents).tolist()
        
        # Add to collection
        collection.add(
            documents=contents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
    
    def get_knowledge_base_stats(self):
        """Get statistics about the knowledge base"""
        
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = collection.count()
        
        return stats