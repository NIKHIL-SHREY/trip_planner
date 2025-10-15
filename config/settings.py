import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Settings:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "trip-planner-agent")
    
    # LLM Configuration - UPDATED MODEL NAME
    LLM_MODEL = "gemini-2.0-flash"  # Changed from gemini-pro
    LLM_TEMPERATURE = 0.1
    
    # API Endpoints
    OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"
    AVIATIONSTACK_BASE_URL = "http://api.aviationstack.com/v1"
    
    # Application Settings
    MAX_ITERATIONS = 10
    DEFAULT_BUDGET = 1000
    MAX_CONVERSATION_HISTORY = 20
    
    # LangSmith Configuration
    LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
    
    def validate_settings(self):
        missing_keys = []
        if not self.GEMINI_API_KEY:
            missing_keys.append("GEMINI_API_KEY")
        if not self.OPENWEATHER_API_KEY:
            missing_keys.append("OPENWEATHER_API_KEY")
        if not self.LANGCHAIN_API_KEY:
            missing_keys.append("LANGCHAIN_API_KEY")
        
        if missing_keys:
            raise ValueError(f"Missing environment variables: {', '.join(missing_keys)}")
        
        # Test LangSmith connection
        if self.LANGCHAIN_TRACING_V2 and self.LANGCHAIN_API_KEY:
            try:
                import langsmith
                client = langsmith.Client()
                print("✅ LangSmith connection successful")
            except Exception as e:
                print(f"⚠️ LangSmith connection issue: {e}")

settings = Settings()