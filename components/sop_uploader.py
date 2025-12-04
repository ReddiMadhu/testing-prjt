"""
SOP Document Uploader Component
Handles uploading and validation of Word (.docx) SOP documents
"""

import streamlit as st
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class SOPFileInfo:
    """Information about uploaded SOP file"""
    name: str
    size: int
    content: str


def render_sop_uploader() -> Optional[any]:
    """
    Render the SOP document uploader widget
    
    Returns:
        Uploaded file object or None
    """
    st.markdown("""
    <div class="info-box">
        <h4 style="color: #D84E00 !important; margin: 0 0 0.5rem 0;">📄 Upload SOP Document</h4>
        <p style="margin: 0; color: #1A1A2E;">
            Upload your Standard Operating Procedure (SOP) document in Word format (.docx).
            The AI will analyze transcripts against this document to identify compliance gaps.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose SOP Document",
        type=["docx"],
        help="Upload a Word document (.docx) containing your SOP",
        key="sop_uploader"
    )
    
    return uploaded_file


def validate_sop_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate the uploaded SOP file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (is_valid, message)
    """
    if uploaded_file is None:
        return False, "No file uploaded"
    
    # Check file extension
    if not uploaded_file.name.lower().endswith('.docx'):
        return False, "Invalid file format. Please upload a Word document (.docx)"
    
    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if uploaded_file.size > max_size:
        return False, f"File too large. Maximum size is 10MB, got {uploaded_file.size / (1024*1024):.1f}MB"
    
    # Check minimum size (not empty)
    if uploaded_file.size < 100:
        return False, "File appears to be empty or too small"
    
    return True, "File is valid"


def render_sop_file_info(file_info: SOPFileInfo):
    """
    Render SOP file information after successful upload
    
    Args:
        file_info: SOPFileInfo object with file details
    """
    st.markdown(f"""
    <div style="
        background: #E8F5E9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E7D32;
        margin: 1rem 0;
    ">
        <p style="margin: 0; font-weight: 600; color: #2E7D32;">
            ✅ SOP Document Loaded Successfully
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
            <strong>File:</strong> {file_info.name} | 
            <strong>Size:</strong> {file_info.size / 1024:.1f} KB | 
            <strong>Content Length:</strong> {len(file_info.content)} characters
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sop_preview(content: str, max_chars: int = 500):
    """
    Render a preview of the SOP content
    
    Args:
        content: SOP document content
        max_chars: Maximum characters to show in preview
    """
    preview_text = content[:max_chars] + "..." if len(content) > max_chars else content
    
    with st.expander("📖 Preview SOP Content", expanded=False):
        st.markdown(f"""
        <div style="
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            line-height: 1.6;
            max-height: 300px;
            overflow-y: auto;
        ">
            {preview_text.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)


def render_sop_upload_error(error_message: str):
    """
    Render error message for SOP upload
    
    Args:
        error_message: Error message to display
    """
    st.markdown(f"""
    <div style="
        background: #FFEBEE;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #C62828;
        margin: 1rem 0;
    ">
        <p style="margin: 0; font-weight: 600; color: #C62828;">
            ❌ Error Loading SOP Document
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
            {error_message}
        </p>
    </div>
    """, unsafe_allow_html=True)
