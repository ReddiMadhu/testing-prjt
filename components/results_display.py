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
    
    # Summary metrics
    render_results_summary(processed_df)
    st.markdown("---")
    
    # Detailed results table
    render_results_table(processed_df)
    st.markdown("---")
    
    # Charts Row 1: Mistake Themes & Root Cause Treemap side by side
    col1, col2 = st.columns(2)
    with col1:
        render_mistake_themes_chart(processed_df)
    with col2:
        render_root_cause_treemap(processed_df)
    
    st.markdown("---")
    
    # Charts Row 2: Agent vs Mistake Themes & Mistake Themes vs Agents
    col3, col4 = st.columns(2)
    with col3:
        render_agent_vs_mistake_themes_chart(processed_df)
    with col4:
        render_mistake_themes_vs_agents_chart(processed_df)
    
    st.markdown("---")
    
    # Charts Row 3: Agent vs Root Cause Treemap & Agent vs Severities Treemap
    col5, col6 = st.columns(2)
    with col5:
        render_agent_vs_root_cause_treemap(processed_df)
    with col6:
        render_agent_vs_severity_treemap(processed_df)
    
    st.markdown("---")
    
    # Agent-wise Training Recommendations
    render_agent_training_recommendations(processed_df)
    



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
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid #E85D04;
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">ANALYZED</p>
            <h2 style="color: #E85D04; margin: 0.5rem 0 0 0; font-size: 2rem;">{total}</h2>
            <p style="color: #2E7D32; margin: 0.25rem 0 0 0; font-size: 0.8rem;">✓ Transcripts</p>
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
            border-top: 4px solid #C62828;
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">TOTAL MISTAKES</p>
            <h2 style="color: #C62828; margin: 0.5rem 0 0 0; font-size: 2rem;">{int(total_mistakes)}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Identified</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_color = "#2E7D32" if avg_mistakes <= 2 else "#F9A825" if avg_mistakes <= 4 else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid {avg_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">AVG MISTAKES</p>
            <h2 style="color: {avg_color}; margin: 0.5rem 0 0 0; font-size: 2rem;">{avg_mistakes:.1f}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Per Transcript</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        severity_color = "#2E7D32" if avg_severity >= 75 else "#F9A825" if avg_severity >= 50 else "#C62828"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 4px solid {severity_color};
        ">
            <p style="color: #666; margin: 0; font-size: 0.85rem; font-weight: 600;">AVG SEVERITY</p>
            <h2 style="color: {severity_color}; margin: 0.5rem 0 0 0; font-size: 2rem;">{avg_severity:.0f}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0; font-size: 0.8rem;">Score /100</p>
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
        textfont=dict(color=text_colors, size=12),
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
        yaxis=dict(autorange='reversed'),
        xaxis=dict(range=[0, max(chart_data['Percentage']) * 1.15], gridcolor='rgba(0,0,0,0.1)')
    )
    
    # Add border styling
    fig.update_xaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    fig.update_yaxes(showline=True, linewidth=2, linecolor=EXLTheme.PRIMARY_ORANGE)
    
    st.plotly_chart(fig, use_container_width=True)


def render_root_cause_treemap(processed_df: pd.DataFrame):
    """
    Render Treemap showing root cause distribution by severity level
    
    Args:
        processed_df: DataFrame containing processed results
    """
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        🌳 Root Cause Treemap
    </h3>
    """, unsafe_allow_html=True)
    
    # Extract root causes (now as strings)
    if 'root_cause' not in processed_df.columns:
        st.info("No root cause data available.")
        return
    
    # Collect root causes with their severity levels
    root_cause_data = []
    for _, row in processed_df.iterrows():
        root_cause = row.get('root_cause', '')
        if root_cause and not pd.isna(root_cause) and root_cause != '' and root_cause != 'No issues identified':
            severity_level = row.get('severity_level', 'MEDIUM')
            root_cause_data.append({
                'root_cause': str(root_cause),
                'severity_level': severity_level
            })
    
    if not root_cause_data:
        st.info("No root causes identified in the transcripts.")
        return
    
    # Create DataFrame and count occurrences
    rc_df = pd.DataFrame(root_cause_data)
    rc_counts = rc_df.groupby(['severity_level', 'root_cause']).size().reset_index(name='count')
    
    # Add "All" as parent for severity levels
    rc_counts['parent'] = rc_counts['severity_level']
    
    # Create hierarchical data for treemap
    labels = ['All Root Causes']
    parents = ['']
    values = [rc_counts['count'].sum()]
    colors = ['#F5F5F5']
    
    # Add severity levels
    severity_colors = {
        'HIGH': '#C62828',
        'MEDIUM': '#F9A825', 
        'LOW': '#2E7D32'
    }
    
    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        severity_data = rc_counts[rc_counts['severity_level'] == severity]
        if len(severity_data) > 0:
            labels.append(severity)
            parents.append('All Root Causes')
            values.append(severity_data['count'].sum())
            colors.append(severity_colors.get(severity, '#E85D04'))
    
    # Add root causes under their severity levels
    for _, row in rc_counts.iterrows():
        labels.append(row['root_cause'][:50] + '...' if len(row['root_cause']) > 50 else row['root_cause'])
        parents.append(row['severity_level'])
        values.append(row['count'])
        # Lighter shade of severity color
        base_color = severity_colors.get(row['severity_level'], '#E85D04')
        colors.append(base_color + '99')  # Add transparency
    
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(width=2, color='white')
        ),
        textinfo='label+value',
        textfont=dict(size=12),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Root Causes by Severity Level</b>',
        margin=dict(l=10, r=10, t=50, b=10),
        height=450,
        paper_bgcolor='white'
    )
    
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
    
    # Generate EXL gradient colors (orange to transparent)
    num_bars = len(chart_data)
    bar_colors = []
    for i in range(num_bars):
        # Gradient so highest value has most opacity
        opacity = max(0.2, 0.2 + (i * 0.8 / max(1, num_bars - 1)))
        bar_colors.append(f'rgba(232, 93, 4, {opacity})')
    
    # Generate text colors based on opacity
    text_colors = []
    for i in range(num_bars):
        opacity = max(0.2, 0.2 + (i * 0.8 / max(1, num_bars - 1)))
        if opacity > 0.5:
            text_colors.append('white')
        else:
            text_colors.append('#E85D04')
    
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
        title='<b>Agents per Mistake Theme</b>',
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


def render_agent_vs_root_cause_treemap(processed_df: pd.DataFrame):
    """
    Render Treemap showing Agent vs Root Cause distribution with green to red gradient
    
    Args:
        processed_df: DataFrame containing processed results
    """
    import plotly.graph_objects as go
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        🌳 Agent vs Root Cause
    </h3>
    """, unsafe_allow_html=True)
    
    if 'agent_name' not in processed_df.columns or 'root_cause' not in processed_df.columns:
        st.info("No agent or root cause data available.")
        return
    
    # Collect agent-root cause data
    agent_rc_data = []
    for _, row in processed_df.iterrows():
        agent_name = row.get('agent_name', 'Unknown')
        root_cause = row.get('root_cause', '')
        if root_cause and not pd.isna(root_cause) and root_cause != '' and root_cause != 'No issues identified':
            agent_rc_data.append({'agent': agent_name, 'root_cause': str(root_cause)})
    
    if not agent_rc_data:
        st.info("No agent-root cause associations found.")
        return
    
    # Create DataFrame and count
    arc_df = pd.DataFrame(agent_rc_data)
    arc_counts = arc_df.groupby(['agent', 'root_cause']).size().reset_index(name='count')
    
    # Create hierarchical data for treemap
    labels = ['All Agents']
    parents = ['']
    values = [arc_counts['count'].sum()]
    colors = ['#E85D04']
    
    # Get agents sorted by total count (highest first for better visibility)
    agent_totals = arc_counts.groupby('agent')['count'].sum().sort_values(ascending=False)
    agents = agent_totals.index.tolist()
    num_agents = len(agents)
    
    # Generate EXL orange gradient for agents (dark to light based on count)
    def get_orange_gradient(index, total):
        """Generate EXL orange gradient from dark (#C44102) to light (#FFAB76)"""
        if total <= 1:
            return '#E85D04'
        ratio = index / (total - 1)
        # Dark orange to light orange
        r = int(196 + (255 - 196) * ratio)  # 196 to 255
        g = int(65 + (171 - 65) * ratio)    # 65 to 171
        b = int(2 + (118 - 2) * ratio)      # 2 to 118
        return f'rgb({r}, {g}, {b})'
    
    # Add agents with gradient colors (darkest = highest count)
    agent_color_map = {}
    for i, agent in enumerate(agents):
        agent_data = arc_counts[arc_counts['agent'] == agent]
        labels.append(agent)
        parents.append('All Agents')
        values.append(agent_data['count'].sum())
        agent_color = get_orange_gradient(i, num_agents)
        colors.append(agent_color)
        agent_color_map[agent] = agent_color
    
    # Add root causes under agents with slightly darker shade
    for agent in agents:
        agent_data = arc_counts[arc_counts['agent'] == agent]
        for _, row in agent_data.iterrows():
            rc_label = row['root_cause'][:40] + '...' if len(row['root_cause']) > 40 else row['root_cause']
            labels.append(rc_label)
            parents.append(agent)
            values.append(row['count'])
            # Use a complementary color for children
            colors.append('#1A1A2E')
    
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(width=2, color='white')
        ),
        textinfo='label+value',
        textfont=dict(size=12, color='white'),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Root Causes by Agent</b>',
        margin=dict(l=10, r=10, t=50, b=10),
        height=400,
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_agent_vs_severity_treemap(processed_df: pd.DataFrame):
    """
    Render Treemap showing Agent vs Severity Level distribution with green to red gradient
    
    Args:
        processed_df: DataFrame containing processed results
    """
    import plotly.graph_objects as go
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        🎯 Agent vs Severity
    </h3>
    """, unsafe_allow_html=True)
    
    if 'agent_name' not in processed_df.columns:
        st.info("No agent data available.")
        return
    
    # Create a copy and ensure severity_level exists
    df_copy = processed_df.copy()
    if 'severity_level' not in df_copy.columns and 'severity_score' in df_copy.columns:
        def get_severity_level(score):
            if score > 80:
                return "HIGH"
            elif score >= 60:
                return "MEDIUM"
            elif score < 50:
                return "LOW"
            else:
                return "MEDIUM"
        df_copy['severity_level'] = df_copy['severity_score'].apply(get_severity_level)
    
    if 'severity_level' not in df_copy.columns:
        st.info("No severity data available.")
        return
    
    # Count agent-severity combinations
    as_counts = df_copy.groupby(['agent_name', 'severity_level']).size().reset_index(name='count')
    
    if as_counts.empty:
        st.info("No agent-severity data found.")
        return
    
    # Create hierarchical data for treemap
    labels = ['All Agents']
    parents = ['']
    values = [as_counts['count'].sum()]
    colors = ['#E85D04']
    
    # Severity colors - clear and distinct
    severity_colors = {
        'LOW': '#2E7D32',      # Green - good
        'MEDIUM': '#F9A825',   # Yellow/Orange - warning
        'HIGH': '#C62828'      # Red - bad
    }
    
    # Get agents sorted by total issues (highest first)
    agent_totals = as_counts.groupby('agent_name')['count'].sum().sort_values(ascending=False)
    agents = agent_totals.index.tolist()
    num_agents = len(agents)
    
    # Generate EXL orange gradient for agents
    def get_orange_gradient(index, total):
        """Generate EXL orange gradient from dark (#C44102) to light (#FFAB76)"""
        if total <= 1:
            return '#E85D04'
        ratio = index / (total - 1)
        # Dark orange to light orange
        r = int(196 + (255 - 196) * ratio)  # 196 to 255
        g = int(65 + (171 - 65) * ratio)    # 65 to 171
        b = int(2 + (118 - 2) * ratio)      # 2 to 118
        return f'rgb({r}, {g}, {b})'
    
    # Add agents with gradient colors (darkest = highest issues)
    for i, agent in enumerate(agents):
        agent_data = as_counts[as_counts['agent_name'] == agent]
        labels.append(agent)
        parents.append('All Agents')
        values.append(agent_data['count'].sum())
        colors.append(get_orange_gradient(i, num_agents))
    
    # Add severity levels under agents with severity-specific colors
    for agent in agents:
        agent_data = as_counts[as_counts['agent_name'] == agent]
        for _, row in agent_data.iterrows():
            severity = row['severity_level']
            labels.append(f"{severity} ({row['count']})")
            parents.append(agent)
            values.append(row['count'])
            colors.append(severity_colors.get(severity, '#F9A825'))
    
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(width=2, color='white')
        ),
        textinfo='label',
        textfont=dict(size=12, color='white'),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Severity Levels by Agent</b>',
        margin=dict(l=10, r=10, t=50, b=10),
        height=400,
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    

def render_results_table(processed_df: pd.DataFrame):
    """
    Render the detailed results table
    
    Args:
        processed_df: DataFrame containing processed results
    """
    
    st.markdown("""
    <h3 style="color: #1A1A2E; margin: 1.5rem 0 1rem 0;">
        📋 Detailed Analysis Results
    </h3>
    """, unsafe_allow_html=True)
    
    # Create a copy of the DataFrame for filtering
    df_copy = processed_df.copy()
    
    # Add severity_level column if not present
    if 'severity_level' not in df_copy.columns and 'severity_score' in df_copy.columns:
        def get_severity_level(score):
            if score > 80:
                return "HIGH"
            elif score >= 60:
                return "MEDIUM"
            elif score < 50:
                return "LOW"
            else:
                return "MEDIUM"
        df_copy['severity_level'] = df_copy['severity_score'].apply(get_severity_level)
    
    # Initialize session state for severity level filter
    if 'severity_level_filter' not in st.session_state:
        st.session_state.severity_level_filter = 'All'
    
    # Severity Level filter buttons with custom styling
    if 'severity_level' in df_copy.columns:
        # Get current selection
        current_filter = st.session_state.severity_level_filter
        
        # Use radio button styled as segmented control
        filter_options = ['All', 'HIGH', 'MEDIUM', 'LOW']
        
        selected = st.radio(
            "Filter by Severity Level:",
            filter_options,
            index=filter_options.index(current_filter),
            horizontal=True,
            label_visibility="visible",
            key="severity_radio"
        )
        
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
    
    # Apply severity level filter
    display_df = df_copy.copy()
    if 'severity_level' in display_df.columns and st.session_state.get('severity_level_filter', 'All') != 'All':
        display_df = display_df[display_df['severity_level'] == st.session_state.severity_level_filter]
    
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
    
    st.info(f"📊 Showing {len(display_df)} of {len(processed_df)} records")


def render_agent_training_recommendations(processed_df: pd.DataFrame):
    """
    Render agent-wise training recommendations based on cumulative analysis data
    Uses LLM to generate personalized training suggestions
    
    Args:
        processed_df: DataFrame containing processed results
    """
    from services.langchain_gemini_service import LangChainGeminiService
    
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 1.5rem 0 1rem 0;
    ">
        <span style="font-size: 1.5rem;">🎯</span>
        <h3 style="
            color: #1A1A2E !important;
            margin: 0;
            font-weight: 700;
            font-size: 1.25rem;
        ">Agent Training Recommendations</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if 'agent_name' not in processed_df.columns:
        st.info("No agent data available for recommendations.")
        return
    
    # Check if recommendations are already cached
    if 'training_recommendations' not in st.session_state:
        st.session_state.training_recommendations = {}
    
    # Collect agent-wise data including agent_id
    agent_data = {}
    for _, row in processed_df.iterrows():
        agent_name = row.get('agent_name', 'Unknown')
        agent_id = row.get('agent_id', 'N/A')
        
        if agent_name not in agent_data:
            agent_data[agent_name] = {
                'agent_id': agent_id,
                'mistakes': [],
                'mistake_themes': [],
                'root_causes': [],
                'severity_scores': [],
                'transcript_count': 0
            }
        
        agent_data[agent_name]['transcript_count'] += 1
        
        # Collect mistakes
        mistakes = parse_json_field(row.get('mistakes', []))
        agent_data[agent_name]['mistakes'].extend(mistakes)
        
        # Collect mistake themes
        themes = parse_json_field(row.get('mistake_themes', []))
        agent_data[agent_name]['mistake_themes'].extend(themes)
        
        # Collect root causes
        root_cause = row.get('root_cause', '')
        if root_cause and not pd.isna(root_cause) and root_cause != 'No issues identified':
            agent_data[agent_name]['root_causes'].append(str(root_cause))
        
        # Collect severity
        if 'severity_score' in row:
            agent_data[agent_name]['severity_scores'].append(row['severity_score'])
    
    # Sort agents alphabetically
    sorted_agents = sorted(agent_data.keys())
    
    # Check if we need to generate recommendations (only if not cached)
    needs_generation = any(agent not in st.session_state.training_recommendations for agent in sorted_agents)
    
    if needs_generation:
        # Generate recommendations only for agents not in cache
        with st.spinner("Generating personalized training recommendations..."):
            try:
                llm_service = LangChainGeminiService()
                
                for agent_name in sorted_agents:
                    # Skip if already cached
                    if agent_name in st.session_state.training_recommendations:
                        continue
                    
                    data = agent_data[agent_name]
                    
                    # Prepare summary for LLM
                    unique_themes = list(set(data['mistake_themes']))
                    unique_root_causes = list(set(data['root_causes']))
                    avg_severity = sum(data['severity_scores']) / len(data['severity_scores']) if data['severity_scores'] else 0
                    
                    # Create prompt for recommendation
                    prompt = f"""Based on the following analysis of call transcripts for agent "{agent_name}", provide a concise 2-3 line training recommendation.

Agent Performance Summary:
- Total Transcripts Analyzed: {data['transcript_count']}
- Total Mistakes: {len(data['mistakes'])}
- Average Severity Score: {avg_severity:.1f}/100
- Key Mistake Themes: {', '.join(unique_themes[:5]) if unique_themes else 'None identified'}
- Root Causes: {', '.join(unique_root_causes[:3]) if unique_root_causes else 'None identified'}

Provide a specific, actionable 2-3 line training recommendation focused on the most critical improvement areas. Be direct and specific about what training modules or skills the agent needs.

Return ONLY the recommendation text, no formatting or prefixes."""

                    # Call LLM
                    recommendation = llm_service.llm.invoke(prompt).content.strip()
                    
                    # Cache the recommendation
                    st.session_state.training_recommendations[agent_name] = {
                        'recommendation': recommendation,
                        'agent_id': data['agent_id']
                    }
                
            except Exception as e:
                st.error(f"Error generating recommendations: {str(e)}")
                return
    
    # Display all recommendations from cache
    for agent_name in sorted_agents:
        if agent_name in st.session_state.training_recommendations:
            cached = st.session_state.training_recommendations[agent_name]
            recommendation = cached['recommendation']
            agent_id = cached['agent_id']
            
            st.markdown(f"""
            <div style="
                background: white;
                padding: 1rem 1.25rem;
                border-radius: 10px;
                border-left: 5px solid #E85D04;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            ">
                <div style="margin-bottom: 0.5rem;">
                    <span style="color: #1A1A2E; font-weight: 700; font-size: 1rem;">👤 {agent_name}</span>
                    <span style="color: #666; font-size: 0.85rem; margin-left: 1rem;">ID: {agent_id}</span>
                </div>
                <p style="color: #333; margin: 0; font-size: 0.9rem; line-height: 1.6;">
                    {recommendation}
                </p>
            </div>
            """, unsafe_allow_html=True)
