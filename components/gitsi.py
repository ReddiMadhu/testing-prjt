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
                st.markdown("""
                <div style="padding: 0.5rem;">
                    <h4 style="color: #1A1A2E; margin: 0 0 1rem 0; font-size: 1rem;">Severity Level Definitions</h4>
                    
                    <div style="margin-bottom: 1rem; padding: 0.75rem; background: #FFEBEE; border-radius: 8px; border-left: 4px solid #C62828;">
                        <strong style="color: #C62828;">🔴 HIGH (Score > 80)</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #333; font-size: 0.85rem;">
                            Critical issues requiring immediate attention. Major compliance violations, 
                            significant customer impact, or severe process failures.
                        </p>
                    </div>
                    
                    <div style="margin-bottom: 1rem; padding: 0.75rem; background: #FFF8E1; border-radius: 8px; border-left: 4px solid #F9A825;">
                        <strong style="color: #F57F17;">🟡 MEDIUM (Score 50-80)</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #333; font-size: 0.85rem;">
                            Moderate issues needing review. Process deviations, communication gaps, 
                            or areas requiring coaching and improvement.
                        </p>
                    </div>
                    
                    <div style="padding: 0.75rem; background: #E8F5E9; border-radius: 8px; border-left: 4px solid #2E7D32;">
                        <strong style="color: #2E7D32;">🟢 LOW (Score < 50)</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #333; font-size: 0.85rem;">
                            Minor issues or good performance. Small improvements possible, 
                            but overall acceptable quality and compliance.
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        