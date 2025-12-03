"""
Transcript Analysis LangGraph Service
Comprehensive multi-step analysis of customer service call transcripts
for mistake identification, theme generation, root cause analysis, and severity scoring.
"""

import os
import json
import time
import logging
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from dataclasses import dataclass, field, asdict
from datetime import datetime
import pandas as pd

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
import operator

from config.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Mistake:
    """Single mistake identified in a transcript"""
    mistake_number: int
    timestamp_or_location: str
    mistake_description: str
    category: str
    impact: str


@dataclass
class TranscriptMistakes:
    """Mistakes identified in a single transcript"""
    transcript_id: str
    agent_id: str
    agent_name: str
    mistakes: List[Dict[str, Any]]
    total_mistakes_found: int


@dataclass
class MistakeTheme:
    """A common mistake theme across transcripts"""
    theme_number: int
    theme_name: str
    definition: str
    examples: List[str]
    frequency_in_dataset: str
    importance: str
    criticality: str = "Non-Critical"  # Critical or Non-Critical


@dataclass
class ThemeMapping:
    """Mapping of mistakes to themes for a transcript"""
    transcript_id: str
    agent_id: str
    themes_present: List[Dict[str, Any]]
    total_unique_themes: int
    most_frequent_theme: str


@dataclass
class RootCauseAnalysis:
    """Root cause analysis for a transcript"""
    transcript_id: str
    agent_id: str
    root_causes: List[Dict[str, Any]]
    primary_root_causes: List[Dict[str, Any]]


@dataclass
class SeverityAssessment:
    """Severity assessment for a transcript"""
    transcript_id: str
    agent_id: str
    theme_criticality: List[Dict[str, Any]]
    total_critical_themes: int
    total_non_critical_themes: int
    severity_score: int
    severity_rating: str


@dataclass
class RootCauseReasoning:
    """Detailed reasoning behind root causes"""
    transcript_id: str
    agent_id: str
    agent_name: str
    root_cause_reasoning: List[Dict[str, Any]]
    overall_assessment: Dict[str, Any]


@dataclass
class FinalTranscriptAnalysis:
    """Final comprehensive analysis for a single transcript"""
    transcript_id: str
    transcript_call: str
    agent_id: str
    agent_name: str
    mistakes: List[Dict[str, Any]]
    mistakes_count: int
    mistake_themes: List[str]
    root_cause: List[Dict[str, Any]]
    primary_root_causes: List[str]
    reasoning_behind_root_cause: Dict[str, Any]
    theme_criticality: List[Dict[str, Any]]
    severity_score: int
    severity_rating: str


# ============================================================================
# LangGraph State
# ============================================================================

class TranscriptAnalysisState(TypedDict):
    """State for the transcript analysis workflow"""
    # Input data
    transcripts_df: Dict[str, Any]  # DataFrame as dict
    
    # Phase 1: Mistake Identification (per transcript)
    all_mistakes: List[Dict[str, Any]]  # List of TranscriptMistakes
    aggregated_mistakes: List[Dict[str, Any]]  # All mistakes aggregated
    
    # Phase 1: Theme Generation (global)
    generated_themes: List[Dict[str, Any]]  # 10 generated themes
    themes_with_criticality: List[Dict[str, Any]]  # Themes with criticality classification
    
    # Phase 2: Per-transcript analysis results
    theme_mappings: List[Dict[str, Any]]  # Theme mappings per transcript
    root_cause_analyses: List[Dict[str, Any]]  # Root causes per transcript
    severity_assessments: List[Dict[str, Any]]  # Severity scores per transcript
    root_cause_reasonings: List[Dict[str, Any]]  # Reasoning per transcript
    
    # Final output
    final_results: List[Dict[str, Any]]  # Final comprehensive results
    
    # Processing state
    current_transcript_idx: int
    total_transcripts: int
    processing_phase: str
    
    # Metadata
    analysis_date: str
    error: Optional[str]


# ============================================================================
# Prompts
# ============================================================================

PROMPT_1_MISTAKE_IDENTIFICATION = """You are an expert call quality analyst reviewing customer service call transcripts. Your task is to identify ALL mistakes made by the agent during the call.

**Context:**
- Transcript ID: {transcript_id}
- Agent ID: {agent_id}
- Agent Name: {agent_name}

**Transcript:**
{transcript_call}

**Instructions:**
Analyze the transcript thoroughly and identify every mistake made by the agent. Consider the following categories:

1. **Compliance & Policy Violations**: Failure to follow required procedures, scripts, or regulatory requirements
2. **Communication Issues**: Unclear explanations, poor listening, interrupting, unprofessional language
3. **Technical Errors**: Incorrect information provided, system navigation errors, documentation mistakes
4. **Customer Service Failures**: Lack of empathy, failure to acknowledge concerns, not offering solutions
5. **Process Deviations**: Skipping required steps, not verifying information, improper authentication
6. **Time Management**: Excessive hold times without explanation, rushing through important information
7. **Resolution Issues**: Problem not resolved, incorrect solutions offered, failure to follow up

**Output Format:**
Provide a detailed list of mistakes in the following JSON format:

```json
{{
  "transcript_id": "{transcript_id}",
  "agent_id": "{agent_id}",
  "agent_name": "{agent_name}",
  "mistakes": [
    {{
      "mistake_number": 1,
      "timestamp_or_location": "Beginning of call/Middle/End",
      "mistake_description": "Detailed description of what went wrong",
      "category": "Category from list above",
      "impact": "How this affected the customer or call outcome"
    }}
  ],
  "total_mistakes_found": 0
}}
```

Be thorough and objective. Even minor mistakes should be documented. If no mistakes are found, return an empty mistakes array with total_mistakes_found: 0.

Return ONLY valid JSON, no additional text."""


PROMPT_2_GENERATE_THEMES = """You are a quality assurance manager analyzing patterns across ALL mistakes identified from call transcripts.

**Context:**
You have collected mistakes from multiple call transcripts. Your task is to analyze ALL these mistakes collectively and identify the 10 MOST COMMON MISTAKE THEMES that emerge from the data.

**All Mistakes Collected:**
{aggregated_mistakes}

**Instructions:**

**STEP 1: Analyze All Mistakes**
Review all mistakes across all transcripts and identify patterns, commonalities, and recurring issues.

**STEP 2: Generate 10 Mistake Themes**
Based on your analysis, create exactly 10 mistake themes that:
- Capture the most frequently occurring mistake types
- Are distinct from each other (minimal overlap)
- Are specific enough to be actionable
- Cover the majority of mistakes identified
- Are relevant to call center quality management

**STEP 3: Define Each Theme**
For each theme, provide:
- Theme name (concise, 2-5 words)
- Clear definition
- Examples of mistakes that fall under this theme
- Why this theme is important for quality management

**Output Format:**
```json
{{
  "analysis_summary": {{
    "total_mistakes_analyzed": {total_mistakes},
    "total_transcripts_analyzed": {total_transcripts},
    "analysis_date": "{analysis_date}"
  }},
  "mistake_themes": [
    {{
      "theme_number": 1,
      "theme_name": "Concise theme name",
      "definition": "Clear definition of what this theme covers",
      "examples": [
        "Example mistake 1 that falls under this theme",
        "Example mistake 2 that falls under this theme",
        "Example mistake 3 that falls under this theme"
      ],
      "frequency_in_dataset": "Number or percentage of mistakes falling under this theme",
      "importance": "Why this theme matters for quality/compliance/customer satisfaction"
    }}
  ],
  "coverage_analysis": {{
    "mistakes_covered_by_themes": 0,
    "coverage_percentage": 0,
    "uncategorized_mistakes": 0
  }}
}}
```

**Important Guidelines:**
1. Themes should be data-driven based on actual mistakes found
2. Prioritize themes that appear most frequently
3. Ensure themes are actionable for training and coaching
4. Themes should be mutually exclusive where possible
5. Use clear, professional language for theme names

Return ONLY valid JSON, no additional text."""


PROMPT_3_MAP_THEMES = """You are a quality analyst mapping individual call mistakes to established theme categories.

**Context:**
**Transcript ID:** {transcript_id}
**Agent ID:** {agent_id}
**Agent Name:** {agent_name}

**Mistakes Identified in This Call:**
{mistakes}

**Established 10 Mistake Themes:**
{themes}

**Instructions:**
Map each mistake from this transcript to one or more of the 10 established mistake themes. 

For each mistake:
1. Identify which theme(s) it belongs to
2. If a mistake fits multiple themes, list all applicable themes
3. If a mistake doesn't fit any theme well, assign it to the closest match

**Output Format:**
```json
{{
  "transcript_id": "{transcript_id}",
  "agent_id": "{agent_id}",
  "mistake_theme_mapping": [
    {{
      "mistake_number": 1,
      "mistake_description": "Brief description",
      "mapped_themes": [
        {{
          "theme_number": 1,
          "theme_name": "Theme name",
          "mapping_confidence": "High/Medium/Low",
          "reasoning": "Why this mistake maps to this theme"
        }}
      ]
    }}
  ],
  "summary": {{
    "themes_present_in_call": [
      {{
        "theme_number": 1,
        "theme_name": "Theme name",
        "occurrence_count": 0,
        "related_mistake_numbers": [1, 3, 5]
      }}
    ],
    "total_unique_themes": 0,
    "most_frequent_theme": "Theme name"
  }}
}}
```

Be precise in your mappings and provide clear reasoning for each assignment.

Return ONLY valid JSON, no additional text."""


PROMPT_4_ROOT_CAUSE = """You are a performance improvement specialist conducting root cause analysis on agent mistakes.

**Context:**
**Transcript ID:** {transcript_id}
**Agent ID:** {agent_id}
**Agent Name:** {agent_name}
**Mistakes Identified:** {mistakes}
**Themes Mapped:** {themes_mapped}

**Instructions:**
For EACH mistake identified, determine the root cause by analyzing what underlying factor led to the error.

**Root Cause Categories:**
1. **Insufficient Training** - Agent lacks knowledge or skills in specific area
2. **System/Tool Limitations** - Technology constraints or system issues
3. **Process Ambiguity** - Unclear or poorly documented procedures
4. **Time Pressure** - Rush to meet metrics affecting quality
5. **Knowledge Gap** - Missing information or outdated knowledge
6. **Communication Skills Deficit** - Inherent communication weaknesses
7. **Attention/Focus Issues** - Distraction, multitasking, or lack of concentration
8. **Policy Understanding Gap** - Misunderstanding of rules or requirements
9. **Resource Unavailability** - Lack of access to needed information or tools
10. **Motivation/Engagement Issues** - Low engagement or carelessness
11. **Coaching/Feedback Gap** - Lack of proper guidance or reinforcement
12. **Complex Customer Scenario** - Unusual or difficult situation beyond typical training

**Output Format:**
```json
{{
  "transcript_id": "{transcript_id}",
  "agent_id": "{agent_id}",
  "root_cause_analysis": [
    {{
      "mistake_number": 1,
      "mistake_description": "Brief description",
      "associated_themes": ["Theme names from mapping"],
      "root_cause": "Primary root cause from categories above",
      "contributing_factors": ["List any secondary contributing factors"],
      "evidence": "Specific evidence from transcript supporting this root cause",
      "confidence_level": "High/Medium/Low"
    }}
  ],
  "root_cause_summary": {{
    "primary_root_causes": [
      {{
        "root_cause": "Root cause name",
        "frequency": 0,
        "affected_themes": ["List of themes affected by this root cause"]
      }}
    ]
  }}
}}
```

Focus on identifying the PRIMARY root cause for each mistake, supported by evidence from the transcript.

Return ONLY valid JSON, no additional text."""


PROMPT_5_SEVERITY = """You are a risk assessment specialist evaluating the severity of agent mistakes in customer service calls.

**Context:**
**Transcript ID:** {transcript_id}
**Agent ID:** {agent_id}
**Themes Present:** {themes_present}
**Root Causes:** {root_causes}
**Established 10 Themes with Definitions:** {all_themes}

**Instructions:**

**STEP 1: Classify Each Theme Present in This Call as Critical or Non-Critical**

For each of the themes present in this call, determine if it should be classified as CRITICAL or NON-CRITICAL based on:
- Regulatory/compliance impact
- Customer satisfaction impact
- Business risk level
- Financial implications
- Reputational damage potential

**STEP 2: Calculate Severity Score (0-100)**

Use this formula:
- **Critical Theme occurrence = -15 points per occurrence**
- **Non-Critical Theme occurrence = -5 points per occurrence**
- **Starting Score = 100**

**Final Severity Score = 100 - (Critical Theme occurrences × 15) - (Non-Critical Theme occurrences × 5)**

Minimum score: 0
Maximum score: 100

**STEP 3: Assign Severity Rating**
- 90-100: Excellent
- 75-89: Good
- 60-74: Fair
- 40-59: Poor
- 0-39: Critical

**Output Format:**
```json
{{
  "transcript_id": "{transcript_id}",
  "agent_id": "{agent_id}",
  "theme_criticality_assessment": [
    {{
      "theme_number": 1,
      "theme_name": "Theme name",
      "present_in_call": true,
      "occurrence_count": 0,
      "criticality": "Critical/Non-Critical",
      "criticality_justification": "Why this theme is classified as critical/non-critical",
      "risk_level": "High/Medium/Low",
      "business_impact": "Description of potential impact"
    }}
  ],
  "severity_calculation": {{
    "total_critical_themes": 0,
    "total_non_critical_themes": 0,
    "total_themes_present": 0,
    "critical_theme_names": ["List of critical themes present"],
    "non_critical_theme_names": ["List of non-critical themes present"],
    "points_deducted_critical": 0,
    "points_deducted_non_critical": 0,
    "final_severity_score": 0,
    "severity_rating": "Excellent/Good/Fair/Poor/Critical"
  }}
}}
```

Return ONLY valid JSON, no additional text."""


PROMPT_6_REASONING = """You are a quality improvement consultant providing actionable insights on agent performance issues.

**Context:**
**Transcript ID:** {transcript_id}
**Agent ID:** {agent_id}
**Agent Name:** {agent_name}
**Mistakes:** {mistakes}
**Themes Present:** {themes_present}
**Root Causes:** {root_causes}
**Severity Score:** {severity_score}
**Severity Rating:** {severity_rating}
**Theme Criticality:** {theme_criticality}

**Instructions:**

Provide comprehensive reasoning for the root causes identified and actionable recommendations.

For EACH root cause found, explain:
1. **Why** this root cause occurred (deeper analysis)
2. **How** it manifested across different themes in the mistakes observed
3. **What** specific evidence supports this conclusion
4. **Impact** on customer experience and business
5. **Recommendations** for addressing this root cause

**Output Format:**
```json
{{
  "transcript_id": "{transcript_id}",
  "agent_id": "{agent_id}",
  "agent_name": "{agent_name}",
  "root_cause_reasoning": [
    {{
      "root_cause": "Root cause name",
      "affected_themes": ["List of themes impacted by this root cause"],
      "detailed_reasoning": "Deep explanation of why this root cause exists",
      "manifestation": "How this root cause showed up across different mistakes",
      "supporting_evidence": ["Specific examples from transcript"],
      "customer_impact": "How this affected the customer experience",
      "business_impact": "Financial, reputational, or operational impact",
      "severity_contribution": "How much this root cause contributed to overall severity score",
      "recommendations": {{
        "immediate_actions": ["Short-term fixes for this specific agent"],
        "training_needs": ["Specific training modules or skills to develop"],
        "systemic_improvements": ["Process or system changes needed"],
        "coaching_focus": ["Specific coaching areas and talking points"],
        "timeline": "Suggested timeline for improvement"
      }}
    }}
  ],
  "overall_assessment": {{
    "performance_summary": "Overall evaluation of agent performance",
    "primary_concern": "Main issue that needs immediate attention",
    "agent_strengths": ["What agent did well, if anything"],
    "priority_improvements": ["Top 3 areas to focus on, ranked by importance"],
    "critical_themes_analysis": "Analysis of critical themes and their implications",
    "follow_up_required": "Yes/No",
    "follow_up_timeline": "When to review progress",
    "escalation_needed": "Yes/No and why"
  }},
  "comparative_analysis": {{
    "severity_context": "How this agent's score compares to typical performance",
    "theme_frequency_vs_norm": "Are certain themes more common for this agent?",
    "improvement_potential": "High/Medium/Low and reasoning"
  }}
}}
```

Be specific, constructive, and solution-oriented in your reasoning. Provide actionable insights that can drive real performance improvements.

Return ONLY valid JSON, no additional text."""


# ============================================================================
# Transcript Analysis Service
# ============================================================================

class TranscriptAnalysisService:
    """
    Service for comprehensive transcript analysis using LangGraph.
    Implements the 6-prompt workflow for mistake identification, theme generation,
    root cause analysis, and severity scoring.
    """
    
    def __init__(self):
        """Initialize the transcript analysis service"""
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        
        # Rate limiting configuration
        self._last_request_time = 0
        self._min_request_interval = 2.0  # Minimum seconds between API calls
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        self.workflow = self._build_workflow()
    
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
        """Parse JSON from LLM response, handling markdown code blocks"""
        # Remove markdown code blocks if present
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
            # Try to find JSON object in response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse response", "raw_response": response[:500]}
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for transcript analysis"""
        workflow = StateGraph(TranscriptAnalysisState)
        
        # Phase 1: Initial Setup and Mistake Identification
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("identify_mistakes", self._identify_mistakes_node)
        workflow.add_node("aggregate_mistakes", self._aggregate_mistakes_node)
        workflow.add_node("generate_themes", self._generate_themes_node)
        
        # Phase 2: Per-transcript Analysis
        workflow.add_node("map_themes", self._map_themes_node)
        workflow.add_node("analyze_root_causes", self._analyze_root_causes_node)
        workflow.add_node("calculate_severity", self._calculate_severity_node)
        workflow.add_node("generate_reasoning", self._generate_reasoning_node)
        
        # Phase 3: Compile Final Results
        workflow.add_node("compile_results", self._compile_results_node)
        
        # Define edges - Sequential workflow
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "identify_mistakes")
        workflow.add_edge("identify_mistakes", "aggregate_mistakes")
        workflow.add_edge("aggregate_mistakes", "generate_themes")
        workflow.add_edge("generate_themes", "map_themes")
        workflow.add_edge("map_themes", "analyze_root_causes")
        workflow.add_edge("analyze_root_causes", "calculate_severity")
        workflow.add_edge("calculate_severity", "generate_reasoning")
        workflow.add_edge("generate_reasoning", "compile_results")
        workflow.add_edge("compile_results", END)
        
        return workflow.compile()
    
    # =========================================================================
    # Node Implementations
    # =========================================================================
    
    def _initialize_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Initialize the analysis workflow"""
        logger.info("Initializing transcript analysis workflow")
        
        try:
            df = pd.DataFrame(state["transcripts_df"])
            state["total_transcripts"] = len(df)
            state["current_transcript_idx"] = 0
            state["processing_phase"] = "initialization"
            state["analysis_date"] = datetime.now().strftime("%Y-%m-%d")
            state["all_mistakes"] = []
            state["aggregated_mistakes"] = []
            state["generated_themes"] = []
            state["themes_with_criticality"] = []
            state["theme_mappings"] = []
            state["root_cause_analyses"] = []
            state["severity_assessments"] = []
            state["root_cause_reasonings"] = []
            state["final_results"] = []
            state["error"] = None
            
            logger.info(f"Initialized workflow for {state['total_transcripts']} transcripts")
            return state
            
        except Exception as e:
            state["error"] = f"Initialization failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _identify_mistakes_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Identify mistakes in each transcript (Prompt 1)"""
        logger.info("Phase 1: Identifying mistakes in all transcripts")
        state["processing_phase"] = "mistake_identification"
        
        try:
            df = pd.DataFrame(state["transcripts_df"])
            all_mistakes = []
            
            for idx, row in df.iterrows():
                transcript_id = str(row.get("Transcript_ID", row.get("transcript_id", f"T{idx+1}")))
                agent_id = str(row.get("Agent_ID", row.get("agent_id", f"A{idx+1}")))
                agent_name = str(row.get("Agent_Name", row.get("agent_name", "Unknown")))
                transcript_call = str(row.get("Transcript_Call", row.get("transcript_call", row.get("Transcript", ""))))
                
                logger.info(f"Analyzing transcript {idx + 1}/{len(df)}: {transcript_id}")
                
                prompt = PROMPT_1_MISTAKE_IDENTIFICATION.format(
                    transcript_id=transcript_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    transcript_call=transcript_call
                )
                
                response = self._call_llm(prompt)
                parsed = self._parse_json_response(response)
                
                # Ensure required fields exist
                if "error" not in parsed:
                    parsed["transcript_id"] = transcript_id
                    parsed["agent_id"] = agent_id
                    parsed["agent_name"] = agent_name
                    if "mistakes" not in parsed:
                        parsed["mistakes"] = []
                    if "total_mistakes_found" not in parsed:
                        parsed["total_mistakes_found"] = len(parsed.get("mistakes", []))
                
                all_mistakes.append(parsed)
            
            state["all_mistakes"] = all_mistakes
            logger.info(f"Identified mistakes in {len(all_mistakes)} transcripts")
            return state
            
        except Exception as e:
            state["error"] = f"Mistake identification failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _aggregate_mistakes_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Aggregate all mistakes from all transcripts"""
        logger.info("Aggregating mistakes from all transcripts")
        state["processing_phase"] = "aggregation"
        
        try:
            aggregated = []
            
            for transcript_mistakes in state["all_mistakes"]:
                transcript_id = transcript_mistakes.get("transcript_id", "Unknown")
                agent_name = transcript_mistakes.get("agent_name", "Unknown")
                
                for mistake in transcript_mistakes.get("mistakes", []):
                    aggregated.append({
                        "transcript_id": transcript_id,
                        "agent_name": agent_name,
                        **mistake
                    })
            
            state["aggregated_mistakes"] = aggregated
            logger.info(f"Aggregated {len(aggregated)} total mistakes")
            return state
            
        except Exception as e:
            state["error"] = f"Aggregation failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _generate_themes_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Generate 10 common mistake themes (Prompt 2)"""
        logger.info("Phase 1: Generating 10 mistake themes")
        state["processing_phase"] = "theme_generation"
        
        try:
            aggregated_mistakes = state["aggregated_mistakes"]
            
            # Format mistakes for the prompt
            mistakes_str = json.dumps(aggregated_mistakes, indent=2)
            
            prompt = PROMPT_2_GENERATE_THEMES.format(
                aggregated_mistakes=mistakes_str,
                total_mistakes=len(aggregated_mistakes),
                total_transcripts=state["total_transcripts"],
                analysis_date=state["analysis_date"]
            )
            
            response = self._call_llm(prompt)
            parsed = self._parse_json_response(response)
            
            themes = parsed.get("mistake_themes", [])
            state["generated_themes"] = themes
            
            logger.info(f"Generated {len(themes)} mistake themes")
            return state
            
        except Exception as e:
            state["error"] = f"Theme generation failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _map_themes_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Map mistakes to themes for each transcript (Prompt 3)"""
        logger.info("Phase 2: Mapping mistakes to themes")
        state["processing_phase"] = "theme_mapping"
        
        try:
            themes = state["generated_themes"]
            themes_str = json.dumps(themes, indent=2)
            theme_mappings = []
            
            for transcript_mistakes in state["all_mistakes"]:
                transcript_id = transcript_mistakes.get("transcript_id", "Unknown")
                agent_id = transcript_mistakes.get("agent_id", "Unknown")
                agent_name = transcript_mistakes.get("agent_name", "Unknown")
                mistakes = transcript_mistakes.get("mistakes", [])
                
                if not mistakes:
                    # No mistakes to map
                    theme_mappings.append({
                        "transcript_id": transcript_id,
                        "agent_id": agent_id,
                        "mistake_theme_mapping": [],
                        "summary": {
                            "themes_present_in_call": [],
                            "total_unique_themes": 0,
                            "most_frequent_theme": "None"
                        }
                    })
                    continue
                
                logger.info(f"Mapping themes for transcript: {transcript_id}")
                
                prompt = PROMPT_3_MAP_THEMES.format(
                    transcript_id=transcript_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    mistakes=json.dumps(mistakes, indent=2),
                    themes=themes_str
                )
                
                response = self._call_llm(prompt)
                parsed = self._parse_json_response(response)
                parsed["transcript_id"] = transcript_id
                parsed["agent_id"] = agent_id
                
                theme_mappings.append(parsed)
            
            state["theme_mappings"] = theme_mappings
            logger.info(f"Completed theme mapping for {len(theme_mappings)} transcripts")
            return state
            
        except Exception as e:
            state["error"] = f"Theme mapping failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _analyze_root_causes_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Analyze root causes for each transcript (Prompt 4)"""
        logger.info("Phase 2: Analyzing root causes")
        state["processing_phase"] = "root_cause_analysis"
        
        try:
            root_cause_analyses = []
            
            for i, transcript_mistakes in enumerate(state["all_mistakes"]):
                transcript_id = transcript_mistakes.get("transcript_id", "Unknown")
                agent_id = transcript_mistakes.get("agent_id", "Unknown")
                agent_name = transcript_mistakes.get("agent_name", "Unknown")
                mistakes = transcript_mistakes.get("mistakes", [])
                
                # Get corresponding theme mapping
                theme_mapping = state["theme_mappings"][i] if i < len(state["theme_mappings"]) else {}
                
                if not mistakes:
                    root_cause_analyses.append({
                        "transcript_id": transcript_id,
                        "agent_id": agent_id,
                        "root_cause_analysis": [],
                        "root_cause_summary": {"primary_root_causes": []}
                    })
                    continue
                
                logger.info(f"Analyzing root causes for transcript: {transcript_id}")
                
                prompt = PROMPT_4_ROOT_CAUSE.format(
                    transcript_id=transcript_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    mistakes=json.dumps(mistakes, indent=2),
                    themes_mapped=json.dumps(theme_mapping, indent=2)
                )
                
                response = self._call_llm(prompt)
                parsed = self._parse_json_response(response)
                parsed["transcript_id"] = transcript_id
                parsed["agent_id"] = agent_id
                
                root_cause_analyses.append(parsed)
            
            state["root_cause_analyses"] = root_cause_analyses
            logger.info(f"Completed root cause analysis for {len(root_cause_analyses)} transcripts")
            return state
            
        except Exception as e:
            state["error"] = f"Root cause analysis failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _calculate_severity_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Calculate severity scores for each transcript (Prompt 5)"""
        logger.info("Phase 2: Calculating severity scores")
        state["processing_phase"] = "severity_calculation"
        
        try:
            themes_str = json.dumps(state["generated_themes"], indent=2)
            severity_assessments = []
            
            for i, transcript_mistakes in enumerate(state["all_mistakes"]):
                transcript_id = transcript_mistakes.get("transcript_id", "Unknown")
                agent_id = transcript_mistakes.get("agent_id", "Unknown")
                
                # Get corresponding mappings
                theme_mapping = state["theme_mappings"][i] if i < len(state["theme_mappings"]) else {}
                root_causes = state["root_cause_analyses"][i] if i < len(state["root_cause_analyses"]) else {}
                
                themes_present = theme_mapping.get("summary", {}).get("themes_present_in_call", [])
                
                if not themes_present:
                    severity_assessments.append({
                        "transcript_id": transcript_id,
                        "agent_id": agent_id,
                        "theme_criticality_assessment": [],
                        "severity_calculation": {
                            "total_critical_themes": 0,
                            "total_non_critical_themes": 0,
                            "total_themes_present": 0,
                            "critical_theme_names": [],
                            "non_critical_theme_names": [],
                            "points_deducted_critical": 0,
                            "points_deducted_non_critical": 0,
                            "final_severity_score": 100,
                            "severity_rating": "Excellent"
                        }
                    })
                    continue
                
                logger.info(f"Calculating severity for transcript: {transcript_id}")
                
                prompt = PROMPT_5_SEVERITY.format(
                    transcript_id=transcript_id,
                    agent_id=agent_id,
                    themes_present=json.dumps(themes_present, indent=2),
                    root_causes=json.dumps(root_causes, indent=2),
                    all_themes=themes_str
                )
                
                response = self._call_llm(prompt)
                parsed = self._parse_json_response(response)
                parsed["transcript_id"] = transcript_id
                parsed["agent_id"] = agent_id
                
                severity_assessments.append(parsed)
            
            state["severity_assessments"] = severity_assessments
            logger.info(f"Completed severity calculation for {len(severity_assessments)} transcripts")
            return state
            
        except Exception as e:
            state["error"] = f"Severity calculation failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _generate_reasoning_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Generate detailed reasoning for root causes (Prompt 6)"""
        logger.info("Phase 2: Generating root cause reasoning")
        state["processing_phase"] = "reasoning_generation"
        
        try:
            root_cause_reasonings = []
            
            for i, transcript_mistakes in enumerate(state["all_mistakes"]):
                transcript_id = transcript_mistakes.get("transcript_id", "Unknown")
                agent_id = transcript_mistakes.get("agent_id", "Unknown")
                agent_name = transcript_mistakes.get("agent_name", "Unknown")
                mistakes = transcript_mistakes.get("mistakes", [])
                
                # Get corresponding data
                theme_mapping = state["theme_mappings"][i] if i < len(state["theme_mappings"]) else {}
                root_causes = state["root_cause_analyses"][i] if i < len(state["root_cause_analyses"]) else {}
                severity = state["severity_assessments"][i] if i < len(state["severity_assessments"]) else {}
                
                themes_present = theme_mapping.get("summary", {}).get("themes_present_in_call", [])
                severity_calc = severity.get("severity_calculation", {})
                severity_score = severity_calc.get("final_severity_score", 100)
                severity_rating = severity_calc.get("severity_rating", "Excellent")
                theme_criticality = severity.get("theme_criticality_assessment", [])
                
                if not mistakes:
                    root_cause_reasonings.append({
                        "transcript_id": transcript_id,
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "root_cause_reasoning": [],
                        "overall_assessment": {
                            "performance_summary": "No mistakes identified - excellent performance",
                            "primary_concern": "None",
                            "agent_strengths": ["Clean call execution"],
                            "priority_improvements": [],
                            "critical_themes_analysis": "No critical themes present",
                            "follow_up_required": "No",
                            "follow_up_timeline": "N/A",
                            "escalation_needed": "No"
                        },
                        "comparative_analysis": {
                            "severity_context": "Above average performance",
                            "theme_frequency_vs_norm": "Better than typical",
                            "improvement_potential": "Low"
                        }
                    })
                    continue
                
                logger.info(f"Generating reasoning for transcript: {transcript_id}")
                
                prompt = PROMPT_6_REASONING.format(
                    transcript_id=transcript_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    mistakes=json.dumps(mistakes, indent=2),
                    themes_present=json.dumps(themes_present, indent=2),
                    root_causes=json.dumps(root_causes, indent=2),
                    severity_score=severity_score,
                    severity_rating=severity_rating,
                    theme_criticality=json.dumps(theme_criticality, indent=2)
                )
                
                response = self._call_llm(prompt)
                parsed = self._parse_json_response(response)
                parsed["transcript_id"] = transcript_id
                parsed["agent_id"] = agent_id
                parsed["agent_name"] = agent_name
                
                root_cause_reasonings.append(parsed)
            
            state["root_cause_reasonings"] = root_cause_reasonings
            logger.info(f"Completed reasoning generation for {len(root_cause_reasonings)} transcripts")
            return state
            
        except Exception as e:
            state["error"] = f"Reasoning generation failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _compile_results_node(self, state: TranscriptAnalysisState) -> TranscriptAnalysisState:
        """Compile all results into final output format"""
        logger.info("Phase 3: Compiling final results")
        state["processing_phase"] = "compilation"
        
        try:
            df = pd.DataFrame(state["transcripts_df"])
            final_results = []
            
            for i, row in df.iterrows():
                transcript_id = str(row.get("Transcript_ID", row.get("transcript_id", f"T{i+1}")))
                agent_id = str(row.get("Agent_ID", row.get("agent_id", f"A{i+1}")))
                agent_name = str(row.get("Agent_Name", row.get("agent_name", "Unknown")))
                transcript_call = str(row.get("Transcript_Call", row.get("transcript_call", row.get("Transcript", ""))))
                
                # Get all analysis data for this transcript
                mistakes_data = state["all_mistakes"][i] if i < len(state["all_mistakes"]) else {}
                theme_mapping = state["theme_mappings"][i] if i < len(state["theme_mappings"]) else {}
                root_causes = state["root_cause_analyses"][i] if i < len(state["root_cause_analyses"]) else {}
                severity = state["severity_assessments"][i] if i < len(state["severity_assessments"]) else {}
                reasoning = state["root_cause_reasonings"][i] if i < len(state["root_cause_reasonings"]) else {}
                
                # Extract data
                mistakes = mistakes_data.get("mistakes", [])
                mistakes_count = len(mistakes)
                
                themes_present = theme_mapping.get("summary", {}).get("themes_present_in_call", [])
                mistake_themes = [t.get("theme_name", "") for t in themes_present]
                
                root_cause_list = root_causes.get("root_cause_analysis", [])
                primary_root_causes = [
                    rc.get("root_cause", "") 
                    for rc in root_causes.get("root_cause_summary", {}).get("primary_root_causes", [])
                ]
                
                severity_calc = severity.get("severity_calculation", {})
                severity_score = severity_calc.get("final_severity_score", 100)
                severity_rating = severity_calc.get("severity_rating", "Excellent")
                theme_criticality = severity.get("theme_criticality_assessment", [])
                
                reasoning_data = {
                    "root_cause_reasoning": reasoning.get("root_cause_reasoning", []),
                    "overall_assessment": reasoning.get("overall_assessment", {}),
                    "comparative_analysis": reasoning.get("comparative_analysis", {})
                }
                
                final_result = {
                    "transcript_id": transcript_id,
                    "transcript_call": transcript_call,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "mistakes": mistakes,
                    "mistakes_count": mistakes_count,
                    "mistake_themes": mistake_themes,
                    "root_cause": root_cause_list,
                    "primary_root_causes": primary_root_causes,
                    "reasoning_behind_root_cause": reasoning_data,
                    "theme_criticality": theme_criticality,
                    "severity_score": severity_score,
                    "severity_rating": severity_rating
                }
                
                final_results.append(final_result)
            
            state["final_results"] = final_results
            state["processing_phase"] = "complete"
            logger.info(f"Compiled {len(final_results)} final results")
            return state
            
        except Exception as e:
            state["error"] = f"Result compilation failed: {str(e)}"
            logger.error(state["error"])
            return state
    
    # =========================================================================
    # Public Methods
    # =========================================================================
    
    def analyze(self, transcripts_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run the complete transcript analysis workflow.
        
        Args:
            transcripts_df: DataFrame with transcript data. Expected columns:
                - Transcript_ID or transcript_id
                - Agent_ID or agent_id  
                - Agent_Name or agent_name
                - Transcript_Call or transcript_call or Transcript
        
        Returns:
            Dictionary containing:
                - final_results: List of FinalTranscriptAnalysis dicts
                - generated_themes: List of 10 generated themes
                - summary: Overall analysis summary
                - success: Boolean indicating success
                - error: Error message if failed
        """
        logger.info(f"Starting transcript analysis for {len(transcripts_df)} transcripts")
        
        try:
            # Initialize state
            initial_state: TranscriptAnalysisState = {
                "transcripts_df": transcripts_df.to_dict(),
                "all_mistakes": [],
                "aggregated_mistakes": [],
                "generated_themes": [],
                "themes_with_criticality": [],
                "theme_mappings": [],
                "root_cause_analyses": [],
                "severity_assessments": [],
                "root_cause_reasonings": [],
                "final_results": [],
                "current_transcript_idx": 0,
                "total_transcripts": 0,
                "processing_phase": "pending",
                "analysis_date": "",
                "error": None
            }
            
            # Run workflow
            final_state = self.workflow.invoke(initial_state)
            
            if final_state.get("error"):
                return {
                    "final_results": [],
                    "generated_themes": [],
                    "summary": {},
                    "success": False,
                    "error": final_state["error"]
                }
            
            # Calculate summary statistics
            total_mistakes = sum(r.get("mistakes_count", 0) for r in final_state["final_results"])
            avg_severity = sum(r.get("severity_score", 0) for r in final_state["final_results"]) / len(final_state["final_results"]) if final_state["final_results"] else 0
            
            summary = {
                "total_transcripts_analyzed": final_state["total_transcripts"],
                "total_mistakes_identified": total_mistakes,
                "average_mistakes_per_transcript": total_mistakes / final_state["total_transcripts"] if final_state["total_transcripts"] > 0 else 0,
                "average_severity_score": round(avg_severity, 1),
                "analysis_date": final_state["analysis_date"],
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
        
        Args:
            analysis_result: Result from analyze() method
            
        Returns:
            DataFrame with all analysis columns
        """
        if not analysis_result.get("success") or not analysis_result.get("final_results"):
            return pd.DataFrame()
        
        records = []
        for result in analysis_result["final_results"]:
            record = {
                "transcript_id": result.get("transcript_id"),
                "transcript_call": result.get("transcript_call"),
                "agent_id": result.get("agent_id"),
                "agent_name": result.get("agent_name"),
                "mistakes": json.dumps(result.get("mistakes", [])),
                "mistakes_count": result.get("mistakes_count", 0),
                "mistake_themes": "; ".join(result.get("mistake_themes", [])),
                "root_cause": json.dumps(result.get("root_cause", [])),
                "primary_root_causes": "; ".join(result.get("primary_root_causes", [])),
                "reasoning_behind_root_cause": json.dumps(result.get("reasoning_behind_root_cause", {})),
                "theme_criticality": json.dumps(result.get("theme_criticality", [])),
                "severity_score": result.get("severity_score", 100),
                "severity_rating": result.get("severity_rating", "Excellent")
            }
            records.append(record)
        
        return pd.DataFrame(records)
