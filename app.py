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
        'error_message': None
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
    agent_name_column: str = None
) -> pd.DataFrame:
    """
    Process transcripts and return results DataFrame
    
    Args:
        df: Source DataFrame
        transcript_column: Column containing transcripts
        num_rows: Number of rows to process
        transcript_id_column: Column containing transcript IDs (optional)
        agent_name_column: Column containing agent names (optional)
        
    Returns:
        DataFrame with analysis results
    """
    # Get provider from session state or default
    provider = st.session_state.get('llm_provider')
    llm_service = get_llm_service(provider)
    
    # Progress indicators
    progress_bar = st.progress(0)
    status_container = st.empty()
    metrics_container = st.container()
    
    processed_rows = []
    start_time = time.time()
    success_count = 0
    
    for idx in range(min(num_rows, len(df))):
        row = df.iloc[idx]
        transcript = str(row[transcript_column]) if pd.notna(row[transcript_column]) else ""
        
        # Extract transcript_id and agent_name from Excel if columns are provided
        transcript_id = str(row[transcript_id_column]) if transcript_id_column and pd.notna(row.get(transcript_id_column)) else f"T{idx+1}"
        agent_name = str(row[agent_name_column]) if agent_name_column and pd.notna(row.get(agent_name_column)) else "Unknown"
        
        # Update status
        elapsed = time.time() - start_time
        status_container.markdown(f"""
        <div style="
            background: #FFF8F0;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #E85D04;
        ">
            <p style="margin: 0; font-weight: 600; color: #E85D04;">
                🔄 Processing transcript {idx + 1} of {num_rows} (ID: {transcript_id})
            </p>
            <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
                Elapsed: {format_duration(elapsed)} | 
                Success rate: {(success_count / (idx + 1) * 100) if idx > 0 else 0:.1f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Validate and analyze
        transcript_validation = validate_transcript_content(transcript)
        
        if transcript_validation.is_valid:
            result = llm_service.analyze_transcript(transcript)
            
            new_row = row.to_dict()
            new_row['Transcript_ID'] = transcript_id
            new_row['Agent_Name'] = agent_name
            new_row['Missed_Points'] = "; ".join(result.missed_points)
            new_row['Num_Missed'] = result.num_missed
            new_row['Sequence_Followed'] = result.sequence_followed
            new_row['Summary_Missed_Things'] = result.summary_missed_things
            processed_rows.append(new_row)
            
            if result.success:
                success_count += 1
        else:
            new_row = row.to_dict()
            new_row['Transcript_ID'] = transcript_id
            new_row['Agent_Name'] = agent_name
            new_row['Missed_Points'] = transcript_validation.message
            new_row['Num_Missed'] = 0
            new_row['Sequence_Followed'] = "N/A"
            new_row['Summary_Missed_Things'] = "Invalid transcript"
            processed_rows.append(new_row)
        
        # Update progress
        progress_bar.progress((idx + 1) / num_rows)
    
    # Clear status and show completion
    total_time = time.time() - start_time
    status_container.markdown(f"""
    <div style="
        background: #E8F5E9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E7D32;
    ">
        <p style="margin: 0; font-weight: 600; color: #2E7D32;">
            ✅ Processing Complete!
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
            Processed {num_rows} transcripts in {format_duration(total_time)} | 
            Success rate: {(success_count / num_rows * 100):.1f}%
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    return pd.DataFrame(processed_rows)


def render_processing_section(df: pd.DataFrame):
    """
    Render the processing configuration and execution section
    
    Args:
        df: DataFrame to process
    """
    render_section_header("Process Transcripts")
    
    st.markdown("""
    <div class="info-box">
        <h4 style="color: #D84E00 !important; margin: 0 0 0.5rem 0;">Processing Information</h4>
        <p style="margin: 0; color: #1A1A2E;">
            The AI will analyze each transcript for SOP compliance and identify missed points, 
            sequence compliance, and provide a summary. Processing time depends on the number 
            of transcripts (approximately 3-5 seconds per transcript).
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
        suggested_col = file_service.find_transcript_column(df)
        default_idx = columns.index(suggested_col) if suggested_col and suggested_col in columns else 0
        
        selected_transcript_col = st.selectbox(
            "Select the transcript column:",
            columns,
            index=default_idx,
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
    
    # Row 2: Transcript ID and Agent Name columns
    st.markdown("##### Optional: Map Excel Columns")
    col3, col4 = st.columns(2)
    
    with col3:
        # Find likely transcript_id column
        id_col_idx = 0
        for i, col in enumerate(columns):
            if 'transcript_id' in col.lower() or 'id' in col.lower():
                id_col_idx = i + 1  # +1 because of "(None - Auto-generate)" option
                break
        
        selected_transcript_id_col = st.selectbox(
            "Transcript ID column:",
            columns_with_none,
            index=id_col_idx,
            help="Column containing transcript IDs (optional - will auto-generate if not selected)"
        )
    
    with col4:
        # Find likely agent_name column
        agent_col_idx = 0
        for i, col in enumerate(columns):
            if 'agent' in col.lower() or 'name' in col.lower():
                agent_col_idx = i + 1  # +1 because of "(None - Auto-generate)" option
                break
        
        selected_agent_name_col = st.selectbox(
            "Agent Name column:",
            columns_with_none,
            index=agent_col_idx,
            help="Column containing agent names - AI bot or human (optional)"
        )
    
    # Process button
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Analysis", type="primary", use_container_width=True):
            with st.spinner("Initializing analysis..."):
                # Handle "None" selections
                transcript_id_col = None if selected_transcript_id_col == "(None - Auto-generate)" else selected_transcript_id_col
                agent_name_col = None if selected_agent_name_col == "(None - Auto-generate)" else selected_agent_name_col
                
                processed_df = process_transcripts(
                    df, 
                    selected_transcript_col, 
                    num_rows,
                    transcript_id_column=transcript_id_col,
                    agent_name_column=agent_name_col
                )
                st.session_state.processed_data = processed_df
                st.session_state.processing_complete = True
                time.sleep(1)
                st.rerun()


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
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Excel download
        excel_data = file_service.export_to_excel(processed_df)
        st.download_button(
            label="Download Excel (.xlsx)",
            data=excel_data,
            file_name=f"{base_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        # CSV download
        csv_data = file_service.export_to_csv(processed_df)
        st.download_button(
            label="Download CSV (.csv)",
            data=csv_data,
            file_name=f"{base_filename}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Reset button
        if st.button("Further Analysis", use_container_width=True):
            reset_session_state()
            st.rerun()


def main():
    """Main application entry point"""
    
    # Configure page
    configure_page()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main header
    # render_header()
    
    # File Upload Section with Clear button
    col_header, col_clear = st.columns([6, 1])
    
    with col_header:
        render_section_header("Upload Transcript File", "📁")
    
    with col_clear:
        st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)  # Spacer for alignment
        if st.button("🗑️ Clear All", type="secondary", use_container_width=True, help="Clear all data and start fresh"):
            reset_session_state()
            st.rerun()
    
    uploaded_file = render_file_uploader()
    
    if uploaded_file is not None:
        # Handle file upload
        if st.session_state.data is None or st.session_state.file_info is None:
            df, file_info, error = handle_file_upload(uploaded_file)
            
            if error:
                render_file_error(error)
                st.stop()  # Stop execution if there's an error
            else:
                st.session_state.data = df
                st.session_state.file_info = file_info
                st.session_state.file_uploaded = True
        
        # Display file info and data
        if st.session_state.data is not None and st.session_state.file_info is not None:
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
        # Show empty state
        if not st.session_state.file_uploaded:
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