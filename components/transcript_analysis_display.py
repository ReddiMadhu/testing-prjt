"""
Transcript Analysis Dashboard Component
Displays comprehensive results from the LangGraph transcript analysis workflow
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List


def render_transcript_analysis_dashboard(analysis_result: Dict[str, Any]):
    """
    Render the complete transcript analysis dashboard.
    
    Args:
        analysis_result: Result from TranscriptAnalysisService.analyze()
    """
    if not analysis_result.get("success"):
        st.error(f"❌ Analysis failed: {analysis_result.get('error', 'Unknown error')}")
        return
    
    # Header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #E85D04 0%, #D84E00 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    ">
        <h1 style="margin: 0; color: white;">📊 Transcript Quality Analysis</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
            Comprehensive mistake identification, theme analysis, and root cause assessment
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary Metrics
    _render_summary_metrics(analysis_result.get("summary", {}))
    
    st.markdown("---")
    
    # Generated Themes Section
    _render_themes_section(analysis_result.get("generated_themes", []))
    
    st.markdown("---")
    
    # Individual Transcript Results
    _render_transcript_results(analysis_result.get("final_results", []))
    
    st.markdown("---")
    
    # Export Section
    _render_export_section(analysis_result)


def _render_summary_metrics(summary: Dict[str, Any]):
    """Render summary metrics cards"""
    st.markdown("### 📈 Analysis Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Transcripts Analyzed",
            value=summary.get("total_transcripts_analyzed", 0)
        )
    
    with col2:
        st.metric(
            label="Total Mistakes Found",
            value=summary.get("total_mistakes_identified", 0)
        )
    
    with col3:
        avg_mistakes = summary.get("average_mistakes_per_transcript", 0)
        st.metric(
            label="Avg. Mistakes/Transcript",
            value=f"{avg_mistakes:.1f}"
        )
    
    with col4:
        avg_severity = summary.get("average_severity_score", 0)
        color = "green" if avg_severity >= 75 else "orange" if avg_severity >= 50 else "red"
        st.metric(
            label="Avg. Severity Score",
            value=f"{avg_severity:.0f}/100"
        )


def _render_themes_section(themes: List[Dict[str, Any]]):
    """Render the generated themes section"""
    st.markdown("### 🎯 Generated Mistake Themes")
    
    if not themes:
        st.info("No themes were generated from the analysis.")
        return
    
    st.markdown(f"""
    <div style="
        background: #FFF8F0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #E85D04;
        margin-bottom: 1rem;
    ">
        <p style="margin: 0; color: #1A1A2E;">
            <strong>{len(themes)} mistake themes</strong> were identified from analyzing all transcripts.
            These themes represent the most common patterns of agent errors.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display themes in expandable sections
    for theme in themes:
        theme_num = theme.get("theme_number", "?")
        theme_name = theme.get("theme_name", "Unknown Theme")
        definition = theme.get("definition", "")
        examples = theme.get("examples", [])
        frequency = theme.get("frequency_in_dataset", "N/A")
        importance = theme.get("importance", "")
        criticality = theme.get("criticality", "Non-Critical")
        
        # Color based on criticality
        badge_color = "#DC3545" if criticality == "Critical" else "#28A745"
        
        with st.expander(f"Theme {theme_num}: {theme_name}", expanded=False):
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <span style="
                    background: {badge_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 4px;
                    font-size: 0.85rem;
                    font-weight: 600;
                ">{criticality}</span>
                <span style="color: #666; font-size: 0.9rem;">Frequency: {frequency}</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**Definition:** {definition}")
            
            if examples:
                st.markdown("**Examples:**")
                for ex in examples[:3]:
                    st.markdown(f"- {ex}")
            
            if importance:
                st.markdown(f"**Why it matters:** {importance}")


def _render_transcript_results(results: List[Dict[str, Any]]):
    """Render individual transcript analysis results"""
    st.markdown("### 📝 Individual Transcript Analysis")
    
    if not results:
        st.info("No transcript results available.")
        return
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📋 Detailed View", "📊 Table View"])
    
    with tab1:
        _render_detailed_transcript_view(results)
    
    with tab2:
        _render_table_view(results)


def _render_detailed_transcript_view(results: List[Dict[str, Any]]):
    """Render detailed view of each transcript"""
    for i, result in enumerate(results):
        transcript_id = result.get("transcript_id", f"T{i+1}")
        agent_name = result.get("agent_name", "Unknown")
        agent_id = result.get("agent_id", "Unknown")
        mistakes_count = result.get("mistakes_count", 0)
        severity_score = result.get("severity_score", 100)
        severity_rating = result.get("severity_rating", "Excellent")
        
        # Severity color
        if severity_score >= 75:
            severity_color = "#28A745"
        elif severity_score >= 50:
            severity_color = "#FFC107"
        else:
            severity_color = "#DC3545"
        
        with st.expander(
            f"📞 {transcript_id} | Agent: {agent_name} | Mistakes: {mistakes_count} | Score: {severity_score}",
            expanded=False
        ):
            # Header with key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: #f8f9fa; border-radius: 8px;">
                    <p style="margin: 0; color: #666; font-size: 0.8rem;">Transcript ID</p>
                    <p style="margin: 0; font-weight: 600;">{transcript_id}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: #f8f9fa; border-radius: 8px;">
                    <p style="margin: 0; color: #666; font-size: 0.8rem;">Agent</p>
                    <p style="margin: 0; font-weight: 600;">{agent_name}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: #f8f9fa; border-radius: 8px;">
                    <p style="margin: 0; color: #666; font-size: 0.8rem;">Mistakes</p>
                    <p style="margin: 0; font-weight: 600; color: {'#DC3545' if mistakes_count > 3 else '#28A745'};">{mistakes_count}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: #f8f9fa; border-radius: 8px;">
                    <p style="margin: 0; color: #666; font-size: 0.8rem;">Severity</p>
                    <p style="margin: 0; font-weight: 600; color: {severity_color};">{severity_score}/100 ({severity_rating})</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mistakes Section
            mistakes = result.get("mistakes", [])
            if mistakes:
                st.markdown("#### 🚫 Mistakes Identified")
                for mistake in mistakes:
                    st.markdown(f"""
                    <div style="
                        background: #FFF3CD;
                        padding: 0.75rem;
                        border-radius: 8px;
                        margin-bottom: 0.5rem;
                        border-left: 4px solid #FFC107;
                    ">
                        <p style="margin: 0; font-weight: 600;">
                            #{mistake.get('mistake_number', '?')}: {mistake.get('category', 'Unknown Category')}
                        </p>
                        <p style="margin: 0.25rem 0 0 0; color: #333;">
                            {mistake.get('mistake_description', '')}
                        </p>
                        <p style="margin: 0.25rem 0 0 0; color: #666; font-size: 0.85rem;">
                            <em>Impact: {mistake.get('impact', 'Unknown')}</em>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No mistakes identified in this transcript!")
            
            # Themes Section
            mistake_themes = result.get("mistake_themes", [])
            if mistake_themes:
                st.markdown("#### 🎯 Mistake Themes Present")
                theme_tags = " ".join([
                    f'<span style="background: #E85D04; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; margin-right: 0.5rem; font-size: 0.85rem;">{theme}</span>'
                    for theme in mistake_themes
                ])
                st.markdown(theme_tags, unsafe_allow_html=True)
            
            # Root Causes Section
            root_causes = result.get("root_cause", [])
            primary_root_causes = result.get("primary_root_causes", [])
            
            if primary_root_causes:
                st.markdown("#### 🔍 Primary Root Causes")
                for rc in primary_root_causes:
                    st.markdown(f"- **{rc}**")
            
            if root_causes:
                st.markdown("#### 📋 Detailed Root Cause Analysis")
                for rc in root_causes:
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            background: #E3F2FD;
                            padding: 0.75rem;
                            border-radius: 8px;
                            margin-bottom: 0.5rem;
                            border-left: 4px solid #2196F3;
                        ">
                            <p style="margin: 0; font-weight: 600;">
                                Mistake #{rc.get('mistake_number', '?')}: {rc.get('root_cause', 'Unknown')}
                            </p>
                            <p style="margin: 0.25rem 0 0 0; color: #333; font-size: 0.9rem;">
                                {rc.get('evidence', '')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Theme Criticality Section
            theme_criticality = result.get("theme_criticality", [])
            if theme_criticality:
                st.markdown("#### ⚠️ Theme Criticality Assessment")
                critical = [t for t in theme_criticality if t.get("criticality") == "Critical"]
                non_critical = [t for t in theme_criticality if t.get("criticality") == "Non-Critical"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Critical Themes:** {len(critical)}")
                    for t in critical:
                        st.markdown(f"- {t.get('theme_name', 'Unknown')}")
                
                with col2:
                    st.markdown(f"**Non-Critical Themes:** {len(non_critical)}")
                    for t in non_critical:
                        st.markdown(f"- {t.get('theme_name', 'Unknown')}")
            
            # Reasoning Section
            reasoning = result.get("reasoning_behind_root_cause", {})
            overall_assessment = reasoning.get("overall_assessment", {})
            
            if overall_assessment:
                st.markdown("#### 💡 Overall Assessment")
                
                if overall_assessment.get("performance_summary"):
                    st.markdown(f"**Summary:** {overall_assessment['performance_summary']}")
                
                if overall_assessment.get("primary_concern"):
                    st.warning(f"**Primary Concern:** {overall_assessment['primary_concern']}")
                
                strengths = overall_assessment.get("agent_strengths", [])
                if strengths:
                    st.markdown("**Strengths:**")
                    for s in strengths:
                        st.markdown(f"- ✅ {s}")
                
                improvements = overall_assessment.get("priority_improvements", [])
                if improvements:
                    st.markdown("**Priority Improvements:**")
                    for idx, imp in enumerate(improvements, 1):
                        st.markdown(f"{idx}. {imp}")


def _render_table_view(results: List[Dict[str, Any]]):
    """Render table view of results"""
    if not results:
        st.info("No results to display.")
        return
    
    # Create simplified DataFrame for display
    table_data = []
    for result in results:
        table_data.append({
            "Transcript ID": result.get("transcript_id", ""),
            "Agent Name": result.get("agent_name", ""),
            "Agent ID": result.get("agent_id", ""),
            "Mistakes Count": result.get("mistakes_count", 0),
            "Themes": ", ".join(result.get("mistake_themes", [])[:3]),  # First 3 themes
            "Primary Root Causes": ", ".join(result.get("primary_root_causes", [])[:2]),  # First 2
            "Severity Score": result.get("severity_score", 100),
            "Severity Rating": result.get("severity_rating", "Excellent")
        })
    
    df = pd.DataFrame(table_data)
    
    # Style the dataframe
    def color_severity(val):
        if isinstance(val, int) or isinstance(val, float):
            if val >= 75:
                return 'background-color: #d4edda'
            elif val >= 50:
                return 'background-color: #fff3cd'
            else:
                return 'background-color: #f8d7da'
        return ''
    
    styled_df = df.style.applymap(
        color_severity, 
        subset=['Severity Score']
    )
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)


def _render_export_section(analysis_result: Dict[str, Any]):
    """Render export options"""
    st.markdown("### 💾 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    # Prepare export data
    final_results = analysis_result.get("final_results", [])
    themes = analysis_result.get("generated_themes", [])
    summary = analysis_result.get("summary", {})
    
    with col1:
        # Export as JSON
        export_data = {
            "summary": summary,
            "generated_themes": themes,
            "transcript_analyses": final_results
        }
        json_str = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name="transcript_analysis_results.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # Export as CSV
        if final_results:
            csv_data = []
            for result in final_results:
                csv_data.append({
                    "transcript_id": result.get("transcript_id", ""),
                    "agent_id": result.get("agent_id", ""),
                    "agent_name": result.get("agent_name", ""),
                    "mistakes_count": result.get("mistakes_count", 0),
                    "mistake_themes": "; ".join(result.get("mistake_themes", [])),
                    "primary_root_causes": "; ".join(result.get("primary_root_causes", [])),
                    "severity_score": result.get("severity_score", 100),
                    "severity_rating": result.get("severity_rating", "Excellent"),
                    "mistakes_json": json.dumps(result.get("mistakes", [])),
                    "root_cause_json": json.dumps(result.get("root_cause", [])),
                    "reasoning_json": json.dumps(result.get("reasoning_behind_root_cause", {}))
                })
            
            df = pd.DataFrame(csv_data)
            csv_str = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_str,
                file_name="transcript_analysis_results.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        # Export themes only
        themes_json = json.dumps(themes, indent=2)
        
        st.download_button(
            label="📥 Download Themes",
            data=themes_json,
            file_name="generated_themes.json",
            mime="application/json",
            use_container_width=True
        )
