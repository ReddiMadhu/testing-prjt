"""
SOP Analysis Display Component
Displays SOP analysis results in table format with download options
"""

import streamlit as st
import pandas as pd
import json
from io import BytesIO
from typing import List, Dict, Any, Optional

from services.sop_analysis_service import SOPAnalysisResult
from utils.helpers import generate_timestamp


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


def render_sop_themes_section(themes: List[str]):
    """
    Render the SOP missing themes section
    
    Args:
        themes: List of SOP missing themes
    """
    st.markdown("### 🏷️ Top 10 SOP Mistake Themes")
    
    # Ensure themes is a list
    if not themes or not isinstance(themes, list):
        st.info("No SOP mistake themes identified - excellent compliance across all transcripts!")
        return
    
    # Display themes in a nice grid
    cols = st.columns(2)
    for idx, theme in enumerate(themes):
        with cols[idx % 2]:
            st.markdown(f"""
            <div style="
                background: #FFF8F0;
                padding: 0.75rem 1rem;
                border-radius: 8px;
                border-left: 4px solid #E85D04;
                margin-bottom: 0.5rem;
            ">
                <span style="font-weight: 600; color: #D84E00;">{idx + 1}.</span>
                <span style="color: #1A1A2E;">{theme}</span>
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


def render_sop_detailed_view(result: SOPAnalysisResult):
    """
    Render detailed expandable view for each transcript
    
    Args:
        result: SOPAnalysisResult object
    """
    st.markdown("### 🔍 Detailed View by Transcript")
    
    for idx, item in enumerate(result.transcript_results):
        transcript_id = str(item.get("transcript_id", f"T{idx+1}"))
        
        # Ensure sop_mistakes is a list
        sop_mistakes = item.get("sop_mistakes", [])
        if not isinstance(sop_mistakes, list):
            sop_mistakes = [str(sop_mistakes)] if sop_mistakes else []
        
        # Determine status color
        if not sop_mistakes:
            status_icon = "✅"
            status_text = "Compliant"
        elif len(sop_mistakes) <= 2:
            status_icon = "⚠️"
            status_text = "Minor Issues"
        else:
            status_icon = "❌"
            status_text = "Needs Improvement"
        
        with st.expander(f"{status_icon} {transcript_id} ({status_text} - {len(sop_mistakes)} mistakes)", expanded=False):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**📋 SOP Mistakes:**")
                if sop_mistakes:
                    for mistake in sop_mistakes:
                        st.markdown(f"- {mistake}")
                else:
                    st.success("No SOP violations found")
                
                st.markdown("**🏷️ Assigned Themes:**")
                themes = item.get("sop_mistake_themes", [])
                if not isinstance(themes, list):
                    themes = [str(themes)] if themes else []
                if themes:
                    st.markdown(", ".join(str(t) for t in themes))
                else:
                    st.info("No themes assigned")
            
            with col2:
                st.markdown("**💡 Reasoning:**")
                reasoning = item.get("sop_mistakes_reasoning", "N/A")
                st.markdown(str(reasoning) if reasoning else "N/A")
                
                st.markdown("**📈 Improvements:**")
                improvements = item.get("sop_improvements", "N/A")
                st.markdown(str(improvements) if improvements else "N/A")


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
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
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
    
    with col3:
        # Download themes only
        themes_list = result.sop_missing_themes if isinstance(result.sop_missing_themes, list) else []
        if themes_list:
            themes_csv = pd.DataFrame({
                "Theme_Number": range(1, len(themes_list) + 1),
                "SOP_Mistake_Theme": themes_list
            }).to_csv(index=False)
        else:
            themes_csv = pd.DataFrame(columns=["Theme_Number", "SOP_Mistake_Theme"]).to_csv(index=False)
        
        st.download_button(
            label="📥 Download Themes",
            data=themes_csv,
            file_name=f"SOP_Themes_{timestamp}.csv",
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
    
    # SOP Themes section
    render_sop_themes_section(result.sop_missing_themes)
    
    st.markdown("---")
    
    # Results table with previous columns
    render_sop_results_table(result, processed_df)
    
    st.markdown("---")
    
    # Detailed view
    render_sop_detailed_view(result)
    
    st.markdown("---")
    
    # Download section with all columns
    render_sop_download_section(result, processed_df)
