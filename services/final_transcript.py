"""
Simplified Transcript Analysis LangGraph Service
Outputs: transcript_id, transcript_call, agent_id, agent_name, mistakes, 
         mistake_themes, root_cause, severity_score, reasoning
"""

import os
import json
import time
import logging
from typing import TypedDict, List, Dict, Any, Optional
import pandas as pd

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# LangGraph State - Only essential fields
# ============================================================================

class TranscriptState(TypedDict):
    """Minimal state for transcript analysis"""
    transcripts_df: Dict[str, Any]
    all_mistakes: List[Dict[str, Any]]
    aggregated_mistakes: List[Dict[str, Any]]
    generated_themes: List[str]
    final_results: List[Dict[str, Any]]
    total_transcripts: int
    error: Optional[str]


# ============================================================================
# Prompts
# ============================================================================

PROMPT_MISTAKES = """You are a call quality analyst. Identify ALL mistakes made by the agent.

**Transcript ID:** {transcript_id}
**Agent ID:** {agent_id}
**Agent Name:** {agent_name}

**Transcript:**
{transcript_call}

**Categories to consider:**
1. Compliance & Policy Violations
2. Communication Issues
3. Technical Errors
4. Customer Service Failures
5. Process Deviations
6. Resolution Issues

**Return ONLY valid JSON:**
```json
{{
  "mistakes": [
    "Mistake description 1",
    "Mistake description 2"
  ]
}}
```

If no mistakes, return: {{"mistakes": []}}
"""


PROMPT_THEMES = """Analyze these mistakes and create 10 common mistake themes.

**All Mistakes:**
{aggregated_mistakes}

**Return ONLY valid JSON with theme names as strings:**
```json
{{
  "themes": [
    "Theme 1 name",
    "Theme 2 name",
    "Theme 3 name",
    "Theme 4 name",
    "Theme 5 name",
    "Theme 6 name",
    "Theme 7 name",
    "Theme 8 name",
    "Theme 9 name",
    "Theme 10 name"
  ]
}}
```
"""


PROMPT_ANALYSIS = """Analyze this transcript's mistakes and provide root causes, severity, and reasoning.

**Transcript ID:** {transcript_id}
**Agent ID:** {agent_id}
**Agent Name:** {agent_name}

**Mistakes Found:**
{mistakes}

**Available Themes:**
{themes}

**Instructions:**
1. Map mistakes to themes from the list
2. Identify root causes for each mistake
3. Calculate severity score (0-100, where 100 is perfect)
4. Provide reasoning behind root causes

**Return ONLY valid JSON:**
```json
{{
  "mistake_themes": ["theme1", "theme2"],
  "root_cause": ["root cause 1", "root cause 2"],
  "severity_score": 75,
  "reasoning": "Detailed reasoning behind the root causes identified"
}}
```
"""


# ============================================================================
# Transcript Analysis Service
# ============================================================================

class FinalTranscriptAnalysis:
    """Simplified transcript analysis using LangGraph"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        
        self._last_request_time = 0
        self._min_request_interval = 2.0
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        self.workflow = self._build_workflow()
    
    def _rate_limit(self):
        """Apply rate limiting"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM with rate limiting"""
        self._rate_limit()
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
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
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse response"}
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(TranscriptState)
        
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("identify_mistakes", self._identify_mistakes)
        workflow.add_node("aggregate_mistakes", self._aggregate_mistakes)
        workflow.add_node("generate_themes", self._generate_themes)
        workflow.add_node("analyze_transcripts", self._analyze_transcripts)
        
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "identify_mistakes")
        workflow.add_edge("identify_mistakes", "aggregate_mistakes")
        workflow.add_edge("aggregate_mistakes", "generate_themes")
        workflow.add_edge("generate_themes", "analyze_transcripts")
        workflow.add_edge("analyze_transcripts", END)
        
        return workflow.compile()
    
    def _initialize(self, state: TranscriptState) -> TranscriptState:
        """Initialize workflow"""
        logger.info("Initializing analysis")
        df = pd.DataFrame(state["transcripts_df"])
        state["total_transcripts"] = len(df)
        state["all_mistakes"] = []
        state["aggregated_mistakes"] = []
        state["generated_themes"] = []
        state["final_results"] = []
        state["error"] = None
        return state
    
    def _identify_mistakes(self, state: TranscriptState) -> TranscriptState:
        """Identify mistakes in each transcript"""
        logger.info("Identifying mistakes")
        df = pd.DataFrame(state["transcripts_df"])
        all_mistakes = []
        
        for idx, row in df.iterrows():
            transcript_id = str(row.get("Transcript_ID", row.get("transcript_id", f"T{idx+1}")))
            agent_id = str(row.get("Agent_ID", row.get("agent_id", f"A{idx+1}")))
            agent_name = str(row.get("Agent_Name", row.get("agent_name", "Unknown")))
            transcript_call = str(row.get("Transcript_Call", row.get("transcript_call", row.get("Transcript", ""))))
            
            logger.info(f"Processing transcript {idx + 1}/{len(df)}: {transcript_id}")
            
            prompt = PROMPT_MISTAKES.format(
                transcript_id=transcript_id,
                agent_id=agent_id,
                agent_name=agent_name,
                transcript_call=transcript_call
            )
            
            response = self._call_llm(prompt)
            parsed = self._parse_json(response)
            
            mistakes = parsed.get("mistakes", [])
            
            all_mistakes.append({
                "transcript_id": transcript_id,
                "transcript_call": transcript_call,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "mistakes": mistakes
            })
        
        state["all_mistakes"] = all_mistakes
        return state
    
    def _aggregate_mistakes(self, state: TranscriptState) -> TranscriptState:
        """Aggregate all mistakes"""
        logger.info("Aggregating mistakes")
        aggregated = []
        for item in state["all_mistakes"]:
            for mistake in item.get("mistakes", []):
                aggregated.append(mistake)
        state["aggregated_mistakes"] = aggregated
        return state
    
    def _generate_themes(self, state: TranscriptState) -> TranscriptState:
        """Generate mistake themes"""
        logger.info("Generating themes")
        
        if not state["aggregated_mistakes"]:
            state["generated_themes"] = []
            return state
        
        prompt = PROMPT_THEMES.format(
            aggregated_mistakes=json.dumps(state["aggregated_mistakes"], indent=2)
        )
        
        response = self._call_llm(prompt)
        parsed = self._parse_json(response)
        
        themes = parsed.get("themes", [])
        state["generated_themes"] = themes
        logger.info(f"Generated {len(themes)} themes")
        return state
    
    def _analyze_transcripts(self, state: TranscriptState) -> TranscriptState:
        """Analyze each transcript for themes, root causes, severity, reasoning"""
        logger.info("Analyzing transcripts")
        final_results = []
        themes = state["generated_themes"]
        
        for item in state["all_mistakes"]:
            transcript_id = item["transcript_id"]
            transcript_call = item["transcript_call"]
            agent_id = item["agent_id"]
            agent_name = item["agent_name"]
            mistakes = item["mistakes"]
            
            if not mistakes:
                final_results.append({
                    "transcript_id": transcript_id,
                    "transcript_call": transcript_call,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "mistakes": [],
                    "mistake_themes": [],
                    "root_cause": [],
                    "severity_score": 100,
                    "reasoning": "No mistakes identified - excellent performance"
                })
                continue
            
            logger.info(f"Analyzing transcript: {transcript_id}")
            
            prompt = PROMPT_ANALYSIS.format(
                transcript_id=transcript_id,
                agent_id=agent_id,
                agent_name=agent_name,
                mistakes=json.dumps(mistakes, indent=2),
                themes=json.dumps(themes, indent=2)
            )
            
            response = self._call_llm(prompt)
            parsed = self._parse_json(response)
            
            final_results.append({
                "transcript_id": transcript_id,
                "transcript_call": transcript_call,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "mistakes": mistakes,
                "mistake_themes": parsed.get("mistake_themes", []),
                "root_cause": parsed.get("root_cause", []),
                "severity_score": parsed.get("severity_score", 100),
                "reasoning": parsed.get("reasoning", "")
            })
        
        state["final_results"] = final_results
        return state
    
    def analyze(self, transcripts_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run transcript analysis.
        
        Args:
            transcripts_df: DataFrame with columns:
                - Transcript_ID or transcript_id
                - Agent_ID or agent_id  
                - Agent_Name or agent_name
                - Transcript_Call or transcript_call or Transcript
        
        Returns:
            Dictionary with final_results, generated_themes, success, error
        """
        logger.info(f"Starting analysis for {len(transcripts_df)} transcripts")
        
        try:
            initial_state: TranscriptState = {
                "transcripts_df": transcripts_df.to_dict(),
                "all_mistakes": [],
                "aggregated_mistakes": [],
                "generated_themes": [],
                "final_results": [],
                "total_transcripts": 0,
                "error": None
            }
            
            final_state = self.workflow.invoke(initial_state)
            
            if final_state.get("error"):
                return {
                    "final_results": [],
                    "generated_themes": [],
                    "success": False,
                    "error": final_state["error"]
                }
            
            return {
                "final_results": final_state["final_results"],
                "generated_themes": final_state["generated_themes"],
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {
                "final_results": [],
                "generated_themes": [],
                "success": False,
                "error": str(e)
            }
    
    def to_dataframe(self, analysis_result: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert results to DataFrame for CSV export.
        
        Args:
            analysis_result: Result from analyze() method
            
        Returns:
            DataFrame with columns: transcript_id, transcript_call, agent_id, 
            agent_name, mistakes, mistake_themes, root_cause, severity_score, reasoning
        """
        if not analysis_result.get("success") or not analysis_result.get("final_results"):
            return pd.DataFrame()
        
        records = []
        for result in analysis_result["final_results"]:
            records.append({
                "transcript_id": result.get("transcript_id"),
                "transcript_call": result.get("transcript_call"),
                "agent_id": result.get("agent_id"),
                "agent_name": result.get("agent_name"),
                "mistakes": json.dumps(result.get("mistakes", [])),
                "mistake_themes": json.dumps(result.get("mistake_themes", [])),
                "root_cause": json.dumps(result.get("root_cause", [])),
                "severity_score": result.get("severity_score", 100),
                "reasoning": result.get("reasoning", "")
            })
        
        return pd.DataFrame(records)
    
    def analyze_csv(self, csv_path: str, output_path: str = None) -> pd.DataFrame:
        """
        Analyze transcripts from CSV file and optionally save results.
        
        Args:
            csv_path: Path to input CSV file
            output_path: Optional path for output CSV (if None, uses input_analyzed.csv)
            
        Returns:
            DataFrame with analysis results
        """
        logger.info(f"Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        
        result = self.analyze(df)
        
        if not result["success"]:
            logger.error(f"Analysis failed: {result['error']}")
            return pd.DataFrame()
        
        output_df = self.to_dataframe(result)
        
        if output_path is None:
            output_path = csv_path.replace(".csv", "_analyzed.csv")
        
        output_df.to_csv(output_path, index=False)
        logger.info(f"Results saved to: {output_path}")
        
        return output_df


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    # Example usage
    import os
    
    # Set API key
    # os.environ["GOOGLE_API_KEY"] = "your-api-key"
    
    # Create sample data
    sample_data = {
        "Transcript_ID": ["T001", "T002"],
        "Agent_ID": ["A001", "A002"],
        "Agent_Name": ["John Doe", "Jane Smith"],
        "Transcript_Call": [
            "Agent: Hello, how can I help? Customer: I need to cancel my order. Agent: Sure, let me check... *puts on hold for 5 minutes without explanation* Agent: Okay, your order is cancelled.",
            "Agent: Hi there! Customer: I want a refund. Agent: I understand your frustration. Let me look into this for you. *verifies account* Agent: I've processed your refund. Is there anything else I can help with?"
        ]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Run analysis
    analyzer = FinalTranscriptAnalysis()
    result = analyzer.analyze(df)
    
    if result["success"]:
        output_df = analyzer.to_dataframe(result)
        print(output_df.to_string())
        # output_df.to_csv("output.csv", index=False)
    else:
        print(f"Error: {result['error']}")
