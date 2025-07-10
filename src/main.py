# src/main.py
import os
import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.append(str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()  # This will load the .env file

from csv_processor import CSVToKnowledgeBase
from sql_generator import HealthcareSQLSystem
def setup_system():
    """Setup the complete system"""
    
    print("🏥 Healthcare Text2SQL System")
    print("=" * 40)
    
    # Step 1: Process CSV files
    print("\n📁 Step 1: Processing CSV files...")
    csv_processor = CSVToKnowledgeBase()
    
    if not csv_processor.process_all_csv_files():
        print("\n❌ Please upload your CSV files to data/csv_files/ directory")
        return None
    
    # Show knowledge base stats
    stats = csv_processor.get_knowledge_base_stats()
    print(f"\n📊 Knowledge Base Stats:")
    for collection, count in stats.items():
        print(f"   {collection}: {count} documents")
    
    # Step 2: Initialize SQL system
    print("\n🤖 Step 2: Initializing SQL generation system...")
    sql_system = HealthcareSQLSystem()
    
    print("✅ System ready!")
    return sql_system

def run_demo(sql_system):
    """Run interactive demo"""
    
    print("\n" + "=" * 40)
    print("💬 Interactive Demo")
    print("Type your questions or 'quit' to exit")
    print("=" * 40)
    
    example_queries = [
        "Find all providers in California",
        "Show me the top prescribers by patient count",
        "What are the most common specialties?",
        "Find providers who received payments over $1000",
        "Show prescription patterns by state"
    ]
    
    print("\n💡 Example queries:")
    for i, example in enumerate(example_queries, 1):
        print(f"   {i}. {example}")
    
    while True:
        print("\n" + "-" * 40)
        user_query = input("🔍 Your question: ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_query:
            continue
        
        try:
            result = sql_system.process_query(user_query)
            
            print(f"\n📝 Generated SQL:")
            print("-" * 30)
            print(result["sql"])
            print("-" * 30)
            
            # Show context summary
            print(f"\n📚 Retrieved Context:")
            for collection, items in result["context"].items():
                print(f"   {collection}: {len(items)} relevant documents")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Check API token
    if not os.getenv("HUGGINGFACE_API_TOKEN"):
        print("❌ Please set HUGGINGFACE_API_TOKEN in your .env file")
        print("Get free token from: https://huggingface.co/settings/tokens")
        exit(1)
    
    # Setup and run
    sql_system = setup_system()
    if sql_system:
        run_demo(sql_system)