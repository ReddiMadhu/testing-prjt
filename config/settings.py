"""
Application Settings and Configuration
Industrial-grade configuration management for EXL FNOL Transcript Analyzer
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Environment(Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SeverityLevel(Enum):
    """Compliance severity levels"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"
    NA = "N/A"


@dataclass
class APIConfig:
    """Claude API Configuration settings"""
    anthropic_api_url: str = "https://api.anthropic.com/v1/messages"
    model_name: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1000
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class GeminiConfig:
    """Gemini API Configuration settings"""
    model_name: str = "gemini-2.5-flash"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class OpenAIConfig:
    """OpenAI/Azure OpenAI Configuration settings"""
    model_name: str = "gpt-4o-2024-08-06"
    max_tokens: int = 125000
    timeout: int = 30
    retry_attempts: int = 4
    retry_delay: float = 1.0
    use_azure: bool = False


@dataclass
class FileConfig:
    """File handling configuration"""
    allowed_extensions: List[str] = field(default_factory=lambda: ['xlsx', 'xls', 'csv'])
    max_file_size_mb: int = 50
    max_rows_to_process: int = 100
    default_rows_to_process: int = 5
    chunk_size: int = 1000


@dataclass
class UIConfig:
    """UI Configuration settings"""
    page_title: str = "EXL FNOL Transcript Analyzer"
    page_icon: str = "./assets/exl_logo.png"
    layout: str = "wide"
    sidebar_state: str = "expanded"
    show_preview_rows: int = 5


@dataclass
class SOPElements:
    """Standard Operating Procedure elements for FNOL analysis"""
    required_elements: List[Dict[str, str]] = field(default_factory=lambda: [
        {"id": "1", "name": "Policyholder verification", "description": "Name, policy number verification"},
        {"id": "2", "name": "Incident datetime & location", "description": "Date, time, and location of incident"},
        {"id": "3", "name": "Incident description", "description": "Detailed description of what happened"},
        {"id": "4", "name": "Parties involved", "description": "Names, contact info of all parties"},
        {"id": "5", "name": "Injuries reported", "description": "Severity, medical attention required"},
        {"id": "6", "name": "Property damage", "description": "Details of property damage"},
        {"id": "7", "name": "Police report", "description": "Police report filed, report number"},
        {"id": "8", "name": "Witness information", "description": "Witness names and contact details"},
        {"id": "9", "name": "Documentation", "description": "Photos/documentation mentioned"},
        {"id": "10", "name": "Next steps", "description": "Next steps communicated to caller"},
        {"id": "11", "name": "Claim number", "description": "Claim number assigned and communicated"},
        {"id": "12", "name": "Professional tone", "description": "Professional and empathetic tone maintained"}
    ])


class Settings:
    """
    Main settings class that aggregates all configuration
    Implements singleton pattern for consistent access across application
    """
    _instance: Optional['Settings'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize all configuration objects"""
        self.environment = self._get_environment()
        self.api = APIConfig()
        self.gemini = GeminiConfig()
        self.openai = OpenAIConfig()
        self.file = FileConfig()
        self.ui = UIConfig()
        self.sop = SOPElements()
        self.debug = self.environment == Environment.DEVELOPMENT
        
        # Load API keys and provider from environment
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
        self.use_azure_openai = os.getenv("USE_AZURE_OPENAI", "").lower() == "true"
        self.llm_provider = os.getenv("LLM_PROVIDER", "claude").lower()
    
    @staticmethod
    def _get_environment() -> Environment:
        """Get current environment from environment variable"""
        env = os.getenv("APP_ENVIRONMENT", "development").lower()
        try:
            return Environment(env)
        except ValueError:
            return Environment.DEVELOPMENT
    
    def get_api_headers(self) -> Dict[str, str]:
        """Get API headers for Claude API calls"""
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers
    
    def validate_file_extension(self, filename: str) -> bool:
        """Validate if file extension is allowed"""
        if not filename:
            return False
        ext = filename.rsplit('.', 1)[-1].lower()
        return ext in self.file.allowed_extensions
    
    def get_sop_elements_list(self) -> List[str]:
        """Get list of SOP element names"""
        return [element["name"] for element in self.sop.required_elements]


# Global settings instance
settings = Settings()
