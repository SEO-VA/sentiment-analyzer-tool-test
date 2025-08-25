import streamlit as st
import json
import time
from core.classifier import ContentClassifier
from core.renderer import HTMLRenderer

def render_admin_debug_ui():
    """Debug interface for admin users with step-by-step analysis"""
    
    st.markdown("# 🔧 Content Classification - Debug Mode")
    st.markdown("Complete step-by-step analysis with debug information at each stage.")
    
    # Text input
    content = st.text_area(
        "Content to analyze:",
        placeholder="Paste your content here for detailed analysis...",
        height=200
    )
    
    # Analyze button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        analyze_button = st.button("🔍 Analyze with Debug", type="primary", use_container_width=True)
    
    if analyze_button and content.strip():
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
            
            # 1. Input Processing
            with st.expander("📝 1. Input Processing", expanded=False):
                st.text_area("Raw Input", value=debug_data['raw_input'], height=100, disabled=True)
                st.json({
                    "character_count": len(debug_data['raw_input']),
                    "line_count": debug_data['raw_input'].count('\n') + 1
                })
            
            # 2. Text Normalization
            with st.expander("🔧 2. Text Normalization", expanded=False):
                st.text_area("Normalized Text", value=debug_data['normalized_text'], height=100, disabled=True)
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
                            st.write(f"• {result['label'].upper()}: {result.get('text', 'N/A')[:50]}...")
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
                        st.text_area("Text", value=result.get('text', ''), height=50, disabled=True, key=f"s2_text_{i}")
                        st.json(result.get('spans', []))
                else:
                    st.info("No sentences processed at phrase level")
            
            # 7. Final HTML Rendering
            with st.expander("🎨 7. Final HTML Rendering", expanded=False):
                renderer = HTMLRenderer()
                html_content = renderer.render_classification_result(result)
                
                st.write("**HTML Statistics:**")
                st.json({
                    "html_size_chars": len(html_content),
                    "total_spans": html_content.count('<span class='),
                    "css_included": "style>" in html_content
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
            html_content = renderer.render_classification_result(result)
            st.components.v1.html(html_content, height=600, scrolling=True)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download HTML Report",
                    data=html_content,
                    file_name=f"content_analysis_{int(time.time())}.html",
                    mime="text/html",
                    type="secondary"
                )
            
            with col2:
                debug_json = json.dumps(debug_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="🔧 Download Debug JSON",
                    data=debug_json,
                    file_name=f"debug_analysis_{int(time.time())}.json",
                    mime="application/json",
                    type="secondary"
                )
            
            # Clear progress
            main_progress.empty()
            main_status.empty()
            
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")
            st.exception(e)  # Show full stack trace in debug mode
    
    elif analyze_button and not content.strip():
        st.warning("Please paste some content to analyze.")