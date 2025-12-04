"""
SOP Analysis Service using LangGraph
Analyzes transcripts against uploaded SOP document to find missing steps and mistakes
Uses Pydantic BaseModel for structured LLM outputs
"""

import os
import json
import time
import logging
import re
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
from docx import Document

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SOP Content Preprocessing
# ============================================================================

def preprocess_sop_content(sop_content: str) -> str:
    """
    Preprocess SOP content to remove IDs, Phase references, and other identifiers
    that we don't want the LLM to include in its output.
    
    Args:
        sop_content: Raw SOP document content
        
    Returns:
        Cleaned SOP content without IDs and phase references
    """
    cleaned = sop_content
    
    # Remove ID references like [ID-1], [ID-2], ID-08, (ID-1), etc.
    cleaned = re.sub(r'\[ID-?\d+\]', '', cleaned)
    cleaned = re.sub(r'\(ID-?\d+\)', '', cleaned)
    cleaned = re.sub(r'ID-?\d+', '', cleaned)
    
    # Remove Phase references like "Phase 1:", "Phase 2:", "(Phase 1)", etc.
    cleaned = re.sub(r'Phase\s*\d+\s*:', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\(Phase\s*\d+\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[Phase\s*\d+\]', '', cleaned, flags=re.IGNORECASE)
    
    # Remove section numbers like "1.1", "2.3.1", etc. at start of lines
    cleaned = re.sub(r'^\s*\d+(\.\d+)*\s*', '', cleaned, flags=re.MULTILINE)
    
    # Remove element/step numbering patterns
    cleaned = re.sub(r'\[Element-?\d+\]', '', cleaned)
    cleaned = re.sub(r'\[Step-?\d+\]', '', cleaned)
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    
    return cleaned.strip()


def clean_output_text(text: str) -> str:
    """
    Post-process LLM output to remove any remaining IDs, Phase references, Theme numbers.
    
    Args:
        text: Raw LLM output text
        
    Returns:
        Cleaned text without IDs or references
    """
    if not text:
        return text
    
    cleaned = text
    
    # Remove ID references
    cleaned = re.sub(r'\[ID-?\d+\]', '', cleaned)
    cleaned = re.sub(r'\(ID-?\d+\)', '', cleaned)
    cleaned = re.sub(r'ID-?\d+', '', cleaned)
    
    # Remove Phase references
    cleaned = re.sub(r'Phase\s*\d+\s*:', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\(Phase\s*\d+\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[Phase\s*\d+\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Phase\s*\d+', '', cleaned, flags=re.IGNORECASE)
    
    # Remove Theme numbering prefixes
    cleaned = re.sub(r'Theme\s*\d+\s*:', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^Theme\s*\d+\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up extra whitespace and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'^\s*[:\-,]\s*', '', cleaned)  # Remove leading punctuation
    
    return cleaned.strip()


def clean_theme_name(theme: str) -> str:
    """
    Clean a theme name to remove prefixes, IDs, descriptions.
    
    Args:
        theme: Raw theme name
        
    Returns:
        Clean short theme name
    """
    if not theme:
        return theme
    
    cleaned = theme
    
    # Remove "Theme X:" prefix
    cleaned = re.sub(r'^Theme\s*\d+\s*:\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove Phase references
    cleaned = re.sub(r'\(Phase\s*\d+\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Phase\s*\d+', '', cleaned, flags=re.IGNORECASE)
    
    # Remove everything after colon (descriptions)
    if ':' in cleaned:
        cleaned = cleaned.split(':')[0]
    
    # Remove IDs
    cleaned = re.sub(r'\[ID-?\d+\]', '', cleaned)
    cleaned = re.sub(r'ID-?\d+', '', cleaned)
    
    # Clean up
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


# ============================================================================
# Pydantic Models for Structured Output
# ============================================================================

class SOPMistakesOutput(BaseModel):
    """Output model for SOP mistakes identification"""
    sop_mistakes: List[str] = Field(
        default_factory=list,
        description="List of SOP steps not followed. Use ONLY simple plain English like 'Did not verify identity', 'Did not ask about injuries'. NEVER include IDs like [ID-1], Phase numbers, or SOP references."
    )


class SOPThemesOutput(BaseModel):
    """Output model for SOP mistake themes generation"""
    sop_missing_themes: List[str] = Field(
        default_factory=list,
        description="List of 10 SHORT theme names (2-4 words, ALL CAPS) like 'IDENTITY VERIFICATION', 'INCIDENT DOCUMENTATION'. NO 'Theme X:' prefix, NO descriptions, NO IDs."
    )


class ThemeAssignmentOutput(BaseModel):
    """Output model for theme assignment and reasoning"""
    assigned_themes: List[str] = Field(
        default_factory=list,
        description="List of themes EXACTLY matching the available themes. Return theme names as-is without modification."
    )
    sop_mistakes_reasoning: str = Field(
        default="",
        description="Brief reasoning (3-4 lines) in plain English. NO IDs like [ID-1], NO Phase references, NO SOP section numbers. Focus on agent behavior and call context."
    )


class ImprovementsOutput(BaseModel):
    """Output model for improvement recommendations"""
    sop_improvements: str = Field(
        default="",
        description="Actionable improvement recommendations in 4-5 lines as a simple paragraph. Focus on practical training and process improvements. No personal info, names, or SOP IDs."
    )


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SOPAnalysisResult:
    """Complete SOP analysis result"""
    transcript_results: List[Dict[str, Any]]
    sop_missing_themes: List[str]
    success: bool
    error_message: Optional[str] = None


# ============================================================================
# LangGraph State
# ============================================================================

class SOPAnalysisState(TypedDict):
    """State for the SOP analysis workflow"""
    # Input data
    transcripts_df: Dict[str, Any]
    sop_content: str
    
    # Step 1: Individual transcript SOP mistakes
    transcript_sop_mistakes: List[Dict[str, Any]]
    
    # Step 2: Aggregated mistakes and themes
    aggregated_sop_mistakes: List[str]
    sop_missing_themes: List[str]
    
    # Step 3: Assigned themes and reasoning per transcript
    transcript_theme_assignments: List[Dict[str, Any]]
    
    # Step 4: Improvements per transcript
    final_results: List[Dict[str, Any]]
    
    # Metadata
    total_transcripts: int
    error: Optional[str]


# ============================================================================
# Prompts (simplified - Pydantic handles output structure)
# ============================================================================

PROMPT_FIND_SOP_MISTAKES = """You are an expert call quality analyst. Analyze this transcript against the Standard Operating Procedure (SOP) document.

**SOP Document:**
{sop_content}

**Transcript Call:**
{transcript_call}

**Task:** Identify ALL SOP steps that were NOT followed or performed incorrectly by the agent.

**CRITICAL INSTRUCTIONS - MUST FOLLOW:**
1. Compare the transcript against each SOP requirement
2. List specific steps/procedures that were missed or done incorrectly
3. DO NOT include any personal information (names, phone numbers, addresses, etc.)
4. NEVER reference any SOP IDs like [ID-1], [ID-2], ID-08, etc.
5. NEVER mention Phase numbers like "Phase 1:", "Phase 2:", "Phase 3:", "Phase 4:"
6. NEVER include element IDs or section references from the SOP document
7. Use ONLY simple, plain English descriptions like:
   - "Did not verify policyholder identity"
   - "Did not ask about incident location and time"
   - "Did not inquire about injuries"
   - "Did not ask about witnesses"
   - "Did not provide documentation instructions"

**WRONG (DO NOT DO THIS):**
- "Failed to verify identity [ID-1]" ❌
- "Skipped Phase 2: Incident Details" ❌
- "Violated the Strict Rule in Phase 1" ❌

**CORRECT (DO THIS):**
- "Did not verify policyholder identity against database" ✓
- "Did not ask when and where incident happened" ✓
- "Did not ask about injuries" ✓

If no SOP violations found, return an empty list."""


PROMPT_GENERATE_SOP_THEMES = """Analyze these SOP mistakes from multiple transcripts and identify the TOP 10 common SOP mistake themes.

**All SOP Mistakes Across Transcripts:**
{aggregated_mistakes}

**Task:** Create 10 distinct themes that categorize these SOP violations.

**CRITICAL INSTRUCTIONS - MUST FOLLOW:**
1. Group similar SOP mistakes together
2. Create SHORT theme names (2-4 words ONLY) that describe the issue category
3. NEVER prefix with "Theme 1:", "Theme 2:", "Theme X:" - just the theme name
4. NEVER include any IDs, numbers, or colons in theme names
5. NEVER add descriptions after the theme name

**WRONG (DO NOT DO THIS):**
- "Theme 1: Failure to Verify Identity" ❌
- "Theme 5: Omitting Liability and Legal Inquiries: Missing critical questions..." ❌
- "Failure to Verify Policyholder Identity: Missing steps to confirm..." ❌

**CORRECT (DO THIS):**
- "IDENTITY VERIFICATION" ✓
- "INCIDENT DOCUMENTATION" ✓  
- "INJURY ASSESSMENT" ✓
- "WITNESS INFORMATION" ✓
- "POLICE REPORT" ✓
- "LIABILITY INQUIRY" ✓
- "DOCUMENTATION GUIDANCE" ✓
- "CLAIM NUMBER HANDLING" ✓
- "NEXT STEPS COMMUNICATION" ✓
- "TONE COMPLIANCE" ✓

Return ONLY short 2-4 word theme names in CAPS, no descriptions or explanations."""


PROMPT_ASSIGN_THEMES = """Assign SOP mistake themes to this transcript's violations and provide brief reasoning.

**SOP Mistakes Found:**
{sop_mistakes}

**Available SOP Mistake Themes:**
{sop_themes}

**Task:** 
1. Select ONLY themes from the available list that match the SOP mistakes
2. Provide brief reasoning (3-4 lines maximum) explaining why these steps were missed

**CRITICAL INSTRUCTIONS:**
- Return themes EXACTLY as they appear in the available themes list
- Do NOT modify or add descriptions to theme names
- Do NOT include any IDs like [ID-1], ID-08, etc.
- Do NOT reference Phase numbers or SOP section numbers
- Keep reasoning focused on call context and agent behavior
- Reasoning should be plain English without technical SOP references

**Example reasoning format:**
The agent appeared rushed and skipped verification steps. Key questions about the incident were not asked, likely due to time pressure. Better call flow structure would help ensure all information is captured."""


PROMPT_IMPROVEMENTS = """Based on the SOP analysis, provide specific improvements for the agent.

**SOP Mistakes Found:**
{sop_mistakes}

**Assigned Themes:**
{assigned_themes}

**Reasoning:**
{reasoning}

**Task:** Provide actionable improvement recommendations in 4-5 lines as a simple paragraph.

**IMPORTANT:** 
- Do NOT include any personal information, names, or IDs
- Do NOT reference SOP document IDs or section numbers
- Write as a simple paragraph (4-5 lines), NOT as a numbered/bulleted list
- Focus on practical training and process improvements"""


# ============================================================================
# SOP Analysis Service
# ============================================================================

class SOPAnalysisService:
    """Service for analyzing transcripts against SOP documents using LangGraph and Pydantic structured outputs"""
    
    def __init__(self):
        """Initialize the SOP analysis service"""
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY.")
        
        # Rate limiting configuration
        self._last_request_time = 0
        self._min_request_interval = 2.0
        
        # Base LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        # Structured output LLMs using Pydantic models
        self.llm_sop_mistakes = self.llm.with_structured_output(SOPMistakesOutput)
        self.llm_sop_themes = self.llm.with_structured_output(SOPThemesOutput)
        self.llm_theme_assignment = self.llm.with_structured_output(ThemeAssignmentOutput)
        self.llm_improvements = self.llm.with_structured_output(ImprovementsOutput)
        
        self.workflow = self._build_workflow()
    
    def _rate_limit(self):
        """Apply rate limiting before API calls"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for SOP analysis"""
        workflow = StateGraph(SOPAnalysisState)
        
        # Add nodes for each step
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("find_sop_mistakes", self._find_sop_mistakes_node)
        workflow.add_node("aggregate_and_generate_themes", self._aggregate_and_generate_themes_node)
        workflow.add_node("assign_themes", self._assign_themes_node)
        workflow.add_node("generate_improvements", self._generate_improvements_node)
        
        # Define edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "find_sop_mistakes")
        workflow.add_edge("find_sop_mistakes", "aggregate_and_generate_themes")
        workflow.add_edge("aggregate_and_generate_themes", "assign_themes")
        workflow.add_edge("assign_themes", "generate_improvements")
        workflow.add_edge("generate_improvements", END)
        
        return workflow.compile()
    
    def _initialize_node(self, state: SOPAnalysisState) -> SOPAnalysisState:
        """Initialize the workflow state"""
        logger.info("Initializing SOP analysis workflow")
        df = pd.DataFrame(state["transcripts_df"])
        state["total_transcripts"] = len(df)
        state["transcript_sop_mistakes"] = []
        state["aggregated_sop_mistakes"] = []
        state["sop_missing_themes"] = []
        state["transcript_theme_assignments"] = []
        state["final_results"] = []
        state["error"] = None
        return state
    
    def _find_sop_mistakes_node(self, state: SOPAnalysisState) -> SOPAnalysisState:
        """Step 1: Find SOP mistakes for each transcript using structured output"""
        logger.info("Step 1: Finding SOP mistakes in transcripts")
        df = pd.DataFrame(state["transcripts_df"])
        # Preprocess SOP content to remove IDs and Phase references
        sop_content = preprocess_sop_content(state["sop_content"])
        transcript_mistakes = []
        
        for idx, row in df.iterrows():
            transcript_id = str(row.get("transcript_id", f"T{idx+1}"))
            agent_id = str(row.get("agent_id", f"A{idx+1}"))
            agent_name = str(row.get("agent_name", "Unknown"))
            transcript_call = str(row.get("transcript_call", ""))
            
            logger.info(f"Processing transcript {idx + 1}/{len(df)}: {transcript_id}")
            
            prompt = PROMPT_FIND_SOP_MISTAKES.format(
                sop_content=sop_content,
                transcript_call=transcript_call
            )
            
            self._rate_limit()
            try:
                result: SOPMistakesOutput = self.llm_sop_mistakes.invoke(prompt)
                # Clean each mistake to remove any remaining IDs/Phase references
                sop_mistakes = [clean_output_text(m) for m in result.sop_mistakes]
            except Exception as e:
                logger.error(f"Error finding SOP mistakes for {transcript_id}: {e}")
                sop_mistakes = []
            
            transcript_mistakes.append({
                "transcript_id": transcript_id,
                "transcript_call": transcript_call,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "sop_mistakes": sop_mistakes
            })
        
        state["transcript_sop_mistakes"] = transcript_mistakes
        return state
    
    def _aggregate_and_generate_themes_node(self, state: SOPAnalysisState) -> SOPAnalysisState:
        """Step 2: Aggregate mistakes and generate 10 SOP mistake themes using structured output"""
        logger.info("Step 2: Aggregating mistakes and generating themes")
        
        # Aggregate all SOP mistakes
        all_mistakes = []
        for item in state["transcript_sop_mistakes"]:
            all_mistakes.extend(item.get("sop_mistakes", []))
        
        state["aggregated_sop_mistakes"] = all_mistakes
        
        if not all_mistakes:
            logger.info("No SOP mistakes found across transcripts")
            state["sop_missing_themes"] = []
            return state
        
        prompt = PROMPT_GENERATE_SOP_THEMES.format(
            aggregated_mistakes=json.dumps(all_mistakes, indent=2)
        )
        
        self._rate_limit()
        try:
            result: SOPThemesOutput = self.llm_sop_themes.invoke(prompt)
            # Clean each theme to remove prefixes, IDs, descriptions
            themes = [clean_theme_name(t) for t in result.sop_missing_themes]
        except Exception as e:
            logger.error(f"Error generating themes: {e}")
            themes = []
        
        state["sop_missing_themes"] = themes
        logger.info(f"Generated {len(themes)} SOP mistake themes")
        
        return state
    
    def _assign_themes_node(self, state: SOPAnalysisState) -> SOPAnalysisState:
        """Step 3: Assign themes to each transcript and provide reasoning using structured output"""
        logger.info("Step 3: Assigning themes and providing reasoning")
        
        themes = state["sop_missing_themes"]
        assignments = []
        
        for item in state["transcript_sop_mistakes"]:
            transcript_id = item["transcript_id"]
            sop_mistakes = item["sop_mistakes"]
            
            if not sop_mistakes:
                assignments.append({
                    "transcript_id": transcript_id,
                    "assigned_themes": [],
                    "sop_mistakes_reasoning": "No SOP violations identified - excellent compliance"
                })
                continue
            
            logger.info(f"Assigning themes to transcript: {transcript_id}")
            
            prompt = PROMPT_ASSIGN_THEMES.format(
                sop_mistakes=json.dumps(sop_mistakes, indent=2),
                sop_themes=json.dumps(themes, indent=2)
            )
            
            self._rate_limit()
            try:
                result: ThemeAssignmentOutput = self.llm_theme_assignment.invoke(prompt)
                # Clean themes and reasoning
                assigned_themes = [clean_theme_name(t) for t in result.assigned_themes]
                reasoning = clean_output_text(result.sop_mistakes_reasoning)
            except Exception as e:
                logger.error(f"Error assigning themes for {transcript_id}: {e}")
                assigned_themes = []
                reasoning = ""
            
            assignments.append({
                "transcript_id": transcript_id,
                "assigned_themes": assigned_themes,
                "sop_mistakes_reasoning": reasoning
            })
        
        state["transcript_theme_assignments"] = assignments
        return state
    
    def _generate_improvements_node(self, state: SOPAnalysisState) -> SOPAnalysisState:
        """Step 4: Generate improvements for each transcript using structured output"""
        logger.info("Step 4: Generating SOP-based improvements")
        
        final_results = []
        
        # Create a lookup for theme assignments
        assignments_lookup = {
            a["transcript_id"]: a for a in state["transcript_theme_assignments"]
        }
        
        for item in state["transcript_sop_mistakes"]:
            transcript_id = item["transcript_id"]
            sop_mistakes = item["sop_mistakes"]
            assignment = assignments_lookup.get(transcript_id, {})
            assigned_themes = assignment.get("assigned_themes", [])
            reasoning = assignment.get("sop_mistakes_reasoning", "")
            
            if not sop_mistakes:
                final_results.append({
                    "transcript_id": transcript_id,
                    "transcript_call": item["transcript_call"],
                    "agent_id": item["agent_id"],
                    "agent_name": item["agent_name"],
                    "sop_mistakes": [],
                    "sop_mistake_themes": [],
                    "sop_mistakes_reasoning": "No SOP violations - excellent compliance",
                    "sop_improvements": "Continue maintaining excellent SOP compliance. Consider mentoring other agents."
                })
                continue
            
            logger.info(f"Generating improvements for transcript: {transcript_id}")
            
            prompt = PROMPT_IMPROVEMENTS.format(
                sop_mistakes=json.dumps(sop_mistakes, indent=2),
                assigned_themes=json.dumps(assigned_themes, indent=2),
                reasoning=reasoning
            )
            
            self._rate_limit()
            try:
                result: ImprovementsOutput = self.llm_improvements.invoke(prompt)
                # Clean improvements text
                improvements = clean_output_text(result.sop_improvements)
            except Exception as e:
                logger.error(f"Error generating improvements for {transcript_id}: {e}")
                improvements = ""
            
            final_results.append({
                "transcript_id": transcript_id,
                "transcript_call": item["transcript_call"],
                "agent_id": item["agent_id"],
                "agent_name": item["agent_name"],
                "sop_mistakes": sop_mistakes,
                "sop_mistake_themes": assigned_themes,
                "sop_mistakes_reasoning": reasoning,
                "sop_improvements": improvements
            })
        
        state["final_results"] = final_results
        return state
    
    def analyze(self, transcripts_df: pd.DataFrame, sop_content: str) -> SOPAnalysisResult:
        """
        Run the complete SOP analysis workflow
        
        Args:
            transcripts_df: DataFrame with processed transcript data
            sop_content: Content of the SOP document
            
        Returns:
            SOPAnalysisResult with all analysis results
        """
        logger.info(f"Starting SOP analysis for {len(transcripts_df)} transcripts")
        
        try:
            initial_state: SOPAnalysisState = {
                "transcripts_df": transcripts_df.to_dict(),
                "sop_content": sop_content,
                "transcript_sop_mistakes": [],
                "aggregated_sop_mistakes": [],
                "sop_missing_themes": [],
                "transcript_theme_assignments": [],
                "final_results": [],
                "total_transcripts": 0,
                "error": None
            }
            
            final_state = self.workflow.invoke(initial_state)
            
            if final_state.get("error"):
                return SOPAnalysisResult(
                    transcript_results=[],
                    sop_missing_themes=[],
                    success=False,
                    error_message=final_state["error"]
                )
            
            return SOPAnalysisResult(
                transcript_results=final_state["final_results"],
                sop_missing_themes=final_state["sop_missing_themes"],
                success=True
            )
            
        except Exception as e:
            logger.error(f"SOP analysis failed: {str(e)}")
            return SOPAnalysisResult(
                transcript_results=[],
                sop_missing_themes=[],
                success=False,
                error_message=str(e)
            )
    
    def to_dataframe(self, result: SOPAnalysisResult) -> pd.DataFrame:
        """
        Convert results to DataFrame for export
        
        Args:
            result: SOPAnalysisResult from analyze()
            
        Returns:
            DataFrame with SOP analysis columns
        """
        if not result.success or not result.transcript_results:
            return pd.DataFrame()
        
        records = []
        for item in result.transcript_results:
            records.append({
                "transcript_id": item.get("transcript_id"),
                "agent_id": item.get("agent_id"),
                "agent_name": item.get("agent_name"),
                "transcript_call": item.get("transcript_call"),
                "sop_mistakes": json.dumps(item.get("sop_mistakes", [])),
                "sop_mistake_themes": json.dumps(item.get("sop_mistake_themes", [])),
                "sop_mistakes_reasoning": item.get("sop_mistakes_reasoning", ""),
                "sop_improvements": item.get("sop_improvements", "")
            })
        
        return pd.DataFrame(records)


def read_word_document(file_path_or_buffer) -> str:
    """
    Read content from a Word document
    
    Args:
        file_path_or_buffer: File path string or file-like object
        
    Returns:
        Text content of the document
    """
    try:
        doc = Document(file_path_or_buffer)
        content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text.strip())
        return "\n\n".join(content)
    except Exception as e:
        logger.error(f"Error reading Word document: {e}")
        raise ValueError(f"Failed to read Word document: {str(e)}")
