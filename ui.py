import streamlit as st
import streamlit.components.v1 as components
import json
import requests
import os
import datetime
from dotenv import load_dotenv
from state import get_timestamp
from image_gen import generate_image_hf

# Load environment variables
load_dotenv()

# Initialize RAG Engine lazily
@st.cache_resource(show_spinner=False)
def get_rag_engine():
    from rag_engine import RAGEngine
    return RAGEngine()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def search_web(query):
    """Perform a web search using Serper API."""
    if not SERPER_API_KEY or SERPER_API_KEY == "your_serper_api_key_here":
        return "Error: Serper API key not configured."
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
        results = response.json()
        
        output = []
        # Priority 1: Google's direct answer box
        if results.get("answerBox"):
            answer = results["answerBox"].get("answer") or results["answerBox"].get("snippet")
            if answer:
                output.append(f"DIRECT ANSWER: {answer}")

        # Priority 2: Knowledge Graph
        if results.get("knowledgeGraph"):
            kg = results["knowledgeGraph"]
            output.append(f"KNOWLEDGE GRAPH: {kg.get('title')} - {kg.get('description')}")

        # Priority 3: Organic snippets
        for result in results.get("organic", []):
            title = result.get('title', 'No Title')
            snippet = result.get('snippet', 'No Snippet')
            link = result.get('link', 'No Link')
            output.append(f"🔍 REAL-TIME TRUTH from {title}\nLINK: {link}\nCONTENT: {snippet}")
        
        return "\n\n---\n\n".join(output[:4]) if output else "No results found."
    except Exception as e:
        return f"Error during search: {e}"

def render_sidebar(messages):
    from state import create_new_session
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h2 style='color: #6366f1; margin: 0;'>🧠 InsightBot</h2>
            <p style='font-size: 0.85rem; color: #94a3b8; font-style: italic;'>Enterprise Intelligence</p>
        </div>
    """, unsafe_allow_html=True)

    # Handle new session creation
    if st.sidebar.button("➕ New Chat Session", use_container_width=True):
        session_id = get_timestamp()
        st.session_state.current_session = session_id
        st.session_state.all_sessions[session_id] = create_new_session()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📜 Chat History")
    
    # Display existing sessions in a cleaner way
    for sid in sorted(st.session_state.all_sessions.keys(), reverse=True):
        is_active = (sid == st.session_state.current_session)
        col1, col2 = st.sidebar.columns([0.8, 0.2])
        with col1:
            if st.sidebar.button(f"📅 {sid}", key=f"switch_{sid}", use_container_width=True, type="secondary" if not is_active else "primary"):
                st.session_state.current_session = sid
                st.rerun()

    # Chat export
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Download Conversation",
        data=json.dumps(messages, indent=2),
        file_name=f"insight_{st.session_state.current_session.replace(':', '-')}.json",
        mime="application/json",
        use_container_width=True
    )


def render_header():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .main-header {
            background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 3.2rem;
            text-align: center;
            margin-bottom: 0;
            letter-spacing: -0.05em;
        }
        
        .sub-header {
            text-align: center;
            color: #94a3b8;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }

        /* Glassmorphism for bubbles */
        .chat-bubble {
            padding: 1rem 1.5rem;
            border-radius: 1.2rem;
            margin-bottom: 1rem;
            max-width: 85%;
            line-height: 1.6;
            font-size: 1rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            position: relative; /* For the copy button positioning */
        }

        .user-bubble {
            background: #6366f1;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 0.2rem;
        }

        .bot-bubble {
            background: #1e293b;
            color: #f1f5f9;
            margin-right: auto;
            border-bottom-left-radius: 0.2rem;
            border: 1px solid #334155;
        }

        /* Copy Button Styling */
        .copy-btn {
            background: none;
            border: none;
            color: #94a3b8;
            cursor: pointer;
            font-size: 0.8rem;
            position: absolute;
            top: 10px;
            right: 15px;
            opacity: 0;
            transition: all 0.2s ease-in-out;
            border-radius: 6px;
            padding: 4px 8px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .chat-bubble:hover .copy-btn {
            opacity: 1;
        }

        .copy-btn:hover {
            color: #6366f1;
            background: rgba(99, 102, 241, 0.1);
        }

        .copy-btn.copied {
            color: #10b981 !important;
        }

        /* File Chip Styling (ChatGPT Style) */
        .file-chip {
            background: #2d3748;
            border: 1px solid #4a5568;
            border-radius: 12px;
            padding: 10px 15px;
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
            width: fit-content;
            max-width: 300px;
            transition: all 0.2s;
        }
        
        .file-chip:hover {
            border-color: #6366f1;
            background: #334155;
        }

        .file-icon {
            background: #e53e3e;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.8rem;
        }

        .file-info {
            display: flex;
            flex-direction: column;
        }

        .file-name {
            color: #f8fafc;
            font-size: 0.9rem;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }

        .file-type {
            color: #94a3b8;
            font-size: 0.75rem;
        }

        .chat-container {
            max-width: 850px;
            margin: 0 auto;
            padding-bottom: 20px;
        }

        /* Sidebar Button Fix (Rectangle) */
        [data-testid="stSidebar"] button {
            border-radius: 8px !important;
            width: 100% !important;
            height: auto !important;
            padding: 0.5rem 1rem !important;
            font-size: 0.9rem !important;
            margin-bottom: 5px !important;
        }

        /* Fixed Chat Input Wrapper */
        .stChatInput {
            border-radius: 12px !important;
        }
        
        /* Premium Popover Button Styling (Circular for attachment) */
        div[data-testid="stPopover"] button {
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 50% !important;
            width: 44px !important;
            height: 44px !important;
            padding: 0 !important;
            font-size: 1.4rem !important;
            color: #94a3b8 !important;
            transition: all 0.2s ease-in-out;
            margin-top: 4px;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        div[data-testid="stPopover"] button:hover {
            color: #6366f1 !important;
            border-color: #6366f1 !important;
            transform: translateY(-2px);
        }
    </style>

    <script>
        function copyToClipboard(elementId) {
            const textElement = document.getElementById(elementId);
            if (!textElement) return;
            
            // Get the text to copy
            const textToCopy = textElement.innerText;
            
            // Fallback copy method for older/insecure environments
            const textArea = document.createElement("textarea");
            textArea.value = textToCopy;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    // Find the button and show feedback
                    const btn = event.target.closest('.copy-btn');
                    if (btn) {
                        const originalContent = btn.innerHTML;
                        btn.innerHTML = "✓ Copied";
                        btn.classList.add("copied");
                        setTimeout(() => {
                            btn.innerHTML = originalContent;
                            btn.classList.remove("copied");
                        }, 2000);
                    }
                }
            } catch (err) {
                console.error('Copy fallback failed', err);
            }
            
            document.body.removeChild(textArea);
        }
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-header'>InsightBot</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Smarter Conversations, Better Insights</p>", unsafe_allow_html=True)
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

def render_messages(messages):
    with st.container():
        for i, msg in enumerate(messages):
            # Skip internal messages (unless they contain generated media)
            if msg.get("role") == "tool" and "image_path" not in msg:
                continue
            if msg.get("role") == "assistant" and "tool_calls" in msg and not msg.get("content") and "image_path" not in msg:
                continue
            
            # Show File Chips if available
            if "files" in msg:
                for file_name in msg["files"]:
                    ext = file_name.split('.')[-1].upper() if '.' in file_name else 'FILE'
                    st.markdown(f"""
                    <div class="file-chip">
                        <div class="file-icon">{ext}</div>
                        <div class="file-info">
                            <span class="file-name">{file_name}</span>
                            <span class="file-type">Document Attached</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Show Generated Images
            if "image_path" in msg and os.path.exists(msg["image_path"]):
                st.image(msg["image_path"], use_column_width=True, caption="InsightBot's Visualization")

            if not msg.get("content"):
                continue

            # Special handling for welcome message - display as centered header
            if i == 0 and msg.get("role") == "assistant" and "Welcome to" in msg.get("content", ""):
                st.markdown(f"""
                <div style="text-align: center; padding: 2rem 0; margin-bottom: 1rem;">
                    <p style="color: #ffffff; font-size: 1.3rem; font-weight: 500; margin: 0;">
                        {msg["content"].replace("**", "")}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                continue

            bubble_type = "user-bubble" if msg["role"] == "user" else "bot-bubble"
            content_escaped = msg["content"].replace("`", "\\`").replace("$", "\\$")
            
            # Using components.html for proper JS execution
            bubble_html = f"""
            <style>
                body {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; background: transparent; }}
                .chat-bubble {{
                    padding: 1rem 1.5rem;
                    border-radius: 1.2rem;
                    line-height: 1.6;
                    font-size: 1rem;
                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                    position: relative;
                }}
                .user-bubble {{
                    background: #6366f1;
                    color: white;
                }}
                .bot-bubble {{
                    background: #1e293b;
                    color: #f1f5f9;
                    border: 1px solid #334155;
                }}
                .copy-btn {{
                    background: none;
                    border: none;
                    color: #94a3b8;
                    cursor: pointer;
                    font-size: 0.8rem;
                    position: absolute;
                    top: 10px;
                    right: 15px;
                    border-radius: 6px;
                    padding: 4px 8px;
                    transition: all 0.2s ease-in-out;
                }}
                .copy-btn:hover {{
                    color: #6366f1;
                    background: rgba(99, 102, 241, 0.1);
                }}
                .copy-btn.copied {{
                    color: #10b981 !important;
                }}
            </style>
            <div class="chat-bubble {bubble_type}">
                <button class="copy-btn" onclick="copyText(this)">📋 Copy</button>
                <div class="msg-content">{content_escaped}</div>
            </div>
            <script>
                function copyText(btn) {{
                    const text = btn.parentElement.querySelector('.msg-content').innerText;
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    btn.innerHTML = "✓ Copied";
                    btn.classList.add("copied");
                    setTimeout(() => {{
                        btn.innerHTML = "📋 Copy";
                        btn.classList.remove("copied");
                    }}, 2000);
                }}
            </script>
            """
            # Estimate height based on content length
            estimated_height = max(80, min(400, 60 + len(msg["content"]) // 3))
            components.html(bubble_html, height=estimated_height)
            
    # Show Pending Files (Files uploaded but not yet "sent" with a prompt)
    session_data = st.session_state.all_sessions[st.session_state.current_session]
    
    # Get all files that have already been attached to messages
    attached_files = set()
    for msg in messages:
        if "files" in msg:
            attached_files.update(msg["files"])
    
    # Only show files as pending if they're uploaded but NOT yet attached to any message
    uploaded_files = session_data.get("uploaded_files", [])
    truly_pending = [f for f in uploaded_files if f not in attached_files]
    
    if truly_pending:
        for file_name in truly_pending:
            ext = file_name.split('.')[-1].upper() if '.' in file_name else 'FILE'
            st.markdown(f"""
            <div class="file-chip" style="opacity: 0.8; border-style: dashed;">
                <div class="file-icon" style="background: #718096;">{ext}</div>
                <div class="file-info">
                    <span class="file-name">{file_name}</span>
                    <span class="file-type">Pending - Send message to analyze</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def handle_chat_input(messages):
    # Get current session data
    session_data = st.session_state.all_sessions[st.session_state.current_session]
    uploaded_files_list = session_data.get("uploaded_files", [])
    pending_files_list = session_data.get("pending_files", [])
    
    # ChatGPT-style Layout: Attachment button next to Input
    # We use a container to keep them together at the bottom
    input_container = st.container()
    
    with input_container:
        col1, col2 = st.columns([0.08, 0.92])
        
        with col1:
            # The "Plus" or "Clip" button for attachments
            with st.popover("📎", help="Add documents (PDF, DOCX, TXT)"):
                st.markdown("### 📂 Add Knowledge")
                # Use session-specific key so each chat has isolated upload state
                uploader_key = f"file_uploader_{st.session_state.current_session.replace(' ', '_').replace(':', '_').replace('-', '_')}"
                uploaded_files = st.file_uploader(
                    "Upload files", 
                    type=['pdf', 'docx', 'txt'], 
                    accept_multiple_files=True,
                    key=uploader_key,
                    label_visibility="collapsed"
                )
                
                if uploaded_files:
                    re = get_rag_engine()
                    processed_any = False
                    for uf in uploaded_files:
                        if uf.name not in uploaded_files_list:
                            with st.status(f"Indexing {uf.name}...", expanded=False) as status:
                                vs, msg = re.process_file(uf, session_data)
                                if vs:
                                    session_data["uploaded_files"].append(uf.name)
                                    session_data["pending_files"].append(uf.name)
                                    status.update(label=f"✅ {uf.name} Ready", state="complete")
                                    processed_any = True
                                else:
                                    st.error(msg)
                    
                    if processed_any:
                        st.rerun()

                if uploaded_files_list:
                    st.divider()
                    st.caption("Indexed Documents:")
                    for f in uploaded_files_list:
                        st.text(f"✔ {f}")
                    
                    if st.button("🗑️ Clear All", use_container_width=True):
                        session_data["vector_store"] = None
                        session_data["uploaded_files"] = []
                        session_data["pending_files"] = []
                        st.rerun()

        with col2:
            prompt = st.chat_input("Ask InsightBot about your files or search the web...")

    if prompt:
        new_msg = {"role": "user", "content": prompt}
        
        # Only attach files that are uploaded but NOT yet attached to any previous message
        attached_files = set()
        for msg in messages:
            if "files" in msg:
                attached_files.update(msg["files"])
        
        uploaded = session_data.get("uploaded_files", [])
        new_files = [f for f in uploaded if f not in attached_files]
        
        if new_files:
            new_msg["files"] = new_files.copy()
            
        messages.append(new_msg)
        session_data["messages"] = messages
        st.rerun()

def handle_interaction(payload, messages):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Step 1: Attempt interaction with potential tool use
        r = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
        
        # Step 2: Fallback if tool-calling fails (Groq specific error handling)
        if r.status_code != 200:
            error_data = r.json()
            err_msg = error_data.get('error', {}).get('message', '')
            
            # If the specific model doesn't support tools or is failing, fallback to no-tool streaming
            if "Failed to call a function" in err_msg or r.status_code == 400:
                fallback_payload = payload.copy()
                fallback_payload.pop("tools", None)
                fallback_payload.pop("tool_choice", None)
                fallback_payload["stream"] = True
                st.info("🔄 Optimizing response path...")
                return stream_response(fallback_payload)
            
            st.error(f"🚀 Groq API Error: {err_msg}")
            return "I'm having trouble connecting right now. Please try again."

        result = r.json()
        if 'choices' not in result or not result['choices']:
            return "The AI returned an empty response."

        message = result['choices'][0]['message']
        
        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])
            if function_name == "web_search":
                with st.status("🔍 Searching the web...", expanded=False):
                    search_results = search_web(function_args.get("query"))
                    if not search_results or "No results found" in search_results:
                        search_results = "The web search returned no relevant results for this query."
                    st.write("Summarizing information...")
                
                # Add the tool results to conversation
                messages.append(message) # Add the assistant tool call message
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function_name,
                    "content": search_results
                })
                
                # Get the final response
                # Clean messages for API
                api_convo = []
                for m in messages:
                    api_convo.append({k: v for k, v in m.items() if k in ["role", "content", "name", "tool_call_id", "tool_calls"]})

                final_payload = {
                    "model": payload["model"],
                    "messages": [
                        payload["messages"][0], # System prompt
                        *api_convo
                    ],
                    "stream": True,
                    "max_tokens": 500
                }
                return stream_response(final_payload)

            elif function_name == "generate_image":
                image_prompt = function_args.get("prompt")
                with st.status(f"🎨 Painting: {image_prompt}...", expanded=True) as status:
                    image, error = generate_image_hf(image_prompt)
                    if error:
                        st.error(error)
                        return f"I tried to generate that image, but ran into an issue: {error}"
                    
                    # Save the image
                    if not os.path.exists("generated_images"):
                        os.makedirs("generated_images")
                    img_path = f"generated_images/img_{get_timestamp().replace(':', '-')}.png"
                    image.save(img_path)
                    status.update(label="✅ Vision complete!", state="complete")
                
                # Add the tool results to conversation for history
                messages.append(message) # Assistant's tool call
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function_name,
                    "content": f"Generated image for: {image_prompt}",
                    "image_path": img_path
                })
                return f"I've generated a visualization for you: **{image_prompt}**"
        
        # Optimization: We already have the full content from the first request.
        # Returning it directly is faster and more reliable than starting a new stream.
        content = message.get("content")
        if content:
            return content
        
        return "I couldn't generate a text response."

    except Exception as e:
        st.error(f"❌ Processing Error: {e}")
        return "I encountered an error while thinking about your request."

def show_user_bubble(text):
    st.markdown(f"""
    <div class="chat-bubble user-bubble">
        {text}
    </div>
    """, unsafe_allow_html=True)

def stream_response(payload):
    response_text = ""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(GROQ_API_URL, json=payload, headers=headers, stream=True, timeout=30)
        
        if r.status_code != 200:
            try:
                error_data = r.json()
                msg = error_data.get('error', {}).get('message', 'Unknown Error')
                st.error(f"Groq API Error ({r.status_code}): {msg}")
                return f"⚠️ Error: {msg}"
            except:
                st.error(f"Groq API Error ({r.status_code}): Connection failed.")
                return f"⚠️ Connection error (Status {r.status_code})."

        placeholder = st.empty()
        placeholder.markdown(loading_bubble(), unsafe_allow_html=True)

        for line in r.iter_lines():
            if line:
                decoded_line = line.decode("utf-8").strip()
                if not decoded_line:
                    continue
                if decoded_line.startswith("data: "):
                    decoded_line = decoded_line[6:] # Strip "data: "
                if decoded_line == "[DONE]":
                    break
                
                try:
                    data = json.loads(decoded_line)
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        response_text += delta
                        placeholder.markdown(bot_bubble(response_text), unsafe_allow_html=True)
                except json.JSONDecodeError:
                    continue
        
        # Final render to remove any artifacts and ensure clean bubble
        if response_text:
            placeholder.markdown(bot_bubble(response_text), unsafe_allow_html=True)
        else:
            placeholder.empty()
            return "The AI did not provide an answer. Please try rephrasing."
            
    except Exception as e:
        st.error(f"❌ Streaming Error: {e}")
        response_text = "Sorry, something went wrong while generating the final response."
    return response_text

def loading_bubble():
    return """
    <div style='text-align:left; background-color:#f1f0f0; padding:10px; margin:10px; border-radius:10px; max-width:80%; float:left; clear:both;'>
        <span class="typing-dot"></span>
        <span class="typing-dot" style="animation-delay: 0.2s;"></span>
        <span class="typing-dot" style="animation-delay: 0.4s;"></span>
    </div>
    <style>
    .typing-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        margin-right: 5px;
        background-color: #555;
        border-radius: 50%;
        animation: blink 1.4s infinite;
    }
    @keyframes blink {
        0%, 80%, 100% { opacity: 0; }
        40% { opacity: 1; }
    }
    </style>
    """

def bot_bubble(text):
    return f"""
    <div class="chat-bubble bot-bubble">
        {text}
    </div>
    """
def loading_dots():
    return """
    <span class="typing-dot"></span>
    <span class="typing-dot" style="animation-delay: 0.2s;"></span>
    <span class="typing-dot" style="animation-delay: 0.4s;"></span>
    <style>
    .typing-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        margin-left: 3px;
        background-color: #555;
        border-radius: 50%;
        animation: blink 1.4s infinite;
    }
    @keyframes blink {
        0%, 80%, 100% { opacity: 0; }
        40% { opacity: 1; }
    }
    </style>
    """
