"""
Header Component
Main application header with EXL branding
"""

import streamlit as st


def render_header(
    title: str = "FNOL Transcript Analyzer",
    subtitle: str = "AI-Powered SOP Compliance Analysis for Insurance Call Transcripts"
):
    """
    Render the main header component
    
    Args:
        title: Main title text
        subtitle: Subtitle/description text
    """
    
    header_html = f'''
    <div style="background: linear-gradient(135deg, #E85D04 0%, #D84E00 40%, #1A1A2E 100%); padding: 2rem 2.5rem; border-radius: 16px; color: white; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(232, 93, 4, 0.25); position: relative; overflow: hidden;">
        <div style="position: absolute; top: -50%; right: -10%; width: 300px; height: 300px; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); border-radius: 50%;"></div>
        <div style="position: relative; z-index: 1;">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                <div style="background: white; padding: 0.5rem 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <span style="color: #E85D04; font-size: 1.5rem; font-weight: 800; letter-spacing: 2px;">EXL</span>
                </div>
                <span style="color: rgba(255,255,255,0.5); font-size: 2rem; font-weight: 200;">|</span>
                <span style="color: rgba(255,255,255,0.9); font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">Insurance Analytics Platform</span>
            </div>
            <h1 style="color: white !important; margin: 0.5rem 0; font-size: 2.25rem; font-weight: 700; letter-spacing: -0.5px;">{title}</h1>
            <p style="color: rgba(255,255,255,0.85) !important; margin: 0.5rem 0 0 0; font-size: 1.1rem; font-weight: 400;">{subtitle}</p>
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <span style="background: rgba(255,255,255,0.15); padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.8rem; color: white;">AI-Powered</span>
                <span style="background: rgba(255,255,255,0.15); padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.8rem; color: white;">Real-time Analysis</span>
                <span style="background: rgba(255,255,255,0.15); padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.8rem; color: white;">Enterprise Grade</span>
            </div>
        </div>
    </div>
    '''
    
    st.markdown(header_html, unsafe_allow_html=True)


def render_section_header(title: str, icon: str = "📌"):
    """
    Render a section header
    
    Args:
        title: Section title
        icon: Emoji icon for the section
    """
    
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.75rem;
    ">
        <span style="font-size: 1.5rem;">{icon}</span>
        <h2 style="
            color: #1A1A2E !important;
            margin: 0;
            font-weight: 700;
            font-size: 1.5rem;
        ">{title}</h2>
    </div>
    """, unsafe_allow_html=True)
