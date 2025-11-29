"""
Metrics Component
Reusable metric display components
"""

import streamlit as st
from typing import Optional, Union

from services.file_service import FileInfo


def render_metrics(metrics: list):
    """
    Render a row of metric cards
    
    Args:
        metrics: List of tuples (label, value, delta, color)
    """
    
    cols = st.columns(len(metrics))
    
    for col, (label, value, delta, color) in zip(cols, metrics):
        with col:
            render_metric_card(label, value, delta, color)


def render_metric_card(
    label: str,
    value: Union[str, int, float],
    delta: Optional[str] = None,
    color: str = "#E85D04"
):
    """
    Render a single metric card
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta/change indicator
        color: Border color
    """
    
    delta_html = ""
    if delta:
        delta_color = "#2E7D32" if "✓" in delta or "+" in delta else "#C62828" if "⚠" in delta or "-" in delta else "#666"
        delta_html = f'<p style="color: {delta_color}; margin: 0.25rem 0 0 0; font-size: 0.8rem;">{delta}</p>'
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        text-align: center;
        border-top: 4px solid {color};
        transition: all 0.3s ease;
    ">
        <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">
            {label}
        </p>
        <h2 style="color: {color}; margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: 700;">
            {value}
        </h2>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_file_metrics(file_info: FileInfo):
    """
    Render file information metrics
    
    Args:
        file_info: FileInfo object containing file details
    """
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-left: 4px solid #E85D04;
        ">
            <p style="color: #666; margin: 0; font-size: 0.8rem;">TOTAL ROWS</p>
            <h3 style="color: #E85D04; margin: 0.5rem 0 0 0; font-size: 1.75rem;">{file_info.row_count:,}</h3>
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
            border-left: 4px solid #0077B6;
        ">
            <p style="color: #666; margin: 0; font-size: 0.8rem;">COLUMNS</p>
            <h3 style="color: #0077B6; margin: 0.5rem 0 0 0; font-size: 1.75rem;">{file_info.column_count}</h3>
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
            border-left: 4px solid #2E7D32;
        ">
            <p style="color: #666; margin: 0; font-size: 0.8rem;">FILE SIZE</p>
            <h3 style="color: #2E7D32; margin: 0.5rem 0 0 0; font-size: 1.75rem;">{file_info.size_formatted}</h3>
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
            border-left: 4px solid #6B2D8F;
        ">
            <p style="color: #666; margin: 0; font-size: 0.8rem;">FILE TYPE</p>
            <h3 style="color: #6B2D8F; margin: 0.5rem 0 0 0; font-size: 1.75rem;">{file_info.file_type}</h3>
        </div>
        """, unsafe_allow_html=True)


def render_processing_metrics(
    processed: int,
    total: int,
    elapsed_time: float,
    success_rate: float
):
    """
    Render processing progress metrics
    
    Args:
        processed: Number of items processed
        total: Total items to process
        elapsed_time: Time elapsed in seconds
        success_rate: Success rate percentage
    """
    
    avg_time = elapsed_time / processed if processed > 0 else 0
    remaining = total - processed
    eta = avg_time * remaining
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Processed", f"{processed}/{total}")
    
    with col2:
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        st.metric("Elapsed Time", f"{elapsed_time:.1f}s")
    
    with col4:
        st.metric("ETA", f"{eta:.1f}s")


def render_stat_card(
    title: str,
    value: Union[str, int, float],
    icon: str = "📊",
    description: Optional[str] = None,
    trend: Optional[str] = None,
    color: str = "#E85D04"
):
    """
    Render a detailed stat card
    
    Args:
        title: Card title
        value: Main value to display
        icon: Emoji icon
        description: Optional description
        trend: Optional trend indicator
        color: Accent color
    """
    
    trend_html = ""
    if trend:
        trend_color = "#2E7D32" if trend.startswith("+") or "↑" in trend else "#C62828" if trend.startswith("-") or "↓" in trend else "#666"
        trend_html = f"""
        <span style="
            color: {trend_color};
            font-size: 0.85rem;
            margin-left: 0.5rem;
        ">{trend}</span>
        """
    
    desc_html = ""
    if description:
        desc_html = f'<p style="color: #666; margin: 0.5rem 0 0 0; font-size: 0.85rem;">{description}</p>'
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 5px solid {color};
        transition: all 0.3s ease;
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.25rem;">{icon}</span>
            <span style="color: #666; font-weight: 600; text-transform: uppercase; font-size: 0.8rem;">
                {title}
            </span>
        </div>
        <div style="display: flex; align-items: baseline;">
            <h2 style="color: {color}; margin: 0; font-size: 2.25rem; font-weight: 700;">
                {value}
            </h2>
            {trend_html}
        </div>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)
