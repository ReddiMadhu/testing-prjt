"""
SOP Analysis Page
Handles the SOP document upload and analysis workflow
"""

import streamlit as st
import pandas as pd
import time
from typing import Optional

from services.sop_analysis_service import SOPAnalysisService, SOPAnalysisResult, read_word_document
from components.sop_uploader import (
    render_sop_uploader,
    validate_sop_file,
    SOPFileInfo,
    render_sop_file_info,
    render_sop_preview,
    render_sop_upload_error
)
from components.sop_analysis_display import render_sop_analysis_dashboard
from utils.helpers import format_duration


def initialize_sop_session_state():
    """Initialize session state for SOP analysis page"""
    defaults = {
        'sop_content': None,
        'sop_file_info': None,
        'sop_uploaded': False,
        'sop_analysis_running': False,
        'sop_analysis_result': None,
        'sop_analysis_complete': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_sop_session_state():
    """Reset SOP analysis session state"""
    st.session_state.sop_content = None
    st.session_state.sop_file_info = None
    st.session_state.sop_uploaded = False
    st.session_state.sop_analysis_running = False
    st.session_state.sop_analysis_result = None
    st.session_state.sop_analysis_complete = False


def render_sop_page_header():
    """Render the SOP analysis page header"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1A1A2E, #16213E);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
    ">
        <h1 style="margin: 0; color: white !important;">📋 SOP Compliance Analysis</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
            Upload your Standard Operating Procedure document to analyze transcript compliance
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_processed_data_summary(processed_df: pd.DataFrame):
    """
    Render summary of the processed data to be analyzed
    
    Args:
        processed_df: DataFrame with processed transcript data
    """
    st.markdown("### 📊 Data to Analyze")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Transcripts", len(processed_df))
    
    with col2:
        unique_agents = processed_df['agent_id'].nunique() if 'agent_id' in processed_df.columns else 0
        st.metric("Unique Agents", unique_agents)
    
    with col3:
        avg_length = processed_df['transcript_call'].str.len().mean() if 'transcript_call' in processed_df.columns else 0
        st.metric("Avg Transcript Length", f"{avg_length:.0f} chars")
    
    # Preview data
    with st.expander("👀 Preview Transcript Data", expanded=False):
        display_cols = ['transcript_id', 'agent_id', 'agent_name']
        available_cols = [col for col in display_cols if col in processed_df.columns]
        if available_cols:
            st.dataframe(processed_df[available_cols].head(5), use_container_width=True)


def handle_sop_upload(uploaded_file) -> Optional[SOPFileInfo]:
    """
    Handle the SOP document upload
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        SOPFileInfo if successful, None otherwise
    """
    # Validate file
    is_valid, message = validate_sop_file(uploaded_file)
    
    if not is_valid:
        render_sop_upload_error(message)
        return None
    
    try:
        # Read document content
        content = read_word_document(uploaded_file)
        
        file_info = SOPFileInfo(
            name=uploaded_file.name,
            size=uploaded_file.size,
            content=content
        )
        
        return file_info
        
    except Exception as e:
        render_sop_upload_error(str(e))
        return None


def run_sop_analysis(processed_df: pd.DataFrame, sop_content: str) -> SOPAnalysisResult:
    """
    Run the SOP analysis workflow
    
    Args:
        processed_df: DataFrame with processed transcript data
        sop_content: Content of the SOP document
        
    Returns:
        SOPAnalysisResult with analysis results
    """
    # Show progress
    status_container = st.empty()
    progress_bar = st.progress(0)
    
    status_container.markdown("""
    <div style="
        background: #FFF8F0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #E85D04;
    ">
        <p style="margin: 0; font-weight: 600; color: #E85D04;">
            🔄 Running SOP Compliance Analysis...
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
            Step 1/4: Finding SOP violations in each transcript...
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    start_time = time.time()
    
    try:
        # Initialize service
        service = SOPAnalysisService()
        
        # Update progress
        progress_bar.progress(10)
        
        # Create a progress callback simulation
        total_transcripts = len(processed_df)
        
        # Run analysis
        result = service.analyze(processed_df, sop_content)
        
        # Update progress through steps
        progress_bar.progress(100)
        
        total_time = time.time() - start_time
        
        if result.success:
            status_container.markdown(f"""
            <div style="
                background: #E8F5E9;
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid #2E7D32;
            ">
                <p style="margin: 0; font-weight: 600; color: #2E7D32;">
                    ✅ SOP Analysis Complete!
                </p>
                <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
                    Analyzed {total_transcripts} transcripts in {format_duration(total_time)}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            status_container.markdown(f"""
            <div style="
                background: #FFEBEE;
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid #C62828;
            ">
                <p style="margin: 0; font-weight: 600; color: #C62828;">
                    ❌ Analysis Failed
                </p>
                <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
                    {result.error_message}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        return result
        
    except Exception as e:
        progress_bar.progress(100)
        status_container.markdown(f"""
        <div style="
            background: #FFEBEE;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #C62828;
        ">
            <p style="margin: 0; font-weight: 600; color: #C62828;">
                ❌ Error During Analysis
            </p>
            <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
                {str(e)}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        return SOPAnalysisResult(
            transcript_results=[],
            sop_missing_themes=[],
            success=False,
            error_message=str(e)
        )


def render_sop_analysis_page(processed_df: pd.DataFrame):
    """
    Main function to render the SOP analysis page
    
    Args:
        processed_df: DataFrame with processed transcript data
    """
    # Initialize session state
    initialize_sop_session_state()
    
    # Check if analysis is complete and results exist
    if st.session_state.sop_analysis_complete and st.session_state.sop_analysis_result:
        # Show results dashboard with processed_df for displaying previous columns
        render_sop_analysis_dashboard(st.session_state.sop_analysis_result, processed_df)
        
        st.markdown("---")
        
        # Option to re-analyze
        if st.button("🔄 Analyze with Different SOP", use_container_width=True):
            reset_sop_session_state()
            st.rerun()
        
        return
    
    # Page header
    render_sop_page_header()
    
    # Show processed data summary
    render_processed_data_summary(processed_df)
    
    st.markdown("---")
    
    # SOP Upload section
    st.markdown("### 📄 Step 1: Upload SOP Document")
    
    uploaded_file = render_sop_uploader()
    
    if uploaded_file is not None:
        # Handle upload if not already processed
        if not st.session_state.sop_uploaded:
            file_info = handle_sop_upload(uploaded_file)
            
            if file_info:
                st.session_state.sop_content = file_info.content
                st.session_state.sop_file_info = file_info
                st.session_state.sop_uploaded = True
                st.rerun()
        
        # Show file info if uploaded
        if st.session_state.sop_uploaded and st.session_state.sop_file_info:
            render_sop_file_info(st.session_state.sop_file_info)
            render_sop_preview(st.session_state.sop_content)
            
            st.markdown("---")
            
            # Analysis section
            st.markdown("### 🚀 Step 2: Run SOP Analysis")
            
            st.markdown("""
            <div class="info-box">
                <h4 style="color: #D84E00 !important; margin: 0 0 0.5rem 0;">Analysis Steps:</h4>
                <ol style="margin: 0; color: #1A1A2E; padding-left: 1.5rem;">
                    <li><strong>Find SOP Mistakes:</strong> Identify missing/incorrect SOP steps per transcript</li>
                    <li><strong>Generate Themes:</strong> Aggregate mistakes and create 10 common themes</li>
                    <li><strong>Assign Themes:</strong> Map themes to each transcript with reasoning</li>
                    <li><strong>Provide Improvements:</strong> Generate SOP-based improvement recommendations</li>
                </ol>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #666;">
                    ⏱️ Estimated time: ~5-10 seconds per transcript
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔍 Start SOP Analysis", type="primary", use_container_width=True):
                    st.session_state.sop_analysis_running = True
                    
                    # Run analysis
                    result = run_sop_analysis(processed_df, st.session_state.sop_content)
                    
                    if result.success:
                        st.session_state.sop_analysis_result = result
                        st.session_state.sop_analysis_complete = True
                        st.session_state.sop_analysis_running = False
                        time.sleep(1)  # Brief pause to show success message
                        st.rerun()
                    else:
                        st.session_state.sop_analysis_running = False
    
    else:
        # Reset if file was removed
        if st.session_state.sop_uploaded:
            reset_sop_session_state()
        
        # Show empty state
        st.markdown("""
        <div style="
            background: #f5f5f5;
            padding: 3rem;
            border-radius: 10px;
            text-align: center;
            border: 2px dashed #ddd;
            margin: 1rem 0;
        ">
            <p style="font-size: 3rem; margin: 0;">📄</p>
            <h3 style="color: #666; margin: 1rem 0 0.5rem 0;">Upload SOP Document</h3>
            <p style="color: #888; margin: 0;">
                Drag and drop a Word document (.docx) or click to browse
            </p>
        </div>
        """, unsafe_allow_html=True)
