import streamlit as st
import logging

logger = logging.getLogger(__name__)

class Authenticator:
    """Handles authentication using Streamlit secrets"""
    
    def __init__(self):
        self.users = st.secrets.get("auth", {}).get("users", {})
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user against secrets
        Returns True if authentication successful
        """
        if username in self.users:
            stored_password = self.users[username]
            if password == stored_password:
                # Set session state
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.session_state['user_type'] = 'admin' if username == 'admin' else 'normal'
                logger.info(f"User '{username}' logged in")
                return True
        return False
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> str:
        """Get current authenticated username"""
        return st.session_state.get('username', '')
    
    def get_user_type(self) -> str:
        """Get current user type (admin/normal)"""
        return st.session_state.get('user_type', 'normal')
    
    def logout(self):
        """Clear authentication session"""
        username = st.session_state.get('username', 'unknown')
        logger.info(f"User '{username}' logged out")
        
        keys_to_clear = ['authenticated', 'username', 'user_type']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear any cached data
        st.cache_data.clear()