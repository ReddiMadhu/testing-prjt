"""
LangChain Gemini Service
Industrial-grade service for Google Gemini API integration using LangChain and LangGraph
Handles FNOL transcript analysis with retry logic, error handling, and structured outputs
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config.settings import Settings, SeverityLevel


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Data Models ---
class SOPAnalysis(BaseModel):
    """Structured output model for SOP compliance analysis"""
    missing_elements: List[str] = Field(
        description="List of SOP elements that were missed or inadequately addressed in the transcript"
    )
    severity: str = Field(
        description="Severity level: High, Medium, or Low based on impact on claim processing"
    )
    summary: str = Field(
        description="Brief 1-2 sentence summary of the main compliance issues found"
    )


class AnalysisState(TypedDict):
    """State definition for LangGraph workflow"""
    transcript: str
    missing_elements: List[str]
    severity: str
    summary: str
    success: bool
    error_message: Optional[str]


@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    missing_elements: List[str]
    severity: str
    summary: str
    raw_response: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class LangChainGeminiService:
    """
    Service class for interacting with Google Gemini API using LangChain and LangGraph
    Implements retry logic, rate limiting, and comprehensive error handling
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LangChain Gemini Service
        
        Args:
            api_key: Optional API key. If not provided, will use from environment
        """
        self.settings = Settings()
        self.model_name = "gemini-2.5-flash"
        self.retry_attempts = 4
        self.retry_delay = 1.0
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.5
        
        # Setup API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Missing Google API key. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        
        # Initialize LLM
        self._setup_llm()
        
        # Build the LangGraph workflow
        self._build_workflow()
    
    def _setup_llm(self):
        """Setup LangChain LLM with structured output"""
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.0
            )
            self.structured_llm = self.llm.with_structured_output(SOPAnalysis)
            logger.info(f"Using Google Gemini model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to setup LLM: {e}")
            raise
    
    def _get_sop_checklist(self) -> str:
        """Get formatted SOP checklist from settings"""
        sop_elements = self.settings.get_sop_elements_list()
        return "\n".join([f"{i+1}. {elem}" for i, elem in enumerate(sop_elements)])
    
    def _build_analysis_prompt(self) -> ChatPromptTemplate:
        """Build the analysis prompt template for FNOL transcript analysis"""
        parser = JsonOutputParser(pydantic_object=SOPAnalysis)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """You are an expert insurance compliance analyst specializing in FNOL (First Notice of Loss) call quality assessment.

Analyze the provided FNOL call transcript between an AI voice agent and an insurance holder. Identify ALL missing or inadequate elements according to standard FNOL SOP requirements.

EVALUATION CRITERIA:
- Mark an element as "missing" if it was not addressed at all in the conversation
- Mark an element as "inadequate" if it was partially addressed but lacks important details
- Consider the severity based on how critical the missing information is for claim processing

SEVERITY GUIDELINES:
- High: Missing critical information that would prevent claim processing (policyholder verification, incident details, claim number)
- Medium: Missing important but supplementary information (witness details, photos, police report)
- Low: Minor omissions that don't significantly impact claim processing

Return your analysis using the required JSON schema."""
            ),
            ("human", 
             """Transcript:
{transcript}

SOP Checklist (Required Elements to Evaluate):
{checklist}

{format_instructions}"""
            )
        ])
        
        return prompt, parser
    
    def _build_workflow(self):
        """Build the LangGraph workflow for transcript analysis"""
        
        def evaluate_sop(state: AnalysisState) -> Dict[str, Any]:
            """Node function to evaluate SOP compliance"""
            transcript = state["transcript"]
            
            if not transcript or not transcript.strip():
                return {
                    "missing_elements": ["No transcript provided"],
                    "severity": SeverityLevel.NA.value,
                    "summary": "Empty transcript - unable to analyze",
                    "success": False,
                    "error_message": "Empty transcript"
                }
            
            prompt_template, parser = self._build_analysis_prompt()
            
            formatted_prompt = prompt_template.format(
                transcript=transcript,
                checklist=self._get_sop_checklist(),
                format_instructions=parser.get_format_instructions()
            )
            
            last_error = None
            delay_seconds = self.retry_delay
            
            for attempt in range(1, self.retry_attempts + 1):
                try:
                    logger.info(f"Gemini API request attempt {attempt}/{self.retry_attempts}")
                    
                    # Apply rate limiting
                    self._rate_limit()
                    
                    # Invoke structured LLM
                    llm_response = self.structured_llm.invoke(formatted_prompt)
                    
                    if llm_response:
                        return {
                            "missing_elements": llm_response.missing_elements,
                            "severity": llm_response.severity,
                            "summary": llm_response.summary,
                            "success": True,
                            "error_message": None
                        }
                    else:
                        last_error = "Empty response from LLM"
                        
                except Exception as e:
                    last_error = str(e)
                    if attempt == self.retry_attempts:
                        logger.error(f"Gemini extraction failed after retries: {e}")
                        break
                    logger.warning(f"Attempt {attempt} failed: {e}")
                    time.sleep(delay_seconds)
                    delay_seconds *= 2
                    continue
            
            # All retries failed
            return {
                "missing_elements": [f"Analysis failed: {last_error}"],
                "severity": SeverityLevel.UNKNOWN.value,
                "summary": "Analysis could not be completed",
                "success": False,
                "error_message": last_error
            }
        
        # Build the graph
        graph = StateGraph(AnalysisState)
        graph.add_node("evaluate_sop", evaluate_sop)
        graph.add_edge(START, "evaluate_sop")
        graph.add_edge("evaluate_sop", END)
        
        self.workflow = graph.compile()
    
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
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
        
        try:
            # Initialize state
            initial_state: AnalysisState = {
                "transcript": transcript,
                "missing_elements": [],
                "severity": "",
                "summary": "",
                "success": False,
                "error_message": None
            }
            
            # Run the workflow
            output = self.workflow.invoke(initial_state)
            
            return AnalysisResult(
                missing_elements=output.get("missing_elements", []),
                severity=output.get("severity", SeverityLevel.UNKNOWN.value),
                summary=output.get("summary", "Analysis completed"),
                raw_response=str(output),
                success=output.get("success", False),
                error_message=output.get("error_message")
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return AnalysisResult(
                missing_elements=[f"Analysis failed: {str(e)}"],
                severity=SeverityLevel.UNKNOWN.value,
                summary="Analysis could not be completed",
                success=False,
                error_message=str(e)
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
            response = self.llm.invoke("Hello, reply with 'OK'")
            return response.content is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
