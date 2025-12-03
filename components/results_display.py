"""
Results Display Component
Handles display of analysis results
"""

import streamlit as st
import pandas as pd
import json
from typing import Optional

from config.theme import EXLTheme


def parse_json_field(value):
    """Parse JSON string field to list"""
    if pd.isna(value) or value == '' or value == '[]':
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(str(value))
    except:
        return [str(value)] if value else []


def render_results(processed_df: pd.DataFrame):
    """
    Render the analysis results section
    
    Args:
        processed_df: DataFrame containing processed results
    """
    
    # Results header
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid #E85D04;
    ">
        <span style="font-size: 1.5rem;">📊</span>
        <h2 style="
            color: #1A1A2E !important;
            margin: 0;
            font-weight: 700;
            font-size: 1.5rem;
        ">Analysis Results</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary metrics
    render_results_summary(processed_df)
    
    st.markdown("---")
    
    # Detailed results table
    render_results_table(processed_df)


def render_results_summary(processed_df: pd.DataFrame):
    """
    Render summary metrics for analysis results
    
    Args:
        processed_df: DataFrame containing processed results
    """
    
    total = len(processed_df)
    
    # Calculate metrics - handle new JSON format columns
    if 'mistakes' in processed_df.columns:
        # Count mistakes from JSON arrays
        total_mistakes = processed_df['mistakes'].apply(
            lambda x: len(parse_json_field(x))
        ).sum()
        avg_mistakes = total_mistakes / total if total > 0 else 0
    else:
        total_mistakes = 0
        avg_mistakes = 0
    
    # Severity score
    if 'severity_score' in processed_df.columns:
        avg_severity = processed_df['severity_score'].mean()
    else:
        avg_severity = 100
    
    # Count by severity rating
    if 'severity_score' in processed_df.columns:
        high_quality = len(processed_df[processed_df['severity_score'] >= 75])
        low_quality = len(processed_df[processed_df['severity_score'] < 50])
    else:
        high_quality = total
        low_quality = 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid #E85D04;
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">ANALYZED</p>
            <h2 style="color: #E85D04; margin: 0.5rem 0 0 0; font-size: 2rem;">{total}</h2>
            <p style="color: #2E7D32; margin: 0.25rem 0 0 0; font-size: 0.8rem;">✓ Transcripts</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid #C62828;
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">TOTAL MISTAKES</p>
            <h2 style="color: #C62828; margin: 0.5rem 0 0 0; font-size: 2rem;">{int(total_mistakes)}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Identified</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_color = "#2E7D32" if avg_mistakes <= 2 else "#F9A825" if avg_mistakes <= 4 else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid {avg_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">AVG MISTAKES</p>
            <h2 style="color: {avg_color}; margin: 0.5rem 0 0 0; font-size: 2rem;">{avg_mistakes:.1f}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Per Transcript</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        severity_color = "#2E7D32" if avg_severity >= 75 else "#F9A825" if avg_severity >= 50 else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid {severity_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">AVG SEVERITY</p>
            <h2 style="color: {severity_color}; margin: 0.5rem 0 0 0; font-size: 2rem;">{avg_severity:.0f}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Score /100</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        quality_color = "#2E7D32" if high_quality > low_quality else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid {quality_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">HIGH QUALITY</p>
            <h2 style="color: {quality_color}; margin: 0.5rem 0 0 0; font-size: 2rem;">{high_quality}/{total}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Score ≥75</p>
        </div>
        """, unsafe_allow_html=True)


def render_results_table(processed_df: pd.DataFrame):
    """
    Render the detailed results table
    
    Args:
        processed_df: DataFrame containing processed results
    """
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        📋 Detailed Analysis Results
    </h3>
    """, unsafe_allow_html=True)
    
    # Severity filter
    if 'severity_score' in processed_df.columns:
        filter_options = ['All', 'High (≥75)', 'Medium (50-74)', 'Low (<50)']
        selected_filter = st.selectbox(
            "Filter by Severity Score:",
            filter_options,
            index=0
        )
        
        # Apply filter
        if selected_filter == 'High (≥75)':
            display_df = processed_df[processed_df['severity_score'] >= 75]
        elif selected_filter == 'Medium (50-74)':
            display_df = processed_df[(processed_df['severity_score'] >= 50) & (processed_df['severity_score'] < 75)]
        elif selected_filter == 'Low (<50)':
            display_df = processed_df[processed_df['severity_score'] < 50]
        else:
            display_df = processed_df
    else:
        display_df = processed_df
    
    # Define columns to display (matching new output format)
    # Expected columns: transcript_id, agent_name, agent_id, transcript_call, mistakes, 
    #                   mistake_themes, root_cause, severity_score, reasoning
    
    display_cols = [
        'transcript_id', 'agent_id', 'agent_name', 'mistakes', 
        'mistake_themes', 'root_cause', 'severity_score', 'reasoning'
    ]
    
    # Filter to only include columns that exist in the dataframe
    display_cols = [col for col in display_cols if col in processed_df.columns]
    
    # Create display dataframe
    display_data = display_df[display_cols].copy() if display_cols else display_df.copy()
    
    # Rename columns for better display
    column_rename = {
        'transcript_id': 'Transcript ID',
        'agent_name': 'Agent Name',
        'agent_id': 'Agent ID',
        'mistakes': 'Mistakes',
        'mistake_themes': 'Mistake Themes',
        'root_cause': 'Root Cause',
        'severity_score': 'Severity Score',
        'reasoning': 'Reasoning'
    }
    display_data = display_data.rename(columns={k: v for k, v in column_rename.items() if k in display_data.columns})
    
    # Style functions
    def style_severity_score(val):
        try:
            num = int(val)
            if num >= 75:
                return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;'
            elif num >= 50:
                return 'background-color: #FFF8E1; color: #F57F17; font-weight: bold;'
            else:
                return 'background-color: #FFEBEE; color: #C62828; font-weight: bold;'
        except:
            return ''
    
    # Apply styling
    styled_df = display_data.style
    if 'Severity Score' in display_data.columns:
        styled_df = styled_df.applymap(style_severity_score, subset=['Severity Score'])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.info(f"📊 Showing {len(display_df)} of {len(processed_df)} records")
    
    # Expandable detail view
    st.markdown("### 🔍 Detailed View")
    st.markdown("Click on a row below to see full details including transcript and reasoning.")
    
    for idx, row in display_df.iterrows():
        transcript_id = row.get('transcript_id', f'Record {idx}')
        agent_name = row.get('agent_name', 'Unknown')
        severity = row.get('severity_score', 100)
        
        # Color based on severity
        if severity >= 75:
            color = "#2E7D32"
            bg_color = "#E8F5E9"
        elif severity >= 50:
            color = "#F57F17"
            bg_color = "#FFF8E1"
        else:
            color = "#C62828"
            bg_color = "#FFEBEE"
        
        with st.expander(f"📄 {transcript_id} | Agent: {agent_name} | Score: {severity}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Mistakes:**")
                mistakes = parse_json_field(row.get('mistakes', ''))
                if mistakes:
                    for m in mistakes:
                        if m and str(m).strip():
                            st.markdown(f"- {str(m).strip()}")
                else:
                    st.markdown("_No mistakes identified_")
                
                st.markdown("**Mistake Themes:**")
                themes = parse_json_field(row.get('mistake_themes', ''))
                if themes:
                    for t in themes:
                        if t and str(t).strip():
                            st.markdown(f"- {str(t).strip()}")
                else:
                    st.markdown("_No themes_")
            
            with col2:
                st.markdown("**Root Cause:**")
                root_causes = parse_json_field(row.get('root_cause', ''))
                if root_causes:
                    for rc in root_causes:
                        if rc and str(rc).strip():
                            st.markdown(f"- {str(rc).strip()}")
                else:
                    st.markdown("_Not analyzed_")
                
                st.markdown("**Reasoning:**")
                reasoning = row.get('reasoning', '')
                st.markdown(reasoning if reasoning else "_Not available_")
            
            # Show transcript if available
            if 'transcript_call' in row:
                st.markdown("---")
                st.markdown("**Full Transcript:**")
                transcript = str(row.get('transcript_call', ''))
                if len(transcript) > 500:
                    st.text_area("", transcript, height=200, disabled=True, label_visibility="collapsed")
                else:
                    st.markdown(f"```\n{transcript}\n```")
