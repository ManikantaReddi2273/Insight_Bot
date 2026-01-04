import streamlit as st
import requests
import json
from datetime import datetime
from state import initialize_state, get_timestamp

# === Page Config ===
st.set_page_config(page_title="InsightBot", page_icon="🧠", layout="wide")

# === Initialize Session State ===
initialize_state()
messages = st.session_state.all_sessions[st.session_state.current_session]

# === UI ===
from ui import render_sidebar, render_header, render_messages, handle_chat_input

try:
    render_sidebar(messages)
    render_header()
    render_messages(messages)
    
    # RESPONSE GENERATION LOGIC:
    # If the last message is from the user, generate the bot response before showing the input bar
    if len(messages) > 0 and messages[-1]["role"] == "user":
        prompt = messages[-1]["content"]
        
        # Retrieve Context from Vector Store
        doc_context = ""
        if st.session_state.vector_store:
            from ui import get_rag_engine
            rag_engine = get_rag_engine()
            doc_context = rag_engine.query_docs(prompt)

        from ui import GROQ_MODEL
        system_prompt = (
            f"Current Date: {datetime.now().strftime('%A, %B %d, %Y')}\n"
            f"Current Time: {datetime.now().strftime('%I:%M:%S %p')}\n\n"
            "You are InsightBot, a smart and friendly AI assistant.\n\n"
        )

        if doc_context:
            system_prompt += (
                "DOCUMENT CONTEXT:\n"
                f"{doc_context}\n\n"
            )

        system_prompt += (
            "BEHAVIOR POLICY:\n"
            "1. GREETINGS: Respond warmly. Do NOT search for these.\n"
            "2. DOMAIN: Use 'web_search' for news/current events not in docs.\n"
            "3. HIERARCHY: Documents > Web > Base Knowledge.\n"
        )

        # Clean messages for API (remove extra keys like 'files' that Groq doesn't support)
        api_messages = []
        for m in messages:
            clean_m = {k: v for k, v in m.items() if k in ["role", "content", "name", "tool_call_id", "tool_calls"]}
            api_messages.append(clean_m)

        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "system", "content": system_prompt}] + api_messages,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for up-to-date or missing information.",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_image",
                        "description": "Generate an artistic image based on a text prompt.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The detailed description of the image to generate."
                                }
                            },
                            "required": ["prompt"]
                        }
                    }
                }
            ],
            "tool_choice": "auto",
            "max_tokens": 500
        }

        from ui import handle_interaction
        response_text = handle_interaction(payload, messages)
        messages.append({"role": "assistant", "content": response_text})
        st.session_state.all_sessions[st.session_state.current_session] = messages
        st.rerun()

    handle_chat_input(messages)
    st.markdown("</div>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Critical Rendering Error: {e}")
    import traceback
    st.code(traceback.format_exc())
