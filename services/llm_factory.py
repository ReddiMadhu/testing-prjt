"""
LLM Service Factory
Factory pattern to select the appropriate LLM service based on configuration
"""

from config.settings import Settings
from services.claude_service import ClaudeService
from services.gemini_service import GeminiService


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
    
    # Use provided provider or fall back to settings
    if not provider:
        provider = settings.llm_provider
    
    provider = provider.lower()
    
    if provider == "gemini":
        return GeminiService()
    elif provider == "openai":
        from services.openai_service import OpenAIService
        return OpenAIService()
    else:
        # Default to Claude
        return ClaudeService()
