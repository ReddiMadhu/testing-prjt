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
        description="List of SOP elements/points that were missed. Each item MUST be exactly as written in the SOP checklist (e.g., 'Did not ask about...')"
    )
    missed_themes: List[str] = Field(
        description="List of unique themes that have missed elements (e.g., 'CALL OPENING & IDENTITY VERIFICATION', 'DAMAGE ASSESSMENT')"
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
    missed_themes: List[str]
    num_missed: int
    sequence_followed: str
    summary_missed_things: str
    success: bool
    error_message: Optional[str]


@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    missed_points: List[str]
    missed_themes: List[str]
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
        """Get formatted SOP checklist with all 61 elements organized by themes"""
        checklist = """
=== VALID SOP ELEMENTS (ONLY PICK FROM THIS LIST) ===

**THEME: CALL OPENING & IDENTITY VERIFICATION**
- Did not ask if caller has policy number upfront using suggested wording
- Did not verify if caller is policyholder/spouse/authorized person
- Did not set clear explanation of FNOL process using suggested wording
- Did not explain call recording/monitoring purpose
- Did not verify if caller needs immediate medical assistance

**THEME: CONTACT INFORMATION VERIFICATION**
- Did not verify/update mailing address
- Did not verify/update phone numbers
- Did not verify/update email address
- Did not read back contact information for verification
- Did not verify language preferences
- Did not verify if caller has different name/address than policy
- Did not identify main contact for claim
- Did not verify/update notification preferences
- Did not verify/update texting program preferences

**THEME: LOSS DETAILS GATHERING**
- Did not verify if loss date/time was approximate
- Did not ask for purpose of trip
- Did not gather complete loss location details (cross streets, mile markers, location type)
- Did not ask about weather conditions
- Did not ask about witnesses
- Did not ask about property damage
- Did not create proper running notes

**THEME: VEHICLE INFORMATION**
- Did not verify vehicle ownership/policy listing
- Did not gather complete vehicle details (style, color, VIN, license plate, state)
- Did not ask for odometer reading
- Did not ask if vehicle was stolen
- Did not ask about vehicle recovery condition (for stolen vehicles)
- Did not ask if vehicle was parked/unoccupied
- Did not ask about anti-theft devices
- Did not ask if vehicle was locked

**THEME: DAMAGE ASSESSMENT**
- Did not properly document point of first impact
- Did not properly document all damaged areas
- Did not ask about airbag deployment
- Did not verify vehicle drivability
- Did not ask if vehicle starts (for non-drivable vehicles)
- Did not ask about equipment failure
- Did not document interior damage
- Did not document personal effects damage

**THEME: INJURY & SAFETY**
- Did not ask about injuries for all parties
- Did not verify intention to seek medical treatment
- Did not ask about number of passengers
- Did not ask about child car seat (especially for California claims)
- Did not gather passenger contact information

**THEME: INCIDENT DOCUMENTATION**
- Did not ask about police notification/report
- Did not ask about citations/tickets
- Did not gather other party's insurance carrier information
- Did not ask about special claim permissions (employee/sensitive)

**THEME: SERVICES OFFERING**
- Did not offer accident scene towing
- Did not offer Auto Repair Network (OYSARN)
- Did not offer Drive-In services
- Did not offer Virtual Appraisal
- Did not offer rental car services
- Did not offer Auto Glass services
- Did not explain services in proper sequence

**THEME: CLAIM PROCESSING**
- Did not explain payment preferences/options
- Did not share deductible information
- Did not explain 'Track Your Claim' functionality
- Did not explain next steps and timeline
- Did not ask if caller has documents/photos to upload
- Did not verify if warm transfer is needed/eligible

**THEME: CALL CONCLUSION**
- Did not provide claim number
- Did not ask if caller wants to write down claim information

=== END OF VALID SOP ELEMENTS ==="""
        return checklist
    
    def _get_sop_content(self) -> str:
        """Get the loaded SOP content for use in prompts"""
        return self._sop_content
    
    def _build_analysis_prompt(self) -> ChatPromptTemplate:
        """Build the analysis prompt template for FNOL transcript analysis"""
        parser = JsonOutputParser(pydantic_object=SOPAnalysis)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """You are an expert insurance compliance analyst specializing in FNOL (First Notice of Loss) call quality assessment.

You will analyze the provided FNOL call transcript between an AI voice agent/human agent and an insurance holder. Your task is to evaluate compliance against the official SOP document and the SOP elements checklist.

=== OFFICIAL SOP DOCUMENT ===
{sop_document}
=== END OF SOP DOCUMENT ===

{checklist}

CRITICAL INSTRUCTIONS:
- You MUST ONLY identify missed elements from the VALID SOP ELEMENTS list above
- Do NOT invent or add any elements that are not in the list
- Each missed_point MUST be exactly as written in the list (e.g., "Did not ask about...")
- Identify which THEMES have missed elements based on the groupings above

EVALUATION CRITERIA:

1. **missed_points**: List ONLY elements from the SOP checklist that were missed or inadequately addressed.
   - Use EXACT wording from the list (e.g., "Did not verify/update mailing address")
   - Only include elements that are clearly missing from the transcript

2. **missed_themes**: List the UNIQUE theme names that have at least one missed element.
   - Valid themes: "CALL OPENING & IDENTITY VERIFICATION", "CONTACT INFORMATION VERIFICATION", "LOSS DETAILS GATHERING", "VEHICLE INFORMATION", "DAMAGE ASSESSMENT", "INJURY & SAFETY", "INCIDENT DOCUMENTATION", "SERVICES OFFERING", "CLAIM PROCESSING", "CALL CONCLUSION"
   - Only include themes that have at least one missed element

3. **num_missed**: Count the total number of missed points (must match length of missed_points list)

4. **sequence_followed**: Determine if the agent followed the proper SOP sequence:
   - 'Yes' if themes were addressed in logical order: Opening → Contact → Loss Details → Vehicle → Damage → Injury → Documentation → Services → Processing → Conclusion
   - 'No' if major themes were out of order or critical steps were skipped

5. **summary_missed_things**: Brief summary explaining:
   - Which themes had the most gaps
   - Critical missing information for claim processing
   - Overall compliance assessment

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
                    "missed_themes": [],
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
                            "missed_themes": llm_response.missed_themes,
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
                "missed_themes": [],
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
                missed_themes=[],
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
                "missed_themes": [],
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
                missed_themes=output.get("missed_themes", []),
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
                missed_themes=[],
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
