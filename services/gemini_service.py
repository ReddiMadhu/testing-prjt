"""
Gemini AI Service
Industrial-grade service for Gemini API integration
Handles transcript analysis with retry logic, error handling, and rate limiting
"""

import json
import re
import time
import logging
from typing import Dict, List, Optional, Any
from google import genai
from google.genai import types

from config.settings import Settings, SeverityLevel
from services.claude_service import AnalysisResult


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service class for interacting with Google Gemini API
    Implements retry logic, rate limiting, and comprehensive error handling
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Service
        
        Args:
            api_key: Optional API key. If not provided, will use from environment
        """
        self.settings = Settings()
        self.api_key = api_key or self.settings.gemini_api_key
        self.model = self.settings.gemini.model_name
        self.timeout = self.settings.gemini.timeout
        self.retry_attempts = self.settings.gemini.retry_attempts
        self.retry_delay = self.settings.gemini.retry_delay
        
        # Initialize client
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            # Try to initialize without explicit key (relies on env vars or ADC)
            try:
                self.client = genai.Client()
            except ValueError:
                logger.warning("Gemini API key not found. Service will fail if called.")
                self.client = None
    
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
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's response and extract JSON
        
        Args:
            response_text: Raw response text from Gemini
            
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
        if not self.client:
            return AnalysisResult(
                missing_elements=["API Configuration Error"],
                severity=SeverityLevel.NA.value,
                summary="Gemini API key is missing. Please configure GEMINI_API_KEY in .env file.",
                success=False,
                error_message="Missing API Key"
            )

        if not transcript or not transcript.strip():
            return AnalysisResult(
                missing_elements=["No transcript provided"],
                severity=SeverityLevel.NA.value,
                summary="Empty transcript - unable to analyze",
                success=False,
                error_message="Empty transcript"
            )
        
        prompt = self._build_analysis_prompt(transcript)
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Gemini API request attempt {attempt + 1}/{self.retry_attempts}")
                
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                
                if response.text:
                    # Parse the response
                    parsed = self._parse_response(response.text)
                    
                    return AnalysisResult(
                        missing_elements=parsed.get("missing_elements", []),
                        severity=parsed.get("severity", SeverityLevel.UNKNOWN.value),
                        summary=parsed.get("summary", "Analysis completed"),
                        raw_response=response.text,
                        success=True
                    )
                else:
                    last_error = "Empty response from API"
                    logger.warning("Empty response from Gemini API")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Gemini API error: {e}")
            
            # Wait before retry
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        # All retries failed
        return AnalysisResult(
            missing_elements=[f"Analysis failed: {last_error}"],
            severity=SeverityLevel.UNKNOWN.value,
            summary="Analysis could not be completed",
            success=False,
            error_message=last_error
        )
    
    def test_connection(self) -> bool:
        """
        Test API connection and authentication
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents="Hello, this is a connection test. Reply with 'OK'."
            )
            return response.text is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
