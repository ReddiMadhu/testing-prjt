"""
EXL Email Agent - Document Search & Retrieval
Professional Streamlit UI for searching insurance documents across cloud storage
"""

import streamlit as st
import os
import sys
from datetime import datetime, date

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import mock storage functions
from mock_storage import search_files, create_mock_data, ACCOUNT_REGISTRY


# ============================================
# THEME CONFIGURATION
# ============================================

class EXLTheme:
    """EXL Brand Theme Configuration"""
    
    # Brand Colors
    PRIMARY_ORANGE = "#E85D04"
    PRIMARY_DARK = "#D84E00"
    PRIMARY_LIGHT = "#F57C2A"
    
    SECONDARY_DARK = "#1A1A2E"
    SECONDARY_GRAY = "#4A4A6A"
    
    ACCENT_BLUE = "#0077B6"
    ACCENT_TEAL = "#00B4D8"
    
    # Status Colors
    SUCCESS_GREEN = "#2E7D32"
    WARNING_YELLOW = "#F9A825"
    ERROR_RED = "#C62828"
    INFO_BLUE = "#1565C0"
    
    # Background Colors
    BG_LIGHT = "#f3f4f6"
    BG_CARD = "#FFFFFF"
    BG_DARK = "#1A1A2E"


def get_custom_css() -> str:
    """Generate complete custom CSS for Streamlit app"""
    return f"""
<style>
    /* ===== EXL Theme - Orange Brand Colors ===== */
    
    /* CSS Variables */
    :root {{
        --exl-orange: {EXLTheme.PRIMARY_ORANGE};
        --exl-orange-dark: {EXLTheme.PRIMARY_DARK};
        --exl-orange-light: {EXLTheme.PRIMARY_LIGHT};
        --exl-dark: {EXLTheme.SECONDARY_DARK};
        --exl-gray: {EXLTheme.SECONDARY_GRAY};
        --exl-blue: {EXLTheme.ACCENT_BLUE};
        --exl-teal: {EXLTheme.ACCENT_TEAL};
        --success: {EXLTheme.SUCCESS_GREEN};
        --warning: {EXLTheme.WARNING_YELLOW};
        --error: {EXLTheme.ERROR_RED};
        --info: {EXLTheme.INFO_BLUE};
    }}
    
    /* ===== Global Styles ===== */
    .stApp {{
        background-color: {EXLTheme.BG_LIGHT};
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    /* ===== Sidebar Styling ===== */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #FFFFFF 0%, #F8F9FA 100%);
        box-shadow: 4px 0 15px rgba(0, 0, 0, 0.08);
        border-right: 1px solid rgba(232, 93, 4, 0.15);
    }}
    
    [data-testid="stSidebar"] > div:first-child {{
        background: transparent;
    }}
    
    [data-testid="stSidebar"] * {{
        color: {EXLTheme.SECONDARY_DARK} !important;
    }}
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {{
        color: {EXLTheme.PRIMARY_ORANGE} !important;
        font-weight: 700;
    }}
    
    [data-testid="stSidebar"] hr {{
        border-color: rgba(232, 93, 4, 0.2);
        margin: 1.5rem 0;
    }}
    
    /* Sidebar toggle button */
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] > button {{
        background: linear-gradient(135deg, {EXLTheme.PRIMARY_ORANGE} 0%, {EXLTheme.PRIMARY_DARK} 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(232, 93, 4, 0.4) !important;
    }}
    
    [data-testid="stSidebarCollapsedControl"] button svg,
    [data-testid="collapsedControl"] > button svg {{
        fill: white !important;
        stroke: white !important;
    }}
    
    /* ===== Buttons ===== */
    .stButton > button {{
        background: linear-gradient(135deg, {EXLTheme.PRIMARY_ORANGE} 0%, {EXLTheme.PRIMARY_DARK} 100%);
        color: white !important;
        border: none;
        padding: 0.875rem 2.5rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.3px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(232, 93, 4, 0.3);
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(135deg, {EXLTheme.PRIMARY_LIGHT} 0%, {EXLTheme.PRIMARY_ORANGE} 100%);
        box-shadow: 0 6px 20px rgba(232, 93, 4, 0.4);
        transform: translateY(-2px);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
        box-shadow: 0 2px 10px rgba(232, 93, 4, 0.3);
    }}
    
    /* ===== Info Boxes ===== */
    .info-box {{
        background: linear-gradient(135deg, #FFF8F0 0%, #FFF3E6 100%);
        border-left: 5px solid {EXLTheme.PRIMARY_ORANGE};
        padding: 1.5rem 2rem;
        border-radius: 0 12px 12px 0;
        margin: 1.5rem 0;
        box-shadow: 0 2px 12px rgba(232, 93, 4, 0.1);
    }}
    
    .info-box h3, .info-box h4 {{
        color: {EXLTheme.PRIMARY_DARK} !important;
        margin-top: 0;
    }}
    
    /* Success Box */
    .success-box {{
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left: 5px solid {EXLTheme.SUCCESS_GREEN};
        padding: 1.5rem 2rem;
        border-radius: 0 12px 12px 0;
        margin: 1.5rem 0;
        box-shadow: 0 2px 12px rgba(46, 125, 50, 0.1);
    }}
    
    /* Warning Box */
    .warning-box {{
        background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
        border-left: 5px solid {EXLTheme.WARNING_YELLOW};
        padding: 1.5rem 2rem;
        border-radius: 0 12px 12px 0;
        margin: 1.5rem 0;
    }}
    
    /* Error Box */
    .error-box {{
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-left: 5px solid {EXLTheme.ERROR_RED};
        padding: 1.5rem 2rem;
        border-radius: 0 12px 12px 0;
        margin: 1.5rem 0;
    }}
    
    /* ===== Metrics ===== */
    [data-testid="stMetricValue"] {{
        color: {EXLTheme.PRIMARY_ORANGE} !important;
        font-weight: 800;
        font-size: 2rem !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {EXLTheme.SECONDARY_GRAY} !important;
        font-weight: 600;
    }}
    
    /* Metric Card Container */
    .metric-card {{
        background: {EXLTheme.BG_CARD};
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid rgba(232, 93, 4, 0.1);
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        box-shadow: 0 4px 20px rgba(232, 93, 4, 0.15);
        transform: translateY(-2px);
    }}
    
    /* ===== Form Inputs ===== */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stDateInput > div > div > input {{
        border-color: rgba(232, 93, 4, 0.3) !important;
        border-radius: 10px !important;
    }}
    
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stDateInput > div > div > input:focus {{
        border-color: {EXLTheme.PRIMARY_ORANGE} !important;
        box-shadow: 0 0 0 3px rgba(232, 93, 4, 0.2) !important;
    }}
    
    /* ===== Progress Bar ===== */
    .stProgress > div > div {{
        background: linear-gradient(90deg, {EXLTheme.PRIMARY_ORANGE} 0%, {EXLTheme.PRIMARY_LIGHT} 100%);
        border-radius: 10px;
    }}
    
    /* ===== Cards ===== */
    .card {{
        background: {EXLTheme.BG_CARD};
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }}
    
    .card:hover {{
        box-shadow: 0 8px 30px rgba(232, 93, 4, 0.12);
    }}
    
    /* ===== Results Card ===== */
    .result-card {{
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid {EXLTheme.PRIMARY_ORANGE};
        transition: all 0.3s ease;
    }}
    
    .result-card:hover {{
        box-shadow: 0 4px 16px rgba(232, 93, 4, 0.15);
        transform: translateX(4px);
    }}
    
    /* ===== Status Badges ===== */
    .status-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    
    .status-ready {{
        background: linear-gradient(135deg, {EXLTheme.SUCCESS_GREEN} 0%, #1B5E20 100%);
        color: white;
    }}
    
    .status-pending {{
        background: linear-gradient(135deg, {EXLTheme.WARNING_YELLOW} 0%, #F57F17 100%);
        color: {EXLTheme.SECONDARY_DARK};
    }}
    
    .status-error {{
        background: linear-gradient(135deg, {EXLTheme.ERROR_RED} 0%, #B71C1C 100%);
        color: white;
    }}
    
    /* ===== Storage Type Badges ===== */
    .storage-aws {{
        background: linear-gradient(135deg, #FF9900 0%, #E68A00 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    
    .storage-azure {{
        background: linear-gradient(135deg, #0078D4 0%, #005A9E 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    
    .storage-local {{
        background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    
    /* ===== Animations ===== */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.5s ease-out;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.7; }}
    }}
    
    .pulse {{
        animation: pulse 2s ease-in-out infinite;
    }}
    
    /* ===== Responsive Adjustments ===== */
    @media (max-width: 768px) {{
        .main-header {{
            padding: 1.5rem;
        }}
        
        .main-header h1 {{
            font-size: 1.75rem;
        }}
        
        .metric-card {{
            padding: 1rem;
        }}
    }}
</style>
"""


# ============================================
# UI COMPONENTS
# ============================================

def render_sidebar():
    """Render the sidebar component with EXL branding and status"""
    
    with st.sidebar:
        # Logo section
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 1.5rem 0;">
            <div style="
                background: linear-gradient(135deg, #E85D04 0%, #D84E00 100%);
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
                Email Agent
            </h3>
            <p style="color: #666666; font-size: 0.85rem; margin-top: 0.25rem;">
                Document Search & Retrieval
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # System Status Section
        st.markdown("### 📊 System Status")
        
        # Status indicators
        status_items = [
            ("AWS S3", "ready", "🟢"),
            ("Azure Blob", "ready", "🟢"),
            ("Local Storage", "ready", "🟢"),
            ("API Connection", "ready", "🟢"),
        ]
        
        for name, status, icon in status_items:
            status_color = "#2E7D32" if status == "ready" else "#F9A825"
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0;
                border-bottom: 1px solid #eee;
            ">
                <span style="color: #1A1A2E; font-size: 0.9rem;">{name}</span>
                <span style="color: {status_color};">{icon}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # About section
        st.markdown("### ℹ️ About")
        st.markdown("""
        <div style="font-size: 0.85rem; color: #666;">
            Intelligent document retrieval agent for insurance claims.
            Searches across AWS S3, Azure Blob, and local storage based on 
            account configuration and policy details.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Supported Accounts
        st.markdown("### 🏢 Configured Accounts")
        
        for account, config in ACCOUNT_REGISTRY.items():
            if account != "DEFAULT":
                storage_type = config.get("storage_type", "Unknown")
                badge_class = {
                    "AWS_S3": "storage-aws",
                    "AZURE_BLOB": "storage-azure",
                    "LOCAL": "storage-local"
                }.get(storage_type, "storage-local")
                
                st.markdown(f"""
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.4rem 0;
                ">
                    <span style="font-weight: 600; color: #1A1A2E;">{account}</span>
                    <span class="{badge_class}">{storage_type.replace('_', ' ')}</span>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Utility buttons
        if st.button("🔄 Initialize Mock Data", use_container_width=True):
            with st.spinner("Creating mock data..."):
                try:
                    create_mock_data()
                    st.success("✅ Mock data created!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def render_header():
    """Render the main header component"""
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #E85D04 0%, #D84E00 40%, #1A1A2E 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(232, 93, 4, 0.25);
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: -50%;
            right: -10%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            border-radius: 50%;
        "></div>
        <div style="position: relative; z-index: 1;">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                <div style="
                    background: white;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <span style="
                        color: #E85D04;
                        font-size: 1.5rem;
                        font-weight: 800;
                        letter-spacing: 2px;
                    ">EXL</span>
                </div>
                <span style="color: rgba(255,255,255,0.5); font-size: 2rem; font-weight: 200;">|</span>
                <span style="
                    color: rgba(255,255,255,0.9);
                    font-size: 0.9rem;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                ">Insurance Document Platform</span>
            </div>
            <h1 style="
                color: white !important;
                margin: 0.5rem 0;
                font-size: 2.25rem;
                font-weight: 700;
                letter-spacing: -0.5px;
            ">Email Agent - Document Search</h1>
            <p style="
                color: rgba(255,255,255,0.85) !important;
                margin: 0.5rem 0 0 0;
                font-size: 1.1rem;
                font-weight: 400;
            ">AI-Powered Document Retrieval Across Multi-Cloud Storage</p>
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <span style="
                    background: rgba(255,255,255,0.15);
                    padding: 0.35rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    color: white;
                ">📧 Email Parsing</span>
                <span style="
                    background: rgba(255,255,255,0.15);
                    padding: 0.35rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    color: white;
                ">☁️ Multi-Cloud</span>
                <span style="
                    background: rgba(255,255,255,0.15);
                    padding: 0.35rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    color: white;
                ">🔍 Smart Search</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title: str, icon: str = "📌"):
    """Render a section header"""
    
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid #E85D04;
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


def render_search_form():
    """Render the search form with styled inputs"""
    
    render_section_header("Search Parameters", "🔍")
    
    st.markdown("""
    <div class="info-box">
        <h4 style="color: #D84E00 !important; margin: 0 0 0.5rem 0;">Search Information</h4>
        <p style="margin: 0; color: #1A1A2E;">
            Enter the policy details to search for loss run documents across configured storage locations.
            The agent will automatically route to the correct storage based on account configuration.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create form columns
    col1, col2 = st.columns(2)
    
    with col1:
        account_name = st.selectbox(
            "🏢 Account Name",
            options=["CHUBBS", "AMEX", "TRAVELERS"],
            help="Select the insurance account"
        )
        
        policy_id = st.text_input(
            "📋 Policy ID",
            placeholder="e.g., 2456",
            help="Enter the policy identifier"
        )
    
    with col2:
        lob = st.selectbox(
            "📁 Line of Business (LoB)",
            options=["WC", "AUTO", "GL", "PROPERTY", "LIABILITY"],
            help="Select the line of business"
        )
        
        search_date = st.date_input(
            "📅 Document Date",
            value=date(2024, 9, 21),
            help="Select the document date to search for"
        )
    
    # Format date for search
    formatted_date = search_date.strftime("%d-%m-%Y") if search_date else ""
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Search button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_clicked = st.button(
            "🔍 Search Documents",
            type="primary",
            use_container_width=True
        )
    
    return {
        "account_name": account_name,
        "lob": lob,
        "policy_id": policy_id,
        "date": formatted_date,
        "search_clicked": search_clicked
    }


def render_search_results(results: list, search_params: dict):
    """Render search results in a styled format"""
    
    render_section_header("Search Results", "📄")
    
    if not results:
        st.markdown("""
        <div class="warning-box">
            <h4 style="color: #F9A825 !important; margin: 0 0 0.5rem 0;">⚠️ No Documents Found</h4>
            <p style="margin: 0; color: #1A1A2E;">
                No documents matching your search criteria were found. Please verify the search parameters 
                or try initializing mock data from the sidebar.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show search details
        with st.expander("🔍 Search Details"):
            st.json(search_params)
        
        return
    
    # Success message
    st.markdown(f"""
    <div class="success-box">
        <h4 style="color: #2E7D32 !important; margin: 0 0 0.5rem 0;">✅ Documents Found</h4>
        <p style="margin: 0; color: #1A1A2E;">
            Found <strong>{len(results)}</strong> document(s) matching your search criteria.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Results metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents Found", len(results))
    with col2:
        st.metric("Account", search_params.get("account_name", "N/A"))
    with col3:
        st.metric("Policy ID", search_params.get("policy_id", "N/A"))
    with col4:
        # Get storage type from first result
        storage_type = results[0].get("source", "Unknown") if results else "N/A"
        st.metric("Storage", storage_type.replace("_", " "))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display each result as a styled card
    for idx, doc in enumerate(results, 1):
        storage_badge = {
            "AWS_S3": "storage-aws",
            "AZURE_BLOB": "storage-azure",
            "LOCAL": "storage-local"
        }.get(doc.get("source", ""), "storage-local")
        
        st.markdown(f"""
        <div class="result-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h4 style="margin: 0 0 0.5rem 0; color: #1A1A2E;">
                        📄 {doc.get("filename", "Unknown")}
                    </h4>
                    <p style="margin: 0; font-size: 0.85rem; color: #666;">
                        <strong>Path:</strong> {doc.get("path", "N/A")}
                    </p>
                    <p style="margin: 0.25rem 0 0 0; font-size: 0.85rem; color: #666;">
                        <strong>Account:</strong> {doc.get("account", "N/A")}
                    </p>
                </div>
                <span class="{storage_badge}">{doc.get("source", "Unknown").replace("_", " ")}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Download/Action buttons
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📥 Download All", use_container_width=True):
            st.info("📥 Download functionality would be implemented here")
    
    with col2:
        if st.button("📧 Send via Email", use_container_width=True):
            st.info("📧 Email functionality would be implemented here")


def render_empty_state():
    """Render empty state when no search has been performed"""
    
    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #FFF8F0 0%, #FFFFFF 100%);
        border-radius: 16px;
        border: 2px dashed #E85D04;
        margin: 2rem 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
        <h3 style="color: #1A1A2E; margin: 0 0 0.5rem 0;">Ready to Search</h3>
        <p style="color: #666; max-width: 400px; margin: 0 auto;">
            Enter the policy details above and click "Search Documents" to find 
            loss run reports across configured cloud storage locations.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# MAIN APPLICATION
# ============================================

def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="EXL Email Agent - Document Search",
        page_icon="📧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom theme
    st.markdown(get_custom_css(), unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'search_results': None,
        'search_performed': False,
        'last_search_params': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """Main application entry point"""
    
    # Configure page
    configure_page()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main header
    render_header()
    
    # Render search form
    search_params = render_search_form()
    
    # Handle search
    if search_params["search_clicked"]:
        if not search_params["policy_id"]:
            st.error("⚠️ Please enter a Policy ID to search")
        else:
            with st.spinner("🔍 Searching across storage locations..."):
                # Perform search
                results = search_files(
                    account_name=search_params["account_name"],
                    lob=search_params["lob"],
                    policy_id=search_params["policy_id"],
                    date=search_params["date"]
                )
                
                # Store results in session state
                st.session_state.search_results = results
                st.session_state.search_performed = True
                st.session_state.last_search_params = search_params
    
    # Display results or empty state
    if st.session_state.search_performed:
        render_search_results(
            st.session_state.search_results,
            st.session_state.last_search_params
        )
    else:
        render_empty_state()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #666;">
        <p style="margin: 0; font-size: 0.85rem;">
            <strong>EXL Email Agent</strong> | Document Search & Retrieval v1.0
        </p>
        <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem;">
            Powered by © 2025 EXL Service
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
