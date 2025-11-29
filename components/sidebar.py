"""
Sidebar Component
EXL branded sidebar with navigation and information
"""

import streamlit as st
import base64
from pathlib import Path


def get_base64_image(image_path: str) -> str:
    """Convert image to base64 for embedding in HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""


def render_sidebar():
    """Render the sidebar component with EXL branding"""
    
    with st.sidebar:
        # Logo section
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 1.5rem 0;">
            <div style="
                background: white;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                display: inline-block;
                box-shadow: 0 4px 15px rgba(232, 93, 4, 0.3);
            ">
                <h2 style="
                    color: #FFFFFF !important;
                    margin: 0;
                    font-size: 2rem;
                    font-weight: 800;
                    letter-spacing: 2px;
                ">EXL</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # App title
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h3 style="color: #E85D04 !important; margin: 0; font-size: 1.1rem;">
                FNOL Transcript Analyzer
            </h3>
            <p style="color: #666666; font-size: 0.85rem; margin-top: 0.25rem;">
                AI-Powered Compliance Analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # About section
        st.markdown("### About")
        st.markdown("""
        Industrial-grade analysis platform for First Notice of Loss (FNOL) 
        call transcripts. Identifies missing SOP elements and compliance 
        issues using advanced AI technology.
        """)
        
        st.markdown("---")

        # Model Selection
        st.markdown("### AI Model")
        
        # Initialize session state for provider if not exists
        if 'llm_provider' not in st.session_state:
            # Default to gemini as per .env preference or fallback to claude
            st.session_state.llm_provider = "gemini"
        
        provider_options = ["Claude", "Gemini", "OpenAI"]
        current_index = 0
        if st.session_state.llm_provider == "gemini":
            current_index = 1
        elif st.session_state.llm_provider == "openai":
            current_index = 2
            
        selected_provider = st.radio(
            "Select Provider:",
            provider_options,
            index=current_index,
            key="provider_radio",
            help="Choose the AI model for analysis (Claude, Gemini, or OpenAI/Azure OpenAI)"
        )
        
        # Update session state
        st.session_state.llm_provider = selected_provider.lower()

      