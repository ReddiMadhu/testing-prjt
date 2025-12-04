"""
LLM Service Factory
Factory pattern to select the appropriate LLM service based on configuration
"""

from config.settings import Settings
from services.claude_service import ClaudeService
from services.gemini_service import GeminiService
from services.langchain_gemini_service import LangChainGeminiService


def get_llm_service(provider: str = None):
    """
    Get the configured LLM service instance
    
    Args:
        provider: Optional provider name ('claude', 'gemini', or 'openai'). 
                 If None, uses configuration default.
    
    Returns:
        Instance of ClaudeService, GeminiService, or OpenAIService
    """
    settings = Settings()
    

        # Default to Claude
    return LangChainGeminiService()



    # Auto-detect columns
    columns = df.columns.tolist()
    columns_lower = [col.lower() for col in columns]
    
    # Auto-map columns
    def find_column(keywords):
        for keyword in keywords:
            for i, col in enumerate(columns_lower):
                if keyword in col:
                    return columns[i]
        return None
    
    transcript_col = find_column(['transcript_call', 'transcript', 'call'])
    transcript_id_col = find_column(['transcript_id', 'transcriptid'])
    agent_id_col = find_column(['agent_id', 'agentid'])
    agent_name_col = find_column(['agent_name', 'agentname', 'agent'])
    
    # Show detected columns
    st.markdown("##### Auto-detected Columns")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info(f"📝 **Transcript:** {transcript_col or 'Not found'}")
    with col2:
        st.info(f"🆔 **Transcript ID:** {transcript_id_col or 'Auto-generate'}")
    with col3:
        st.info(f"👤 **Agent ID:** {agent_id_col or 'Auto-generate'}")
    with col4:
        st.info(f"📛 **Agent Name:** {agent_name_col or 'Auto-generate'}")
    
    if not transcript_col:
        st.error("❌ Could not find transcript column. Please ensure your file has a column with 'transcript' or 'call' in the name.")
        return
    
    # Number of rows slider
    max_rows = min(settings.file.max_rows_to_process, len(df))
    num_rows = st.slider(
        "Number of transcripts to process:",
        min_value=1,
        max_value=max_rows,
        value=min(settings.file.default_rows_to_process, max_rows),
        help=f"Select number of transcripts to analyze (max {max_rows})"
    )
    
    # Process button
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            processed_df = process_transcripts(
                df,
                transcript_col,
                num_rows,
                transcript_id_col,
                agent_name_col,
                agent_id_col
            )
            
            if not processed_df.empty:
                st.session_state.processed_data = processed_df
                st.rerun()
