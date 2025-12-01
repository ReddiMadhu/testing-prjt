"""
LLM Service Factory
Factory pattern to select the appropriate LLM service based on configuration
"""

from config.settings import Settings
from services.claude_service import ClaudeService
from services.gemini_service import GeminiService
from services.langchain_gemini_service import LangChainGeminiService


def get_llm_service(provider: str = None):
    """
    Get the configured LLM service instance
    
    Args:
        provider: Optional provider name ('claude', 'gemini', or 'openai'). 
                 If None, uses configuration default.
    
    Returns:
        Instance of ClaudeService, GeminiService, or OpenAIService
    """
    settings = Settings()
    

        # Default to Claude
    return LangChainGeminiService()
