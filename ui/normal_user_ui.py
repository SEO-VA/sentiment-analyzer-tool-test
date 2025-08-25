import streamlit as st
import time
from core.classifier import ContentClassifier
from core.renderer import HTMLRenderer

def render_normal_user_ui():
    """Clean, simple UI for normal users"""
    
    st.markdown("# 🔍 Content Classification")
    st.markdown("Paste your content below to analyze and highlight different content types.")
    
    # Text input
    content = st.text_area(
        "Content to analyze:",
        placeholder="Paste your content here...",
        height=200,
        help="Paste any text content. The system will classify and highlight informational, promotional, and risk warning content."
    )
    
    # Analyze button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        analyze_button = st.button("🚀 Analyze Content", type="primary", use_container_width=True)
    
    if analyze_button and content.strip():
        try:
            # Initialize classifier
            classifier = ContentClassifier()
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process content
            status_text.text("Processing content...")
            progress_bar.progress(20)
            
            # Run classification
            result = classifier.classify_content(content)
            progress_bar.progress(80)
            
            # Render HTML
            status_text.text("Generating visualization...")
            renderer = HTMLRenderer()
            html_content = renderer.render_classification_result(result)
            progress_bar.progress(100)
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            # Show results
            st.markdown("## 📊 Analysis Results")
            
            # Display statistics
            col1, col2, col3 = st.columns(3)
            stats = result.get_statistics()
            
            with col1:
                st.metric("📋 Informational", stats['info_count'])
            with col2:
                st.metric("📢 Promotional", stats['promo_count'])
            with col3:
                st.metric("⚠️ Risk Warning", stats['risk_count'])
            
            # Display HTML result
            st.components.v1.html(html_content, height=600, scrolling=True)
            
            # Download button
            st.download_button(
                label="📥 Download HTML Report",
                data=html_content,
                file_name=f"content_analysis_{int(time.time())}.html",
                mime="text/html",
                type="secondary",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")
            st.info("Please try again or contact support if the issue persists.")
    
    elif analyze_button and not content.strip():
        st.warning("Please paste some content to analyze.")
    
    # Add footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666; font-size: 0.8em;'>"
        "Content classification powered by AI • Secure and private"
        "</p>", 
        unsafe_allow_html=True
    )