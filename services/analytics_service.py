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
    theme: str  # Theme category
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
    
    # SOP Elements mapping - using "Did not..." descriptions as keys for matching
    # Format: description -> {"short_name": short name, "theme": theme}
    SOP_ELEMENTS = {
        # CALL OPENING & IDENTITY VERIFICATION (5 elements)
        "Did not ask if caller has policy number upfront using suggested wording": {"short_name": "Policy number inquiry", "theme": "CALL OPENING & IDENTITY VERIFICATION"},
        "Did not verify if caller is policyholder/spouse/authorized person": {"short_name": "Caller authorization verification", "theme": "CALL OPENING & IDENTITY VERIFICATION"},
        "Did not set clear explanation of FNOL process using suggested wording": {"short_name": "FNOL process explanation", "theme": "CALL OPENING & IDENTITY VERIFICATION"},
        "Did not explain call recording/monitoring purpose": {"short_name": "Call recording disclosure", "theme": "CALL OPENING & IDENTITY VERIFICATION"},
        "Did not verify if caller needs immediate medical assistance": {"short_name": "Medical assistance check", "theme": "CALL OPENING & IDENTITY VERIFICATION"},
        
        # CONTACT INFORMATION VERIFICATION (9 elements)
        "Did not verify/update mailing address": {"short_name": "Mailing address verification", "theme": "CONTACT INFORMATION VERIFICATION"},
        "Did not verify/update phone numbers": {"short_name": "Phone numbers verification", "theme": "CONTACT INFORMATION VERIFICATION"},
        "Did not verify/update email address": {"short_name": "Email address verification", "theme": "CONTACT INFORMATION VERIFICATION"},
        "Did not read back contact information for verification": {"short_name": "Contact info read-back", "theme": "CONTACT INFORMATION VERIFICATION"},
        "Did not verify language preferences": {"short_name": "Language preferences", "theme": "CONTACT INFORMATION VERIFICATION"},
        "Did not verify if caller has different name/address than policy": {"short_name": "Name/address mismatch check", "theme": "CONTACT INFORMATION VERIFICATION"},
        "Did not identify main contact for claim": {"short_name": "Main contact identification", "theme": "CONTACT INFORMATION VERIFICATION"},
        "Did not verify/update notification preferences": {"short_name": "Notification preferences", "theme": "CONTACT INFORMATION VERIFICATION"},
        "Did not verify/update texting program preferences": {"short_name": "Texting program preferences", "theme": "CONTACT INFORMATION VERIFICATION"},
        
        # LOSS DETAILS GATHERING (7 elements)
        "Did not verify if loss date/time was approximate": {"short_name": "Loss date/time approximation", "theme": "LOSS DETAILS GATHERING"},
        "Did not ask for purpose of trip": {"short_name": "Trip purpose inquiry", "theme": "LOSS DETAILS GATHERING"},
        "Did not gather complete loss location details (cross streets, mile markers, location type)": {"short_name": "Complete loss location details", "theme": "LOSS DETAILS GATHERING"},
        "Did not ask about weather conditions": {"short_name": "Weather conditions inquiry", "theme": "LOSS DETAILS GATHERING"},
        "Did not ask about witnesses": {"short_name": "Witness inquiry", "theme": "LOSS DETAILS GATHERING"},
        "Did not ask about property damage": {"short_name": "Property damage inquiry", "theme": "LOSS DETAILS GATHERING"},
        "Did not create proper running notes": {"short_name": "Running notes documentation", "theme": "LOSS DETAILS GATHERING"},
        
        # VEHICLE INFORMATION (8 elements)
        "Did not verify vehicle ownership/policy listing": {"short_name": "Vehicle ownership verification", "theme": "VEHICLE INFORMATION"},
        "Did not gather complete vehicle details (style, color, VIN, license plate, state)": {"short_name": "Complete vehicle details", "theme": "VEHICLE INFORMATION"},
        "Did not ask for odometer reading": {"short_name": "Odometer reading", "theme": "VEHICLE INFORMATION"},
        "Did not ask if vehicle was stolen": {"short_name": "Vehicle theft inquiry", "theme": "VEHICLE INFORMATION"},
        "Did not ask about vehicle recovery condition (for stolen vehicles)": {"short_name": "Stolen vehicle recovery condition", "theme": "VEHICLE INFORMATION"},
        "Did not ask if vehicle was parked/unoccupied": {"short_name": "Parked/unoccupied status", "theme": "VEHICLE INFORMATION"},
        "Did not ask about anti-theft devices": {"short_name": "Anti-theft devices inquiry", "theme": "VEHICLE INFORMATION"},
        "Did not ask if vehicle was locked": {"short_name": "Vehicle locked status", "theme": "VEHICLE INFORMATION"},
        
        # DAMAGE ASSESSMENT (8 elements)
        "Did not properly document point of first impact": {"short_name": "Point of first impact", "theme": "DAMAGE ASSESSMENT"},
        "Did not properly document all damaged areas": {"short_name": "All damaged areas documentation", "theme": "DAMAGE ASSESSMENT"},
        "Did not ask about airbag deployment": {"short_name": "Airbag deployment inquiry", "theme": "DAMAGE ASSESSMENT"},
        "Did not verify vehicle drivability": {"short_name": "Vehicle drivability verification", "theme": "DAMAGE ASSESSMENT"},
        "Did not ask if vehicle starts (for non-drivable vehicles)": {"short_name": "Vehicle starts inquiry", "theme": "DAMAGE ASSESSMENT"},
        "Did not ask about equipment failure": {"short_name": "Equipment failure inquiry", "theme": "DAMAGE ASSESSMENT"},
        "Did not document interior damage": {"short_name": "Interior damage documentation", "theme": "DAMAGE ASSESSMENT"},
        "Did not document personal effects damage": {"short_name": "Personal effects damage", "theme": "DAMAGE ASSESSMENT"},
        
        # INJURY & SAFETY (5 elements)
        "Did not ask about injuries for all parties": {"short_name": "Injuries for all parties", "theme": "INJURY & SAFETY"},
        "Did not verify intention to seek medical treatment": {"short_name": "Medical treatment intention", "theme": "INJURY & SAFETY"},
        "Did not ask about number of passengers": {"short_name": "Number of passengers", "theme": "INJURY & SAFETY"},
        "Did not ask about child car seat (especially for California claims)": {"short_name": "Child car seat inquiry", "theme": "INJURY & SAFETY"},
        "Did not gather passenger contact information": {"short_name": "Passenger contact information", "theme": "INJURY & SAFETY"},
        
        # INCIDENT DOCUMENTATION (4 elements)
        "Did not ask about police notification/report": {"short_name": "Police notification/report", "theme": "INCIDENT DOCUMENTATION"},
        "Did not ask about citations/tickets": {"short_name": "Citations/tickets inquiry", "theme": "INCIDENT DOCUMENTATION"},
        "Did not gather other party's insurance carrier information": {"short_name": "Other party insurance info", "theme": "INCIDENT DOCUMENTATION"},
        "Did not ask about special claim permissions (employee/sensitive)": {"short_name": "Special claim permissions", "theme": "INCIDENT DOCUMENTATION"},
        
        # SERVICES OFFERING (7 elements)
        "Did not offer accident scene towing": {"short_name": "Accident scene towing offer", "theme": "SERVICES OFFERING"},
        "Did not offer Auto Repair Network (OYSARN)": {"short_name": "Auto Repair Network offer", "theme": "SERVICES OFFERING"},
        "Did not offer Drive-In services": {"short_name": "Drive-In services offer", "theme": "SERVICES OFFERING"},
        "Did not offer Virtual Appraisal": {"short_name": "Virtual Appraisal offer", "theme": "SERVICES OFFERING"},
        "Did not offer rental car services": {"short_name": "Rental car services offer", "theme": "SERVICES OFFERING"},
        "Did not offer Auto Glass services": {"short_name": "Auto Glass services offer", "theme": "SERVICES OFFERING"},
        "Did not explain services in proper sequence": {"short_name": "Services sequence explanation", "theme": "SERVICES OFFERING"},
        
        # CLAIM PROCESSING (6 elements)
        "Did not explain payment preferences/options": {"short_name": "Payment preferences explanation", "theme": "CLAIM PROCESSING"},
        "Did not share deductible information": {"short_name": "Deductible information sharing", "theme": "CLAIM PROCESSING"},
        "Did not explain 'Track Your Claim' functionality": {"short_name": "Track Your Claim explanation", "theme": "CLAIM PROCESSING"},
        "Did not explain next steps and timeline": {"short_name": "Next steps and timeline", "theme": "CLAIM PROCESSING"},
        "Did not ask if caller has documents/photos to upload": {"short_name": "Documents/photos upload inquiry", "theme": "CLAIM PROCESSING"},
        "Did not verify if warm transfer is needed/eligible": {"short_name": "Warm transfer eligibility", "theme": "CLAIM PROCESSING"},
        
        # CALL CONCLUSION (2 elements)
        "Did not provide claim number": {"short_name": "Claim number provision", "theme": "CALL CONCLUSION"},
        "Did not ask if caller wants to write down claim information": {"short_name": "Claim info write-down offer", "theme": "CALL CONCLUSION"}
    }
    
    # Theme list for categorization
    THEMES = [
        "CALL OPENING & IDENTITY VERIFICATION",
        "CONTACT INFORMATION VERIFICATION",
        "LOSS DETAILS GATHERING",
        "VEHICLE INFORMATION",
        "DAMAGE ASSESSMENT",
        "INJURY & SAFETY",
        "INCIDENT DOCUMENTATION",
        "SERVICES OFFERING",
        "CLAIM PROCESSING",
        "CALL CONCLUSION"
    ]
    
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
                
                # Parse missed points - match against "Did not..." descriptions
                for element_desc, element_info in self.SOP_ELEMENTS.items():
                    # Check if the element description appears in the missed points
                    if element_desc.lower() in missed_points.lower():
                        element_counter[element_desc] += 1
                        if element_desc not in element_agents:
                            element_agents[element_desc] = set()
                        element_agents[element_desc].add(agent)
            
            # Create top missed elements list
            total = state["total_transcripts"]
            top_missed = []
            
            for element_desc, count in element_counter.most_common(15):  # Top 15 for more coverage
                percentage = (count / total * 100) if total > 0 else 0
                severity = "High" if percentage > 30 else "Medium" if percentage > 15 else "Low"
                element_info = self.SOP_ELEMENTS.get(element_desc, {"short_name": element_desc, "theme": "Unknown"})
                
                top_missed.append({
                    "element_id": element_desc[:50] + "..." if len(element_desc) > 50 else element_desc,  # Truncate for display
                    "element_name": element_desc,
                    "theme": element_info["theme"],
                    "miss_count": count,
                    "miss_percentage": round(percentage, 1),
                    "affected_agents": list(element_agents.get(element_desc, [])),
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
                    missed_points = str(row.get("Missed_Points", "")).lower()
                    for element_desc in self.SOP_ELEMENTS.keys():
                        if element_desc.lower() in missed_points:
                            agent_missed_elements[element_desc] += 1
                
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
                    "area": f"{top_element['theme']}: {top_element['element_name']}",
                    "suggestion": f"Focus training on '{top_element['element_name']}' ({top_element['theme']}) - missed in {top_element['miss_percentage']}% of calls",
                    "expected_impact": "Could improve overall SOP compliance by 10-15%"
                })
                
                # Add theme-level insight if multiple elements from same theme are missed
                theme_counter = Counter()
                for elem in top_missed:
                    theme_counter[elem.get("theme", "Unknown")] += 1
                
                most_problematic_theme = theme_counter.most_common(1)
                if most_problematic_theme and most_problematic_theme[0][1] > 1:
                    theme_name = most_problematic_theme[0][0]
                    theme_count = most_problematic_theme[0][1]
                    suggestions.append({
                        "target": "Team",
                        "priority": "High",
                        "area": theme_name,
                        "suggestion": f"Theme '{theme_name}' has {theme_count} elements frequently missed - consider comprehensive training module",
                        "expected_impact": "Address multiple compliance gaps with targeted theme training"
                    })
            
            # Agent-specific suggestions for bottom performers
            bottom_performers = [a for a in agent_rankings if a["performance_grade"] in ["D", "F"]]
            
            for agent in bottom_performers[:3]:  # Top 3 worst performers
                if agent["most_missed_elements"]:
                    missed_names = [
                        self.SOP_ELEMENTS.get(e, {"short_name": e})["short_name"] 
                        for e in agent["most_missed_elements"]
                    ]
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
            
            # Calculate theme-level statistics
            theme_counter = Counter()
            for elem in state["top_missed_elements"]:
                theme_counter[elem.get("theme", "Unknown")] += elem.get("miss_count", 0)
            
            # Prepare summary data for LLM
            summary = {
                "total_transcripts": state["total_transcripts"],
                "overall_compliance_rate": state["overall_compliance_rate"],
                "top_missed_elements": state["top_missed_elements"][:7],
                "theme_breakdown": dict(theme_counter.most_common(5)),
                "agent_count": len(state["agent_rankings"]),
                "bottom_performers": [a for a in state["agent_rankings"] if a["performance_grade"] in ["D", "F"]],
                "top_performers": [a for a in state["agent_rankings"] if a["performance_grade"] == "A"]
            }
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert insurance call center analyst. Analyze the FNOL (First Notice of Loss) 
                transcript analysis data and provide actionable insights.
                
                The SOP elements are organized into 10 themes:
                1. CALL OPENING & IDENTITY VERIFICATION
                2. CONTACT INFORMATION VERIFICATION
                3. LOSS DETAILS GATHERING
                4. VEHICLE INFORMATION
                5. DAMAGE ASSESSMENT
                6. INJURY & SAFETY
                7. INCIDENT DOCUMENTATION
                8. SERVICES OFFERING
                9. CLAIM PROCESSING
                10. CALL CONCLUSION
                
                Be specific, data-driven, and focus on:
                1. Key patterns in SOP compliance issues by theme
                2. Agent performance trends
                3. Priority areas for training (theme-based)
                4. Quick wins for improvement
                
                Keep the response concise but impactful (max 350 words)."""),
                ("human", """Here's the analysis summary:

Total Transcripts Analyzed: {total_transcripts}
Overall Sequence Compliance Rate: {overall_compliance_rate}%

Top Missed SOP Elements (with Theme):
{top_missed}

Theme-Level Miss Summary:
{theme_summary}

Number of Agents: {agent_count}
Top Performers (Grade A): {top_performers}
Bottom Performers (Grade D/F): {bottom_performers}

Provide executive-level insights and theme-based recommendations.""")
            ])
            
            # Format the data
            top_missed_str = "\n".join([
                f"- [{e['element_id']}] {e['element_name']} ({e['theme']}): {e['miss_percentage']}% miss rate ({e['severity']} severity)"
                for e in summary["top_missed_elements"]
            ])
            
            theme_summary_str = "\n".join([
                f"- {theme}: {count} total misses"
                for theme, count in summary["theme_breakdown"].items()
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
                "theme_summary": theme_summary_str,
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