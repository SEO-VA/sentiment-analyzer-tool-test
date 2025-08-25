import streamlit as st
from auth.authenticator import Authenticator

def render_login_page(auth: Authenticator):
    """Render the login page"""
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.markdown("# 🔍 Content Classifier")
        st.markdown("---")
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### Please sign in")
            
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                elif auth.authenticate(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Add some spacing
        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; color: #666; font-size: 0.8em;'>"
            "Secure content classification tool"
            "</p>", 
            unsafe_allow_html=True
        )