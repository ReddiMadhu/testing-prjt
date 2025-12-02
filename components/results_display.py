"""
Results Display Component
Handles display of analysis results
"""

import streamlit as st
import pandas as pd
from typing import Optional

from config.theme import EXLTheme


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
    
    # Calculate metrics based on new format
    total_missed = processed_df['Num_Missed'].sum() if 'Num_Missed' in processed_df.columns else 0
    avg_missed = processed_df['Num_Missed'].mean() if 'Num_Missed' in processed_df.columns else 0
    
    # Sequence followed counts
    sequence_counts = processed_df['Sequence_Followed'].value_counts() if 'Sequence_Followed' in processed_df.columns else pd.Series()
    seq_yes = sequence_counts.get('Yes', 0)
    seq_no = sequence_counts.get('No', 0)
    
    # Calculate compliance rate (based on sequence followed)
    compliance_rate = (seq_yes / total * 100) if total > 0 else 0
    
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
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">PROCESSED</p>
            <h2 style="color: #E85D04; margin: 0.5rem 0 0 0; font-size: 2rem;">{total}</h2>
            <p style="color: #2E7D32; margin: 0.25rem 0 0 0; font-size: 0.8rem;">✓ Complete</p>
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
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">TOTAL MISSED</p>
            <h2 style="color: #C62828; margin: 0.5rem 0 0 0; font-size: 2rem;">{int(total_missed)}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Points Across All</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_color = "#2E7D32" if avg_missed <= 2 else "#F9A825" if avg_missed <= 4 else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid {avg_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">AVG MISSED</p>
            <h2 style="color: {avg_color}; margin: 0.5rem 0 0 0; font-size: 2rem;">{avg_missed:.1f}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Per Transcript</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        seq_color = "#2E7D32" if seq_yes > seq_no else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid {seq_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">SEQUENCE</p>
            <h2 style="color: {seq_color}; margin: 0.5rem 0 0 0; font-size: 2rem;">{seq_yes}/{total}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Followed SOP</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        rate_color = "#2E7D32" if compliance_rate >= 70 else "#F9A825" if compliance_rate >= 40 else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid {rate_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">COMPLIANCE</p>
            <h2 style="color: {rate_color}; margin: 0.5rem 0 0 0; font-size: 2rem;">{compliance_rate:.0f}%</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Overall Rate</p>
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
    
    # Sequence filter
    filter_options = ['All'] + processed_df['Sequence_Followed'].unique().tolist() if 'Sequence_Followed' in processed_df.columns else ['All']
    selected_filter = st.selectbox(
        "Filter by Sequence Followed:",
        filter_options,
        index=0
    )
    
    # Filter data
    if selected_filter != 'All':
        display_df = processed_df[processed_df['Sequence_Followed'] == selected_filter]
    else:
        display_df = processed_df
    
    # Prepare display columns with new format (including Missed_Themes)
    display_cols = ['Transcript_ID', 'Agent_Name', 'Missed_Points', 'Missed_Themes', 'Num_Missed', 'Sequence_Followed', 'Summary_Missed_Things']
    
    # Filter to only include columns that exist in the dataframe
    display_cols = [col for col in display_cols if col in processed_df.columns]
    
    # Style the dataframe
    def style_sequence(val):
        if val == 'Yes':
            return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;'
        elif val == 'No':
            return 'background-color: #FFEBEE; color: #C62828; font-weight: bold;'
        return ''
    
    def style_num_missed(val):
        try:
            num = int(val)
            if num == 0:
                return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;'
            elif num <= 2:
                return 'background-color: #FFF8E1; color: #F57F17; font-weight: bold;'
            else:
                return 'background-color: #FFEBEE; color: #C62828; font-weight: bold;'
        except:
            return ''
    
    # Apply styling
    styled_df = display_df[display_cols].style
    if 'Sequence_Followed' in display_cols:
        styled_df = styled_df.applymap(style_sequence, subset=['Sequence_Followed'])
    if 'Num_Missed' in display_cols:
        styled_df = styled_df.applymap(style_num_missed, subset=['Num_Missed'])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.info(f"📊 Showing {len(display_df)} of {len(processed_df)} records")


def render_individual_result(
    index: int,
    sequence_followed: str,
    missed_points: str,
    num_missed: int,
    summary_missed_things: str,
    transcript_id: Optional[str] = None,
    agent_name: Optional[str] = None
):
    """
    Render an individual result card
    
    Args:
        index: Result index
        sequence_followed: Whether SOP sequence was followed (Yes/No)
        missed_points: Missed points string
        num_missed: Number of missed points
        summary_missed_things: Summary of missed things
        transcript_id: Optional transcript ID
        agent_name: Optional agent name
    """
    
    # Color based on sequence followed
    if sequence_followed == 'Yes':
        color, bg_color = '#2E7D32', '#E8F5E9'
    else:
        color, bg_color = '#C62828', '#FFEBEE'
    
    st.markdown(f"""
    <div style="
        background: {bg_color};
        border-left: 4px solid {color};
        padding: 1rem 1.5rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: #1A1A2E;">
                {f'ID: {transcript_id}' if transcript_id else f'Record #{index + 1}'} 
                {f'| Agent: {agent_name}' if agent_name else ''}
            </span>
            <div style="display: flex; gap: 0.5rem;">
                <span style="
                    background: {color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                ">Sequence: {sequence_followed}</span>
                <span style="
                    background: {'#C62828' if num_missed > 2 else '#F9A825' if num_missed > 0 else '#2E7D32'};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                ">Missed: {num_missed}</span>
            </div>
        </div>
        <p style="margin: 0.5rem 0; color: #1A1A2E; font-size: 0.9rem;">
            <strong>Missed Points:</strong> {missed_points}
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.85rem;">
            <strong>Summary:</strong> {summary_missed_things}
        </p>
    </div>
    """, unsafe_allow_html=True)
