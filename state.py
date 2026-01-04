from datetime import datetime
import streamlit as st

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def initialize_state():
    if "all_sessions" not in st.session_state:
        st.session_state.all_sessions = {}

    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None

    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    if "pending_files" not in st.session_state:
        st.session_state.pending_files = []

    if "current_session" not in st.session_state or st.session_state.current_session not in st.session_state.all_sessions:
        session_id = get_timestamp()
        st.session_state.current_session = session_id
        st.session_state.all_sessions[session_id] = [
            {"role": "assistant", "content": "Welcome to **InsightBot**. How can I help you today?"}
        ]
