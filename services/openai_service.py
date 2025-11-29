"""
OpenAI Service
Industrial-grade service for OpenAI API integration (including Azure OpenAI)
Handles transcript analysis with retry logic, error handling, and rate limiting
"""

import json
import re
import time
import logging
import importlib.util
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import os

from config.settings import Settings, SeverityLevel


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Try to import OpenAI
try:
    from openai import OpenAI, AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Please install: pip install openai>=1.30.0")


@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    missing_elements: List[str]
    severity: str
    summary: str
    raw_response: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


def load_config(config_file: str = "config.py") -> Optional[Dict[str, str]]:
    """
    Load configuration from config.py file
    
    Args:
        config_file: Path to config file
        
    Returns:
        Configuration dictionary or None
    """
    config_path = Path(config_file)
    if not config_path.exists():
        return None
    
    try:
        spec = importlib.util.spec_from_file_location("config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        cfg = {
            'use_azure': getattr(config_module, 'USE_AZURE_OPENAI', False),
            'openai_api_key': getattr(config_module, 'OPENAI_API_KEY', None),
            'openai_model': getattr(config_module, 'OPENAI_MODEL', 'gpt-4o-2024-08-06'),
            'azure_endpoint': getattr(config_module, 'AZURE_OPENAI_ENDPOINT', None),
            'azure_api_key': getattr(config_module, 'AZURE_OPENAI_API_KEY', None),
            'azure_deployment': getattr(config_module, 'AZURE_OPENAI_DEPLOYMENT_NAME', None),
        }
        
        # Validation
        if cfg['use_azure']:
            missing = [k for k in ['azure_endpoint', 'azure_api_key', 'azure_deployment'] if not cfg[k]]
            if missing:
                logger.error(f"Missing Azure OpenAI config fields: {missing}")
                return None
        else:
            if not cfg['openai_api_key']:
                logger.error("Missing OPENAI_API_KEY in config.py")
                return None
        
        return cfg
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None


class OpenAIService:
    """
    Service class for interacting with OpenAI/Azure OpenAI API
    Implements retry logic, rate limiting, and comprehensive error handling
    """
    
    def __init__(self, api_key: Optional[str] = None, use_azure: bool = False):
        """
        Initialize OpenAI Service
        
        Args:
            api_key: Optional API key. If not provided, will use from environment/config
            use_azure: Whether to use Azure OpenAI
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Please install: pip install openai>=1.30.0")
        
        self.settings = Settings()
        self.client = None
        self.model = "gpt-4o-2024-08-06"
        self.max_tokens = 125000
        self.retry_attempts = 4
        self.retry_delay = 1.0
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.5
        
        # Try to load from config.py first
        config = load_config()
        
        if config:
            self._setup_from_config(config)
        else:
            # Fall back to environment variables
            self._setup_from_env(api_key, use_azure)
    
    def _setup_from_config(self, config: Dict[str, Any]):
        """Setup client from config dictionary"""
        try:
            if config['use_azure']:
                self.client = AzureOpenAI(
                    api_key=config['azure_api_key'],
                    azure_endpoint=config['azure_endpoint'],
                    api_version="2024-02-15-preview"
                )
                self.model = config['azure_deployment']
                logger.info("Using Azure OpenAI")
            else:
                self.client = OpenAI(api_key=config['openai_api_key'])
                self.model = config.get('openai_model', 'gpt-4o-2024-08-06')
                logger.info("Using OpenAI")
        except Exception as e:
            logger.error(f"Failed to setup OpenAI client from config: {e}")
            raise
    
    def _setup_from_env(self, api_key: Optional[str], use_azure: bool):
        """Setup client from environment variables"""
        try:
            if use_azure or os.getenv("USE_AZURE_OPENAI", "").lower() == "true":
                azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                azure_key = os.getenv("AZURE_OPENAI_API_KEY")
                azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                
                if not all([azure_endpoint, azure_key, azure_deployment]):
                    raise ValueError("Missing Azure OpenAI environment variables")
                
                self.client = AzureOpenAI(
                    api_key=azure_key,
                    azure_endpoint=azure_endpoint,
                    api_version="2024-02-15-preview"
                )
                self.model = azure_deployment
                logger.info("Using Azure OpenAI from environment")
            else:
                openai_key = api_key or os.getenv("OPENAI_API_KEY")
                if not openai_key:
                    raise ValueError("Missing OPENAI_API_KEY")
                
                self.client = OpenAI(api_key=openai_key)
                self.model = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
                logger.info("Using OpenAI from environment")
        except Exception as e:
            logger.error(f"Failed to setup OpenAI client from env: {e}")
            raise
    
    def _build_analysis_prompt(self, transcript: str) -> str:
        """
        Build the analysis prompt for FNOL transcript analysis
        
        Args:
            transcript: The call transcript to analyze
            
        Returns:
            Formatted prompt string
        """
        sop_elements = self.settings.get_sop_elements_list()
        sop_list = "\n".join([f"{i+1}. {elem}" for i, elem in enumerate(sop_elements)])
        
        return f"""You are an expert insurance compliance analyst specializing in FNOL (First Notice of Loss) call quality assessment.

Analyze the following FNOL call transcript between an AI voice agent and an insurance holder. Identify ALL missing or inadequate elements according to standard FNOL SOP requirements.

TRANSCRIPT:
{transcript}

REQUIRED SOP ELEMENTS TO EVALUATE:
{sop_list}

EVALUATION CRITERIA:
- Mark an element as "missing" if it was not addressed at all in the conversation
- Mark an element as "inadequate" if it was partially addressed but lacks important details
- Consider the severity based on how critical the missing information is for claim processing

SEVERITY GUIDELINES:
- HIGH: Missing critical information that would prevent claim processing (policyholder verification, incident details, claim number)
- MEDIUM: Missing important but supplementary information (witness details, photos, police report)
- LOW: Minor omissions that don't significantly impact claim processing

Respond ONLY with a valid JSON object in this exact format (no additional text):
{{
  "missing_elements": ["element1", "element2"],
  "severity": "High|Medium|Low",
  "summary": "Brief 1-2 sentence summary of the main compliance issues found"
}}"""
    
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse OpenAI's response and extract JSON
        
        Args:
            response_text: Raw response text from OpenAI
            
        Returns:
            Parsed JSON dictionary
        """
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed: {e}")
        
        # Return default structure if parsing fails
        return {
            "missing_elements": ["Response parsing failed"],
            "severity": SeverityLevel.UNKNOWN.value,
            "summary": "Could not parse analysis response"
        }
    
    def analyze_transcript(self, transcript: str) -> AnalysisResult:
        """
        Analyze a single transcript for SOP compliance
        
        Args:
            transcript: The call transcript to analyze
            
        Returns:
            AnalysisResult object containing the analysis
        """
        if not transcript or not transcript.strip():
            return AnalysisResult(
                missing_elements=["No transcript provided"],
                severity=SeverityLevel.NA.value,
                summary="Empty transcript - unable to analyze",
                success=False,
                error_message="Empty transcript"
            )
        
        if not self.client:
            return AnalysisResult(
                missing_elements=["OpenAI client not initialized"],
                severity=SeverityLevel.UNKNOWN.value,
                summary="Service initialization failed",
                success=False,
                error_message="OpenAI client not configured properly"
            )
        
        # Apply rate limiting
        self._rate_limit()
        
        prompt = self._build_analysis_prompt(transcript)
        last_error = None
        delay_seconds = self.retry_delay
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                logger.info(f"OpenAI API request attempt {attempt}/{self.retry_attempts}")
                
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                content = resp.choices[0].message.content
                obj = json.loads(content)
                
                if isinstance(obj, dict) and 'claims' in obj and isinstance(obj['claims'], list):
                    obj.setdefault('evaluation_date', '')
                    obj.setdefault('carrier', '')
                
                # Parse the response for our format
                parsed = self._parse_response(content)
                
                return AnalysisResult(
                    missing_elements=parsed.get("missing_elements", []),
                    severity=parsed.get("severity", SeverityLevel.UNKNOWN.value),
                    summary=parsed.get("summary", "Analysis completed"),
                    raw_response=content,
                    success=True
                )
                
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}"
                logger.warning(f"JSON parsing failed on attempt {attempt}: {e}")
                
            except Exception as e:
                last_error = str(e)
                if attempt == self.retry_attempts:
                    logger.error(f"OpenAI extraction failed after retries: {e}")
                    break
                logger.warning(f"Attempt {attempt} failed: {e}")
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue
        
        # All retries failed
        return AnalysisResult(
            missing_elements=[f"Analysis failed: {last_error}"],
            severity=SeverityLevel.UNKNOWN.value,
            summary="Analysis could not be completed",
            success=False,
            error_message=last_error
        )
    
    def analyze_batch(
        self, 
        transcripts: List[str], 
        progress_callback: Optional[callable] = None
    ) -> List[AnalysisResult]:
        """
        Analyze multiple transcripts with progress tracking
        
        Args:
            transcripts: List of transcripts to analyze
            progress_callback: Optional callback function(current, total) for progress updates
            
        Returns:
            List of AnalysisResult objects
        """
        results = []
        total = len(transcripts)
        
        for i, transcript in enumerate(transcripts):
            result = self.analyze_transcript(transcript)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
    
    def test_connection(self) -> bool:
        """
        Test API connection and authentication
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.client:
                return False
            
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello, reply with 'OK'"}],
                max_tokens=10
            )
            return resp.choices[0].message.content is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
