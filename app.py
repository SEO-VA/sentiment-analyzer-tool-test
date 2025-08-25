import streamlit as st
from modules.auth import check_auth, get_user_type
from modules.processing import split_sentences, call_openai_assistant
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
    
    content = st.text_area("Paste content here:", height=200, value=st.session_state.content)
    
    if st.button("Classify"):
        if not content.strip():
            st.error("Please enter content")
            return
        
        st.session_state.content = content
        st.session_state.workflow_step = 1
        st.rerun()
    
    # Process workflow based on step
    if st.session_state.workflow_step > 0:
        if user_type == "admin":
            admin_workflow()
        else:
            normal_workflow()

def normal_workflow():
    content = st.session_state.content
    sentences = split_sentences(content)
    response = call_openai_assistant(sentences)
    validated_results = validate_response(response, sentences)
    render_results(sentences, validated_results)
    generate_html_download(sentences, validated_results)
    
    # Reset workflow
    st.session_state.workflow_step = 0

def admin_workflow():
    step = st.session_state.workflow_step
    
    if step == 1:
        # Step 1: Split sentences
        st.session_state.sentences = split_sentences(st.session_state.content)
        with st.expander("Debug: Sentence Splitting", expanded=True):
            st.json(st.session_state.sentences)
        
        if st.button("Continue to API Call"):
            st.session_state.workflow_step = 2
            st.rerun()
    
    elif step == 2:
        # Step 2: API Call
        st.session_state.response = call_openai_assistant(st.session_state.sentences)
        with st.expander("Debug: Assistant Response", expanded=True):
            st.json(st.session_state.response)
        
        if st.button("Continue to Validation"):
            st.session_state.workflow_step = 3
            st.rerun()
    
    elif step == 3:
        # Step 3: Validation
        st.session_state.validated_results = validate_response(st.session_state.response, st.session_state.sentences)
        with st.expander("Debug: Validation Results", expanded=True):
            st.json(st.session_state.validated_results)
        
        if st.button("Continue to Rendering"):
            st.session_state.workflow_step = 4
            st.rerun()
    
    elif step == 4:
        # Step 4: Render
        render_results(st.session_state.sentences, st.session_state.validated_results)
        generate_html_download(st.session_state.sentences, st.session_state.validated_results)
        
        # Reset workflow
        if st.button("Start New Classification"):
            st.session_state.workflow_step = 0
            st.session_state.content = ""
            st.session_state.sentences = []
            st.session_state.response = []
            st.session_state.validated_results = []
            st.rerun()

if __name__ == "__main__":
    main()
