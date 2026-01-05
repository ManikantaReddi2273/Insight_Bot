from datetime import datetime
import streamlit as st

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_new_session():
    """Creates a new session with all required fields."""
    return {
        "messages": [{"role": "assistant", "content": "Welcome to **InsightBot**. How can I help you today?"}],
        "vector_store": None,
        "uploaded_files": [],
        "pending_files": []
    }

def get_current_session_data():
    """Returns the current session's data dictionary."""
    session_id = st.session_state.current_session
    return st.session_state.all_sessions.get(session_id, create_new_session())

def initialize_state():
    if "all_sessions" not in st.session_state:
        st.session_state.all_sessions = {}

    # Migrate old sessions (list format) to new format (dict format)
    for session_id, session_data in st.session_state.all_sessions.items():
        if isinstance(session_data, list):
            # Old format: session_data is a list of messages
            st.session_state.all_sessions[session_id] = {
                "messages": session_data,
                "vector_store": None,
                "uploaded_files": [],
                "pending_files": []
            }

    if "current_session" not in st.session_state or st.session_state.current_session not in st.session_state.all_sessions:
        session_id = get_timestamp()
        st.session_state.current_session = session_id
        st.session_state.all_sessions[session_id] = create_new_session()
