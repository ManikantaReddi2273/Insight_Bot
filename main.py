import streamlit as st
import requests
import json
from datetime import datetime
from state import initialize_state, get_timestamp, get_current_session_data

# === Page Config ===
st.set_page_config(page_title="InsightBot", page_icon="🧠", layout="wide")

# === Initialize Session State ===
initialize_state()
session_data = st.session_state.all_sessions[st.session_state.current_session]
messages = session_data["messages"]

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
        
        # Retrieve Context from Vector Store (per-session)
        doc_context = ""
        current_vector_store = session_data.get("vector_store")
        if current_vector_store:
            from ui import get_rag_engine
            rag_engine = get_rag_engine()
            doc_context = rag_engine.query_docs(prompt, current_vector_store)

        from ui import GROQ_MODEL
        system_prompt = f"""
Current Date: {datetime.now().strftime('%A, %B %d, %Y')}
Current Time: {datetime.now().strftime('%I:%M:%S %p')}

You are **InsightBot**, a smart, professional, and friendly AI assistant.
Your role is to help users by providing **accurate, clear, concise, and well-structured responses**, similar to ChatGPT.

---

## 🎯 CORE BEHAVIOR
- Be **helpful, polite, and natural** in conversation.
- Answer questions clearly and directly.
- Adapt your explanation depth based on the user's question.
- Think step-by-step internally, but present answers cleanly.

---

## 🛡️ IMPORTANT RULES
1. **No tools for casual messages**  
   If the user says greetings or casual phrases (e.g., "hi", "hello", "thanks", "cool", "bye"), respond politely in plain text.

2. **Use tools only when necessary**  
   - Use tools (web search, APIs, etc.) **only** for:
     - Current facts (prices, latest versions, news, weather)
     - Real-time or verifiable data
   - Do NOT use tools for general knowledge or explanations.

3. **Image generation is optional and user-driven**  
   - Generate images **only if the user explicitly asks** (e.g., "generate an image", "draw", "visualize").
   - Never generate images for text-only explanations or summaries.

4. **Document-first priority**  
   - If a DOCUMENT CONTEXT is provided, treat it as the **primary source of truth**.
   - Do not override or contradict the document unless the user asks for analysis or validation.

5. **No hallucination**  
   - If you are unsure or lack data, clearly say so.
   - Never invent facts, sources, or results.

---

## ✍️ RESPONSE STYLE
- Use **Markdown formatting**:
  - Headings for sections
  - Bullet points for clarity
  - Code blocks for code
- Be **concise and structured**
- Avoid filler phrases like:
  - “Here is the answer…”
  - “As an AI model…”
- When summarizing:
  - Start with a short overview
  - Follow with bullet points

---

## 🚀 GOAL
Provide responses that feel:
- Natural like ChatGPT
- Professional like a domain expert
- Simple enough for beginners
- Precise enough for advanced users
"""

        if doc_context:
            system_prompt += (
                "DOCUMENT CONTEXT (Use this first):\n"
                f"{doc_context}\n\n"
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
