"""
Claude AI Service
Industrial-grade service for Claude API integration
Handles transcript analysis with retry logic, error handling, and rate limiting
"""

import json
import re
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import requests

from config.settings import Settings, SeverityLevel


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    missing_elements: List[str]
    severity: str
    summary: str
    raw_response: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class ClaudeService:
    """
    Service class for interacting with Claude AI API
    Implements retry logic, rate limiting, and comprehensive error handling
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude Service
        
        Args:
            api_key: Optional API key. If not provided, will use from environment
        """
        self.settings = Settings()
        self.api_key = api_key or self.settings.api_key
        self.api_url = self.settings.api.anthropic_api_url
        self.model = self.settings.api.model_name
        self.max_tokens = self.settings.api.max_tokens
        self.timeout = self.settings.api.timeout
        self.retry_attempts = self.settings.api.retry_attempts
        self.retry_delay = self.settings.api.retry_delay
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.5  # Minimum seconds between requests
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers
    
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
        Parse Claude's response and extract JSON
        
        Args:
            response_text: Raw response text from Claude
            
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
    
    def _make_api_request(self, prompt: str) -> requests.Response:
        """
        Make API request to Claude
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Response object
        """
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        return requests.post(
            self.api_url,
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout
        )
    
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
        
        # Apply rate limiting
        self._rate_limit()
        
        prompt = self._build_analysis_prompt(transcript)
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"API request attempt {attempt + 1}/{self.retry_attempts}")
                
                response = self._make_api_request(prompt)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract text content from response
                    text_content = ""
                    for content in result.get("content", []):
                        if content.get("type") == "text":
                            text_content = content.get("text", "")
                            break
                    
                    # Parse the response
                    parsed = self._parse_response(text_content)
                    
                    return AnalysisResult(
                        missing_elements=parsed.get("missing_elements", []),
                        severity=parsed.get("severity", SeverityLevel.UNKNOWN.value),
                        summary=parsed.get("summary", "Analysis completed"),
                        raw_response=text_content,
                        success=True
                    )
                
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    last_error = "Rate limited by API"
                    
                elif response.status_code == 401:
                    return AnalysisResult(
                        missing_elements=["API authentication failed"],
                        severity=SeverityLevel.UNKNOWN.value,
                        summary="Invalid API key",
                        success=False,
                        error_message="Authentication failed - check API key"
                    )
                
                else:
                    last_error = f"API error: {response.status_code}"
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                logger.warning(f"Request timed out on attempt {attempt + 1}")
                
            except requests.exceptions.ConnectionError:
                last_error = "Connection error"
                logger.warning(f"Connection error on attempt {attempt + 1}")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error: {e}")
            
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
            response = self._make_api_request("Hello, this is a connection test. Reply with 'OK'.")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
