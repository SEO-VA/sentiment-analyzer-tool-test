import streamlit as st
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from auth.authenticator import Authenticator
from ui.login_page import render_login_page
from ui.normal_user_ui import render_normal_user_ui
from ui.admin_debug_ui import render_admin_debug_ui

def main():
    """Main application entry point - authentication first"""
    
    # Page config
    st.set_page_config(
        page_title="Content Classification Tool",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize authenticator
    auth = Authenticator()
    
    # Check authentication status
    if not auth.is_authenticated():
        # Show login page
        render_login_page(auth)
    else:
        # User is authenticated, route based on user type
        user_type = st.session_state.get('user_type')
        username = st.session_state.get('username')
        
        # Show header with logout
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.markdown(f"👋 **{username}**")
        with col3:
            if st.button("Logout", type="secondary"):
                auth.logout()
                st.rerun()
        
        # Route to appropriate UI
        if user_type == 'admin':
            render_admin_debug_ui()
        else:  # normal user (seoapp)
            render_normal_user_ui()

if __name__ == "__main__":
    main()