"""
Analytics Service using LangGraph for Further Analysis
Provides insights on SOP compliance, agent performance, and improvement suggestions
"""

import os
import time
import logging
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass
from collections import Counter
import pandas as pd

from langchain_google_genai import ChatGoogleGenerativeAI

# Configure logging
logger = logging.getLogger(__name__)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END

from config.settings import Settings

settings = Settings()


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SOPElementAnalysis:
    """Analysis of a single SOP element"""
    element_id: str
    element_name: str
    miss_count: int
    miss_percentage: float
    affected_agents: List[str]
    severity: str  # High, Medium, Low


@dataclass
class AgentPerformance:
    """Performance metrics for an agent"""
    agent_name: str
    total_transcripts: int
    total_missed_points: int
    avg_missed_per_transcript: float
    sequence_compliance_rate: float
    most_missed_elements: List[str]
    performance_grade: str  # A, B, C, D, F
    rank: int


@dataclass
class ImprovementSuggestion:
    """Improvement suggestion for an agent or team"""
    target: str  # Agent name or "Team"
    priority: str  # High, Medium, Low
    area: str
    suggestion: str
    expected_impact: str


@dataclass
class AnalyticsResult:
    """Complete analytics result"""
    top_missed_elements: List[SOPElementAnalysis]
    agent_rankings: List[AgentPerformance]
    worst_performers: List[AgentPerformance]
    improvement_suggestions: List[ImprovementSuggestion]
    overall_compliance_rate: float
    total_transcripts_analyzed: int
    llm_insights: str
    success: bool
    error_message: Optional[str] = None


# ============================================================================
# LangGraph State
# ============================================================================

class AnalyticsState(TypedDict):
    """State for the analytics workflow"""
    # Input data
    processed_df: Dict[str, Any]  # DataFrame as dict
    
    # Computed metrics
    missed_elements_counter: Dict[str, int]
    agent_metrics: Dict[str, Dict[str, Any]]
    sequence_compliance: Dict[str, float]
    
    # Analysis results
    top_missed_elements: List[Dict[str, Any]]
    agent_rankings: List[Dict[str, Any]]
    improvement_suggestions: List[Dict[str, Any]]
    
    # LLM insights
    llm_insights: str
    
    # Metadata
    total_transcripts: int
    overall_compliance_rate: float
    error: Optional[str]


# ============================================================================
# Analytics Service
# ============================================================================

class AnalyticsService:
    """Service for analyzing processed transcript data using LangGraph"""
    
    # SOP Element ID to Name mapping
    SOP_ELEMENTS = {
        "ID-1": "Warm Greeting & Brand Identification",
        "ID-2": "Caller's Full Name",
        "ID-3": "Policy Number or Last 4 SSN",
        "ID-4": "Callback Number Confirmation",
        "ID-5": "Incident Date & Time",
        "ID-6": "Incident Location",
        "ID-7": "Vehicle/Property Involved",
        "ID-8": "Incident Description",
        "ID-9": "Injuries or Damages",
        "ID-10": "Third-Party Involvement",
        "ID-11": "Police Report Filed",
        "ID-12": "Claim Summary & Next Steps"
    }
    
    def __init__(self):
        """Initialize the analytics service"""
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google API key not found")
        
        # Rate limiting configuration
        self._last_request_time = 0
        self._min_request_interval = 2.0  # Minimum seconds between API calls
        self._sleep_before_llm = 1.5  # Sleep before LLM insight generation
        
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
            logger.info(f"Analytics rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for analytics"""
        workflow = StateGraph(AnalyticsState)
        
        # Add nodes
        workflow.add_node("parse_data", self._parse_data_node)
        workflow.add_node("analyze_missed_elements", self._analyze_missed_elements_node)
        workflow.add_node("calculate_agent_metrics", self._calculate_agent_metrics_node)
        workflow.add_node("rank_agents", self._rank_agents_node)
        workflow.add_node("generate_improvements", self._generate_improvements_node)
        workflow.add_node("generate_llm_insights", self._generate_llm_insights_node)
        
        # Define edges
        workflow.set_entry_point("parse_data")
        workflow.add_edge("parse_data", "analyze_missed_elements")
        workflow.add_edge("analyze_missed_elements", "calculate_agent_metrics")
        workflow.add_edge("calculate_agent_metrics", "rank_agents")
        workflow.add_edge("rank_agents", "generate_improvements")
        workflow.add_edge("generate_improvements", "generate_llm_insights")
        workflow.add_edge("generate_llm_insights", END)
        
        return workflow.compile()
    
    def _parse_data_node(self, state: AnalyticsState) -> AnalyticsState:
        """Parse and prepare the data for analysis"""
        try:
            df_dict = state["processed_df"]
            df = pd.DataFrame(df_dict)
            
            state["total_transcripts"] = len(df)
            
            # Initialize counters
            state["missed_elements_counter"] = {}
            state["agent_metrics"] = {}
            state["sequence_compliance"] = {}
            
            return state
        except Exception as e:
            state["error"] = f"Error parsing data: {str(e)}"
            return state
    
    def _analyze_missed_elements_node(self, state: AnalyticsState) -> AnalyticsState:
        """Analyze which SOP elements are missed most often"""
        try:
            df = pd.DataFrame(state["processed_df"])
            
            # Count missed elements
            element_counter = Counter()
            element_agents = {}  # Track which agents missed which elements
            
            for _, row in df.iterrows():
                missed_points = str(row.get("Missed_Points", ""))
                agent = str(row.get("Agent_Name", "Unknown"))
                
                # Parse missed points - look for IDs like [ID-1], [ID-2], etc.
                for element_id in self.SOP_ELEMENTS.keys():
                    if element_id in missed_points or element_id.replace("-", "") in missed_points:
                        element_counter[element_id] += 1
                        if element_id not in element_agents:
                            element_agents[element_id] = set()
                        element_agents[element_id].add(agent)
                
                # Also check for element names
                for element_id, element_name in self.SOP_ELEMENTS.items():
                    if element_name.lower() in missed_points.lower():
                        element_counter[element_id] += 1
                        if element_id not in element_agents:
                            element_agents[element_id] = set()
                        element_agents[element_id].add(agent)
            
            # Create top missed elements list
            total = state["total_transcripts"]
            top_missed = []
            
            for element_id, count in element_counter.most_common(10):
                percentage = (count / total * 100) if total > 0 else 0
                severity = "High" if percentage > 30 else "Medium" if percentage > 15 else "Low"
                
                top_missed.append({
                    "element_id": element_id,
                    "element_name": self.SOP_ELEMENTS.get(element_id, element_id),
                    "miss_count": count,
                    "miss_percentage": round(percentage, 1),
                    "affected_agents": list(element_agents.get(element_id, [])),
                    "severity": severity
                })
            
            state["top_missed_elements"] = top_missed
            state["missed_elements_counter"] = dict(element_counter)
            
            return state
        except Exception as e:
            state["error"] = f"Error analyzing missed elements: {str(e)}"
            return state
    
    def _calculate_agent_metrics_node(self, state: AnalyticsState) -> AnalyticsState:
        """Calculate performance metrics for each agent"""
        try:
            df = pd.DataFrame(state["processed_df"])
            
            agent_metrics = {}
            
            for agent in df["Agent_Name"].unique():
                agent_df = df[df["Agent_Name"] == agent]
                
                total_transcripts = len(agent_df)
                total_missed = agent_df["Num_Missed"].sum()
                avg_missed = total_missed / total_transcripts if total_transcripts > 0 else 0
                
                # Calculate sequence compliance rate
                sequence_yes = len(agent_df[agent_df["Sequence_Followed"] == "Yes"])
                sequence_rate = (sequence_yes / total_transcripts * 100) if total_transcripts > 0 else 0
                
                # Find most missed elements for this agent
                agent_missed_elements = Counter()
                for _, row in agent_df.iterrows():
                    missed_points = str(row.get("Missed_Points", ""))
                    for element_id in self.SOP_ELEMENTS.keys():
                        if element_id in missed_points:
                            agent_missed_elements[element_id] += 1
                
                most_missed = [elem for elem, _ in agent_missed_elements.most_common(3)]
                
                agent_metrics[agent] = {
                    "total_transcripts": total_transcripts,
                    "total_missed_points": int(total_missed),
                    "avg_missed_per_transcript": round(avg_missed, 2),
                    "sequence_compliance_rate": round(sequence_rate, 1),
                    "most_missed_elements": most_missed
                }
            
            state["agent_metrics"] = agent_metrics
            
            # Calculate overall compliance rate
            total_sequence_yes = len(df[df["Sequence_Followed"] == "Yes"])
            state["overall_compliance_rate"] = round(
                (total_sequence_yes / len(df) * 100) if len(df) > 0 else 0, 1
            )
            
            return state
        except Exception as e:
            state["error"] = f"Error calculating agent metrics: {str(e)}"
            return state
    
    def _rank_agents_node(self, state: AnalyticsState) -> AnalyticsState:
        """Rank agents by performance"""
        try:
            agent_metrics = state["agent_metrics"]
            
            # Create ranking based on avg missed (lower is better) and sequence compliance (higher is better)
            rankings = []
            
            for agent, metrics in agent_metrics.items():
                # Performance score: lower missed + higher compliance = better
                # Score = sequence_compliance - (avg_missed * 10)
                score = metrics["sequence_compliance_rate"] - (metrics["avg_missed_per_transcript"] * 10)
                
                # Determine grade
                if score >= 80:
                    grade = "A"
                elif score >= 60:
                    grade = "B"
                elif score >= 40:
                    grade = "C"
                elif score >= 20:
                    grade = "D"
                else:
                    grade = "F"
                
                rankings.append({
                    "agent_name": agent,
                    "total_transcripts": metrics["total_transcripts"],
                    "total_missed_points": metrics["total_missed_points"],
                    "avg_missed_per_transcript": metrics["avg_missed_per_transcript"],
                    "sequence_compliance_rate": metrics["sequence_compliance_rate"],
                    "most_missed_elements": metrics["most_missed_elements"],
                    "performance_grade": grade,
                    "score": score
                })
            
            # Sort by score (descending - best first)
            rankings.sort(key=lambda x: x["score"], reverse=True)
            
            # Add rank
            for i, agent in enumerate(rankings):
                agent["rank"] = i + 1
            
            state["agent_rankings"] = rankings
            
            return state
        except Exception as e:
            state["error"] = f"Error ranking agents: {str(e)}"
            return state
    
    def _generate_improvements_node(self, state: AnalyticsState) -> AnalyticsState:
        """Generate improvement suggestions"""
        try:
            suggestions = []
            agent_rankings = state["agent_rankings"]
            top_missed = state["top_missed_elements"]
            
            # Team-level suggestions based on top missed elements
            if top_missed:
                top_element = top_missed[0]
                suggestions.append({
                    "target": "Team",
                    "priority": "High",
                    "area": top_element["element_name"],
                    "suggestion": f"Focus training on '{top_element['element_name']}' - missed in {top_element['miss_percentage']}% of calls",
                    "expected_impact": "Could improve overall SOP compliance by 10-15%"
                })
            
            # Agent-specific suggestions for bottom performers
            bottom_performers = [a for a in agent_rankings if a["performance_grade"] in ["D", "F"]]
            
            for agent in bottom_performers[:3]:  # Top 3 worst performers
                if agent["most_missed_elements"]:
                    missed_names = [self.SOP_ELEMENTS.get(e, e) for e in agent["most_missed_elements"]]
                    suggestions.append({
                        "target": agent["agent_name"],
                        "priority": "High" if agent["performance_grade"] == "F" else "Medium",
                        "area": "SOP Compliance",
                        "suggestion": f"Needs coaching on: {', '.join(missed_names[:2])}",
                        "expected_impact": f"Could reduce missed points from {agent['avg_missed_per_transcript']:.1f} to under 2.0"
                    })
                
                if agent["sequence_compliance_rate"] < 50:
                    suggestions.append({
                        "target": agent["agent_name"],
                        "priority": "High",
                        "area": "Call Flow",
                        "suggestion": "Review proper FNOL call sequence - only {:.0f}% compliance".format(
                            agent["sequence_compliance_rate"]
                        ),
                        "expected_impact": "Improved customer experience and data quality"
                    })
            
            state["improvement_suggestions"] = suggestions
            
            return state
        except Exception as e:
            state["error"] = f"Error generating improvements: {str(e)}"
            return state
    
    def _generate_llm_insights_node(self, state: AnalyticsState) -> AnalyticsState:
        """Generate LLM-powered insights and recommendations"""
        try:
            # Apply rate limiting before LLM call
            self._rate_limit()
            
            # Additional sleep to be safe with rate limits
            if self._sleep_before_llm > 0:
                logger.info(f"Sleeping {self._sleep_before_llm}s before LLM insights generation")
                time.sleep(self._sleep_before_llm)
            
            # Prepare summary data for LLM
            summary = {
                "total_transcripts": state["total_transcripts"],
                "overall_compliance_rate": state["overall_compliance_rate"],
                "top_missed_elements": state["top_missed_elements"][:5],
                "agent_count": len(state["agent_rankings"]),
                "bottom_performers": [a for a in state["agent_rankings"] if a["performance_grade"] in ["D", "F"]],
                "top_performers": [a for a in state["agent_rankings"] if a["performance_grade"] == "A"]
            }
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert insurance call center analyst. Analyze the FNOL (First Notice of Loss) 
                transcript analysis data and provide actionable insights.
                
                Be specific, data-driven, and focus on:
                1. Key patterns in SOP compliance issues
                2. Agent performance trends
                3. Priority areas for training
                4. Quick wins for improvement
                
                Keep the response concise but impactful (max 300 words)."""),
                ("human", """Here's the analysis summary:

Total Transcripts Analyzed: {total_transcripts}
Overall Sequence Compliance Rate: {overall_compliance_rate}%

Top Missed SOP Elements:
{top_missed}

Number of Agents: {agent_count}
Top Performers (Grade A): {top_performers}
Bottom Performers (Grade D/F): {bottom_performers}

Provide executive-level insights and recommendations.""")
            ])
            
            # Format the data
            top_missed_str = "\n".join([
                f"- {e['element_name']}: {e['miss_percentage']}% miss rate ({e['severity']} severity)"
                for e in summary["top_missed_elements"]
            ])
            
            top_performers_str = ", ".join([a["agent_name"] for a in summary["top_performers"]]) or "None"
            bottom_performers_str = ", ".join([
                f"{a['agent_name']} (Grade {a['performance_grade']})" 
                for a in summary["bottom_performers"]
            ]) or "None"
            
            chain = prompt | self.llm
            
            response = chain.invoke({
                "total_transcripts": summary["total_transcripts"],
                "overall_compliance_rate": summary["overall_compliance_rate"],
                "top_missed": top_missed_str,
                "agent_count": summary["agent_count"],
                "top_performers": top_performers_str,
                "bottom_performers": bottom_performers_str
            })
            
            state["llm_insights"] = response.content
            
            return state
        except Exception as e:
            state["llm_insights"] = f"Unable to generate AI insights: {str(e)}"
            return state
    
    def analyze(self, processed_df: pd.DataFrame) -> AnalyticsResult:
        """
        Run the complete analytics workflow
        
        Args:
            processed_df: DataFrame with processed transcript analysis results
            
        Returns:
            AnalyticsResult with all insights
        """
        try:
            # Convert DataFrame to dict for state
            initial_state: AnalyticsState = {
                "processed_df": processed_df.to_dict(),
                "missed_elements_counter": {},
                "agent_metrics": {},
                "sequence_compliance": {},
                "top_missed_elements": [],
                "agent_rankings": [],
                "improvement_suggestions": [],
                "llm_insights": "",
                "total_transcripts": 0,
                "overall_compliance_rate": 0.0,
                "error": None
            }
            
            # Run workflow
            final_state = self.workflow.invoke(initial_state)
            
            if final_state.get("error"):
                return AnalyticsResult(
                    top_missed_elements=[],
                    agent_rankings=[],
                    worst_performers=[],
                    improvement_suggestions=[],
                    overall_compliance_rate=0.0,
                    total_transcripts_analyzed=0,
                    llm_insights="",
                    success=False,
                    error_message=final_state["error"]
                )
            
            # Convert to dataclass objects
            top_missed = [
                SOPElementAnalysis(**elem) for elem in final_state["top_missed_elements"]
            ]
            
            agent_rankings = [
                AgentPerformance(**{k: v for k, v in agent.items() if k != "score"})
                for agent in final_state["agent_rankings"]
            ]
            
            worst_performers = [a for a in agent_rankings if a.performance_grade in ["D", "F"]]
            
            improvement_suggestions = [
                ImprovementSuggestion(**sugg) for sugg in final_state["improvement_suggestions"]
            ]
            
            return AnalyticsResult(
                top_missed_elements=top_missed,
                agent_rankings=agent_rankings,
                worst_performers=worst_performers,
                improvement_suggestions=improvement_suggestions,
                overall_compliance_rate=final_state["overall_compliance_rate"],
                total_transcripts_analyzed=final_state["total_transcripts"],
                llm_insights=final_state["llm_insights"],
                success=True
            )
            
        except Exception as e:
            return AnalyticsResult(
                top_missed_elements=[],
                agent_rankings=[],
                worst_performers=[],
                improvement_suggestions=[],
                overall_compliance_rate=0.0,
                total_transcripts_analyzed=0,
                llm_insights="",
                success=False,
                error_message=str(e)
            )