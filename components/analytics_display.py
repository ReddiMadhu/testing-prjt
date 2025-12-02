"""
Analytics Display Component
Renders charts and insights from the analytics service
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List

from services.analytics_service import (
    AnalyticsResult,
    SOPElementAnalysis,
    AgentPerformance,
    ImprovementSuggestion
)


def render_analytics_header():
    """Render the analytics section header"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    ">
        <h2 style="color: #E85D04; margin: 0;">📊 Advanced Analytics Dashboard</h2>
        <p style="color: #FFFFFF; margin: 0.5rem 0 0 0; opacity: 0.9;">
            AI-powered insights on SOP compliance, agent performance, and improvement opportunities
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_overall_metrics(result: AnalyticsResult):
    """Render overall metrics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 Transcripts Analyzed",
            value=result.total_transcripts_analyzed
        )
    
    with col2:
        compliance_delta = result.overall_compliance_rate - 70  # 70% as baseline
        st.metric(
            label="✅ Sequence Compliance",
            value=f"{result.overall_compliance_rate}%",
            delta=f"{compliance_delta:+.1f}% vs target" if compliance_delta != 0 else None,
            delta_color="normal" if compliance_delta >= 0 else "inverse"
        )
    
    with col3:
        st.metric(
            label="👥 Agents Analyzed",
            value=len(result.agent_rankings)
        )
    
    with col4:
        poor_performers = len(result.worst_performers)
        st.metric(
            label="⚠️ Needs Improvement",
            value=poor_performers,
            delta=f"{poor_performers} agents" if poor_performers > 0 else None,
            delta_color="inverse" if poor_performers > 0 else "off"
        )


def render_top_missed_elements(elements: List[SOPElementAnalysis]):
    """Render top missed SOP elements chart"""
    st.markdown("### 🎯 Top Missed SOP Elements")
    
    if not elements:
        st.info("No missed elements data available")
        return
    
    # Create DataFrame for chart
    df = pd.DataFrame([
        {
            "Element": f"{e.element_id}: {e.element_name[:30]}...",
            "Full Name": e.element_name,
            "Miss Count": e.miss_count,
            "Miss Rate (%)": e.miss_percentage,
            "Severity": e.severity,
            "Affected Agents": len(e.affected_agents)
        }
        for e in elements
    ])
    
    # Create horizontal bar chart
    fig = px.bar(
        df,
        y="Element",
        x="Miss Rate (%)",
        orientation="h",
        color="Severity",
        color_discrete_map={"High": "#E53935", "Medium": "#FB8C00", "Low": "#43A047"},
        hover_data=["Full Name", "Miss Count", "Affected Agents"],
        title=""
    )
    
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed table
    with st.expander("📋 View Detailed Breakdown"):
        for elem in elements:
            severity_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[elem.severity]
            st.markdown(f"""
            **{severity_color} {elem.element_id}: {elem.element_name}**
            - Miss Rate: {elem.miss_percentage}% ({elem.miss_count} times)
            - Affected Agents: {', '.join(elem.affected_agents[:5])}{'...' if len(elem.affected_agents) > 5 else ''}
            """)


def render_agent_rankings(rankings: List[AgentPerformance]):
    """Render agent performance rankings"""
    st.markdown("### 🏆 Agent Performance Rankings")
    
    if not rankings:
        st.info("No agent data available")
        return
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            "Rank": a.rank,
            "Agent": a.agent_name,
            "Grade": a.performance_grade,
            "Transcripts": a.total_transcripts,
            "Avg Missed": a.avg_missed_per_transcript,
            "Sequence Compliance": f"{a.sequence_compliance_rate}%",
            "Total Missed": a.total_missed_points
        }
        for a in rankings
    ])
    
    # Grade color mapping
    grade_colors = {"A": "#4CAF50", "B": "#8BC34A", "C": "#FFC107", "D": "#FF9800", "F": "#F44336"}
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Top performers
        st.markdown("#### ⭐ Top Performers")
        top_performers = [a for a in rankings if a.performance_grade in ["A", "B"]][:5]
        
        if top_performers:
            for agent in top_performers:
                grade_emoji = {"A": "🥇", "B": "🥈"}[agent.performance_grade]
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #E8F5E9 0%, #FFFFFF 100%);
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    margin-bottom: 0.5rem;
                    border-left: 4px solid #4CAF50;
                ">
                    <span style="font-weight: 600;">{grade_emoji} #{agent.rank} {agent.agent_name}</span>
                    <span style="float: right; color: #4CAF50;">Grade {agent.performance_grade}</span>
                    <br><small style="color: #666;">
                        {agent.sequence_compliance_rate}% compliance | Avg {agent.avg_missed_per_transcript} missed
                    </small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No top performers found")
    
    with col2:
        # Needs improvement
        st.markdown("#### ⚠️ Needs Improvement")
        bottom_performers = [a for a in rankings if a.performance_grade in ["D", "F"]][:5]
        
        if bottom_performers:
            for agent in bottom_performers:
                grade_emoji = {"D": "⚠️", "F": "🚨"}[agent.performance_grade]
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #FFEBEE 0%, #FFFFFF 100%);
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    margin-bottom: 0.5rem;
                    border-left: 4px solid #F44336;
                ">
                    <span style="font-weight: 600;">{grade_emoji} #{agent.rank} {agent.agent_name}</span>
                    <span style="float: right; color: #F44336;">Grade {agent.performance_grade}</span>
                    <br><small style="color: #666;">
                        {agent.sequence_compliance_rate}% compliance | Avg {agent.avg_missed_per_transcript} missed
                    </small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No agents need immediate improvement!")
    
    # Full ranking table
    with st.expander("📊 View Full Rankings Table"):
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Grade": st.column_config.TextColumn("Grade", width="small"),
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "Avg Missed": st.column_config.NumberColumn("Avg Missed", format="%.2f")
            }
        )


def render_agent_comparison_chart(rankings: List[AgentPerformance]):
    """Render agent comparison scatter plot"""
    st.markdown("### 📈 Agent Performance Comparison")
    
    if not rankings or len(rankings) < 2:
        st.info("Need at least 2 agents for comparison")
        return
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            "Agent": a.agent_name,
            "Avg Missed Points": a.avg_missed_per_transcript,
            "Sequence Compliance (%)": a.sequence_compliance_rate,
            "Total Transcripts": a.total_transcripts,
            "Grade": a.performance_grade
        }
        for a in rankings
    ])
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x="Avg Missed Points",
        y="Sequence Compliance (%)",
        size="Total Transcripts",
        color="Grade",
        color_discrete_map={"A": "#4CAF50", "B": "#8BC34A", "C": "#FFC107", "D": "#FF9800", "F": "#F44336"},
        hover_name="Agent",
        title="",
        size_max=50
    )
    
    # Add quadrant lines
    fig.add_hline(y=70, line_dash="dash", line_color="gray", annotation_text="Target: 70%")
    fig.add_vline(x=2, line_dash="dash", line_color="gray", annotation_text="Target: <2")
    
    fig.update_layout(
        height=450,
        xaxis_title="Average Missed Points (Lower is Better)",
        yaxis_title="Sequence Compliance % (Higher is Better)",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("💡 **Goal:** Move agents to the upper-left quadrant (high compliance, low missed points)")


def render_improvement_suggestions(suggestions: List[ImprovementSuggestion]):
    """Render improvement suggestions"""
    st.markdown("### 💡 Improvement Recommendations")
    
    if not suggestions:
        st.success("No critical improvements needed at this time!")
        return
    
    # Group by priority
    high_priority = [s for s in suggestions if s.priority == "High"]
    medium_priority = [s for s in suggestions if s.priority == "Medium"]
    low_priority = [s for s in suggestions if s.priority == "Low"]
    
    if high_priority:
        st.markdown("#### 🔴 High Priority")
        for sugg in high_priority:
            st.markdown(f"""
            <div style="
                background: #FFEBEE;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 0.75rem;
                border-left: 4px solid #E53935;
            ">
                <strong>Target:</strong> {sugg.target} | <strong>Area:</strong> {sugg.area}
                <p style="margin: 0.5rem 0; color: #333;">{sugg.suggestion}</p>
                <small style="color: #666;">📈 Expected Impact: {sugg.expected_impact}</small>
            </div>
            """, unsafe_allow_html=True)
    
    if medium_priority:
        st.markdown("#### 🟡 Medium Priority")
        for sugg in medium_priority:
            st.markdown(f"""
            <div style="
                background: #FFF3E0;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 0.75rem;
                border-left: 4px solid #FB8C00;
            ">
                <strong>Target:</strong> {sugg.target} | <strong>Area:</strong> {sugg.area}
                <p style="margin: 0.5rem 0; color: #333;">{sugg.suggestion}</p>
                <small style="color: #666;">📈 Expected Impact: {sugg.expected_impact}</small>
            </div>
            """, unsafe_allow_html=True)
    
    if low_priority:
        with st.expander("🟢 Low Priority Suggestions"):
            for sugg in low_priority:
                st.markdown(f"**{sugg.target}** - {sugg.area}: {sugg.suggestion}")


def render_llm_insights(insights: str):
    """Render LLM-generated insights"""
    st.markdown("### 🤖 AI-Powered Insights")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #E3F2FD 0%, #F3E5F5 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #7B1FA2;
    ">
        {insights}
    </div>
    """, unsafe_allow_html=True)


def render_analytics_dashboard(result: AnalyticsResult):
    """Render the complete analytics dashboard"""
    
    if not result.success:
        st.error(f"❌ Analytics Error: {result.error_message}")
        return
    
    # Header
    render_analytics_header()
    
    # Overall metrics
    render_overall_metrics(result)
    
    st.markdown("---")
    
    # Two column layout for main charts
    col1, col2 = st.columns(2)
    
    with col1:
        render_top_missed_elements(result.top_missed_elements)
    
    with col2:
        render_agent_rankings(result.agent_rankings)
    
    st.markdown("---")
    
    # Agent comparison chart
    render_agent_comparison_chart(result.agent_rankings)
    
    st.markdown("---")
    
    # Two column layout for suggestions and insights
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_improvement_suggestions(result.improvement_suggestions)
    
    with col2:
        render_llm_insights(result.llm_insights)