"""
EXL Theme Configuration
Industrial-grade theming with EXL brand colors (Orange)
"""


class EXLTheme:
    """
    EXL Brand Theme Configuration
    Primary color: Orange (#E85D04)
    """
    
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
    
    # Text Colors
    TEXT_PRIMARY = "#1A1A2E"
    TEXT_SECONDARY = "#666666"
    TEXT_LIGHT = "#FFFFFF"
    
    @classmethod
    def get_custom_css(cls) -> str:
        """Generate complete custom CSS for Streamlit app"""
        return f"""
<style>
    /* ===== EXL Theme - Orange Brand Colors ===== */
    
    /* CSS Variables */
    :root {{
        --exl-orange: {cls.PRIMARY_ORANGE};
        --exl-orange-dark: {cls.PRIMARY_DARK};
        --exl-orange-light: {cls.PRIMARY_LIGHT};
        --exl-dark: {cls.SECONDARY_DARK};
        --exl-gray: {cls.SECONDARY_GRAY};
        --exl-blue: {cls.ACCENT_BLUE};
        --exl-teal: {cls.ACCENT_TEAL};
        --success: {cls.SUCCESS_GREEN};
        --warning: {cls.WARNING_YELLOW};
        --error: {cls.ERROR_RED};
        --info: {cls.INFO_BLUE};
    }}
    
    /* ===== Global Styles ===== */
    .stApp {{
        background-color: {cls.BG_LIGHT};
    }}
    
    /* Hide Streamlit branding but keep header for sidebar toggle */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Style the header/toolbar area */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    /* Ensure sidebar toggle button is always visible */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarNavCollapseButton"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {{
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
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
        color: {cls.TEXT_PRIMARY} !important;
    }}
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {{
        color: {cls.PRIMARY_ORANGE} !important;
        font-weight: 700;
    }}
    
    [data-testid="stSidebar"] hr {{
        border-color: rgba(232, 93, 4, 0.2);
        margin: 1.5rem 0;
    }}
    
    /* ===== Sidebar Toggle Button ===== */
    [data-testid="stSidebarCollapsedControl"] {{
        background: transparent !important;
    }}
    
    [data-testid="stSidebarCollapsedControl"] button {{
        background: linear-gradient(135deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_DARK} 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(232, 93, 4, 0.4) !important;
        transition: all 0.3s ease !important;
    }}
    
    [data-testid="stSidebarCollapsedControl"] button:hover {{
        background: linear-gradient(135deg, {cls.PRIMARY_LIGHT} 0%, {cls.PRIMARY_ORANGE} 100%) !important;
        box-shadow: 0 6px 16px rgba(232, 93, 4, 0.5) !important;
        transform: scale(1.05);
    }}
    
    [data-testid="stSidebarCollapsedControl"] button svg {{
        fill: white !important;
        stroke: white !important;
    }}
    
    /* Sidebar collapse button inside sidebar */
    [data-testid="stSidebar"] button[kind="header"] {{
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }}
    
    [data-testid="stSidebar"] button[kind="header"]:hover {{
        background: rgba(255, 255, 255, 0.25) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
    }}
    
    [data-testid="stSidebar"] button[kind="header"] svg {{
        fill: white !important;
        stroke: white !important;
    }}
    
    /* Alternative sidebar toggle selectors for compatibility */
    button[data-testid="baseButton-header"] {{
        background: linear-gradient(135deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_DARK} 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(232, 93, 4, 0.4) !important;
    }}
    
    button[data-testid="baseButton-header"]:hover {{
        background: linear-gradient(135deg, {cls.PRIMARY_LIGHT} 0%, {cls.PRIMARY_ORANGE} 100%) !important;
    }}
    
    button[data-testid="baseButton-header"] svg {{
        fill: white !important;
        stroke: white !important;
    }}
    
    /* Collapsed sidebar button */
    [data-testid="collapsedControl"] {{
        background: transparent !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 0.5rem !important;
        left: 0.5rem !important;
        z-index: 999999 !important;
    }}
    
    [data-testid="collapsedControl"] > button {{
        background: linear-gradient(135deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_DARK} 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(232, 93, 4, 0.4) !important;
        visibility: visible !important;
        opacity: 1 !important;
    }}
    
    [data-testid="collapsedControl"] > button:hover {{
        background: linear-gradient(135deg, {cls.PRIMARY_LIGHT} 0%, {cls.PRIMARY_ORANGE} 100%) !important;
        box-shadow: 0 6px 16px rgba(232, 93, 4, 0.5) !important;
    }}
    
    [data-testid="collapsedControl"] > button svg {{
        fill: white !important;
        stroke: white !important;
    }}
    
    /* Additional selectors for sidebar expand button when collapsed */
    section[data-testid="stSidebarCollapsedControl"] {{
        visibility: visible !important;
        opacity: 1 !important;
        display: block !important;
        position: fixed !important;
        top: 0.75rem !important;
        left: 0.75rem !important;
        z-index: 999999 !important;
    }}
    
    section[data-testid="stSidebarCollapsedControl"] button {{
        background: linear-gradient(135deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_DARK} 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(232, 93, 4, 0.4) !important;
        padding: 0.5rem !important;
        cursor: pointer !important;
    }}
    
    section[data-testid="stSidebarCollapsedControl"] button svg {{
        fill: white !important;
        stroke: white !important;
        width: 1.25rem !important;
        height: 1.25rem !important;
    }}
    
    /* ===== Main Header ===== */
    .main-header {{
        background: linear-gradient(135deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_DARK} 50%, {cls.SECONDARY_DARK} 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(232, 93, 4, 0.25);
        position: relative;
        overflow: hidden;
    }}
    
    .main-header::before {{
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 40%;
        height: 100%;
        background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.1) 100%);
    }}
    
    .main-header h1 {{
        color: white !important;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }}
    
    .main-header p {{
        color: rgba(255,255,255,0.9) !important;
        margin: 0.75rem 0 0 0;
        font-size: 1.15rem;
        font-weight: 400;
    }}
    
    /* ===== Logo Container ===== */
    .logo-container {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }}
    
    .logo-container img {{
        height: 50px;
        filter: brightness(0) invert(1);
    }}
    
    /* ===== Buttons ===== */
    .stButton > button {{
        background: linear-gradient(135deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_DARK} 100%);
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
        background: linear-gradient(135deg, {cls.PRIMARY_LIGHT} 0%, {cls.PRIMARY_ORANGE} 100%);
        box-shadow: 0 6px 20px rgba(232, 93, 4, 0.4);
        transform: translateY(-2px);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
        box-shadow: 0 2px 10px rgba(232, 93, 4, 0.3);
    }}
    
    /* Secondary Button Style */
    .secondary-btn > button {{
        background: transparent !important;
        border: 2px solid {cls.PRIMARY_ORANGE} !important;
        color: {cls.PRIMARY_ORANGE} !important;
    }}
    
    .secondary-btn > button:hover {{
        background: rgba(232, 93, 4, 0.1) !important;
    }}
    
    /* ===== Info Boxes ===== */
    .info-box {{
        background: linear-gradient(135deg, #FFF8F0 0%, #FFF3E6 100%);
        border-left: 5px solid {cls.PRIMARY_ORANGE};
        padding: 1.5rem 2rem;
        border-radius: 0 12px 12px 0;
        margin: 1.5rem 0;
        box-shadow: 0 2px 12px rgba(232, 93, 4, 0.1);
    }}
    
    .info-box h3, .info-box h4 {{
        color: {cls.PRIMARY_DARK} !important;
        margin-top: 0;
    }}
    
    /* Success Box */
    .success-box {{
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left: 5px solid {cls.SUCCESS_GREEN};
        padding: 1.5rem 2rem;
        border-radius: 0 12px 12px 0;
        margin: 1.5rem 0;
        box-shadow: 0 2px 12px rgba(46, 125, 50, 0.1);
    }}
    
    .success-box h3 {{
        color: {cls.SUCCESS_GREEN} !important;
        margin-top: 0;
    }}
    
    /* Warning Box */
    .warning-box {{
        background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
        border-left: 5px solid {cls.WARNING_YELLOW};
        padding: 1.5rem 2rem;
        border-radius: 0 12px 12px 0;
        margin: 1.5rem 0;
    }}
    
    /* Error Box */
    .error-box {{
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-left: 5px solid {cls.ERROR_RED};
        padding: 1.5rem 2rem;
        border-radius: 0 12px 12px 0;
        margin: 1.5rem 0;
    }}
    
    /* ===== Metrics ===== */
    [data-testid="stMetricValue"] {{
        color: {cls.PRIMARY_ORANGE} !important;
        font-weight: 800;
        font-size: 2rem !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {cls.SECONDARY_GRAY} !important;
        font-weight: 600;
    }}
    
    [data-testid="stMetricDelta"] svg {{
        stroke: {cls.PRIMARY_ORANGE};
    }}
    
    /* Metric Card Container */
    .metric-card {{
        background: {cls.BG_CARD};
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
    
    /* ===== File Uploader ===== */
    [data-testid="stFileUploader"] {{
        border: 2px dashed {cls.PRIMARY_ORANGE};
        border-radius: 16px;
        padding: 2.5rem;
        background: linear-gradient(135deg, #FFF8F0 0%, {cls.BG_CARD} 100%);
        transition: all 0.3s ease;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: {cls.PRIMARY_DARK};
        background: linear-gradient(135deg, #FFF3E6 0%, {cls.BG_CARD} 100%);
    }}
    
    [data-testid="stFileUploader"] label {{
        color: {cls.PRIMARY_DARK} !important;
        font-weight: 600;
    }}
    
    /* ===== Dataframe & Tables ===== */
    .dataframe {{
        border: none !important;
        border-radius: 12px !important;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }}
    
    .dataframe thead th {{
        background: linear-gradient(135deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_DARK} 100%) !important;
        color: white !important;
        font-weight: 600;
        padding: 1rem !important;
    }}
    
    .dataframe tbody tr:nth-child(even) {{
        background-color: #FFF8F0;
    }}
    
    .dataframe tbody tr:hover {{
        background-color: #FFEDD5 !important;
    }}
    
    /* ===== Expander ===== */
    .streamlit-expanderHeader {{
        background: linear-gradient(135deg, #FFF8F0 0%, #FFF3E6 100%);
        border-radius: 10px;
        font-weight: 600;
        color: {cls.PRIMARY_DARK} !important;
        border: 1px solid rgba(232, 93, 4, 0.2);
    }}
    
    .streamlit-expanderHeader:hover {{
        background: linear-gradient(135deg, #FFF3E6 0%, #FFEDD5 100%);
    }}
    
    /* ===== Progress Bar ===== */
    .stProgress > div > div {{
        background: linear-gradient(90deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_LIGHT} 100%);
        border-radius: 10px;
    }}
    
    /* ===== Selectbox & Input ===== */
    .stSelectbox > div > div {{
        border-color: rgba(232, 93, 4, 0.3);
        border-radius: 10px;
    }}
    
    .stSelectbox > div > div:focus-within {{
        border-color: {cls.PRIMARY_ORANGE};
        box-shadow: 0 0 0 3px rgba(232, 93, 4, 0.2);
    }}
    
    /* ===== Slider ===== */
    .stSlider > div > div > div {{
        background: {cls.PRIMARY_ORANGE} !important;
    }}
    
    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: {cls.BG_CARD};
        border-radius: 10px 10px 0 0;
        border: 1px solid rgba(232, 93, 4, 0.2);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: {cls.SECONDARY_GRAY};
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {cls.PRIMARY_ORANGE} 0%, {cls.PRIMARY_DARK} 100%);
        color: white !important;
        border-color: {cls.PRIMARY_ORANGE};
    }}
    
    /* ===== Section Headers ===== */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid {cls.PRIMARY_ORANGE};
    }}
    
    .section-header h2 {{
        color: {cls.PRIMARY_DARK} !important;
        margin: 0;
        font-weight: 700;
    }}
    
    /* ===== Cards ===== */
    .card {{
        background: {cls.BG_CARD};
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }}
    
    .card:hover {{
        box-shadow: 0 8px 30px rgba(232, 93, 4, 0.12);
    }}
    
    /* ===== Severity Badges ===== */
    .severity-high {{
        background: linear-gradient(135deg, {cls.ERROR_RED} 0%, #B71C1C 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
    }}
    
    .severity-medium {{
        background: linear-gradient(135deg, {cls.WARNING_YELLOW} 0%, #F57F17 100%);
        color: {cls.SECONDARY_DARK};
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
    }}
    
    .severity-low {{
        background: linear-gradient(135deg, {cls.SUCCESS_GREEN} 0%, #1B5E20 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
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

    @classmethod
    def get_sidebar_logo_html(cls, logo_path: str = "assets/exl_logo.png") -> str:
        """Generate sidebar logo HTML"""
        return f"""
        <div style="text-align: center; padding: 1rem 0;">
            <img src="{logo_path}" alt="EXL Logo" style="max-width: 120px; margin-bottom: 0.5rem;">
        </div>
        """
    
    @classmethod
    def get_severity_color(cls, severity: str) -> str:
        """Get color for severity level"""
        severity_colors = {
            "High": cls.ERROR_RED,
            "Medium": cls.WARNING_YELLOW,
            "Low": cls.SUCCESS_GREEN,
            "Unknown": cls.SECONDARY_GRAY,
            "N/A": cls.SECONDARY_GRAY
        }
        return severity_colors.get(severity, cls.SECONDARY_GRAY)
    
    @classmethod
    def get_severity_bg_color(cls, severity: str) -> str:
        """Get background color for severity level"""
        severity_bg = {
            "High": "#FFEBEE",
            "Medium": "#FFF8E1",
            "Low": "#E8F5E9",
            "Unknown": "#F5F5F5",
            "N/A": "#F5F5F5"
        }
        return severity_bg.get(severity, "#F5F5F5")
