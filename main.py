# main.py - Updated Streamlit Frontend Interface
import streamlit as st
from datetime import datetime
import traceback
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import core modules
from core.system_initializer import SystemInitializer
from core.query_processor import QueryProcessor
from utils.ui_components import UIComponents
from utils.logging_utils import setup_logging, log_query_result
from config.app_config import APP_CONFIG

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class HealthcareText2SQLApp:
    """Main Streamlit application for Healthcare Text2SQL"""
    
    def __init__(self):
        self.ui = UIComponents()
        self.system_initializer = SystemInitializer()
        self.query_processor = None
        
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=APP_CONFIG['app_title'],
            page_icon=APP_CONFIG['app_icon'],
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    @st.cache_resource
    def initialize_systems(_self):
        """Initialize all system components with caching"""
        return _self.system_initializer.initialize_all()
    
    def handle_query_processing(self, query: str):
        """Handle the main query processing workflow"""
        if not query or not query.strip():
            st.error("Please enter a query")
            return
        
        with st.spinner("🤖 Processing your query..."):
            start_time = datetime.now()
            
            try:
                # Process the query
                result = self.query_processor.process_complete_query(query)
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                result['processing_time'] = processing_time
                
                # Log the result
                log_query_result(query, result)
                
                # Display results
                if result.get('success', False):
                    self.ui.display_successful_result(result)
                    self.ui.display_detailed_analysis(result)
                else:
                    self.ui.display_error_result(result)
                    
            except Exception as e:
                logger.error(f"Query processing failed: {e}")
                st.error(f"❌ Query processing failed: {e}")
                
                with st.expander("🔍 Error Details", expanded=False):
                    st.code(traceback.format_exc())
    
    def run(self):
        """Main application entry point"""
        try:
            # Setup page configuration
            self.setup_page_config()
            
            # Display header
            self.ui.display_header()
            
            # Initialize systems
            with st.spinner("🚀 Initializing systems..."):
                systems = self.initialize_systems()
                
                if not systems['success']:
                    st.error("❌ Failed to initialize systems. Please check your setup.")
                    st.error(systems['error'])
                    st.stop()
                
                # Initialize query processor with systems
                self.query_processor = QueryProcessor(
                    hybrid_generator=systems['hybrid_generator'],
                    index=systems['index'],
                    sample_values=systems['sample_values']
                )
            
            st.success("✅ All systems initialized successfully!")
            
            # Display sidebar
            self.ui.display_sidebar()
            
            # Main query interface
            query = self.ui.display_query_interface()
            
            # Handle query submission
            if st.session_state.get('generate_clicked', False):
                self.handle_query_processing(query)
                st.session_state['generate_clicked'] = False
                
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"❌ Application error: {e}")
            st.error("Please check the logs for more details.")

def main():
    """Application entry point"""
    app = HealthcareText2SQLApp()
    app.run()

if __name__ == "__main__":
    main()