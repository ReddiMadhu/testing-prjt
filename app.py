"""
EXL FNOL Transcript Analyzer
Industrial-Grade Application for Insurance Call Transcript Analysis

Main application entry point with modular architecture
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Configuration
from config.settings import Settings
from config.theme import EXLTheme

# Services
from services.llm_factory import get_llm_service
from services.file_service import FileService
from services.analytics_service import AnalyticsService
from services.final_transcript import FinalTranscriptAnalysis

# Components
from components.sidebar import render_sidebar
from components.header import render_header, render_section_header
from components.file_uploader import (
    render_file_uploader,
    render_file_success,
    render_file_error,
    render_data_preview,
    render_empty_state
)
from components.results_display import render_results
from components.metrics import render_file_metrics
from components.analytics_display import render_analytics_dashboard
from components.transcript_analysis_display import render_transcript_analysis_dashboard

# Utilities
from utils.helpers import format_duration, generate_timestamp
from utils.validators import validate_dataframe, validate_transcript_content


# Initialize settings
settings = Settings()


def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title=settings.ui.page_title,
        page_icon=settings.ui.page_icon,
        layout=settings.ui.layout,
        initial_sidebar_state=settings.ui.sidebar_state
    )
    
    # Apply custom theme
    st.markdown(EXLTheme.get_custom_css(), unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'data': None,
        'processed_data': None,
        'file_uploaded': False,
        'file_info': None,
        'processing_started': False,
        'processing_complete': False,
        'error_message': None,
        'show_analytics': False,  # Track analytics view
        'analytics_result': None,  # Store analytics result
        'show_transcript_analysis': False,  # Track transcript analysis view
        'transcript_analysis_result': None  # Store transcript analysis result
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session_state():
    """Reset session state for new file upload"""
    st.session_state.data = None
    st.session_state.processed_data = None
    st.session_state.file_uploaded = False
    st.session_state.file_info = None
    st.session_state.processing_started = False
    st.session_state.processing_complete = False
    st.session_state.error_message = None
    st.session_state.show_analytics = False
    st.session_state.analytics_result = None
    st.session_state.show_transcript_analysis = False
    st.session_state.transcript_analysis_result = None


# ...existing code for handle_file_upload, process_transcripts, render_processing_section...


def handle_file_upload(uploaded_file):
    """
    Handle file upload and validation
    
    Args:
        uploaded_file: Uploaded file object
        
    Returns:
        Tuple of (DataFrame or None, FileInfo or None, error message or None)
    """
    file_service = FileService()
    
    # Validate file
    validation = file_service.validate_file(uploaded_file, uploaded_file.name)
    if not validation.is_valid:
        return None, None, validation.message
    
    # Read file
    df, error = file_service.read_file(uploaded_file, uploaded_file.name)
    if error:
        return None, None, error
    
    # Validate DataFrame
    df_validation = validate_dataframe(df)
    if not df_validation.is_valid:
        return None, None, df_validation.message
    
    # Get file info
    file_info = file_service.get_file_info(uploaded_file, uploaded_file.name, df)
    
    # Show warnings if any
    for warning in validation.warnings + df_validation.warnings:
        st.warning(f"⚠️ {warning}")

    render_file_success(file_info)

    return df, file_info, None


def process_transcripts(
    df: pd.DataFrame,
    transcript_column: str,
    num_rows: int,
    transcript_id_column: str = None,
    agent_name_column: str = None,
    agent_id_column: str = None
) -> pd.DataFrame:
    """
    Process transcripts using FinalTranscriptAnalysis LangGraph service
    
    Args:
        df: Source DataFrame
        transcript_column: Column containing transcripts
        num_rows: Number of rows to process
        transcript_id_column: Column containing transcript IDs (optional)
        agent_name_column: Column containing agent names (optional)
        agent_id_column: Column containing agent IDs (optional)
        
    Returns:
        DataFrame with analysis results
    """
    # Prepare DataFrame for analysis
    analysis_df = df.head(num_rows).copy()
    
    # Map columns to expected format
    column_mapping = {}
    
    # Map transcript column
    if transcript_column:
        column_mapping[transcript_column] = 'Transcript_Call'
    
    # Map transcript_id column
    if transcript_id_column and transcript_id_column != "(None - Auto-generate)":
        column_mapping[transcript_id_column] = 'Transcript_ID'
    else:
        analysis_df['Transcript_ID'] = [f"T{i+1}" for i in range(len(analysis_df))]
    
    # Map agent_name column
    if agent_name_column and agent_name_column != "(None - Auto-generate)":
        column_mapping[agent_name_column] = 'Agent_Name'
    else:
        analysis_df['Agent_Name'] = "Unknown"
    
    # Map agent_id column
    if agent_id_column and agent_id_column != "(None - Auto-generate)":
        column_mapping[agent_id_column] = 'Agent_ID'
    else:
        analysis_df['Agent_ID'] = [f"A{i+1}" for i in range(len(analysis_df))]
    
    # Apply column mapping
    analysis_df = analysis_df.rename(columns=column_mapping)
    
    # Show progress
    status_container = st.empty()
    status_container.markdown(f"""
    <div style="
        background: #FFF8F0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #E85D04;
    ">
        <p style="margin: 0; font-weight: 600; color: #E85D04;">
            🔄 Running LangGraph Transcript Analysis...
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
            Processing {num_rows} transcripts. This may take a few minutes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    start_time = time.time()
    
    # Run FinalTranscriptAnalysis
    try:
        analyzer = FinalTranscriptAnalysis()
        result = analyzer.analyze(analysis_df)
        
        if result["success"]:
            output_df = analyzer.to_dataframe(result)
            
            total_time = time.time() - start_time
            status_container.markdown(f"""
            <div style="
                background: #E8F5E9;
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid #2E7D32;
            ">
                <p style="margin: 0; font-weight: 600; color: #2E7D32;">
                    ✅ Analysis Complete!
                </p>
                <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
                    Processed {num_rows} transcripts in {format_duration(total_time)}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            return output_df
        else:
            st.error(f"Analysis failed: {result['error']}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        return pd.DataFrame()


def render_processing_section(df: pd.DataFrame):
    """
    Render the processing configuration and execution section
    
    Args:
        df: DataFrame to process
    """
    render_section_header("Process Transcripts")
    
    st.markdown("""
    <div class="info-box">
        <h4 style="color: #D84E00 !important; margin: 0 0 0.5rem 0;">LangGraph Transcript Analysis</h4>
        <p style="margin: 0; color: #1A1A2E;">
            The AI will analyze each transcript to identify mistakes, generate themes, 
            determine root causes, calculate severity scores, and provide reasoning.
            Processing time: approximately 5-10 seconds per transcript.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Column selection
    file_service = FileService()
    columns = df.columns.tolist()
    columns_with_none = ["(None - Auto-generate)"] + columns
    
    # Row 1: Transcript column and number of rows
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Find likely transcript column
        transcript_col_idx = 0
        for i, col in enumerate(columns):
            if 'transcript_call' in col.lower() or 'transcript' in col.lower() or 'call' in col.lower():
                transcript_col_idx = i  
                break
        
        selected_transcript_col = st.selectbox(
            "Select the transcript column:",
            columns,
            index=transcript_col_idx,
            help="Choose the column containing the call transcripts to analyze"
        )
    
    with col2:
        max_rows = min(settings.file.max_rows_to_process, len(df))
        num_rows = st.slider(
            "Transcripts to process:",
            min_value=1,
            max_value=max_rows,
            value=min(settings.file.default_rows_to_process, max_rows),
            help=f"Select number of transcripts to analyze (max {max_rows})"
        )
    
    # Row 2: Transcript ID, Agent ID, Agent Name columns
    st.markdown("##### Optional: Map Excel Columns")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        # Find likely transcript_id column
        id_col_idx = 0
        for i, col in enumerate(columns):
            if 'transcript_id' in col.lower() or 'id' in col.lower():
                id_col_idx = i + 1
                break
        
        selected_transcript_id_col = st.selectbox(
            "Transcript ID column:",
            columns_with_none,
            index=id_col_idx,
            help="Column containing transcript IDs (optional)"
        )
    
    with col4:
        # Find likely agent_id column
        agent_id_col_idx = 0
        for i, col in enumerate(columns):
            if 'agent_id' in col.lower():
                agent_id_col_idx = i + 1
                break
        
        selected_agent_id_col = st.selectbox(
            "Agent ID column:",
            columns_with_none,
            index=agent_id_col_idx,
            help="Column containing agent IDs (optional)"
        )
    
    with col5:
        # Find likely agent_name column
        agent_name_col_idx = 0
        for i, col in enumerate(columns):
            if 'agent_name' in col.lower() or 'agent' in col.lower():
                agent_name_col_idx = i + 1
                break
        
        selected_agent_name_col = st.selectbox(
            "Agent Name column:",
            columns_with_none,
            index=agent_name_col_idx,
            help="Column containing agent names (optional)"
        )
    
    # Process button
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            # Process transcripts
            transcript_id_col = selected_transcript_id_col if selected_transcript_id_col != "(None - Auto-generate)" else None
            agent_id_col = selected_agent_id_col if selected_agent_id_col != "(None - Auto-generate)" else None
            agent_name_col = selected_agent_name_col if selected_agent_name_col != "(None - Auto-generate)" else None
            
            processed_df = process_transcripts(
                df,
                selected_transcript_col,
                num_rows,
                transcript_id_col,
                agent_name_col,
                agent_id_col
            )
            
            if not processed_df.empty:
                st.session_state.processed_data = processed_df
                st.rerun()


def run_further_analysis():
    """Run the LangGraph analytics workflow"""
    try:
        with st.spinner("🔄 Running AI-powered analytics..."):
            analytics_service = AnalyticsService()
            result = analytics_service.analyze(st.session_state.processed_data)
            st.session_state.analytics_result = result
            st.session_state.show_analytics = True
    except Exception as e:
        st.error(f"❌ Error running analytics: {str(e)}")


def render_download_section(processed_df: pd.DataFrame):
    """
    Render the download section for results
    
    Args:
        processed_df: Processed DataFrame to download
    """
    render_section_header("Download Results", "💾")
    
    file_service = FileService()
    
    # Generate filename with timestamp
    timestamp = generate_timestamp()
    base_filename = f"FNOL_Analysis_Results_{timestamp}"
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        # Excel download
        excel_data = file_service.export_to_excel(processed_df)
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name=f"{base_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        # CSV download
        csv_data = file_service.export_to_csv(processed_df)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"{base_filename}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Further Analysis button
        if st.button("📊 Further Analysis", type="primary", use_container_width=True):
            run_further_analysis()
            st.rerun()
    


def main():
    """Main application entry point"""
    
    # Configure page
    configure_page()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Check if we should show transcript analysis view
    if st.session_state.show_transcript_analysis and st.session_state.transcript_analysis_result:
        # Back button
        col1 = st.columns([1, 9])[0]
        with col1:
            if st.button("← Back to Results"):
                st.session_state.show_transcript_analysis = False
                st.rerun()
        
        # Render transcript analysis dashboard
        render_transcript_analysis_dashboard(st.session_state.transcript_analysis_result)
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: #666;">
            <p style="margin: 0; font-size: 0.85rem;">
                <strong>EXL FNOL Transcript Analyzer</strong> | Industrial Edition v2.0
            </p>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem;">
                Powered by © 2025 EXL Service
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Check if we should show analytics view
    if st.session_state.show_analytics and st.session_state.analytics_result:
        # Back button
        col1= st.columns([1, 9])[0]
        with col1:
            if st.button("← Back to Results"):
                st.session_state.show_analytics = False
                st.rerun()
        
        # Render analytics dashboard
        render_analytics_dashboard(st.session_state.analytics_result)
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: #666;">
            <p style="margin: 0; font-size: 0.85rem;">
                <strong>EXL FNOL Transcript Analyzer</strong> | Industrial Edition v2.0
            </p>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem;">
                Powered by © 2025 EXL Service
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # File Upload Section with Clear button
    col_header, col_clear = st.columns([6, 1])
    
    with col_header:
        render_section_header("Upload Transcript File", "📁")
    
    with col_clear:
        st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)  # Spacer for alignment
        if st.button("❌ Clear All", type="secondary", use_container_width=True, help="Clear all data and start fresh"):
            reset_session_state()
            st.rerun()
    
    uploaded_file = render_file_uploader()
    
    if uploaded_file is not None:
        # Handle file upload
        if not st.session_state.file_uploaded:
            df, file_info, error = handle_file_upload(uploaded_file)
            
            if error:
                render_file_error(error)
                st.stop()  # Stop execution if there's an error
            else:
                st.session_state.data = df
                st.session_state.file_info = file_info
                st.session_state.file_uploaded = True
        
        # Display file info and data
        if st.session_state.file_uploaded and st.session_state.data is not None:
            render_file_metrics(st.session_state.file_info)
            
            st.markdown("---")
            
            render_data_preview(st.session_state.data, settings.ui.show_preview_rows)
            
            st.markdown("---")
            
            # Show processing section or results
            if st.session_state.processed_data is None:
                render_processing_section(st.session_state.data)
            else:
                render_results(st.session_state.processed_data)
                st.markdown("---")
                render_download_section(st.session_state.processed_data)
    
    else:
        # File was removed - reset state if previously uploaded
        if st.session_state.file_uploaded:
            reset_session_state()
        # Show empty state
        render_empty_state()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #666;">
        <p style="margin: 0; font-size: 0.85rem;">
            <strong>EXL FNOL Transcript Analyzer</strong> | Industrial Edition v2.0
        </p>
        <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem;">
            Powered by © 2025 EXL Service
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()