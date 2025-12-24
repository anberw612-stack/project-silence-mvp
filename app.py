"""
Confuser Web App - Streamlit Interface

A privacy-preserving chat application that enables cross-user knowledge sharing
through AI-powered text perturbation.

Features:
- Supabase Auth (Email/Password)
- Multi-session chat history
- Privacy-preserving peer insights
"""

import streamlit as st
from openai import OpenAI
from layer1_matching import SemanticMatcher
from layer2_confuser import perturb_text, sanitize_response_consistency, perturb_pair
from layer3_consistency import check_and_fix_response
from layer4_decoy_factory import generate_decoys
import database_manager as db
import auth_ui
import numpy as np
import threading
import uuid
import os

# Default API key for DeepSeek
DEFAULT_API_KEY = os.environ.get("DEEPSEEK_API_KEY", st.secrets.get("DEEPSEEK_API_KEY", ""))


# ===================================================================
# AUTHENTICATION CHECK (Must be first!)
# ===================================================================
auth_ui.init_auth_state()

# If not logged in, show auth page and stop
if not auth_ui.is_logged_in():
    auth_ui.render_auth_page()
    st.stop()


# ===================================================================
# PAGE CONFIG (Only runs if logged in)
# ===================================================================
st.set_page_config(
    page_title="Confuser - Privacy-First Chat",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ===================================================================
# SESSION STATE INITIALIZATION
# ===================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "matcher" not in st.session_state:
    with st.spinner("Loading semantic matching model..."):
        st.session_state.matcher = SemanticMatcher()

if "api_key" not in st.session_state:
    st.session_state.api_key = DEFAULT_API_KEY

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def get_ai_response(query, api_key):
    """
    Get response from DeepSeek API for the user's query.
    """
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise, and accurate answers."},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        raise Exception(f"API Error: {str(e)}")


def find_stratified_insights(user_query, api_key, debug_mode=False, exclude_source_id=None):
    """
    Search for similar past queries and return a STRATIFIED list of insights.
    """
    past_conversations = db.get_all_queries()
    
    if not past_conversations:
        return []
    
    candidate_ids = [conv[0] for conv in past_conversations]
    candidate_queries = [conv[1] for conv in past_conversations]
    source_ids = [conv[3] for conv in past_conversations]
    
    matcher = st.session_state.matcher
    
    matches = matcher.get_stratified_matches(user_query, candidate_queries, candidate_ids, source_ids, exclude_source_id=exclude_source_id)
    
    insights = []
    
    for match in matches:
        try:
            query_text = match['query']
            response_text = db.get_response_by_query(query_text)
            
            insights.append({
                "question": query_text,
                "response": response_text,
                "layer": match['layer'],
                "score": match['score']
            })
        except Exception as e:
            print(f"Error processing match: {e}")
            continue
            
    return insights


def load_session(session_id):
    """
    Load a chat session from the database into session state.
    """
    st.session_state.current_session_id = session_id
    st.session_state.messages = db.get_messages_by_session(session_id)


def start_new_chat():
    """
    Start a new chat session.
    """
    st.session_state.current_session_id = None
    st.session_state.messages = []


# ===================================================================
# SIDEBAR
# ===================================================================
with st.sidebar:
    st.title("🛡️ Confuser Chat")
    
    # --- User Info & Logout ---
    auth_ui.render_user_info()
    auth_ui.render_logout_button()
    
    st.divider()
    
    # --- New Chat Button ---
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()
    
    st.divider()
    
    # --- Chat History ---
    st.subheader("📜 Chat History")
    
    sessions = db.get_all_sessions(limit=20)
    
    if sessions:
        for session_id, title, created_at in sessions:
            is_current = session_id == st.session_state.current_session_id
            
            col1, col2 = st.columns([5, 1])
            
            with col1:
                display_title = title[:25] + "..." if len(title) > 25 else title
                if st.button(f"{'▶ ' if is_current else ''}{display_title}", key=f"session_{session_id}", use_container_width=True):
                    load_session(session_id)
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_{session_id}", help="Delete this chat"):
                    db.delete_session(session_id)
                    if session_id == st.session_state.current_session_id:
                        start_new_chat()
                    st.rerun()
    else:
        st.caption("No chat history yet. Start a new conversation!")
    
    st.divider()
    
    # --- Settings ---
    with st.expander("⚙️ Settings", expanded=False):
        api_key_input = st.text_input(
            "DeepSeek API Key",
            type="password",
            help="Enter your DeepSeek API key.",
            value=st.session_state.api_key or ""
        )
        
        if api_key_input:
            st.session_state.api_key = api_key_input
            st.success("✅ API Key set!")
        else:
            st.warning("⚠️ API key required")
        
        st.session_state.debug_mode = st.checkbox(
            "🔍 Debug Mode",
            value=st.session_state.debug_mode,
            help="Show debug information"
        )
    
    st.divider()
    
    # --- Database Stats ---
    with st.expander("📊 Stats", expanded=False):
        conv_count = db.get_conversation_count()
        session_count = len(db.get_all_sessions(limit=100))
        st.metric("Total Decoys", conv_count)
        st.metric("Your Chats", session_count)


# ===================================================================
# MAIN CHAT AREA
# ===================================================================
st.title("💬 Confuser Chat")

if st.session_state.current_session_id:
    st.caption(f"Session: {st.session_state.current_session_id[:8]}...")
else:
    st.caption("New conversation - start typing below!")

st.markdown("*Privacy-preserving chat with cross-user knowledge sharing*")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if "peer_insights" in message and message["peer_insights"]:
            insights = message["peer_insights"]
            
            for insight in insights:
                layer_icon = "🎯" if insight['layer'] == 'Precision' else "💡" if insight['layer'] == 'Resonance' else "🎁"
                
                with st.expander(f"{layer_icon} Someone asked: {insight['question'][:60]}...", expanded=False):
                    st.caption(f"Layer: {insight['layer']} ({insight['score']:.0%})")
                    st.markdown(f"**AI Answer:** {insight['response']}")


# ===================================================================
# CHAT INPUT HANDLING
# ===================================================================
if prompt := st.chat_input("Ask anything...", disabled=not st.session_state.api_key):
    
    if not st.session_state.api_key:
        st.error("⚠️ Please enter your API key in the sidebar first!")
        st.stop()
    
    # Create session if needed
    if st.session_state.current_session_id is None:
        session_title = prompt[:50] if len(prompt) <= 50 else prompt[:47] + "..."
        new_session_id = db.create_session(title=session_title)
        st.session_state.current_session_id = new_session_id
    
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Save user message to database
    db.save_message(st.session_state.current_session_id, "user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process the query
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            
            current_source_id = str(uuid.uuid4())
            
            # Step 1: Check for peer insights
            peer_insights = []
            try:
                peer_insights = find_stratified_insights(prompt, st.session_state.api_key, st.session_state.debug_mode, exclude_source_id=current_source_id)
            except Exception as e:
                st.warning(f"Could not search for peer insights: {e}")
            
            # Display insights
            if peer_insights:
                st.markdown("### 🧬 Peer Wisdom Found")
                for insight in peer_insights:
                    layer_icon = "🎯" if insight['layer'] == 'Precision' else "💡" if insight['layer'] == 'Resonance' else "🎁"
                    
                    with st.expander(f"{layer_icon} Someone asked: {insight['question'][:60]}...", expanded=False):
                         st.caption(f"Layer: {insight['layer']} ({insight['score']:.0%})")
                         st.markdown(f"**AI Answer:** {insight['response']}")
            
            # Step 2: Get AI response
            try:
                response = get_ai_response(prompt, st.session_state.api_key)
                
                st.markdown(response)
                
                # Save assistant message to database
                db.save_message(st.session_state.current_session_id, "assistant", response, peer_insights=peer_insights)
                
                # Trigger async decoy generation
                generation_thread = threading.Thread(
                    target=generate_decoys,
                    args=(prompt, response, st.session_state.api_key),
                    kwargs={"num_decoys": 3, "source_id": current_source_id}
                )
                generation_thread.start()
                
                st.caption("🛡️ Privacy: Decoys are being generated in the background...")
                
            except Exception as e:
                response = f"❌ Error: {str(e)}"
                st.error(response)
    
    # Add assistant message to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "peer_insights": peer_insights
    })
    
    st.rerun()


# ===================================================================
# FOOTER
# ===================================================================
st.divider()
st.caption("🛡️ Confuser MVP - Privacy-preserving AI chat with cross-user knowledge sharing")
st.caption("Powered by DeepSeek AI • Supabase Auth • Layer 1: Semantic Matching • Layer 2: Privacy Perturbation")
