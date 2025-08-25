# app.py

import streamlit as st
from modules.auth import check_auth, get_user_type
from modules.text_processing import split_sentences, normalize_text
from modules.web_extraction import extract_webpage_content
from modules.llm_client import call_openai_assistant, estimate_api_cost
from modules.validation import validate_response
from modules.rendering import render_results, generate_html_download

def main():
    st.set_page_config(page_title="Content Classifier", layout="wide")
    
    if not check_auth():
        return
    
    user_type = get_user_type()
    st.title("Content Classifier")
    
    # Initialize session state
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 0
    if 'content' not in st.session_state:
        st.session_state.content = ""
    if 'sentences' not in st.session_state:
        st.session_state.sentences = []
    if 'response' not in st.session_state:
        st.session_state.response = []
    if 'validated_results' not in st.session_state:
        st.session_state.validated_results = []
    if 'webpage_data' not in st.session_state:
        st.session_state.webpage_data = None
    if 'input_method' not in st.session_state:
        st.session_state.input_method = "Text Input"
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        options=["Text Input", "Web Page URL"],
        horizontal=True,
        key="input_method_radio"
    )
    
    content = ""
    webpage_data = None
    
    if input_method == "Text Input":
        # Text input mode
        content = st.text_area(
            "Paste content here:", 
            height=200, 
            value=st.session_state.content,
            help="Paste any text content for classification analysis."
        )
        
        if st.button("Classify Text"):
            if not content.strip():
                st.error("Please enter content")
                return
            
            # Normalize text content
            content = normalize_text(content)
            st.session_state.content = content
            st.session_state.webpage_data = None
            st.session_state.workflow_step = 1
            st.rerun()
    
    else:  # Web Page URL
        # URL input mode
        url = st.text_input(
            "Web page URL:",
            placeholder="https://example.com/page",
            help="Enter the URL of a web page to extract and analyze its main content."
        )
        
        if st.button("Extract & Classify"):
            if not url.strip():
                st.error("Please enter a URL")
                return
            
            # Show extraction progress
            with st.spinner("Extracting content from webpage..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("Fetching webpage...")
                    progress_bar.progress(25)
                    
                    # Extract webpage content
                    webpage_data = extract_webpage_content(url)
                    progress_bar.progress(75)
                    
                    if webpage_data['success']:
                        content = webpage_data['text']
                        status_text.text("Content extracted successfully!")
                        progress_bar.progress(100)
                        
                        # Show extraction info
                        st.success(f"✅ Extracted {len(content)} characters from: {webpage_data['title']}")
                        
                        # Show preview in expander
                        with st.expander("📄 Extracted Content Preview", expanded=False):
                            preview_text = content[:1000] + "..." if len(content) > 1000 else content
                            st.text_area("Preview", value=preview_text, height=150, disabled=True)
                        
                        # Store data and proceed
                        st.session_state.content = content
                        st.session_state.webpage_data = webpage_data
                        st.session_state.workflow_step = 1
                        
                        # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.rerun()
                        
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ Failed to extract content: {webpage_data['error']}")
                        return
                        
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"An error occurred during extraction: {str(e)}")
                    return
    
    # Process workflow based on step
    if st.session_state.workflow_step > 0:
        if user_type == "admin":
            admin_workflow()
        else:
            normal_workflow()

def normal_workflow():
    """Normal user workflow - streamlined process"""
    content = st.session_state.content
    webpage_data = st.session_state.webpage_data
    
    with st.spinner("Processing content..."):
        # Process the content
        sentences = split_sentences(content)
        
        # Show API cost estimate for transparency
        cost_info = estimate_api_cost(sentences)
        st.info(f"Processing {cost_info['sentences']} sentences (~{cost_info['estimated_total_tokens']} tokens)")
        
        # Call assistant
        response = call_openai_assistant(sentences)
        
        # Validate results
        validated_results = validate_response(response, sentences)
        
        # Store results
        st.session_state.sentences = sentences
        st.session_state.response = response
        st.session_state.validated_results = validated_results
    
    # Render results
    render_results(sentences, validated_results, webpage_data)
    generate_html_download(sentences, validated_results, webpage_data)
    
    # Reset workflow
    if st.button("🔄 New Classification", type="secondary"):
        _reset_session_state()
        st.rerun()

def admin_workflow():
    """Admin workflow with step-by-step debugging"""
    step = st.session_state.workflow_step
    
    # Show current step indicator
    step_names = ["Input", "Sentence Splitting", "API Call", "Validation", "Results"]
    current_step = min(step, len(step_names) - 1)
    
    cols = st.columns(len(step_names))
    for i, name in enumerate(step_names):
        with cols[i]:
            if i < current_step:
                st.success(f"✅ {name}")
            elif i == current_step:
                st.info(f"🔄 {name}")
            else:
                st.write(f"⏳ {name}")
    
    st.markdown("---")
    
    if step == 1:
        # Step 1: Process sentences
        content = st.session_state.content
        webpage_data = st.session_state.webpage_data
        
        st.subheader("Step 1: Input Processing")
        
        # Show input source info
        if webpage_data:
            with st.expander("🌐 Source Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.json({
                        "source_type": "webpage",
                        "page_title": webpage_data.get('title', ''),
                        "url": webpage_data.get('url', ''),
                        "text_length": len(content)
                    })
                with col2:
                    st.json({
                        "extraction_success": webpage_data.get('success', False),
                        "has_structure": bool(webpage_data.get('structure', '')),
                        "structure_length": len(webpage_data.get('structure', ''))
                    })
        
        # Process sentences
        st.session_state.sentences = split_sentences(content)
        
        with st.expander("📝 Debug: Sentence Splitting", expanded=True):
            sentences = st.session_state.sentences
            st.write(f"**Processed into {len(sentences)} sentences:**")
            
            # Show first 10 sentences
            for i, sentence in enumerate(sentences[:10]):
                st.text_area(f"Sentence {i+1}", value=sentence['content'], height=60, disabled=True, key=f"debug_sent_{i}")
            
            if len(sentences) > 10:
                st.info(f"Showing first 10 sentences. Total: {len(sentences)}")
            
            # Show processing stats
            st.json({
                "total_sentences": len(sentences),
                "avg_sentence_length": sum(len(s['content']) for s in sentences) / len(sentences) if sentences else 0,
                "total_characters": sum(len(s['content']) for s in sentences)
            })
        
        # Show API cost estimate
        cost_info = estimate_api_cost(st.session_state.sentences)
        with st.expander("💰 API Cost Estimate", expanded=False):
            st.json(cost_info)
        
        if st.button("Continue to API Call", type="primary"):
            st.session_state.workflow_step = 2
            st.rerun()
    
    elif step == 2:
        # Step 2: API Call
        st.subheader("Step 2: OpenAI Assistant Call")
        
        with st.spinner("Calling OpenAI Assistant..."):
            st.session_state.response = call_openai_assistant(st.session_state.sentences)
        
        with st.expander("🤖 Debug: Assistant Response", expanded=True):
            response = st.session_state.response
            st.write(f"**Received {len(response)} classification results:**")
            
            # Show response structure
            if response:
                st.json(response[:3])  # Show first 3 results
                if len(response) > 3:
                    st.info(f"Showing first 3 results. Total: {len(response)}")
            
            # Analyze response types
            span_count = sum(1 for r in response if 'spans' in r)
            label_count = len(response) - span_count
            
            st.json({
                "total_results": len(response),
                "sentence_level_classifications": label_count,
                "phrase_level_classifications": span_count
            })
        
        if st.button("Continue to Validation", type="primary"):
            st.session_state.workflow_step = 3
            st.rerun()
    
    elif step == 3:
        # Step 3: Validation
        st.subheader("Step 3: Response Validation")
        
        st.session_state.validated_results = validate_response(
            st.session_state.response, 
            st.session_state.sentences
        )
        
        with st.expander("✅ Debug: Validation Results", expanded=True):
            validated = st.session_state.validated_results
            original = st.session_state.response
            
            st.write(f"**Validation Summary:**")
            st.json({
                "original_results": len(original),
                "validated_results": len(validated),
                "validation_success_rate": f"{len(validated)/len(original)*100:.1f}%" if original else "0%"
            })
            
            # Show first few validated results
            if validated:
                st.write("**Sample validated results:**")
                st.json(validated[:3])
        
        if st.button("Continue to Results", type="primary"):
            st.session_state.workflow_step = 4
            st.rerun()
    
    elif step == 4:
        # Step 4: Final Results
        st.subheader("Step 4: Final Results")
        
        sentences = st.session_state.sentences
        validated_results = st.session_state.validated_results
        webpage_data = st.session_state.webpage_data
        
        # Render results with debug info
        with st.expander("🎨 Debug: Rendering Information", expanded=False):
            render_info = {
                "total_sentences": len(sentences),
                "total_classifications": len(validated_results),
                "render_mode": "webpage_structure" if webpage_data else "simple_text",
                "has_webpage_structure": bool(webpage_data and webpage_data.get('structure'))
            }
            st.json(render_info)
        
        # Show the actual results
        render_results(sentences, validated_results, webpage_data)
        generate_html_download(sentences, validated_results, webpage_data)
        
        # Reset workflow
        if st.button("🆕 Start New Classification", type="primary"):
            _reset_session_state()
            st.rerun()

def _reset_session_state():
    """Reset all session state variables"""
    keys_to_reset = [
        'workflow_step', 'content', 'sentences', 'response', 
        'validated_results', 'webpage_data'
    ]
    
    for key in keys_to_reset:
        if key in st.session_state:
            if key == 'workflow_step':
                st.session_state[key] = 0
            elif key in ['content']:
                st.session_state[key] = ""
            elif key in ['sentences', 'response', 'validated_results']:
                st.session_state[key] = []
            else:
                st.session_state[key] = None

if __name__ == "__main__":
    main()