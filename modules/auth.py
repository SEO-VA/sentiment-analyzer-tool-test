import streamlit as st

def check_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_type = None
    
    if not st.session_state.authenticated:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users = st.secrets["auth"]["users"]
            if username in users and password == users[username]:
                st.session_state.authenticated = True
                st.session_state.user_type = "admin" if username == "admin" else "normal"
                st.rerun()
            else:
                st.error("Invalid credentials")
        return False
    
    return True

def get_user_type():
    return st.session_state.user_type
