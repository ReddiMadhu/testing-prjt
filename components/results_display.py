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
    
    severity_counts = processed_df['Compliance_Severity'].value_counts()
    
    total = len(processed_df)
    high_count = severity_counts.get('High', 0)
    medium_count = severity_counts.get('Medium', 0)
    low_count = severity_counts.get('Low', 0)
    
    # Calculate compliance rate
    compliant = low_count
    compliance_rate = (compliant / total * 100) if total > 0 else 0
    
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
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">HIGH SEVERITY</p>
            <h2 style="color: #C62828; margin: 0.5rem 0 0 0; font-size: 2rem;">{high_count}</h2>
            <p style="color: {'#C62828' if high_count > 0 else '#666'}; margin: 0.25rem 0 0 0; font-size: 0.8rem;">
                {'⚠️ Needs Review' if high_count > 0 else '✓ None'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid #F9A825;
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">MEDIUM SEVERITY</p>
            <h2 style="color: #F9A825; margin: 0.5rem 0 0 0; font-size: 2rem;">{medium_count}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Moderate Issues</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid #2E7D32;
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">LOW SEVERITY</p>
            <h2 style="color: #2E7D32; margin: 0.5rem 0 0 0; font-size: 2rem;">{low_count}</h2>
            <p style="color: #2E7D32; margin: 0.25rem 0 0 0; font-size: 0.8rem;">✓ Minor Issues</p>
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
    
    # Severity filter
    severity_options = ['All'] + processed_df['Compliance_Severity'].unique().tolist()
    selected_severity = st.selectbox(
        "Filter by Severity:",
        severity_options,
        index=0
    )
    
    # Filter data
    if selected_severity != 'All':
        display_df = processed_df[processed_df['Compliance_Severity'] == selected_severity]
    else:
        display_df = processed_df
    
    # Prepare display columns
    display_cols = ['Missing_Elements', 'Compliance_Severity', 'Analysis_Summary']
    
    # Add ID column if exists
    id_cols = [col for col in processed_df.columns if 'id' in col.lower()]
    if id_cols:
        display_cols = [id_cols[0]] + display_cols
    
    # Style the dataframe
    def style_severity(val):
        if val == 'High':
            return 'background-color: #FFEBEE; color: #C62828; font-weight: bold;'
        elif val == 'Medium':
            return 'background-color: #FFF8E1; color: #F57F17; font-weight: bold;'
        elif val == 'Low':
            return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;'
        return ''
    
    # Apply styling
    styled_df = display_df[display_cols].style.applymap(
        style_severity, 
        subset=['Compliance_Severity']
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.info(f"📊 Showing {len(display_df)} of {len(processed_df)} records")


def render_individual_result(
    index: int,
    severity: str,
    missing_elements: str,
    summary: str,
    transcript_id: Optional[str] = None
):
    """
    Render an individual result card
    
    Args:
        index: Result index
        severity: Severity level
        missing_elements: Missing elements string
        summary: Analysis summary
        transcript_id: Optional transcript ID
    """
    
    severity_colors = {
        'High': ('#C62828', '#FFEBEE'),
        'Medium': ('#F57F17', '#FFF8E1'),
        'Low': ('#2E7D32', '#E8F5E9')
    }
    
    color, bg_color = severity_colors.get(severity, ('#666', '#F5F5F5'))
    
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
            </span>
            <span style="
                background: {color};
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
            ">{severity}</span>
        </div>
        <p style="margin: 0.5rem 0; color: #1A1A2E; font-size: 0.9rem;">
            <strong>Missing Elements:</strong> {missing_elements}
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.85rem;">
            <strong>Summary:</strong> {summary}
        </p>
    </div>
    """, unsafe_allow_html=True)
