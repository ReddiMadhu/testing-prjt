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
    """Standard Operating Procedure elements for FNOL analysis - organized by themes"""
    
    # Theme definitions
    themes: List[Dict[str, str]] = field(default_factory=lambda: [
        {"id": "T1", "name": "CALL OPENING & IDENTITY VERIFICATION", "element_range": "1-5"},
        {"id": "T2", "name": "CONTACT INFORMATION VERIFICATION", "element_range": "6-14"},
        {"id": "T3", "name": "LOSS DETAILS GATHERING", "element_range": "15-21"},
        {"id": "T4", "name": "VEHICLE INFORMATION", "element_range": "22-29"},
        {"id": "T5", "name": "DAMAGE ASSESSMENT", "element_range": "30-37"},
        {"id": "T6", "name": "INJURY & SAFETY", "element_range": "38-42"},
        {"id": "T7", "name": "INCIDENT DOCUMENTATION", "element_range": "43-46"},
        {"id": "T8", "name": "SERVICES OFFERING", "element_range": "47-53"},
        {"id": "T9", "name": "CLAIM PROCESSING", "element_range": "54-59"},
        {"id": "T10", "name": "CALL CONCLUSION", "element_range": "60-61"}
    ])
    
    required_elements: List[Dict[str, str]] = field(default_factory=lambda: [
        # THEME: CALL OPENING & IDENTITY VERIFICATION (1-5)
        {"id": "1", "name": "Did not ask if caller has policy number upfront using suggested wording", "theme": "CALL OPENING & IDENTITY VERIFICATION", "description": "Policy number inquiry"},
        {"id": "2", "name": "Did not verify if caller is policyholder/spouse/authorized person", "theme": "CALL OPENING & IDENTITY VERIFICATION", "description": "Caller authorization verification"},
        {"id": "3", "name": "Did not set clear explanation of FNOL process using suggested wording", "theme": "CALL OPENING & IDENTITY VERIFICATION", "description": "FNOL process explanation"},
        {"id": "4", "name": "Did not explain call recording/monitoring purpose", "theme": "CALL OPENING & IDENTITY VERIFICATION", "description": "Call recording disclosure"},
        {"id": "5", "name": "Did not verify if caller needs immediate medical assistance", "theme": "CALL OPENING & IDENTITY VERIFICATION", "description": "Medical assistance check"},
        
        # THEME: CONTACT INFORMATION VERIFICATION (6-14)
        {"id": "6", "name": "Did not verify/update mailing address", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Mailing address verification"},
        {"id": "7", "name": "Did not verify/update phone numbers", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Phone numbers verification"},
        {"id": "8", "name": "Did not verify/update email address", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Email address verification"},
        {"id": "9", "name": "Did not read back contact information for verification", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Contact info read-back"},
        {"id": "10", "name": "Did not verify language preferences", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Language preferences"},
        {"id": "11", "name": "Did not verify if caller has different name/address than policy", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Name/address mismatch check"},
        {"id": "12", "name": "Did not identify main contact for claim", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Main contact identification"},
        {"id": "13", "name": "Did not verify/update notification preferences", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Notification preferences"},
        {"id": "14", "name": "Did not verify/update texting program preferences", "theme": "CONTACT INFORMATION VERIFICATION", "description": "Texting program preferences"},
        
        # THEME: LOSS DETAILS GATHERING (15-21)
        {"id": "15", "name": "Did not verify if loss date/time was approximate", "theme": "LOSS DETAILS GATHERING", "description": "Loss date/time approximation"},
        {"id": "16", "name": "Did not ask for purpose of trip", "theme": "LOSS DETAILS GATHERING", "description": "Trip purpose inquiry"},
        {"id": "17", "name": "Did not gather complete loss location details (cross streets, mile markers, location type)", "theme": "LOSS DETAILS GATHERING", "description": "Complete loss location details"},
        {"id": "18", "name": "Did not ask about weather conditions", "theme": "LOSS DETAILS GATHERING", "description": "Weather conditions inquiry"},
        {"id": "19", "name": "Did not ask about witnesses", "theme": "LOSS DETAILS GATHERING", "description": "Witness inquiry"},
        {"id": "20", "name": "Did not ask about property damage", "theme": "LOSS DETAILS GATHERING", "description": "Property damage inquiry"},
        {"id": "21", "name": "Did not create proper running notes", "theme": "LOSS DETAILS GATHERING", "description": "Running notes documentation"},
        
        # THEME: VEHICLE INFORMATION (22-29)
        {"id": "22", "name": "Did not verify vehicle ownership/policy listing", "theme": "VEHICLE INFORMATION", "description": "Vehicle ownership verification"},
        {"id": "23", "name": "Did not gather complete vehicle details (style, color, VIN, license plate, state)", "theme": "VEHICLE INFORMATION", "description": "Complete vehicle details"},
        {"id": "24", "name": "Did not ask for odometer reading", "theme": "VEHICLE INFORMATION", "description": "Odometer reading"},
        {"id": "25", "name": "Did not ask if vehicle was stolen", "theme": "VEHICLE INFORMATION", "description": "Vehicle theft inquiry"},
        {"id": "26", "name": "Did not ask about vehicle recovery condition (for stolen vehicles)", "theme": "VEHICLE INFORMATION", "description": "Stolen vehicle recovery condition"},
        {"id": "27", "name": "Did not ask if vehicle was parked/unoccupied", "theme": "VEHICLE INFORMATION", "description": "Parked/unoccupied status"},
        {"id": "28", "name": "Did not ask about anti-theft devices", "theme": "VEHICLE INFORMATION", "description": "Anti-theft devices inquiry"},
        {"id": "29", "name": "Did not ask if vehicle was locked", "theme": "VEHICLE INFORMATION", "description": "Vehicle locked status"},
        
        # THEME: DAMAGE ASSESSMENT (30-37)
        {"id": "30", "name": "Did not properly document point of first impact", "theme": "DAMAGE ASSESSMENT", "description": "Point of first impact"},
        {"id": "31", "name": "Did not properly document all damaged areas", "theme": "DAMAGE ASSESSMENT", "description": "All damaged areas documentation"},
        {"id": "32", "name": "Did not ask about airbag deployment", "theme": "DAMAGE ASSESSMENT", "description": "Airbag deployment inquiry"},
        {"id": "33", "name": "Did not verify vehicle drivability", "theme": "DAMAGE ASSESSMENT", "description": "Vehicle drivability verification"},
        {"id": "34", "name": "Did not ask if vehicle starts (for non-drivable vehicles)", "theme": "DAMAGE ASSESSMENT", "description": "Vehicle starts inquiry"},
        {"id": "35", "name": "Did not ask about equipment failure", "theme": "DAMAGE ASSESSMENT", "description": "Equipment failure inquiry"},
        {"id": "36", "name": "Did not document interior damage", "theme": "DAMAGE ASSESSMENT", "description": "Interior damage documentation"},
        {"id": "37", "name": "Did not document personal effects damage", "theme": "DAMAGE ASSESSMENT", "description": "Personal effects damage"},
        
        # THEME: INJURY & SAFETY (38-42)
        {"id": "38", "name": "Did not ask about injuries for all parties", "theme": "INJURY & SAFETY", "description": "Injuries for all parties"},
        {"id": "39", "name": "Did not verify intention to seek medical treatment", "theme": "INJURY & SAFETY", "description": "Medical treatment intention"},
        {"id": "40", "name": "Did not ask about number of passengers", "theme": "INJURY & SAFETY", "description": "Number of passengers"},
        {"id": "41", "name": "Did not ask about child car seat (especially for California claims)", "theme": "INJURY & SAFETY", "description": "Child car seat inquiry"},
        {"id": "42", "name": "Did not gather passenger contact information", "theme": "INJURY & SAFETY", "description": "Passenger contact information"},
        
        # THEME: INCIDENT DOCUMENTATION (43-46)
        {"id": "43", "name": "Did not ask about police notification/report", "theme": "INCIDENT DOCUMENTATION", "description": "Police notification/report"},
        {"id": "44", "name": "Did not ask about citations/tickets", "theme": "INCIDENT DOCUMENTATION", "description": "Citations/tickets inquiry"},
        {"id": "45", "name": "Did not gather other party's insurance carrier information", "theme": "INCIDENT DOCUMENTATION", "description": "Other party insurance info"},
        {"id": "46", "name": "Did not ask about special claim permissions (employee/sensitive)", "theme": "INCIDENT DOCUMENTATION", "description": "Special claim permissions"},
        
        # THEME: SERVICES OFFERING (47-53)
        {"id": "47", "name": "Did not offer accident scene towing", "theme": "SERVICES OFFERING", "description": "Accident scene towing offer"},
        {"id": "48", "name": "Did not offer Auto Repair Network (OYSARN)", "theme": "SERVICES OFFERING", "description": "Auto Repair Network offer"},
        {"id": "49", "name": "Did not offer Drive-In services", "theme": "SERVICES OFFERING", "description": "Drive-In services offer"},
        {"id": "50", "name": "Did not offer Virtual Appraisal", "theme": "SERVICES OFFERING", "description": "Virtual Appraisal offer"},
        {"id": "51", "name": "Did not offer rental car services", "theme": "SERVICES OFFERING", "description": "Rental car services offer"},
        {"id": "52", "name": "Did not offer Auto Glass services", "theme": "SERVICES OFFERING", "description": "Auto Glass services offer"},
        {"id": "53", "name": "Did not explain services in proper sequence", "theme": "SERVICES OFFERING", "description": "Services sequence explanation"},
        
        # THEME: CLAIM PROCESSING (54-59)
        {"id": "54", "name": "Did not explain payment preferences/options", "theme": "CLAIM PROCESSING", "description": "Payment preferences explanation"},
        {"id": "55", "name": "Did not share deductible information", "theme": "CLAIM PROCESSING", "description": "Deductible information sharing"},
        {"id": "56", "name": "Did not explain 'Track Your Claim' functionality", "theme": "CLAIM PROCESSING", "description": "Track Your Claim explanation"},
        {"id": "57", "name": "Did not explain next steps and timeline", "theme": "CLAIM PROCESSING", "description": "Next steps and timeline"},
        {"id": "58", "name": "Did not ask if caller has documents/photos to upload", "theme": "CLAIM PROCESSING", "description": "Documents/photos upload inquiry"},
        {"id": "59", "name": "Did not verify if warm transfer is needed/eligible", "theme": "CLAIM PROCESSING", "description": "Warm transfer eligibility"},
        
        # THEME: CALL CONCLUSION (60-61)
        {"id": "60", "name": "Did not provide claim number", "theme": "CALL CONCLUSION", "description": "Claim number provision"},
        {"id": "61", "name": "Did not ask if caller wants to write down claim information", "theme": "CALL CONCLUSION", "description": "Claim info write-down offer"}
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
