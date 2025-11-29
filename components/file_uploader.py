"""
File Uploader Component
Handles file upload UI and validation display
"""

import streamlit as st
from typing import Optional, Callable
import pandas as pd

from services.file_service import FileService, FileInfo


def render_file_uploader(
    on_file_change: Optional[Callable] = None,
    allowed_types: list = ['xlsx', 'xls', 'csv']
) -> Optional[any]:
    """
    Render the file uploader component
    
    Args:
        on_file_change: Callback function when file changes
        allowed_types: List of allowed file extensions
        
    Returns:
        Uploaded file object or None
    """
    
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=allowed_types,
        help=f"Supported formats: {', '.join(allowed_types).upper()}",
        label_visibility="collapsed"
    )
    
    if uploaded_file and on_file_change:
        on_file_change(uploaded_file)
    
    return uploaded_file


def render_file_success(file_info: FileInfo):
    """
    Render success message after file upload
    
    Args:
        file_info: FileInfo object with file details
    """
    st.toast(f"File uploaded successfully: {file_info.filename}", icon="✅")


def render_file_error(error_message: str):
    """
    Render error message for file upload
    
    Args:
        error_message: Error message to display
    """
    
    error_html = f'''
    <div style="background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%); border-left: 5px solid #C62828; padding: 1.5rem 2rem; border-radius: 0 12px 12px 0; margin: 1.5rem 0;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.5rem;">❌</span>
            <div>
                <h3 style="color: #C62828 !important; margin: 0; font-size: 1.1rem;">Upload Error</h3>
                <p style="margin: 0.25rem 0 0 0; color: #1A1A2E;">{error_message}</p>
            </div>
        </div>
    </div>
    '''
    st.markdown(error_html, unsafe_allow_html=True)


def render_data_preview(df: pd.DataFrame, num_rows: int = 5):
    """
    Render data preview section
    
    Args:
        df: DataFrame to preview
        num_rows: Number of rows to show
    """
    
    preview_html = '''
    <div style="background: #FFFFFF; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 1rem;">
        <h4 style="color: #1A1A2E; margin: 0 0 1rem 0;">Data Preview</h4>
    </div>
    '''
    st.markdown(preview_html, unsafe_allow_html=True)
    
    # Column info expander
    with st.expander("📋 View Column Information", expanded=False):
        cols_display = ", ".join([f"`{col}`" for col in df.columns])
        st.markdown(f"**Available Columns ({len(df.columns)}):**")
        st.markdown(cols_display)
        
        # Column types
        st.markdown("**Column Data Types:**")
        col_types = pd.DataFrame({
            'Column': df.columns,
            'Type': [str(dtype) for dtype in df.dtypes]
        })
        st.dataframe(col_types, use_container_width=True, hide_index=True)
    
    # Data preview
    st.dataframe(
        df.head(num_rows),
        use_container_width=True,
        hide_index=False
    )
    
    st.info(f"📌 Showing first {min(num_rows, len(df))} of {len(df)} total rows")


def render_empty_state():
    """Render empty state when no file is uploaded"""
    
    empty_html = '''
    <div style="background: linear-gradient(135deg, #FFF8F0 0%, #FFF3E6 100%); border-left: 5px solid #E85D04; padding: 2rem; border-radius: 0 12px 12px 0; margin: 1.5rem 0;">
        <h3 style="color: #D84E00 !important; margin: 0 0 1rem 0;">Get Started</h3>
        <p style="margin: 0 0 1rem 0; color: #1A1A2E;">Upload an Excel or CSV file containing FNOL call transcripts to begin the analysis.</p>
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <p style="margin: 0 0 0.5rem 0; color: #1A1A2E; font-weight: 600;">📋 Required Columns:</p>
            <ul style="margin: 0; padding-left: 1.5rem; color: #666;">
                <li>Transcript ID (unique identifier for each call)</li>
                <li>Transcript/Call content (the actual conversation text)</li>
            </ul>
        </div>
        <div style="display: flex; gap: 1rem; margin-top: 1.5rem; flex-wrap: wrap;">
            <span style="background: #E85D04; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem;">📁 .xlsx</span>
            <span style="background: #E85D04; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem;">📁 .xls</span>
            <span style="background: #E85D04; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem;">📁 .csv</span>
        </div>
    </div>
    '''
    st.markdown(empty_html, unsafe_allow_html=True)
