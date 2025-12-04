"""
Transcript Analysis Service with Pydantic Structured Output
Simplified service for SOP-based transcript analysis
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from config.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()


# ============================================================================
# Pydantic Models for Structured Output
# ============================================================================

class MistakeItem(BaseModel):
    """Single mistake identified in a transcript"""
    mistake_description: str = Field(description="Description of the mistake")


class TranscriptAnalysisOutput(BaseModel):
    """Structured output for a single transcript analysis"""
    transcript_id: str = Field(description="Unique identifier for the transcript")
    agent_name: str = Field(description="Name of the agent")
    agent_id: str = Field(description="ID of the agent")
    transcript_call: str = Field(description="The full transcript text")
    mistakes: List[str] = Field(default_factory=list, description="List of mistakes identified")
    mistake_themes: List[str] = Field(default_factory=list, description="Themes of the mistakes")
    root_cause: str = Field(default="", description="Root cause analysis text")
    root_cause_reasoning: str = Field(default="", description="Reasoning behind root cause")
    severity_score: int = Field(default=100, description="Severity score 0-100")


# ============================================================================
# LangGraph State
# ============================================================================

class AnalysisState(dict):
    """State for the analysis workflow"""
    pass


# ============================================================================
# Prompts
# ============================================================================

PROMPT_IDENTIFY_MISTAKES = """You are an expert call quality analyst. Analyze this customer service call transcript against the provided SOP (Standard Operating Procedure).

**SOP Document:**
{sop_content}

**Transcript:**
ID: {transcript_id}
Agent: {agent_name} (ID: {agent_id})

{transcript_call}

**Instructions:**
1. Compare the agent's actions against the SOP requirements
2. Identify ALL mistakes where the agent deviated from or failed to follow the SOP
3. Be specific about what was missed or done incorrectly

Return ONLY valid JSON in this exact format:
```json
{{
  "mistakes": [
    "Specific mistake 1 - what the agent did wrong or failed to do",
    "Specific mistake 2 - what the agent did wrong or failed to do"
  ]
}}
```

If no mistakes found, return: {{"mistakes": []}}
"""


PROMPT_GENERATE_THEMES = """You are a quality assurance manager. Analyze ALL mistakes from multiple transcripts and identify common SOP-related mistake themes.

**SOP Document:**
{sop_content}

**All Mistakes Collected:**
{all_mistakes}

**Instructions:**
Generate the most common mistake themes based on SOP violations. Each theme should:
- Be directly related to SOP requirements
- Be specific and actionable
- Cover multiple similar mistakes

Return ONLY valid JSON:
```json
{{
  "themes": [
    "Theme 1: Brief descriptive name",
    "Theme 2: Brief descriptive name",
    "Theme 3: Brief descriptive name"
  ]
}}
```

Generate 5-10 themes based on the mistakes found.
"""


PROMPT_MAP_THEMES = """You are a quality analyst. Map the mistakes from this transcript to the established SOP mistake themes.

**SOP Document:**
{sop_content}

**Transcript ID:** {transcript_id}

**Mistakes in this transcript:**
{mistakes}

**Established Mistake Themes:**
{themes}

**Instructions:**
For each mistake, identify which theme(s) it belongs to from the established list.

Return ONLY valid JSON:
```json
{{
  "mapped_themes": [
    "Theme that applies to mistakes in this transcript",
    "Another theme if applicable"
  ]
}}
```

Only include themes that actually apply to the mistakes found.
"""


PROMPT_ROOT_CAUSE_AND_SEVERITY = """You are a performance improvement specialist. Analyze the mistakes and themes for this transcript.

**SOP Document:**
{sop_content}

**Transcript ID:** {transcript_id}
**Agent:** {agent_name}

**Mistakes:**
{mistakes}

**Themes Identified:**
{themes}

**Instructions:**
1. Determine the ROOT CAUSE - why did these mistakes happen?
2. Provide REASONING explaining the root cause in detail
3. Calculate SEVERITY SCORE (0-100):
   - Start at 100
   - Deduct 15 points for each critical SOP violation
   - Deduct 5 points for each minor SOP deviation
   - Minimum score is 0

Return ONLY valid JSON:
```json
{{
  "root_cause": "Primary reason why the mistakes occurred",
  "root_cause_reasoning": "Detailed explanation of why the agent made these mistakes and what factors contributed",
  "severity_score": 85
}}
```

If no mistakes, return: {{"root_cause": "No issues identified", "root_cause_reasoning": "Agent followed SOP correctly", "severity_score": 100}}
"""


# ============================================================================
# Transcript Analysis Service
# ============================================================================

class TranscriptAnalysisService:
    """
    Service for SOP-based transcript analysis using LangGraph.
    Uses Pydantic for structured output.
    """
    
    def __init__(self, sop_content: str = ""):
        """
        Initialize the transcript analysis service
        
        Args:
            sop_content: The SOP document content to analyze against
        """
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        
        self.sop_content = sop_content
        
        # Rate limiting configuration
        self._last_request_time = 0
        self._min_request_interval = 2.0
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        self.workflow = self._build_workflow()
    
    def set_sop_content(self, sop_content: str):
        """Set the SOP content for analysis"""
        self.sop_content = sop_content
    
    def _rate_limit(self):
        """Apply rate limiting before API calls"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM with rate limiting and error handling"""
        self._rate_limit()
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse response"}
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AnalysisState)
        
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("identify_mistakes", self._identify_mistakes_node)
        workflow.add_node("generate_themes", self._generate_themes_node)
        workflow.add_node("map_themes", self._map_themes_node)
        workflow.add_node("analyze_root_cause", self._analyze_root_cause_node)
        workflow.add_node("compile_results", self._compile_results_node)
        
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "identify_mistakes")
        workflow.add_edge("identify_mistakes", "generate_themes")
        workflow.add_edge("generate_themes", "map_themes")
        workflow.add_edge("map_themes", "analyze_root_cause")
        workflow.add_edge("analyze_root_cause", "compile_results")
        workflow.add_edge("compile_results", END)
        
        return workflow.compile()
    
    def _initialize_node(self, state: AnalysisState) -> AnalysisState:
        """Initialize the workflow"""
        logger.info("Initializing analysis workflow")
        
        state["all_mistakes"] = {}
        state["generated_themes"] = []
        state["theme_mappings"] = {}
        state["root_cause_data"] = {}
        state["final_results"] = []
        state["error"] = None
        
        return state
    
    def _identify_mistakes_node(self, state: AnalysisState) -> AnalysisState:
        """Identify mistakes in each transcript"""
        logger.info("Phase 1: Identifying SOP mistakes in all transcripts")
        
        try:
            df = pd.DataFrame(state["transcripts_df"])
            all_mistakes = {}
            
            for idx, row in df.iterrows():
                transcript_id = str(row.get("Transcript_ID", row.get("transcript_id", f"T{idx+1}")))
                agent_id = str(row.get("Agent_ID", row.get("agent_id", f"A{idx+1}")))
                agent_name = str(row.get("Agent_Name", row.get("agent_name", "Unknown")))
                transcript_call = str(row.get("Transcript_Call", row.get("transcript_call", row.get("Transcript", ""))))
                
                logger.info(f"Analyzing transcript {idx + 1}/{len(df)}: {transcript_id}")
                
                prompt = PROMPT_IDENTIFY_MISTAKES.format(
                    sop_content=self.sop_content,
                    transcript_id=transcript_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    transcript_call=transcript_call
                )
                
                response = self._call_llm(prompt)
                parsed = self._parse_json_response(response)
                
                mistakes = parsed.get("mistakes", [])
                all_mistakes[transcript_id] = {
                    "mistakes": mistakes,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "transcript_call": transcript_call
                }
            
            state["all_mistakes"] = all_mistakes
            return state
            
        except Exception as e:
            state["error"] = f"Mistake identification failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _generate_themes_node(self, state: AnalysisState) -> AnalysisState:
        """Generate common mistake themes"""
        logger.info("Phase 2: Generating SOP mistake themes")
        
        try:
            # Aggregate all mistakes
            all_mistakes_list = []
            for tid, data in state["all_mistakes"].items():
                for mistake in data["mistakes"]:
                    all_mistakes_list.append(f"[{tid}] {mistake}")
            
            if not all_mistakes_list:
                state["generated_themes"] = []
                return state
            
            prompt = PROMPT_GENERATE_THEMES.format(
                sop_content=self.sop_content,
                all_mistakes="\n".join(all_mistakes_list)
            )
            
            response = self._call_llm(prompt)
            parsed = self._parse_json_response(response)
            
            state["generated_themes"] = parsed.get("themes", [])
            logger.info(f"Generated {len(state['generated_themes'])} themes")
            return state
            
        except Exception as e:
            state["error"] = f"Theme generation failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _map_themes_node(self, state: AnalysisState) -> AnalysisState:
        """Map mistakes to themes for each transcript"""
        logger.info("Phase 3: Mapping mistakes to themes")
        
        try:
            themes = state["generated_themes"]
            theme_mappings = {}
            
            if not themes:
                for tid in state["all_mistakes"]:
                    theme_mappings[tid] = []
                state["theme_mappings"] = theme_mappings
                return state
            
            for tid, data in state["all_mistakes"].items():
                mistakes = data["mistakes"]
                
                if not mistakes:
                    theme_mappings[tid] = []
                    continue
                
                logger.info(f"Mapping themes for transcript: {tid}")
                
                prompt = PROMPT_MAP_THEMES.format(
                    sop_content=self.sop_content,
                    transcript_id=tid,
                    mistakes="\n".join([f"- {m}" for m in mistakes]),
                    themes="\n".join([f"- {t}" for t in themes])
                )
                
                response = self._call_llm(prompt)
                parsed = self._parse_json_response(response)
                
                theme_mappings[tid] = parsed.get("mapped_themes", [])
            
            state["theme_mappings"] = theme_mappings
            return state
            
        except Exception as e:
            state["error"] = f"Theme mapping failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _analyze_root_cause_node(self, state: AnalysisState) -> AnalysisState:
        """Analyze root cause and calculate severity"""
        logger.info("Phase 4: Analyzing root causes and severity")
        
        try:
            root_cause_data = {}
            
            for tid, data in state["all_mistakes"].items():
                mistakes = data["mistakes"]
                themes = state["theme_mappings"].get(tid, [])
                
                if not mistakes:
                    root_cause_data[tid] = {
                        "root_cause": "No issues identified",
                        "root_cause_reasoning": "Agent followed SOP correctly",
                        "severity_score": 100
                    }
                    continue
                
                logger.info(f"Analyzing root cause for transcript: {tid}")
                
                prompt = PROMPT_ROOT_CAUSE_AND_SEVERITY.format(
                    sop_content=self.sop_content,
                    transcript_id=tid,
                    agent_name=data["agent_name"],
                    mistakes="\n".join([f"- {m}" for m in mistakes]),
                    themes="\n".join([f"- {t}" for t in themes]) if themes else "No themes mapped"
                )
                
                response = self._call_llm(prompt)
                parsed = self._parse_json_response(response)
                
                root_cause_data[tid] = {
                    "root_cause": parsed.get("root_cause", "Unable to determine"),
                    "root_cause_reasoning": parsed.get("root_cause_reasoning", ""),
                    "severity_score": parsed.get("severity_score", 100)
                }
            
            state["root_cause_data"] = root_cause_data
            return state
            
        except Exception as e:
            state["error"] = f"Root cause analysis failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _compile_results_node(self, state: AnalysisState) -> AnalysisState:
        """Compile final results"""
        logger.info("Phase 5: Compiling final results")
        
        try:
            final_results = []
            
            for tid, data in state["all_mistakes"].items():
                root_cause_info = state["root_cause_data"].get(tid, {})
                
                result = TranscriptAnalysisOutput(
                    transcript_id=tid,
                    agent_name=data["agent_name"],
                    agent_id=data["agent_id"],
                    transcript_call=data["transcript_call"],
                    mistakes=data["mistakes"],
                    mistake_themes=state["theme_mappings"].get(tid, []),
                    root_cause=root_cause_info.get("root_cause", ""),
                    root_cause_reasoning=root_cause_info.get("root_cause_reasoning", ""),
                    severity_score=root_cause_info.get("severity_score", 100)
                )
                
                final_results.append(result.model_dump())
            
            state["final_results"] = final_results
            state["processing_phase"] = "complete"
            logger.info(f"Compiled {len(final_results)} results")
            return state
            
        except Exception as e:
            state["error"] = f"Result compilation failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def analyze(self, transcripts_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run the transcript analysis workflow.
        
        Args:
            transcripts_df: DataFrame with transcript data
        
        Returns:
            Dictionary with final_results, generated_themes, summary, success, error
        """
        if not self.sop_content:
            return {
                "final_results": [],
                "generated_themes": [],
                "summary": {},
                "success": False,
                "error": "SOP content not provided. Please upload an SOP document."
            }
        
        logger.info(f"Starting analysis for {len(transcripts_df)} transcripts")
        
        try:
            initial_state = AnalysisState({
                "transcripts_df": transcripts_df.to_dict(),
                "all_mistakes": {},
                "generated_themes": [],
                "theme_mappings": {},
                "root_cause_data": {},
                "final_results": [],
                "error": None
            })
            
            final_state = self.workflow.invoke(initial_state)
            
            if final_state.get("error"):
                return {
                    "final_results": [],
                    "generated_themes": [],
                    "summary": {},
                    "success": False,
                    "error": final_state["error"]
                }
            
            # Calculate summary
            results = final_state["final_results"]
            total_mistakes = sum(len(r.get("mistakes", [])) for r in results)
            avg_severity = sum(r.get("severity_score", 0) for r in results) / len(results) if results else 0
            
            summary = {
                "total_transcripts": len(results),
                "total_mistakes": total_mistakes,
                "avg_mistakes_per_transcript": total_mistakes / len(results) if results else 0,
                "avg_severity_score": round(avg_severity, 1),
                "themes_generated": len(final_state["generated_themes"])
            }
            
            return {
                "final_results": final_state["final_results"],
                "generated_themes": final_state["generated_themes"],
                "summary": summary,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {
                "final_results": [],
                "generated_themes": [],
                "summary": {},
                "success": False,
                "error": str(e)
            }
    
    def get_results_dataframe(self, analysis_result: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert analysis results to a DataFrame for export.
        
        Output columns (as requested):
        - transcript_id
        - agent_name
        - agent_id
        - transcript_call
        - mistakes (list as string)
        - mistake_themes (list as string)
        - root_cause
        - root_cause_reasoning
        - severity_score
        """
        if not analysis_result.get("success") or not analysis_result.get("final_results"):
            return pd.DataFrame()
        
        records = []
        for result in analysis_result["final_results"]:
            # Format mistakes as comma-separated list
            mistakes_list = result.get("mistakes", [])
            mistakes_str = ", ".join(mistakes_list) if mistakes_list else ""
            
            # Format themes as comma-separated list
            themes_list = result.get("mistake_themes", [])
            themes_str = ", ".join(themes_list) if themes_list else ""
            
            record = {
                "transcript_id": result.get("transcript_id", ""),
                "agent_name": result.get("agent_name", ""),
                "agent_id": result.get("agent_id", ""),
                "transcript_call": result.get("transcript_call", ""),
                "mistakes": mistakes_str,
                "mistake_themes": themes_str,
                "root_cause": result.get("root_cause", ""),
                "root_cause_reasoning": result.get("root_cause_reasoning", ""),
                "severity_score": result.get("severity_score", 100)
            }
            records.append(record)
        
        return pd.DataFrame(records)
