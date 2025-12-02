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
from pathlib import Path
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config.settings import Settings


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Data Models ---
class SOPAnalysis(BaseModel):
    """Structured output model for SOP compliance analysis"""
    missed_points: List[str] = Field(
        description="List of SOP elements/points that were missed or inadequately addressed in the transcript"
    )
    num_missed: int = Field(
        description="Total count of missed points"
    )
    sequence_followed: str = Field(
        description="Whether the proper SOP sequence was followed: 'Yes' or 'No'"
    )
    summary_missed_things: str = Field(
        description="Brief summary of what was missed and why it matters for claim processing"
    )


class AnalysisState(TypedDict):
    """State definition for LangGraph workflow"""
    transcript: str
    transcript_id: Optional[str]
    agent_name: Optional[str]
    missed_points: List[str]
    num_missed: int
    sequence_followed: str
    summary_missed_things: str
    success: bool
    error_message: Optional[str]


@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    missed_points: List[str]
    num_missed: int
    sequence_followed: str
    summary_missed_things: str
    transcript_id: Optional[str] = None
    agent_name: Optional[str] = None
    raw_response: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class LangChainGeminiService:
    """
    Service class for interacting with Google Gemini API using LangChain and LangGraph
    Implements retry logic, rate limiting, and comprehensive error handling
    """
    
    # SOP file path relative to project root
    SOP_FILE_PATH = "../SOP.txt"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LangChain Gemini Service
        
        Args:
            api_key: Optional API key. If not provided, will use from environment
        """
        self.settings = Settings()
        self.model_name = "gemini-2.5-flash"
        self.retry_attempts = 4
        self.retry_delay = 2.0  # Initial retry delay in seconds
        
        # Rate limiting configuration - adjust these to overcome rate limits
        self._last_request_time = 0
        self._min_request_interval = 2.0  # Minimum seconds between API calls
        self._sleep_between_calls = 1.5  # Additional sleep time between transcript analyses
        
        # Setup API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Missing Google API key. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        
        # Load SOP content
        self._sop_content = self._load_sop_file()
        
        # Initialize LLM
        self._setup_llm()
        
        # Build the LangGraph workflow
        self._build_workflow()
    
    def _load_sop_file(self) -> str:
        """
        Load the SOP file content from disk
        
        Returns:
            String content of the SOP file
        """
        try:
            # Try multiple potential paths
            potential_paths = [
                Path(__file__).parent.parent / self.SOP_FILE_PATH,  # Project root
                Path.cwd() / self.SOP_FILE_PATH,  # Current working directory
                Path(__file__).parent / self.SOP_FILE_PATH,  # Services folder
            ]
            
            for sop_path in potential_paths:
                if sop_path.exists():
                    with open(sop_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    logger.info(f"Loaded SOP file from: {sop_path}")
                    return content
            
            # If no file found, log warning and return default checklist
            logger.warning(f"SOP file not found in expected locations. Using default checklist.")
            return self._get_default_sop_checklist()
            
        except Exception as e:
            logger.error(f"Error loading SOP file: {e}")
            return self._get_default_sop_checklist()
    
    def _get_default_sop_checklist(self) -> str:
        """Get default SOP checklist from settings as fallback"""
        sop_elements = self.settings.get_sop_elements_list()
        return "\n".join([f"{i+1}. {elem}" for i, elem in enumerate(sop_elements)])
    
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
    
    def _get_sop_content(self) -> str:
        """Get the loaded SOP content for use in prompts"""
        return self._sop_content
    
    def _build_analysis_prompt(self) -> ChatPromptTemplate:
        """Build the analysis prompt template for FNOL transcript analysis"""
        parser = JsonOutputParser(pydantic_object=SOPAnalysis)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """You are an expert insurance compliance analyst specializing in FNOL (First Notice of Loss) call quality assessment.

You will analyze the provided FNOL call transcript between an AI voice agent/human agent and an insurance holder. Your task is to evaluate compliance against the official SOP document provided below.

=== OFFICIAL SOP DOCUMENT ===
{sop_document}
=== END OF SOP DOCUMENT ===

EVALUATION CRITERIA:
Based on the SOP document above, evaluate the transcript for:
{checklist}
1. **missed_points**: Identify ALL elements from the SOP that were missed or inadequately addressed. Reference the specific Data IDs (e.g., [ID-1], [ID-2], etc.) and phase requirements:
   - Phase 1: Initiation & Verification (Greeting, Safety Check, Policyholder Verification [ID-1])
   - Phase 2: Incident Details (Datetime/Location [ID-2], Description [ID-3], Property Damage [ID-6])
   - Phase 3: Liability & Legal (Injuries [ID-5], Parties Involved [ID-4], Witnesses [ID-8], Police Report [ID-7])
   - Phase 4: Closing (Documentation [ID-9], Claim Number [ID-11], Next Steps [ID-10])
   - Core Behavioral Guidelines: Tone Protocol [ID-12], Safety First, Active Listening, No Hallucinations

2. **num_missed**: Count the total number of missed points

3. **sequence_followed**: Determine if the agent followed the proper SOP sequence:
   - 'Yes' if the call followed: Phase 1 → Phase 2 → Phase 3 → Phase 4
   - 'No' if major phases were out of order or critical steps were skipped

4. **summary_missed_things**: Provide a brief summary explaining what was missed and the impact on claim processing

Return your analysis using the required JSON schema."""
            ),
            ("human", 
             """Transcript to Analyze:
{transcript}

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
                    "missed_points": ["No transcript provided"],
                    "num_missed": 0,
                    "sequence_followed": "N/A",
                    "summary_missed_things": "Empty transcript - unable to analyze",
                    "success": False,
                    "error_message": "Empty transcript"
                }
            
            prompt_template, parser = self._build_analysis_prompt()
            
            formatted_prompt = prompt_template.format(
                sop_document=self._get_sop_content(),
                checklist=self._get_sop_checklist(),
                transcript=transcript,
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
                            "missed_points": llm_response.missed_points,
                            "num_missed": llm_response.num_missed,
                            "sequence_followed": llm_response.sequence_followed,
                            "summary_missed_things": llm_response.summary_missed_things,
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
                "missed_points": [f"Analysis failed: {last_error}"],
                "num_missed": 0,
                "sequence_followed": "Unknown",
                "summary_missed_things": "Analysis could not be completed",
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
        """Implement rate limiting between requests to avoid API rate limits"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        # Ensure minimum interval between requests
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        # Additional sleep to be safe with rate limits
        if self._sleep_between_calls > 0:
            time.sleep(self._sleep_between_calls)
        
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
                missed_points=["No transcript provided"],
                num_missed=0,
                sequence_followed="N/A",
                summary_missed_things="Empty transcript - unable to analyze",
                success=False,
                error_message="Empty transcript"
            )
        
        try:
            # Initialize state
            initial_state: AnalysisState = {
                "transcript": transcript,
                "transcript_id": None,
                "agent_name": None,
                "missed_points": [],
                "num_missed": 0,
                "sequence_followed": "",
                "summary_missed_things": "",
                "success": False,
                "error_message": None
            }
            
            # Run the workflow
            output = self.workflow.invoke(initial_state)
            
            return AnalysisResult(
                missed_points=output.get("missed_points", []),
                num_missed=output.get("num_missed", 0),
                sequence_followed=output.get("sequence_followed", "Unknown"),
                summary_missed_things=output.get("summary_missed_things", "Analysis completed"),
                raw_response=str(output),
                success=output.get("success", False),
                error_message=output.get("error_message")
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return AnalysisResult(
                missed_points=[f"Analysis failed: {str(e)}"],
                num_missed=0,
                sequence_followed="Unknown",
                summary_missed_things="Analysis could not be completed",
                success=False,
                error_message=str(e)
            )
    
    def analyze_batch(
        self, 
        transcripts: List[str], 
        progress_callback: Optional[callable] = None,
        sleep_between: float = 2.0
    ) -> List[AnalysisResult]:
        """
        Analyze multiple transcripts with progress tracking and rate limiting
        
        Args:
            transcripts: List of transcripts to analyze
            progress_callback: Optional callback function(current, total) for progress updates
            sleep_between: Seconds to sleep between each transcript analysis (default: 2.0)
            
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
            
            # Sleep between calls to avoid rate limiting (except for last item)
            if i < total - 1 and sleep_between > 0:
                logger.info(f"Sleeping {sleep_between}s between transcript analyses to avoid rate limits")
                time.sleep(sleep_between)
        
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
