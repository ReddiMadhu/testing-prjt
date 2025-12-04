"""
SOP Analysis Display Component
Displays SOP analysis results in table format with download options and charts
"""

import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from io import BytesIO
from typing import List, Dict, Any, Optional
from collections import Counter

from services.sop_analysis_service import SOPAnalysisResult
from utils.helpers import generate_timestamp
from config.theme import EXLTheme


def render_sop_analysis_header():
    """Render the SOP analysis results header"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #E85D04, #D84E00);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
    ">
        <h2 style="margin: 0; color: white !important;">📊 SOP Compliance Analysis Results</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
            Analysis of transcripts against Standard Operating Procedure requirements
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sop_summary_metrics(result: SOPAnalysisResult):
    """
    Render summary metrics for SOP analysis
    
    Args:
        result: SOPAnalysisResult object
    """
    total_transcripts = len(result.transcript_results)
    
    # Calculate metrics with type safety
    transcripts_with_issues = 0
    total_mistakes = 0
    
    for r in result.transcript_results:
        sop_mistakes = r.get("sop_mistakes", [])
        if not isinstance(sop_mistakes, list):
            sop_mistakes = [sop_mistakes] if sop_mistakes else []
        
        if sop_mistakes:
            transcripts_with_issues += 1
            total_mistakes += len(sop_mistakes)
    
    compliance_rate = ((total_transcripts - transcripts_with_issues) / total_transcripts * 100) if total_transcripts > 0 else 100
    
    avg_mistakes = total_mistakes / total_transcripts if total_transcripts > 0 else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 Total Transcripts",
            value=total_transcripts
        )
    
    with col2:
        st.metric(
            label="⚠️ With SOP Issues",
            value=transcripts_with_issues,
            delta=f"-{total_transcripts - transcripts_with_issues} compliant" if transcripts_with_issues < total_transcripts else None
        )
    
    with col3:
        st.metric(
            label="✅ Compliance Rate",
            value=f"{compliance_rate:.1f}%"
        )
    
    with col4:
        st.metric(
            label="📊 Avg Mistakes/Call",
            value=f"{avg_mistakes:.1f}"
        )


def render_sop_results_table(result: SOPAnalysisResult, processed_df: Optional[pd.DataFrame] = None):
    """
    Render the SOP analysis results in a table format with original columns
    
    Args:
        result: SOPAnalysisResult object
        processed_df: Optional DataFrame with original processed data (for including previous columns)
    """
    st.markdown("### 📝 SOP Analysis Results")
    
    if not result.transcript_results:
        st.warning("No results to display")
        return
    
    # Create display dataframe with cleaner format
    display_data = []
    for item in result.transcript_results:
        # Start with transcript_id
        row_data = {
            "Transcript ID": str(item.get("transcript_id", "N/A"))
        }
        
        # Add original columns from processed_df if available
        if processed_df is not None and not processed_df.empty:

            
            transcript_id = item.get("transcript_id", "")
            # Find matching row in processed_df
            original_cols = ['mistakes', 'mistake_themes', 'root_cause', 'agent_behavior', 'severity']
            for col in original_cols:
                if col in processed_df.columns:
                    match_row = processed_df[processed_df['transcript_id'] == transcript_id]
                    if not match_row.empty:
                        val = match_row.iloc[0][col] if col in match_row.columns else "N/A"
                        # Format list values
                        if isinstance(val, list):
                            val = "; ".join(str(v) for v in val)
                        elif pd.isna(val):
                            val = "N/A"
                        row_data[col.replace('_', ' ').title()] = str(val) if val else "N/A"
        
        # Ensure sop_mistakes is a list
        sop_mistakes = item.get("sop_mistakes", [])
        if not isinstance(sop_mistakes, list):
            sop_mistakes = [str(sop_mistakes)] if sop_mistakes else []
        
        # Ensure sop_themes is a list
        sop_themes = item.get("sop_mistake_themes", [])
        if not isinstance(sop_themes, list):
            sop_themes = [str(sop_themes)] if sop_themes else []
        
        # Safely get string values
        reasoning = item.get("sop_mistakes_reasoning", "N/A")
        if not isinstance(reasoning, str):
            reasoning = str(reasoning) if reasoning else "N/A"
        
        improvements = item.get("sop_improvements", "N/A")
        if not isinstance(improvements, str):
            improvements = str(improvements) if improvements else "N/A"
        
        # Add SOP analysis columns
        row_data.update({
            "# SOP Mistakes": len(sop_mistakes),
            "SOP Mistakes": "; ".join(str(m) for m in sop_mistakes) if sop_mistakes else "None",
            "SOP Themes": ", ".join(str(t) for t in sop_themes) if sop_themes else "None",
            "SOP Reasoning": reasoning,
            "SOP Improvements": improvements
        })
        
        display_data.append(row_data)
    
    display_df = pd.DataFrame(display_data)
    
    # Build column config dynamically
    column_config = {
        "Transcript ID": st.column_config.TextColumn("Transcript ID", width="small"),
        "# SOP Mistakes": st.column_config.NumberColumn("# SOP Mistakes", width="small"),
        "SOP Mistakes": st.column_config.TextColumn("SOP Mistakes", width="large"),
        "SOP Themes": st.column_config.TextColumn("SOP Themes", width="medium"),
        "SOP Reasoning": st.column_config.TextColumn("SOP Reasoning", width="large"),
        "SOP Improvements": st.column_config.TextColumn("SOP Improvements", width="large")
    }
    
    # Add config for original columns if present
    if "Mistakes" in display_df.columns:
        column_config["Mistakes"] = st.column_config.TextColumn("Mistakes", width="medium")
    if "Mistake Themes" in display_df.columns:
        column_config["Mistake Themes"] = st.column_config.TextColumn("Mistake Themes", width="medium")
    if "Root Cause" in display_df.columns:
        column_config["Root Cause"] = st.column_config.TextColumn("Root Cause", width="medium")
    if "Agent Behavior" in display_df.columns:
        column_config["Agent Behavior"] = st.column_config.TextColumn("Agent Behavior", width="medium")
    if "Severity" in display_df.columns:
        column_config["Severity"] = st.column_config.TextColumn("Severity", width="small")
    
    # Display as dataframe with custom styling
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        column_config=column_config
    )


def render_sop_mistake_themes_chart(result: SOPAnalysisResult):
    """
    Render bar chart showing percentage distribution of SOP mistake themes
    
    Args:
        result: SOPAnalysisResult object
    """
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        📊 SOP Mistake Themes Distribution
    </h3>
    """, unsafe_allow_html=True)
    
    # Extract all SOP mistake themes from results
    all_themes = []
    for item in result.transcript_results:
        themes = item.get("sop_mistake_themes", [])
        if not isinstance(themes, list):
            themes = [str(themes)] if themes else []
        all_themes.extend(themes)
    
    if not all_themes:
        st.info("No SOP mistake themes to display")
        return
    
    # Count theme occurrences
    theme_counts = Counter(all_themes)
    total_themes = sum(theme_counts.values())
    
    # Create DataFrame for chart
    chart_data = pd.DataFrame([
        {'Theme': theme, 'Count': count, 'Percentage': (count / total_themes) * 100}
        for theme, count in theme_counts.most_common()
    ])
    
    # Calculate number of bars
    num_bars = len(chart_data)
    
    # Generate gradient colors from full orange to transparent
    exl_colors = []
    for i in range(num_bars):
        opacity = 1.0 - (i * 0.7 / max(num_bars - 1, 1))
        exl_colors.append(f'rgba(232, 93, 4, {opacity})')
    
    # Generate text colors - dark for transparent bars, white for opaque
    text_colors = []
    for i in range(num_bars):
        opacity = 1.0 - (i * 0.7 / max(num_bars - 1, 1))
        if opacity > 0.5:
            text_colors.append('white')
        else:
            text_colors.append('#1A1A2E')
    
    # Create horizontal bar chart with Plotly
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=chart_data['Theme'],
        x=chart_data['Percentage'],
        orientation='h',
        marker=dict(
            color=exl_colors,
            line=dict(color='#E85D04', width=1)
        ),
        text=[f"{p:.1f}%" for p in chart_data['Percentage']],
        textposition='inside',
        textfont=dict(color=text_colors, size=12),
        hovertemplate='<b>%{y}</b><br>Count: %{customdata}<br>Percentage: %{x:.1f}%<extra></extra>',
        customdata=chart_data['Count']
    ))
    
    fig.update_layout(
        title='<b>% of SOP Mistake Themes</b>',
        xaxis_title='Percentage (%)',
        yaxis_title='',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=40),
        height=max(300, len(chart_data) * 40 + 100),
        showlegend=False,
        yaxis=dict(autorange='reversed'),
        xaxis=dict(range=[0, max(chart_data['Percentage']) * 1.15], gridcolor='rgba(0,0,0,0.1)')
    )
    
    # Add border styling
    fig.update_xaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    fig.update_yaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    
    st.plotly_chart(fig, use_container_width=True)


def render_sop_themes_vs_agents_chart(result: SOPAnalysisResult):
    """
    Render horizontal bar chart showing each SOP Mistake Theme and how many agents committed it
    
    Args:
        result: SOPAnalysisResult object
    """
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        ⚠️ SOP Mistake Themes vs Agents
    </h3>
    """, unsafe_allow_html=True)
    
    # Count unique agents per SOP mistake theme
    theme_agent_data = {}
    for item in result.transcript_results:
        agent_name = item.get("agent_name", "Unknown")
        themes = item.get("sop_mistake_themes", [])
        if not isinstance(themes, list):
            themes = [str(themes)] if themes else []
        
        for theme in themes:
            if theme not in theme_agent_data:
                theme_agent_data[theme] = set()
            theme_agent_data[theme].add(agent_name)
    
    if not theme_agent_data:
        st.info("No SOP mistake themes to display")
        return
    
    # Create DataFrame with theme and agent count
    chart_data = pd.DataFrame([
        {'Theme': theme, 'Agent Count': len(agents)}
        for theme, agents in theme_agent_data.items()
    ])
    chart_data = chart_data.sort_values('Agent Count', ascending=True)
    
    # Generate EXL gradient colors (orange to transparent)
    num_bars = len(chart_data)
    bar_colors = []
    for i in range(num_bars):
        opacity = 0.3 + (i * 0.7 / max(num_bars - 1, 1))
        bar_colors.append(f'rgba(232, 93, 4, {opacity})')
    
    # Generate text colors based on opacity
    text_colors = []
    for i in range(num_bars):
        opacity = 0.3 + (i * 0.7 / max(num_bars - 1, 1))
        if opacity > 0.5:
            text_colors.append('white')
        else:
            text_colors.append('#1A1A2E')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=chart_data['Theme'],
        x=chart_data['Agent Count'],
        orientation='h',
        marker=dict(
            color=bar_colors,
            line=dict(color='#E85D04', width=1)
        ),
        text=chart_data['Agent Count'],
        textposition='inside',
        textfont=dict(color=text_colors, size=12, weight='bold'),
        hovertemplate='<b>%{y}</b><br>Agents with this mistake: %{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Agents per SOP Mistake Theme</b>',
        xaxis_title='Number of Agents',
        yaxis_title='',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=40),
        height=max(300, len(chart_data) * 40 + 100),
        showlegend=False
    )
    
    fig.update_xaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    
    st.plotly_chart(fig, use_container_width=True)


def render_agent_vs_sop_themes_chart(result: SOPAnalysisResult):
    """
    Render horizontal stacked bar chart showing Agent vs SOP Mistake Themes distribution
    
    Args:
        result: SOPAnalysisResult object
    """
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        👤 Agent vs SOP Mistake Themes
    </h3>
    """, unsafe_allow_html=True)
    
    # Collect agent-theme data
    agent_theme_data = []
    for item in result.transcript_results:
        agent_name = item.get("agent_name", "Unknown")
        themes = item.get("sop_mistake_themes", [])
        if not isinstance(themes, list):
            themes = [str(themes)] if themes else []
        
        for theme in themes:
            agent_theme_data.append({'agent': agent_name, 'theme': theme})
    
    if not agent_theme_data:
        st.info("No data available for Agent vs SOP Themes chart")
        return
    
    # Create DataFrame and count
    at_df = pd.DataFrame(agent_theme_data)
    at_counts = at_df.groupby(['agent', 'theme']).size().reset_index(name='count')
    
    # Sort agents by total mistake count (highest to lowest)
    agent_totals = at_counts.groupby('agent')['count'].sum().sort_values(ascending=False)
    agents = agent_totals.index.tolist()
    
    # Sort themes by total count (highest to lowest)
    theme_totals = at_counts.groupby('theme')['count'].sum().sort_values(ascending=False)
    themes = theme_totals.index.tolist()
    
    # Generate EXL gradient colors (orange to transparent) for themes
    num_themes = len(themes)
    theme_colors = []
    for i in range(num_themes):
        opacity = 1.0 - (i * 0.6 / max(num_themes - 1, 1))
        theme_colors.append(f'rgba(232, 93, 4, {opacity})')
    
    fig = go.Figure()
    
    for i, theme in enumerate(themes):
        theme_data = at_counts[at_counts['theme'] == theme]
        counts = []
        for agent in agents:
            agent_theme_count = theme_data[theme_data['agent'] == agent]['count'].sum()
            counts.append(agent_theme_count)
        
        fig.add_trace(go.Bar(
            y=agents,
            x=counts,
            name=theme,
            orientation='h',
            marker=dict(color=theme_colors[i], line=dict(color='#E85D04', width=0.5)),
            hovertemplate=f'<b>{theme}</b><br>Agent: %{{y}}<br>Count: %{{x}}<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        xaxis_title='Count',
        yaxis_title='',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=250, t=10, b=80),
        height=max(400, len(agents) * 50 + 100),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=9),
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='#E85D04',
            borderwidth=1,
            tracegroupgap=2
        ),
        yaxis=dict(categoryorder='array', categoryarray=agents[::-1])
    )
    
    fig.update_xaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    
    st.plotly_chart(fig, use_container_width=True)


def export_to_excel(result: SOPAnalysisResult, processed_df: Optional[pd.DataFrame] = None) -> bytes:
    """
    Export SOP analysis results to Excel with all columns
    
    Args:
        result: SOPAnalysisResult object
        processed_df: Optional DataFrame with original processed data
        
    Returns:
        Excel file as bytes
    """
    output = BytesIO()
    
    # Create detailed results dataframe with all columns
    records = []
    for item in result.transcript_results:
        transcript_id = str(item.get("transcript_id", ""))
        
        row = {"transcript_id": transcript_id}
        
        # Add original columns from processed_df if available
        if processed_df is not None and not processed_df.empty:
            match_row = processed_df[processed_df['transcript_id'] == item.get("transcript_id", "")]
            if not match_row.empty:
                original_cols = ['agent_id', 'agent_name', 'mistakes', 'mistake_themes', 'root_cause', 'agent_behavior', 'severity']
                for col in original_cols:
                    if col in processed_df.columns:
                        val = match_row.iloc[0][col] if col in match_row.columns else ""
                        if isinstance(val, list):
                            val = json.dumps(val)
                        elif pd.isna(val):
                            val = ""
                        row[col] = str(val) if val else ""
        
        # Add SOP analysis columns
        sop_mistakes = item.get("sop_mistakes", [])
        if not isinstance(sop_mistakes, list):
            sop_mistakes = [str(sop_mistakes)] if sop_mistakes else []
        
        sop_themes = item.get("sop_mistake_themes", [])
        if not isinstance(sop_themes, list):
            sop_themes = [str(sop_themes)] if sop_themes else []
        
        row.update({
            "sop_mistakes": json.dumps(sop_mistakes),
            "sop_mistake_themes": json.dumps(sop_themes),
            "sop_mistakes_reasoning": str(item.get("sop_mistakes_reasoning", "") or ""),
            "sop_improvements": str(item.get("sop_improvements", "") or "")
        })
        
        records.append(row)
    
    results_df = pd.DataFrame(records)
    
    # Create themes dataframe
    themes_list = result.sop_missing_themes if isinstance(result.sop_missing_themes, list) else []
    themes_df = pd.DataFrame({
        "Theme_Number": range(1, len(themes_list) + 1),
        "SOP_Mistake_Theme": themes_list
    }) if themes_list else pd.DataFrame(columns=["Theme_Number", "SOP_Mistake_Theme"])
    
    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        results_df.to_excel(writer, sheet_name='SOP_Analysis_Results', index=False)
        themes_df.to_excel(writer, sheet_name='SOP_Mistake_Themes', index=False)
    
    output.seek(0)
    return output.getvalue()


def export_to_csv(result: SOPAnalysisResult, processed_df: Optional[pd.DataFrame] = None) -> str:
    """
    Export SOP analysis results to CSV with all columns
    
    Args:
        result: SOPAnalysisResult object
        processed_df: Optional DataFrame with original processed data
        
    Returns:
        CSV content as string
    """
    records = []
    for item in result.transcript_results:
        transcript_id = str(item.get("transcript_id", ""))
        
        row = {"transcript_id": transcript_id}
        
        # Add original columns from processed_df if available
        if processed_df is not None and not processed_df.empty:
            match_row = processed_df[processed_df['transcript_id'] == item.get("transcript_id", "")]
            if not match_row.empty:
                original_cols = ['agent_id', 'agent_name', 'mistakes', 'mistake_themes', 'root_cause', 'agent_behavior', 'severity']
                for col in original_cols:
                    if col in processed_df.columns:
                        val = match_row.iloc[0][col] if col in match_row.columns else ""
                        if isinstance(val, list):
                            val = json.dumps(val)
                        elif pd.isna(val):
                            val = ""
                        row[col] = str(val) if val else ""
        
        # Add SOP analysis columns
        sop_mistakes = item.get("sop_mistakes", [])
        if not isinstance(sop_mistakes, list):
            sop_mistakes = [str(sop_mistakes)] if sop_mistakes else []
        
        sop_themes = item.get("sop_mistake_themes", [])
        if not isinstance(sop_themes, list):
            sop_themes = [str(sop_themes)] if sop_themes else []
        
        row.update({
            "sop_mistakes": json.dumps(sop_mistakes),
            "sop_mistake_themes": json.dumps(sop_themes),
            "sop_mistakes_reasoning": str(item.get("sop_mistakes_reasoning", "") or ""),
            "sop_improvements": str(item.get("sop_improvements", "") or "")
        })
        
        records.append(row)
    
    df = pd.DataFrame(records)
    return df.to_csv(index=False)


def render_sop_download_section(result: SOPAnalysisResult, processed_df: Optional[pd.DataFrame] = None):
    """
    Render download buttons for SOP analysis results
    
    Args:
        result: SOPAnalysisResult object
        processed_df: Optional DataFrame with original processed data
    """
    st.markdown("### 💾 Download Results")
    
    timestamp = generate_timestamp()
    base_filename = f"SOP_Analysis_Results_{timestamp}"
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        excel_data = export_to_excel(result, processed_df)
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"{base_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        csv_data = export_to_csv(result, processed_df)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"{base_filename}.csv",
            mime="text/csv",
            use_container_width=True
        )


def render_sop_analysis_dashboard(result: SOPAnalysisResult, processed_df: Optional[pd.DataFrame] = None):
    """
    Main function to render the complete SOP analysis dashboard
    
    Args:
        result: SOPAnalysisResult object
        processed_df: Optional DataFrame with original processed data (for including previous columns)
    """
    # Header
    render_sop_analysis_header()
    
    # Summary metrics
    render_sop_summary_metrics(result)
    
    st.markdown("---")
    
    # Results table with previous columns
    render_sop_results_table(result, processed_df)
    
    st.markdown("---")
    
    # Charts Row: SOP Mistake Themes Distribution & SOP Themes vs Agents
    col1, col2 = st.columns(2)
    with col1:
        render_sop_mistake_themes_chart(result)
    with col2:
        render_sop_themes_vs_agents_chart(result)
    
    st.markdown("---")
    
    # Agent vs SOP Themes chart
    render_agent_vs_sop_themes_chart(result)
    
    st.markdown("---")
    
    # Download section with all columns
    render_sop_download_section(result, processed_df)
