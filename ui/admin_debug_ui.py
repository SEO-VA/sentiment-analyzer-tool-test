# ui/admin_debug_ui.py

import streamlit as st
import json
import time
from core.classifier import ContentClassifier
from core.renderer import HTMLRenderer
from core.web_extractor import WebContentExtractor

def render_admin_debug_ui():
    """Debug interface for admin users with step-by-step analysis"""
    
    st.markdown("# 🔧 Content Classification - Debug Mode")
    st.markdown("Complete step-by-step analysis with debug information at each stage.")
    
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
            placeholder="Paste your content here for detailed analysis...",
            height=200
        )
        
    else:  # Web Page URL
        # URL input mode
        url = st.text_input(
            "Web page URL:",
            placeholder="https://example.com/page",
            help="Enter the URL of a web page to extract and analyze its main content with full debug information."
        )
        
        # URL extraction with debug info
        if url:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                extract_button = st.button("📥 Extract Content (Debug)", type="secondary", use_container_width=True)
            
            if extract_button:
                try:
                    # Show detailed extraction progress
                    extract_progress = st.progress(0)
                    extract_status = st.empty()
                    
                    extract_status.text("Initializing web extractor...")
                    extract_progress.progress(10)
                    
                    # Initialize extractor with debug info
                    extractor = WebContentExtractor()
                    
                    extract_status.text("Fetching webpage...")
                    extract_progress.progress(30)
                    
                    # Extract with full debug
                    webpage_data = extractor.extract_content(url)
                    extract_progress.progress(90)
                    
                    if webpage_data['success']:
                        content = webpage_data['text']
                        extract_progress.progress(100)
                        extract_status.success(f"✅ Successfully extracted content!")
                        
                        # Debug extraction details
                        with st.expander("🔧 Extraction Debug Information", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.json({
                                    "page_title": webpage_data['title'],
                                    "url": webpage_data['url'],
                                    "text_length": len(webpage_data['text']),
                                    "extraction_success": webpage_data['success']
                                })
                            
                            with col2:
                                structure_info = webpage_data.get('structure', {})
                                st.json({
                                    "structure_tag": structure_info.get('tag_name', 'unknown'),
                                    "has_tables": structure_info.get('has_tables', False),
                                    "has_lists": structure_info.get('has_lists', False),
                                    "heading_count": structure_info.get('heading_count', 0),
                                    "paragraph_count": structure_info.get('paragraph_count', 0)
                                })
                        
                        # Show extraction preview with more detail
                        with st.expander("📄 Extracted Content Preview", expanded=False):
                            st.write("**First 500 characters:**")
                            st.text_area("Content Start", value=content[:500], height=100, disabled=True)
                            
                            if len(content) > 1000:
                                st.write("**Middle section:**")
                                mid_start = len(content) // 2 - 250
                                mid_end = len(content) // 2 + 250
                                st.text_area("Content Middle", value=content[mid_start:mid_end], height=100, disabled=True)
                                
                                st.write("**Last 500 characters:**")
                                st.text_area("Content End", value=content[-500:], height=100, disabled=True)
                        
                        # Store in session state for analysis
                        st.session_state['debug_extracted_content'] = content
                        st.session_state['debug_webpage_data'] = webpage_data
                        
                    else:
                        extract_status.error(f"❌ Extraction failed!")
                        st.error(f"Error details: {webpage_data['error']}")
                        content = ""
                        
                    # Clear progress
                    extract_progress.empty()
                    
                except Exception as e:
                    st.error(f"An error occurred during content extraction: {str(e)}")
                    st.exception(e)  # Show full stack trace in debug mode
                    content = ""
            
            # Use extracted content from session state if available
            if 'debug_extracted_content' in st.session_state and not extract_button:
                content = st.session_state['debug_extracted_content']
                webpage_data = st.session_state.get('debug_webpage_data')
                
                # Show current extracted content info
                if webpage_data:
                    st.success(f"📄 Ready to analyze: **{webpage_data['title']}** ({len(content)} characters)")
    
    # Analyze button
    if content.strip():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            analyze_button = st.button("🔍 Analyze with Debug", type="primary", use_container_width=True)
        
        if analyze_button:
            try:
                # Initialize classifier with debug mode
                classifier = ContentClassifier(debug_mode=True)
                
                # Show overall progress
                main_progress = st.progress(0)
                main_status = st.empty()
                
                # Process content with debug info
                main_status.text("Starting analysis...")
                result = classifier.classify_content(content)
                main_progress.progress(100)
                main_status.text("Analysis complete!")
                
                # Debug sections
                debug_data = result.debug_info
                
                # 0. Input Source Information (new section for webpage data)
                if webpage_data:
                    with st.expander("🌐 0. Source Information", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.json({
                                "source_type": "webpage",
                                "page_title": webpage_data.get('title', ''),
                                "url": webpage_data.get('url', ''),
                                "extraction_method": "selenium + beautifulsoup"
                            })
                        
                        with col2:
                            structure = webpage_data.get('structure', {})
                            st.json({
                                "content_structure": {
                                    "main_tag": structure.get('tag_name', 'unknown'),
                                    "has_tables": structure.get('has_tables', False),
                                    "has_lists": structure.get('has_lists', False),
                                    "headings": structure.get('heading_count', 0),
                                    "paragraphs": structure.get('paragraph_count', 0)
                                }
                            })
                
                # 1. Input Processing
                with st.expander("📝 1. Input Processing", expanded=False):
                    st.text_area("Raw Input", value=debug_data['raw_input'][:1000] + ("..." if len(debug_data['raw_input']) > 1000 else ""), height=100, disabled=True)
                    st.json({
                        "character_count": len(debug_data['raw_input']),
                        "line_count": debug_data['raw_input'].count('\n') + 1,
                        "source_type": "webpage" if webpage_data else "text_input"
                    })
                
                # 2. Text Normalization
                with st.expander("🔧 2. Text Normalization", expanded=False):
                    st.text_area("Normalized Text", value=debug_data['normalized_text'][:1000] + ("..." if len(debug_data['normalized_text']) > 1000 else ""), height=100, disabled=True)
                    st.json({
                        "normalization_changes": debug_data.get('normalization_changes', []),
                        "character_count_after": len(debug_data['normalized_text'])
                    })
                
                # 3. Sentence Splitting
                with st.expander("✂️ 3. Sentence Splitting", expanded=False):
                    sentences = debug_data['sentences']
                    st.write(f"**Total sentences found: {len(sentences)}**")
                    
                    for i, sentence in enumerate(sentences[:10]):  # Show first 10
                        st.text_area(f"Sentence {i+1}", value=sentence['text'], height=50, disabled=True, key=f"sent_{i}")
                    
                    if len(sentences) > 10:
                        st.info(f"Showing first 10 sentences. Total: {len(sentences)}")
                    
                    st.json({
                        "sentence_count": len(sentences),
                        "avg_sentence_length": sum(len(s['text']) for s in sentences) / len(sentences) if sentences else 0
                    })
                
                # 4. Stage 1 Classification
                with st.expander("🎯 4. Stage 1 Classification", expanded=False):
                    stage1_results = debug_data.get('stage1_results', [])
                    
                    if stage1_results:
                        st.write(f"**Sentences classified: {len(stage1_results)}**")
                        
                        # Show classification summary
                        label_counts = {}
                        needs_phrase_count = 0
                        
                        for result in stage1_results:
                            label = result['label']
                            label_counts[label] = label_counts.get(label, 0) + 1
                            if result.get('needs_phrase_level', False):
                                needs_phrase_count += 1
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.json({
                                "classification_summary": label_counts,
                                "needs_phrase_level": needs_phrase_count
                            })
                        
                        with col2:
                            # Show first few results
                            st.write("**Sample results:**")
                            for i, result in enumerate(stage1_results[:5]):
                                sentence_text = next((s['text'] for s in sentences if s['hash'] == result['hash']), 'N/A')
                                st.write(f"• {result['label'].upper()}: {sentence_text[:50]}...")
                    else:
                        st.warning("Stage 1 classification not completed or failed")
                
                # 5. Stage 2 Candidate Selection
                with st.expander("🎨 5. Stage 2 Candidate Selection", expanded=False):
                    stage2_candidates = debug_data.get('stage2_candidates', [])
                    st.write(f"**Sentences selected for phrase-level analysis: {len(stage2_candidates)}**")
                    
                    if stage2_candidates:
                        st.json({
                            "selection_criteria": debug_data.get('stage2_criteria', []),
                            "candidate_count": len(stage2_candidates)
                        })
                        
                        for i, candidate in enumerate(stage2_candidates[:3]):  # Show first 3
                            st.text_area(f"Candidate {i+1}", value=candidate.get('text', ''), height=50, disabled=True, key=f"cand_{i}")
                    else:
                        st.info("No sentences required phrase-level analysis")
                
                # 6. Stage 2 Phrase Analysis
                with st.expander("🔍 6. Stage 2 Phrase Analysis", expanded=False):
                    stage2_results = debug_data.get('stage2_results', [])
                    st.write(f"**Sentences with phrase-level spans: {len(stage2_results)}**")
                    
                    if stage2_results:
                        for i, result in enumerate(stage2_results[:3]):  # Show first 3
                            st.write(f"**Result {i+1}:**")
                            # Find corresponding sentence text
                            sentence_text = next((s['text'] for s in sentences if s['hash'] == result['hash']), '')
                            st.text_area("Text", value=sentence_text, height=50, disabled=True, key=f"s2_text_{i}")
                            st.json(result.get('spans', []))
                    else:
                        st.info("No sentences processed at phrase level")
                
                # 7. Final HTML Rendering
                with st.expander("🎨 7. Final HTML Rendering", expanded=False):
                    renderer = HTMLRenderer()
                    html_content = renderer.render_classification_result(result, webpage_data)
                    
                    st.write("**HTML Statistics:**")
                    st.json({
                        "html_size_chars": len(html_content),
                        "total_spans": html_content.count('<span class='),
                        "css_included": "style>" in html_content,
                        "webpage_structure_preserved": webpage_data is not None
                    })
                    
                    st.code(html_content[:500] + "..." if len(html_content) > 500 else html_content, language="html")
                
                # Final Results
                st.markdown("## 📊 Final Results")
                
                # Statistics
                stats = result.get_statistics()
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📋 Informational", stats['info_count'])
                with col2:
                    st.metric("📢 Promotional", stats['promo_count'])  
                with col3:
                    st.metric("⚠️ Risk Warning", stats['risk_count'])
                
                # Display final HTML
                renderer = HTMLRenderer()
                html_content = renderer.render_classification_result(result, webpage_data)
                st.components.v1.html(html_content, height=600, scrolling=True)
                
                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    filename_suffix = "webpage" if webpage_data else "text"
                    st.download_button(
                        label="📥 Download HTML Report",
                        data=html_content,
                        file_name=f"content_analysis_{filename_suffix}_{int(time.time())}.html",
                        mime="text/html",
                        type="secondary"
                    )
                
                with col2:
                    # Enhanced debug JSON with webpage data
                    debug_json_data = debug_data.copy()
                    if webpage_data:
                        debug_json_data['webpage_extraction'] = {
                            'title': webpage_data.get('title', ''),
                            'url': webpage_data.get('url', ''),
                            'structure_info': webpage_data.get('structure', {})
                        }
                    
                    debug_json = json.dumps(debug_json_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="🔧 Download Debug JSON",
                        data=debug_json,
                        file_name=f"debug_analysis_{filename_suffix}_{int(time.time())}.json",
                        mime="application/json",
                        type="secondary"
                    )
                
                # Clear session state after successful analysis
                if 'debug_extracted_content' in st.session_state:
                    del st.session_state['debug_extracted_content']
                if 'debug_webpage_data' in st.session_state:
                    del st.session_state['debug_webpage_data']
                
                # Clear progress
                main_progress.empty()
                main_status.empty()
                
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                st.exception(e)  # Show full stack trace in debug mode
    
    else:
        # Show disabled button when no content
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.button("🔍 Analyze with Debug", type="primary", disabled=True, use_container_width=True, help="Please provide content first")