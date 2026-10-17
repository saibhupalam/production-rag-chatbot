import streamlit as st
import time
from services.api import (
    upload_document,
    create_conversation,
    list_conversations,
    get_conversation,
    get_conversation_messages,
    delete_conversation,
    send_chat_message,
    check_backend_health,
    register_user,
    login_user,
    get_current_user_profile,
)

# Page configuration
st.set_page_config(
    page_title="Production RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, modern production appearance
st.markdown("""
<style>
    /* Metric and card aesthetics */
    .stCard {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #e9ecef;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 80%;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.25rem;
    }
    .badge-success {
        color: #fff;
        background-color: #28a745;
    }
    .badge-info {
        color: #fff;
        background-color: #17a2b8;
    }
    .badge-danger {
        color: #fff;
        background-color: #dc3545;
    }
    .chat-bubble-user {
        background-color: #e3f2fd;
        padding: 0.8rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }
    .chat-bubble-assistant {
        background-color: #f1f8e9;
        padding: 0.8rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize necessary session state variables."""
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "active_conversation_id" not in st.session_state:
        st.session_state.active_conversation_id = None
    if "active_conversation_title" not in st.session_state:
        st.session_state.active_conversation_title = None
    if "active_document_id" not in st.session_state:
        st.session_state.active_document_id = None
    if "active_document_name" not in st.session_state:
        st.session_state.active_document_name = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversations" not in st.session_state:
        st.session_state.conversations = []
    if "last_upload" not in st.session_state:
        st.session_state.last_upload = None


def refresh_conversations():
    """Fetch the list of conversations from the backend."""
    res = list_conversations(token=st.session_state.token)
    if res.get("success"):
        st.session_state.conversations = res.get("data", [])
    else:
        st.session_state.conversations = []


def load_conversation(conversation_id: int):
    """Load conversation messages and metadata into session state."""
    st.session_state.active_conversation_id = conversation_id
    
    # Fetch details
    conv_res = get_conversation(conversation_id, token=st.session_state.token)
    if conv_res.get("success"):
        data = conv_res.get("data", {})
        st.session_state.active_conversation_title = data.get("title", f"Conversation #{conversation_id}")
        st.session_state.active_document_id = data.get("document_id")
    
    # Fetch messages
    msg_res = get_conversation_messages(conversation_id, token=st.session_state.token)
    if msg_res.get("success"):
        st.session_state.messages = msg_res.get("data", [])
    else:
        st.session_state.messages = []


def render_auth_section():
    """Render Login/Register or User Profile in the sidebar."""
    st.sidebar.markdown("### 👤 User Account")
    
    if st.session_state.token and st.session_state.user:
        st.sidebar.success(f"Logged in as **{st.session_state.user.get('username')}**")
        st.sidebar.caption(f"Email: {st.session_state.user.get('email')}")
        if st.sidebar.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.active_conversation_id = None
            st.session_state.messages = []
            st.session_state.conversations = []
            st.rerun()
    else:
        auth_mode = st.sidebar.radio("Account Access", ["Guest Mode", "Login", "Register"], horizontal=True)
        
        if auth_mode == "Login":
            with st.sidebar.form("login_form"):
                ident = st.text_input("Username or Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                if submit:
                    if not ident or not password:
                        st.error("Please enter both credentials.")
                    else:
                        res = login_user(ident, password)
                        if res.get("success"):
                            data = res.get("data", {})
                            st.session_state.token = data.get("access_token")
                            st.session_state.user = data.get("user")
                            st.success("Logged in successfully!")
                            refresh_conversations()
                            st.rerun()
                        else:
                            st.error(f"Login failed: {res.get('error')}")

        elif auth_mode == "Register":
            with st.sidebar.form("register_form"):
                reg_username = st.text_input("Username")
                reg_email = st.text_input("Email")
                reg_password = st.text_input("Password", type="password")
                submit_reg = st.form_submit_button("Create Account", use_container_width=True)
                if submit_reg:
                    if not reg_username or not reg_email or not reg_password:
                        st.error("Please fill in all fields.")
                    else:
                        res = register_user(reg_username, reg_email, reg_password)
                        if res.get("success"):
                            st.success("Account created! Please switch to Login.")
                        else:
                            st.error(f"Registration failed: {res.get('error')}")
        else:
            st.sidebar.info("Operating in open mode (default user)")


def render_sidebar():
    """Render sidebar with conversations list and document upload."""
    st.sidebar.title("📚 RAG Chatbot")
    
    # System Health Badge
    health = check_backend_health()
    if health.get("healthy"):
        st.sidebar.caption("🟢 Backend: **Connected**")
    else:
        st.sidebar.caption("🔴 Backend: **Offline / Error**")
        st.sidebar.error(f"{health.get('error')}")

    render_auth_section()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Upload Document")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload a PDF or TXT file",
        type=["pdf", "txt"],
        help="Upload a technical document or report to query with RAG."
    )
    
    custom_conv_title = st.sidebar.text_input(
        "Conversation Title (optional)",
        placeholder="e.g., Deep Learning Discussion",
        help="Specify a custom title or leave blank to use the file name."
    )

    if uploaded_file is not None:
        upload_btn = st.sidebar.button("🚀 Process & Start Chat", use_container_width=True)
        if upload_btn:
            with st.sidebar.status("Processing document...", expanded=True) as status_box:
                st.write("📤 Uploading file to backend...")
                progress_bar = st.sidebar.progress(20)
                time.sleep(0.3)
                
                upload_res = upload_document(uploaded_file, token=st.session_state.token)
                progress_bar.progress(60)
                
                if upload_res.get("success"):
                    doc_data = upload_res.get("data", {})
                    doc_id = doc_data.get("document_id")
                    doc_name = doc_data.get("filename")
                    chunks_count = doc_data.get("chunks", 0)
                    
                    st.session_state.last_upload = doc_data
                    st.write(f"✅ Extracted & stored **{chunks_count}** chunks in Qdrant")
                    progress_bar.progress(85)
                    
                    # Create conversation automatically
                    conv_title = custom_conv_title.strip() if custom_conv_title.strip() else f"Chat: {doc_name}"
                    user_id = st.session_state.user.get("id") if st.session_state.user else 1
                    
                    st.write("💬 Initializing conversation...")
                    conv_res = create_conversation(
                        title=conv_title,
                        document_id=doc_id,
                        user_id=user_id,
                        token=st.session_state.token
                    )
                    progress_bar.progress(100)
                    
                    if conv_res.get("success"):
                        conv_data = conv_res.get("data", {})
                        new_conv_id = conv_data.get("id")
                        status_box.update(label="Document processed successfully!", state="complete", expanded=False)
                        st.sidebar.success(f"Ready to chat with **{doc_name}**!")
                        refresh_conversations()
                        load_conversation(new_conv_id)
                        st.rerun()
                    else:
                        status_box.update(label="Document uploaded, but conversation creation failed", state="error")
                        st.sidebar.error(f"Conversation error: {conv_res.get('error')}")
                else:
                    progress_bar.progress(100)
                    status_box.update(label="Upload and extraction failed", state="error")
                    st.sidebar.error(upload_res.get("error", "Unknown error during upload."))

    st.sidebar.markdown("---")
    col_head, col_refresh = st.sidebar.columns([3, 1])
    col_head.subheader("💬 Conversations")
    if col_refresh.button("🔄", help="Refresh conversations list"):
        refresh_conversations()
        st.rerun()

    if not st.session_state.conversations:
        refresh_conversations()

    if st.session_state.conversations:
        for conv in st.session_state.conversations:
            conv_id = conv.get("id")
            conv_title = conv.get("title", f"Chat #{conv_id}")
            is_active = conv_id == st.session_state.active_conversation_id
            
            c1, c2 = st.sidebar.columns([4, 1])
            button_label = f"👉 **{conv_title}**" if is_active else conv_title
            
            if c1.button(button_label, key=f"select_conv_{conv_id}", use_container_width=True):
                load_conversation(conv_id)
                st.rerun()
                
            if c2.button("🗑️", key=f"del_conv_{conv_id}", help=f"Delete '{conv_title}'"):
                del_res = delete_conversation(conv_id, token=st.session_state.token)
                if del_res.get("success"):
                    st.sidebar.success(f"Deleted #{conv_id}")
                    if st.session_state.active_conversation_id == conv_id:
                        st.session_state.active_conversation_id = None
                        st.session_state.messages = []
                        st.session_state.active_conversation_title = None
                    refresh_conversations()
                    st.rerun()
                else:
                    st.sidebar.error(f"Failed to delete: {del_res.get('error')}")
    else:
        st.sidebar.caption("No conversations yet. Upload a document to start!")


def render_main_chat():
    """Render active conversation header, chat history, and question input."""
    # Active conversation banner
    if st.session_state.active_conversation_id:
        st.subheader(f"💬 {st.session_state.active_conversation_title}")
        doc_info = f"Document ID: **{st.session_state.active_document_id}**" if st.session_state.active_document_id else "Document attached"
        st.caption(f"Conversation ID: `{st.session_state.active_conversation_id}` • {doc_info}")
        st.divider()

        # Display message history
        for msg in st.session_state.messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(content)
            elif role == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content)

        # Chat input box
        prompt = st.chat_input("Ask a question grounded in this document...")
        if prompt:
            # Immediately display user question
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(prompt)
                
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Assistant response with feedback spinner
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Searching document context and generating answer..."):
                    chat_res = send_chat_message(
                        conversation_id=st.session_state.active_conversation_id,
                        question=prompt,
                        token=st.session_state.token
                    )
                    
                    if chat_res.get("success"):
                        answer = chat_res.get("data", {}).get("answer", "No answer generated.")
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = f"⚠️ Could not generate answer: {chat_res.get('error')}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        # Welcome & Getting Started View
        st.title("📚 Production RAG Chatbot")
        st.markdown("""
        Welcome to your conversational **Retrieval-Augmented Generation (RAG)** assistant.
        
        ### 🚀 How to get started:
        1. **Upload a document** in the sidebar (supports `.pdf` and `.txt`).
        2. Click **Process & Start Chat** to extract text, chunk content, generate embeddings with Nomic Embed, and store vectors in Qdrant.
        3. Ask questions in the chat window — answers will be grounded directly in your uploaded material!
        4. Manage or reopen previous conversations anytime from the sidebar.
        """)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("⚡ **Vector Search**\n\nFast dense semantic retrieval via Qdrant vector database.")
        with col2:
            st.success("🔒 **Isolated History**\n\nConversations and messages persisted safely in PostgreSQL.")
        with col3:
            st.warning("🧠 **Accurate LLM Answers**\n\nHigh-quality answers powered by Groq LLM with strict context grounding.")


def main():
    init_session_state()
    render_sidebar()
    render_main_chat()


if __name__ == "__main__":
    main()