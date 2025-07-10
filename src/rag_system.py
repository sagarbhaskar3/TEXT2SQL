# src/rag_system.py
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class HealthcareRAGSystem:
    def __init__(self, chroma_directory: str = "./knowledge_base"):
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=chroma_directory)
        
        # Initialize embedding model (same as used for indexing)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load collections
        self.collections = {
            "schema_info": self.chroma_client.get_collection("schema_info"),
            "sample_data": self.chroma_client.get_collection("sample_data"),
            "column_relationships": self.chroma_client.get_collection("column_relationships"),
            "data_patterns": self.chroma_client.get_collection("data_patterns")
        }
    
    def retrieve_context(self, query: str, top_k: int = 5) -> dict[str, List]:
        """Retrieve relevant context for a query"""
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Retrieve from all collections
        context = {}
        
        for collection_name, collection in self.collections.items():
            try:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                
                # Format results
                context[collection_name] = []
                if results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        context[collection_name].append({
                            "content": doc,
                            "metadata": results['metadatas'][0][i],
                            "distance": results['distances'][0][i]
                        })
            
            except Exception as e:
                print(f"Warning: Could not query {collection_name}: {e}")
                context[collection_name] = []
        
        return context
    
    def build_context_prompt(self, query: str, context: dict) -> str:
        """Build enhanced prompt with RAG context"""
        
        prompt_parts = []
        
        # Add schema information
        if context.get("schema_info"):
            prompt_parts.append("### Database Schema Information:")
            for item in context["schema_info"][:3]:  # Top 3 most relevant
                prompt_parts.append(f"- {item['content']}")
        
        # Add sample data
        if context.get("sample_data"):
            prompt_parts.append("\n### Sample Data Examples:")
            for item in context["sample_data"][:2]:  # Top 2 examples
                prompt_parts.append(f"- {item['content']}")
        
        # Add relationship info
        if context.get("column_relationships"):
            prompt_parts.append("\n### Column Relationships:")
            for item in context["column_relationships"][:2]:
                prompt_parts.append(f"- {item['content']}")
        
        # Add patterns
        if context.get("data_patterns"):
            prompt_parts.append("\n### Query Patterns:")
            for item in context["data_patterns"][:2]:
                prompt_parts.append(f"- {item['content']}")
        
        # Build final prompt
        enhanced_prompt = f"""### Task
Generate a ClickHouse SQL query based on the following information:

{chr(10).join(prompt_parts)}

### User Question
{query}

### Instructions
- Use the schema information to identify correct table and column names
- Follow the patterns shown in the examples
- Use ClickHouse SQL syntax
- Include appropriate JOINs if multiple tables are needed
- Add LIMIT clause for "top N" queries

### SQL Query
"""
        
        return enhanced_prompt