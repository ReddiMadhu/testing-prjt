"""
Results Display Component
Handles display of analysis results
"""

import streamlit as st
import pandas as pd
import json
from typing import Optional
from collections import Counter

from config.theme import EXLTheme


def parse_json_field(value):
    """Parse JSON string field to list"""
    if pd.isna(value) or value == '' or value == '[]':
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(str(value))
    except:
        return [str(value)] if value else []


def render_results(processed_df: pd.DataFrame):
    """
    Render the analysis results section
    
    Args:
        processed_df: DataFrame containing processed results
    """
    
    # Results header
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 3px solid #E85D04;
    ">
        <span style="font-size: 1.5rem;">📊</span>
        <h2 style="
            color: #1A1A2E !important;
            margin: 0;
            font-weight: 700;
            font-size: 1.5rem;
        ">Analysis Results</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a copy of the DataFrame and add severity_level if needed
    df_with_severity = processed_df.copy()
    if 'severity_level' not in df_with_severity.columns and 'severity_score' in df_with_severity.columns:
        def get_severity_level(score):
            if score > 80:
                return "HIGH"
            elif score >= 60:
                return "MEDIUM"
            elif score < 50:
                return "LOW"
            else:
                return "MEDIUM"
        df_with_severity['severity_level'] = df_with_severity['severity_score'].apply(get_severity_level)
    
    # Initialize session state for severity level filter
    if 'severity_level_filter' not in st.session_state:
        st.session_state.severity_level_filter = 'All'
    
    # Apply severity level filter FIRST to get filtered dataframe
    filtered_df = df_with_severity.copy()
    if 'severity_level' in filtered_df.columns and st.session_state.get('severity_level_filter', 'All') != 'All':
        filtered_df = filtered_df[filtered_df['severity_level'] == st.session_state.severity_level_filter]
    
    # Summary metrics (using filtered data)
    render_results_summary(filtered_df)
    
    st.markdown("---")
    
    # Severity Level filter buttons AFTER cards and BEFORE table
    if 'severity_level' in df_with_severity.columns:
        current_filter = st.session_state.severity_level_filter
        filter_options = ['All', 'HIGH', 'MEDIUM', 'LOW']
        
        # Create columns for radio buttons and info icon
        filter_col, info_col = st.columns([10, 1])
        
        with filter_col:
            selected = st.radio(
                "Filter by Severity Level:",
                filter_options,
                index=filter_options.index(current_filter),
                horizontal=True,
                label_visibility="visible",
                key="severity_radio_main"
            )
        
        with info_col:
            # Info icon with popover for severity level explanations
            with st.popover("ℹ️", use_container_width=False):
                st.subheader("Severity Level Definitions")
                
                st.markdown("🔴 **HIGH (Score > 80)**")
                st.caption("Critical issues requiring immediate attention. Major compliance violations, significant customer impact, or severe process failures.")
                
                st.markdown("🟡 **MEDIUM (Score 50-80)**")
                st.caption("Moderate issues needing review. Process deviations, communication gaps, or areas requiring coaching and improvement.")
                
                st.markdown("🟢 **LOW (Score < 50)**")
                st.caption("Minor issues or good performance. Small improvements possible, but overall acceptable quality and compliance.")
        
        if selected != current_filter:
            st.session_state.severity_level_filter = selected
            st.rerun()
        
        # Custom CSS for radio buttons to look like styled buttons
        st.markdown(f"""
        <style>
            /* Make label and buttons in same row */
            div[data-testid="stRadio"] {{
                display: flex !important;
                flex-direction: row !important;
                align-items: center !important;
                gap: 1rem !important;
            }}
            
            /* Style the label */
            div[data-testid="stRadio"] > label {{
                font-size: 0.875rem !important;
                font-weight: 600 !important;
                margin-bottom: 0 !important;
                white-space: nowrap !important;
            }}
            
            /* Style the radio button container - add gap between buttons */
            div[data-testid="stRadio"] > div {{
                gap: 0.5rem !important;
                display: flex !important;
                flex-direction: row !important;
            }}
            
            /* Style all radio button labels */
            div[data-testid="stRadio"] > div label {{
                padding: 0.25rem 0.75rem !important;
                border-radius: 6px !important;
                font-size: 0.75rem !important;
                font-weight: 600 !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
                text-align: center !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin: 0 !important;
            }}
            
            /* Hide the actual radio circle */
            div[data-testid="stRadio"] > div label > div:first-child {{
                display: none !important;
            }}
            
            /* Center the text in label - target all text elements */
            div[data-testid="stRadio"] > div label p,
            div[data-testid="stRadio"] > div label span,
            div[data-testid="stRadio"] > div label div {{
                text-align: center !important;
                margin: 0 auto !important;
                display: block !important;
                width: 100% !important;
            }}
            
            /* All option */
            div[data-testid="stRadio"] > div label:nth-of-type(1) {{
                border: 2px solid #E85D04 !important;
                {f"background-color: #E85D04 !important; color: white !important;" if current_filter == 'All' else "background-color: transparent !important; color: #E85D04 !important;"}
            }}
            div[data-testid="stRadio"] > div label:nth-of-type(1) p,
            div[data-testid="stRadio"] > div label:nth-of-type(1) span {{
                {f"color: white !important;" if current_filter == 'All' else "color: #E85D04 !important;"}
            }}
            
            /* HIGH option */
            div[data-testid="stRadio"] > div label:nth-of-type(2) {{
                border: 2px solid #C62828 !important;
                {f"background-color: #C62828 !important; color: white !important;" if current_filter == 'HIGH' else "background-color: transparent !important; color: #C62828 !important;"}
            }}
            div[data-testid="stRadio"] > div label:nth-of-type(2) p,
            div[data-testid="stRadio"] > div label:nth-of-type(2) span {{
                {f"color: white !important;" if current_filter == 'HIGH' else "color: #C62828 !important;"}
            }}
            
            /* MEDIUM option */
            div[data-testid="stRadio"] > div label:nth-of-type(3) {{
                border: 2px solid #F9A825 !important;
                {f"background-color: #F9A825 !important; color: white !important;" if current_filter == 'MEDIUM' else "background-color: transparent !important; color: #F9A825 !important;"}
            }}
            div[data-testid="stRadio"] > div label:nth-of-type(3) p,
            div[data-testid="stRadio"] > div label:nth-of-type(3) span {{
                {f"color: white !important;" if current_filter == 'MEDIUM' else "color: #F9A825 !important;"}
            }}
            
            /* LOW option */
            div[data-testid="stRadio"] > div label:nth-of-type(4) {{
                border: 2px solid #2E7D32 !important;
                {f"background-color: #2E7D32 !important; color: white !important;" if current_filter == 'LOW' else "background-color: transparent !important; color: #2E7D32 !important;"}
            }}
            div[data-testid="stRadio"] > div label:nth-of-type(4) p,
            div[data-testid="stRadio"] > div label:nth-of-type(4) span {{
                {f"color: white !important;" if current_filter == 'LOW' else "color: #2E7D32 !important;"}
            }}
        </style>
        """, unsafe_allow_html=True)
    
    # Show filter status
    filter_status = st.session_state.get('severity_level_filter', 'All')
    if filter_status != 'All':
        st.info(f"🔍 Showing {len(filtered_df)} of {len(df_with_severity)} records filtered by **{filter_status}** severity")
    
    st.markdown("---")
    
    # Detailed results table (using filtered data)
    render_results_table(filtered_df)
    st.markdown("---")
    
    # Charts Row 1: Mistake Themes & Root Cause Treemap side by side (using filtered data)
    col1, col2 = st.columns(2)
    with col1:
        render_mistake_themes_chart(filtered_df)
    with col2:
        render_mistake_themes_vs_agents_chart(filtered_df)
    
    st.markdown("---")
    
    # Charts Row 2: Agent vs Mistake Themes & Mistake Themes vs Agents (using filtered data)
    col3, col4 = st.columns(2)
    with col3:
        render_agent_vs_mistake_themes_chart(filtered_df)
        

    



def render_results_summary(processed_df: pd.DataFrame):
    """
    Render summary metrics for analysis results
    
    Args:
        processed_df: DataFrame containing processed results
    """
    
    total = len(processed_df)
    
    # Calculate metrics - handle new JSON format columns
    if 'mistakes' in processed_df.columns:
        # Count mistakes from JSON arrays
        total_mistakes = processed_df['mistakes'].apply(
            lambda x: len(parse_json_field(x))
        ).sum()
        avg_mistakes = total_mistakes / total if total > 0 else 0
    else:
        total_mistakes = 0
        avg_mistakes = 0
    
    # Severity score
    if 'severity_score' in processed_df.columns:
        avg_severity = processed_df['severity_score'].mean()
    else:
        avg_severity = 100
    
    # Count by severity rating
    if 'severity_score' in processed_df.columns:
        low_quality = len(processed_df[processed_df['severity_score'] < 50])
    else:
        low_quality = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 0.75rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            text-align: center;
            border-top: 3px solid #E85D04;
        ">
            <p style="color: #666; margin: 0; font-size: 0.7rem; font-weight: 600;">ANALYZED</p>
            <h2 style="color: #E85D04; margin: 0.25rem 0 0 0; font-size: 1.5rem;">{total}</h2>
            <p style="color: #2E7D32; margin: 0.15rem 0 0 0; font-size: 0.65rem;">✓ Transcripts</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 0.75rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            text-align: center;
            border-top: 3px solid #C62828;
        ">
            <p style="color: #666; margin: 0; font-size: 0.7rem; font-weight: 600;">TOTAL MISTAKES</p>
            <h2 style="color: #C62828; margin: 0.25rem 0 0 0; font-size: 1.5rem;">{int(total_mistakes)}</h2>
            <p style="color: #666; margin: 0.15rem 0 0 0; font-size: 0.65rem;">Identified</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_color = "#2E7D32" if avg_mistakes <= 2 else "#F9A825" if avg_mistakes <= 4 else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 0.75rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            text-align: center;
            border-top: 3px solid {avg_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.7rem; font-weight: 600;">AVG MISTAKES</p>
            <h2 style="color: {avg_color}; margin: 0.25rem 0 0 0; font-size: 1.5rem;">{avg_mistakes:.1f}</h2>
            <p style="color: #666; margin: 0.15rem 0 0 0; font-size: 0.65rem;">Per Transcript</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        severity_color = "#2E7D32" if avg_severity >= 75 else "#F9A825" if avg_severity >= 50 else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 0.75rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            text-align: center;
            border-top: 3px solid {severity_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.7rem; font-weight: 600;">AVG SEVERITY</p>
            <h2 style="color: {severity_color}; margin: 0.25rem 0 0 0; font-size: 1.5rem;">{avg_severity:.0f}</h2>
            <p style="color: #666; margin: 0.15rem 0 0 0; font-size: 0.65rem;">Score /100</p>
        </div>
        """, unsafe_allow_html=True)


def render_mistake_themes_chart(processed_df: pd.DataFrame):
    """
    Render bar chart showing percentage distribution of mistake themes
    
    Args:
        processed_df: DataFrame containing processed results
    """
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        📊 Mistake Themes Distribution
    </h3>
    """, unsafe_allow_html=True)
    
    # Extract all mistake themes
    if 'mistake_themes' not in processed_df.columns:
        st.info("No mistake themes data available.")
        return
    
    all_themes = []
    for themes in processed_df['mistake_themes']:
        parsed = parse_json_field(themes)
        if parsed:
            all_themes.extend(parsed)
    
    if not all_themes:
        st.info("No mistake themes identified in the transcripts.")
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
        # Opacity decreases from 1.0 to 0.2
        opacity = max(0.2, 1.0 - (i * 0.8 / max(1, num_bars - 1)))
        exl_colors.append(f'rgba(232, 93, 4, {opacity})')
    
    # Generate text colors - dark for transparent bars, white for opaque
    text_colors = []
    for i in range(num_bars):
        opacity = max(0.2, 1.0 - (i * 0.8 / max(1, num_bars - 1)))
        if opacity > 0.5:
            text_colors.append('white')
        else:
            text_colors.append('#E85D04')
    
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
        textfont=dict(color='#1A1A2E', size=12, family='Arial Black'),
        hovertemplate='<b>%{y}</b><br>Count: %{customdata}<br>Percentage: %{x:.1f}%<extra></extra>',
        customdata=chart_data['Count']
    ))
    
    fig.update_layout(
        title='<b>% of Mistake Themes</b>',
        xaxis_title='Percentage (%)',
        yaxis_title='',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=40),
        height=max(300, len(chart_data) * 40 + 100),
        showlegend=False,
        yaxis=dict(
            autorange='reversed',
            tickfont=dict(size=12, color='#1A1A2E', family='Arial', weight='bold')
        ),
        xaxis=dict(range=[0, max(chart_data['Percentage']) * 1.15], gridcolor='rgba(0,0,0,0.1)')
    )
    
    # Add border styling
    fig.update_xaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    fig.update_yaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    
    st.plotly_chart(fig, use_container_width=True)





def render_agent_vs_mistake_themes_chart(processed_df: pd.DataFrame):
    """
    Render horizontal stacked bar chart showing Agent vs Mistake Themes distribution
    
    Args:
        processed_df: DataFrame containing processed results
    """
    import plotly.graph_objects as go
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        👤 Agent vs Mistake Themes
    </h3>
    """, unsafe_allow_html=True)
    
    if 'agent_name' not in processed_df.columns or 'mistake_themes' not in processed_df.columns:
        st.info("No agent or mistake themes data available.")
        return
    
    # Collect agent-theme data
    agent_theme_data = []
    for _, row in processed_df.iterrows():
        agent_name = row.get('agent_name', 'Unknown')
        themes = parse_json_field(row.get('mistake_themes', []))
        for theme in themes:
            agent_theme_data.append({'agent': agent_name, 'theme': theme})
    
    if not agent_theme_data:
        st.info("No agent-theme associations found.")
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
    
    # Generate EXL gradient colors (orange to transparent) for themes - highest count gets darkest
    num_themes = len(themes)
    theme_colors = []
    for i in range(num_themes):
        opacity = max(0.2, 1.0 - (i * 0.8 / max(1, num_themes - 1)))
        theme_colors.append(f'rgba(232, 93, 4, {opacity})')
    
    fig = go.Figure()
    
    for i, theme in enumerate(themes):
        theme_data = at_counts[at_counts['theme'] == theme]
        counts = [theme_data[theme_data['agent'] == agent]['count'].sum() if agent in theme_data['agent'].values else 0 for agent in agents]
        
        fig.add_trace(go.Bar(
            name=theme,  # Show full theme name in legend
            y=agents,
            x=counts,
            orientation='h',
            marker=dict(
                color=theme_colors[i % len(theme_colors)],
                line=dict(color='#E85D04', width=1)
            ),
            hovertemplate='<b>%{y}</b><br>Theme: ' + theme + '<br>Count: %{x}<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        xaxis_title='Count',
        yaxis_title='',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=10, b=40),
        height=max(400, len(agents) * 50 + 100),
        showlegend=False,
        yaxis=dict(categoryorder='array', categoryarray=agents[::-1])
    )
    
    fig.update_xaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    
    st.plotly_chart(fig, use_container_width=True)


def render_mistake_themes_vs_agents_chart(processed_df: pd.DataFrame):
    """
    Render horizontal bar chart showing each Mistake Theme and how many agents committed it
    
    Args:
        processed_df: DataFrame containing processed results
    """
    import plotly.graph_objects as go
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        ⚠️ Mistake Themes vs Agents
    </h3>
    """, unsafe_allow_html=True)
    
    if 'agent_name' not in processed_df.columns or 'mistake_themes' not in processed_df.columns:
        st.info("No agent or mistake themes data available.")
        return
    
    # Count unique agents per mistake theme
    theme_agent_data = {}
    for _, row in processed_df.iterrows():
        agent_name = row.get('agent_name', 'Unknown')
        themes = parse_json_field(row.get('mistake_themes', []))
        for theme in themes:
            if theme not in theme_agent_data:
                theme_agent_data[theme] = set()
            theme_agent_data[theme].add(agent_name)
    
    if not theme_agent_data:
        st.info("No mistake themes data found.")
        return
    
    # Create DataFrame with theme and agent count
    chart_data = pd.DataFrame([
        {'Theme': theme, 'Agent Count': len(agents)}
        for theme, agents in theme_agent_data.items()
    ])
    chart_data = chart_data.sort_values('Agent Count', ascending=True)
    
    # Generate blue gradient colors (dark blue to light blue)
    num_bars = len(chart_data)
    bar_colors = []
    for i in range(num_bars):
        # Gradient so highest value has most opacity
        opacity = max(0.3, 0.3 + (i * 0.7 / max(1, num_bars - 1)))
        bar_colors.append(f'rgba(30, 136, 229, {opacity})')  # Blue color
    
    # Generate text colors based on opacity
    text_colors = []
    for i in range(num_bars):
        opacity = max(0.3, 0.3 + (i * 0.7 / max(1, num_bars - 1)))
        if opacity > 0.5:
            text_colors.append('white')
        else:
            text_colors.append('#1565C0')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=chart_data['Theme'],
        x=chart_data['Agent Count'],
        orientation='h',
        marker=dict(
            color=bar_colors,
            line=dict(color='#1565C0', width=1)  # Dark blue border
        ),
        text=chart_data['Agent Count'],
        textposition='inside',
        textfont=dict(color=text_colors, size=12, weight='bold'),
        hovertemplate='<b>%{y}</b><br>Agents with this mistake: %{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Agents per Mistake Theme</b>',
        xaxis_title='Number of Agents',
        yaxis_title='',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=40),
        height=max(300, len(chart_data) * 40 + 100),
        showlegend=False
    )
    
    fig.update_xaxes(showline=True, linewidth=2, linecolor='#1565C0', gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='#1565C0')
    
    st.plotly_chart(fig, use_container_width=True)





def render_results_table(processed_df: pd.DataFrame):
    """
    Render the detailed results table
    
    Args:
        processed_df: DataFrame containing processed results (already filtered by severity)
    """
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        📋 Detailed Analysis Results
    </h3>
    """, unsafe_allow_html=True)
    
    # Use the already filtered dataframe
    display_df = processed_df.copy()
    
    # Define columns to display (matching new output format)
    # Expected columns: transcript_id, agent_name, agent_id, transcript_call, mistakes, 
    #                   mistake_themes, root_cause, severity_score, severity_level, reasoning, recommendation
    
    display_cols = [
        'transcript_id', 'agent_id', 'agent_name', 'mistakes', 
        'mistake_themes', 'root_cause', 'severity_score', 'severity_level', 'reasoning', 'recommendation'
    ]
    
    # Filter to only include columns that exist in the dataframe
    display_cols = [col for col in display_cols if col in display_df.columns]
    
    # Create display dataframe
    display_data = display_df[display_cols].copy() if display_cols else display_df.copy()
    
    # Rename columns for better display
    column_rename = {
        'transcript_id': 'Transcript ID',
        'agent_name': 'Agent Name',
        'agent_id': 'Agent ID',
        'mistakes': 'Mistakes',
        'mistake_themes': 'Mistake Themes',
        'root_cause': 'Root Cause',
        'severity_score': 'Severity Score',
        'severity_level': 'Severity Level',
        'reasoning': 'Reasoning',
        'recommendation': 'Recommendation'
    }
    display_data = display_data.rename(columns={k: v for k, v in column_rename.items() if k in display_data.columns})
    
    # Style functions
    def style_severity_score(val):
        try:
            num = int(val)
            if num >= 75:
                return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;'
            elif num >= 50:
                return 'background-color: #FFF8E1; color: #F57F17; font-weight: bold;'
            else:
                return 'background-color: #FFEBEE; color: #C62828; font-weight: bold;'
        except:
            return ''
    
    def style_severity_level(val):
        if val == 'HIGH':
            return 'background-color: #FFEBEE; color: #C62828; font-weight: bold;'
        elif val == 'MEDIUM':
            return 'background-color: #FFF8E1; color: #F57F17; font-weight: bold;'
        elif val == 'LOW':
            return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;'
        else:
            return ''
    
    # Apply styling
    styled_df = display_data.style
    if 'Severity Score' in display_data.columns:
        styled_df = styled_df.applymap(style_severity_score, subset=['Severity Score'])
    if 'Severity Level' in display_data.columns:
        styled_df = styled_df.applymap(style_severity_level, subset=['Severity Level'])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
