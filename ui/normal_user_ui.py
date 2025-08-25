# ui/normal_user_ui.py

import streamlit as st
import time
from core.classifier import ContentClassifier
from core.renderer import HTMLRenderer
from core.web_extractor import WebContentExtractor

def render_normal_user_ui():
    """Clean, simple UI for normal users with text and URL input options"""
    
    st.markdown("# 🔍 Content Classification")
    st.markdown("Analyze content from text or web pages to highlight informational, promotional, and risk warning content.")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        options=["Text Input", "Web Page URL"],
        horizontal=True,
        help="Select whether to analyze pasted text or extract content from a web page"
    )
    
    # Initialize variables
    content = ""
    webpage_data = None
    
    if input_method == "Text Input":
        # Text input mode
        content = st.text_area(
            "Content to analyze:",
            placeholder="Paste your content here...",
            height=200,
            help="Paste any text content for classification analysis."
        )
        
    else:  # Web Page URL
        # URL input mode
        url = st.text_input(
            "Web page URL:",
            placeholder="https://example.com/page",
            help="Enter the URL of a web page to extract and analyze its main content."
        )
        
        # URL extraction button
        if url:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                extract_button = st.button("📥 Extract Content", type="secondary", use_container_width=True)
            
            if extract_button:
                try:
                    # Show extraction progress
                    extract_progress = st.progress(0)
                    extract_status = st.empty()
                    
                    extract_status.text("Extracting content from webpage...")
                    extract_progress.progress(20)
                    
                    # Extract content
                    extractor = WebContentExtractor()
                    webpage_data = extractor.extract_content(url)
                    extract_progress.progress(80)
                    
                    if webpage_data['success']:
                        content = webpage_data['text']
                        extract_progress.progress(100)
                        extract_status.success(f"✅ Extracted {len(content)} characters from: {webpage_data['title']}")
                        
                        # Show extraction preview
                        with st.expander("📄 Extracted Content Preview", expanded=False):
                            st.text_area("Extracted Text", value=content[:1000] + "..." if len(content) > 1000 else content, height=200, disabled=True)
                            st.info(f"Page Title: {webpage_data['title']}")
                        
                        # Store in session state for analysis
                        st.session_state['extracted_content'] = content
                        st.session_state['webpage_data'] = webpage_data
                        
                    else:
                        extract_status.error(f"❌ Failed to extract content: {webpage_data['error']}")
                        content = ""
                        
                    # Clear progress
                    extract_progress.empty()
                    
                except Exception as e:
                    st.error(f"An error occurred during content extraction: {str(e)}")
                    content = ""
            
            # Use extracted content from session state if available
            if 'extracted_content' in st.session_state and not extract_button:
                content = st.session_state['extracted_content']
                webpage_data = st.session_state.get('webpage_data')
                
                # Show current extracted content info
                if webpage_data:
                    st.info(f"📄 Ready to analyze content from: **{webpage_data['title']}**")
    
    # Analyze button (shown for both input methods when content is available)
    if content.strip():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            analyze_button = st.button("🚀 Analyze Content", type="primary", use_container_width=True)
        
        if analyze_button:
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
                html_content = renderer.render_classification_result(result, webpage_data)
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
                filename_suffix = "webpage" if webpage_data else "text"
                st.download_button(
                    label="📥 Download HTML Report",
                    data=html_content,
                    file_name=f"content_analysis_{filename_suffix}_{int(time.time())}.html",
                    mime="text/html",
                    type="secondary",
                    use_container_width=True
                )
                
                # Clear session state after successful analysis
                if 'extracted_content' in st.session_state:
                    del st.session_state['extracted_content']
                if 'webpage_data' in st.session_state:
                    del st.session_state['webpage_data']
                
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                st.info("Please try again or contact support if the issue persists.")
    
    elif input_method == "Text Input":
        # Show placeholder for text input
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.button("🚀 Analyze Content", type="primary", disabled=True, use_container_width=True, help="Please paste some content first")
    
    # Add footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666; font-size: 0.8em;'>"
        "Content classification powered by AI • Secure and private • Supports text and web page analysis"
        "</p>", 
        unsafe_allow_html=True
    )