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
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from openai import OpenAI
from layer0_router import route_query, classify_query
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
import json

# Default API key for DeepSeek
DEFAULT_API_KEY = os.environ.get("DEEPSEEK_API_KEY", st.secrets.get("DEEPSEEK_API_KEY", "sk-78279640394f4be3a0308ef6f589f880"))


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

# DEBUG: Print at app start to confirm code version
print("=" * 60)
print("🚀 APP STARTED - CODE VERSION: 2025-12-25-v3-SYNC-MODE")
print(f"🚀 SYNC_DECOY_GENERATION will be: {os.environ.get('SYNC_DECOY_GENERATION', 'true')}")
print("=" * 60)


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

if "generated_decoy_sources" not in st.session_state:
    # Track source_ids of decoys generated in this session to prevent self-matching
    st.session_state.generated_decoy_sources = set()

# Email composer state
if "show_email_composer" not in st.session_state:
    st.session_state.show_email_composer = False
if "email_to" not in st.session_state:
    st.session_state.email_to = ""  # Will store the decoy owner's REAL email
if "email_subject" not in st.session_state:
    st.session_state.email_subject = ""
if "email_insight_context" not in st.session_state:
    st.session_state.email_insight_context = ""
if "email_recipient_email" not in st.session_state:
    st.session_state.email_recipient_email = ""  # The actual recipient email (looked up from decoy)

# Toggle for sync vs async decoy generation
# HARDCODED TO TRUE - async has issues with st.rerun() killing threads
SYNC_DECOY_GENERATION = True  # Hardcoded for stability


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def send_peer_message(to_email: str, subject: str, body: str, insight_context: str = "", sender_email: str = None) -> dict:
    """
    Send an anonymous relay email to a peer user via Outlook SMTP.

    The email is sent FROM the system bot account (configured in secrets)
    TO the real user's email address (looked up from the decoy owner).

    Args:
        to_email: Recipient's real email address (from decoy owner lookup)
        subject: Email subject line
        body: Email body content
        insight_context: The decoy question that triggered this conversation
        sender_email: The sender's email (for reply-to, optional)

    Returns:
        dict with status and message
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    print(f"📧 [EMAIL] Attempting to send email...")
    print(f"   To: {to_email}")
    print(f"   Subject: {subject}")

    # Validate recipient
    if not to_email or to_email == "anonymous_peer" or "@" not in to_email:
        print(f"❌ [EMAIL] Invalid recipient: {to_email}")
        return {
            "status": "error",
            "message": "Could not find recipient email. The decoy owner may not have an email on file."
        }

    try:
        # Load bot credentials from Streamlit secrets
        bot_email = st.secrets["email"]["EMAIL_ADDRESS"]
        bot_password = st.secrets["email"]["EMAIL_PASSWORD"]

        print(f"   Bot: {bot_email}")

        # Create the email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[Confuser] {subject}"
        msg['From'] = f"Confuser Bot <{bot_email}>"
        msg['To'] = to_email

        # Build email body with context
        email_body = f"""
Hi there,

Someone on Confuser wants to connect with you regarding a question you asked.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Your Original Question (paraphrased):
{insight_context[:200]}{'...' if len(insight_context) > 200 else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 Their Message:
{body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an anonymous relay message. The sender's identity is protected.
To reply, you can respond to this email (it will be relayed back anonymously).

—
Confuser - Privacy-Preserving AI Chat
🛡️ Your data, your control.
"""

        # Create plain text and HTML versions
        text_part = MIMEText(email_body, 'plain', 'utf-8')
        msg.attach(text_part)

        # Connect to Outlook SMTP server
        print(f"   Connecting to smtp.office365.com:587...")
        with smtplib.SMTP('smtp.office365.com', 587) as server:
            server.starttls()  # Enable TLS
            print(f"   Logging in...")
            server.login(bot_email, bot_password)
            print(f"   Sending email...")
            server.sendmail(bot_email, to_email, msg.as_string())

        print(f"✅ [EMAIL] Successfully sent to {to_email}")
        return {
            "status": "success",
            "message": f"Message sent successfully!",
            "timestamp": str(uuid.uuid4())[:8]
        }

    except KeyError as ke:
        print(f"❌ [EMAIL] Missing secret: {ke}")
        return {
            "status": "error",
            "message": "Email configuration missing. Please set up email secrets."
        }
    except smtplib.SMTPAuthenticationError as auth_err:
        print(f"❌ [EMAIL] Authentication failed: {auth_err}")
        return {
            "status": "error",
            "message": "Email authentication failed. Check bot credentials."
        }
    except smtplib.SMTPException as smtp_err:
        print(f"❌ [EMAIL] SMTP error: {smtp_err}")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(smtp_err)}"
        }
    except Exception as e:
        print(f"❌ [EMAIL] Unexpected error: {e}")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }


def inject_insight_bar_css():
    """
    Inject CSS for the insight bar '...' button with tooltip and email composer overlay.
    """
    css = """
    <style>
    /* Style the "..." chat button in insight bars */
    /* Target buttons containing the ellipsis character */
    button[kind="secondary"]:has(p) {
        min-width: 40px !important;
        padding: 4px 8px !important;
    }

    /* Style for insight bar chat buttons */
    [data-testid="stHorizontalBlock"] button {
        font-size: 16px !important;
        min-height: 38px !important;
    }

    /* Hover effect for chat buttons */
    [data-testid="column"]:last-child button:hover {
        background-color: rgba(102, 126, 234, 0.1) !important;
        border-color: #667eea !important;
    }

    /* Email Composer Overlay - Gmail/LinkedIn style */
    .email-composer-overlay {
        position: fixed;
        bottom: 0;
        right: 20px;
        width: 400px;
        max-width: 90vw;
        background: white;
        border-radius: 12px 12px 0 0;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        animation: slideUp 0.3s ease-out;
    }

    @keyframes slideUp {
        from {
            transform: translateY(100%);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    .composer-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 12px 12px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .composer-header h4 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
    }

    .composer-close-btn {
        background: transparent;
        border: none;
        color: white;
        font-size: 20px;
        cursor: pointer;
        padding: 0;
        line-height: 1;
        opacity: 0.8;
        transition: opacity 0.2s;
    }

    .composer-close-btn:hover {
        opacity: 1;
    }

    .composer-body {
        padding: 16px;
    }

    .composer-field {
        margin-bottom: 12px;
    }

    .composer-field label {
        display: block;
        font-size: 12px;
        color: #666;
        margin-bottom: 4px;
        font-weight: 500;
    }

    .composer-field input,
    .composer-field textarea {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        font-size: 14px;
        transition: border-color 0.2s, box-shadow 0.2s;
        box-sizing: border-box;
    }

    .composer-field input:focus,
    .composer-field textarea:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .composer-field textarea {
        min-height: 120px;
        resize: vertical;
    }

    .composer-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        padding-top: 8px;
    }

    .composer-send-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .composer-send-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .composer-cancel-btn {
        background: #f5f5f5;
        color: #666;
        border: none;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.2s;
    }

    .composer-cancel-btn:hover {
        background: #e8e8e8;
    }

    /* Context preview */
    .composer-context {
        background: #f8f9fa;
        border-left: 3px solid #667eea;
        padding: 8px 12px;
        margin-bottom: 12px;
        border-radius: 0 8px 8px 0;
        font-size: 12px;
        color: #666;
    }

    .composer-context strong {
        color: #333;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_insight_with_chat_button(insight: dict, index: int):
    """
    Render an insight bar with the '...' chat button.

    Args:
        insight: Dict with question, response, layer, score
        index: Unique index for this insight (for button keys)
    """
    layer_icon = "🎯" if insight['layer'] == 'Precision' else "💡" if insight['layer'] == 'Resonance' else "🎁"
    question_preview = insight['question'][:60] + "..." if len(insight['question']) > 60 else insight['question']

    # Create columns for expander header and menu button
    col1, col2 = st.columns([0.95, 0.05])

    with col1:
        with st.expander(f"{layer_icon} Someone asked: {question_preview}", expanded=False):
            st.caption(f"Layer: {insight['layer']} ({insight['score']:.0%})")
            st.markdown(f"**AI Answer:** {insight['response']}")

    with col2:
        # Custom HTML button with tooltip
        button_html = f"""
        <div style="margin-top: 8px;">
            <button class="insight-menu-btn" onclick="window.parent.postMessage({{type: 'openComposer', index: {index}, question: '{insight['question'][:100].replace("'", "\\'")}'}}, '*')">
                ⋯
                <span class="tooltip">💬 Chat with them</span>
            </button>
        </div>
        """
        st.markdown(button_html, unsafe_allow_html=True)

    return index


def render_email_composer():
    """
    Render the fixed-position email composer overlay using Streamlit dialog.
    Looks up the decoy owner's email and sends a real email via SMTP.
    """
    if not st.session_state.show_email_composer:
        return

    # Use st.dialog for the email composer (Streamlit 1.33+)
    @st.dialog("💬 Message Anonymous Peer", width="large")
    def email_dialog():
        # Context preview - shows what question this is about
        if st.session_state.email_insight_context:
            st.markdown(f"""
            <div class="composer-context">
                <strong>Regarding:</strong> {st.session_state.email_insight_context[:100]}...
            </div>
            """, unsafe_allow_html=True)

        # Look up the owner's email from the decoy
        recipient_email = st.session_state.get("email_recipient_email", "")

        # Check if we have a valid recipient
        if recipient_email and "@" in recipient_email:
            st.caption(f"📨 To: Anonymous peer (email on file)")
        else:
            st.warning("⚠️ This decoy doesn't have owner information. Email may not be deliverable.")
            st.caption("📨 To: Anonymous peer (no email on file)")

        subject = st.text_input(
            "Subject",
            value=st.session_state.email_subject or "Re: Your question about...",
            placeholder="Enter subject..."
        )

        body = st.text_area(
            "Message",
            height=150,
            placeholder="Write your message here...\n\nYour identity remains private - only your message content will be shared."
        )

        # Action buttons
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_email_composer = False
                st.rerun()

        with col2:
            if st.button("Send Message", type="primary", use_container_width=True):
                if body.strip():
                    # Get the recipient email that was looked up when the button was clicked
                    to_email = st.session_state.get("email_recipient_email", "")

                    # Send the actual email via SMTP
                    result = send_peer_message(
                        to_email=to_email,
                        subject=subject,
                        body=body,
                        insight_context=st.session_state.email_insight_context
                    )

                    if result["status"] == "success":
                        st.success("✅ Message sent successfully!")
                        st.session_state.show_email_composer = False
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to send: {result['message']}")
                else:
                    st.warning("⚠️ Please enter a message")

    # Call the dialog
    email_dialog()


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
            max_tokens=4096  # Increased from 1000 to allow complete code responses
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise Exception(f"API Error: {str(e)}")


def find_stratified_insights(user_query, api_key, debug_mode=False, exclude_source_id=None):
    """
    Search for similar past queries from GLOBAL DECOYS and return a STRATIFIED list of insights.
    
    The global_decoys table is anonymous - no user_id is stored, so all authenticated users
    can see all decoys. This is the core privacy feature.
    
    Args:
        user_query (str): The user's query to find matches for
        api_key (str): DeepSeek API key for LLM validation
        debug_mode (bool): Enable debug output
        exclude_source_id (str): Source ID to exclude (prevents seeing your own just-generated decoys)
        
    Returns:
        list: List of insight dicts with question, response, layer, score
    """
    # Get all global decoys (anonymous, shared across all users)
    global_decoys = db.get_all_global_decoys()
    
    if not global_decoys:
        return []
    
    candidate_ids = [conv[0] for conv in global_decoys]
    candidate_queries = [conv[1] for conv in global_decoys]
    source_ids = [conv[3] for conv in global_decoys]
    
    # Additional self-match filtering: exclude decoys from this session
    # This prevents seeing decoys that were just generated from your own queries
    # DISABLED FOR TESTING - uncomment to re-enable self-exclusion
    # session_excluded_sources = st.session_state.get('generated_decoy_sources', set())

    # Filter out candidates from excluded sources
    # DISABLED FOR TESTING - allows seeing your own decoys to verify pipeline
    # if session_excluded_sources or exclude_source_id:
    #     filtered_data = []
    #     for i, (cid, cquery, _, sid) in enumerate(global_decoys):
    #         # Skip if source_id matches current generation OR is in session exclusion list
    #         if sid == exclude_source_id:
    #             continue
    #         if sid in session_excluded_sources:
    #             continue
    #         filtered_data.append((cid, cquery, sid))
    #
    #     if not filtered_data:
    #         return []
    #
    #     candidate_ids = [d[0] for d in filtered_data]
    #     candidate_queries = [d[1] for d in filtered_data]
    #     source_ids = [d[2] for d in filtered_data]
    
    matcher = st.session_state.matcher
    
    matches = matcher.get_stratified_matches(user_query, candidate_queries, candidate_ids, source_ids, exclude_source_id=exclude_source_id)
    
    insights = []
    
    for match in matches:
        try:
            query_text = match['query']
            # Get response from global_decoys table
            response_text = db.get_global_decoy_response(query_text)
            
            if response_text:
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

# Inject custom CSS for insight bar and email composer
inject_insight_bar_css()

# Render email composer dialog if triggered
render_email_composer()

st.title("💬 Confuser Chat")

if st.session_state.current_session_id:
    st.caption(f"Session: {st.session_state.current_session_id[:8]}...")
else:
    st.caption("New conversation - start typing below!")

st.markdown("*Privacy-preserving chat with cross-user knowledge sharing*")

# Display chat messages
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if "peer_insights" in message and message["peer_insights"]:
            insights = message["peer_insights"]

            for insight_idx, insight in enumerate(insights):
                layer_icon = "🎯" if insight['layer'] == 'Precision' else "💡" if insight['layer'] == 'Resonance' else "🎁"
                question_preview = insight['question'][:60] + "..." if len(insight['question']) > 60 else insight['question']

                # Create container for insight + chat button
                insight_container = st.container()
                with insight_container:
                    col1, col2 = st.columns([0.92, 0.08])

                    with col1:
                        with st.expander(f"{layer_icon} Someone asked: {question_preview}", expanded=False):
                            st.caption(f"Layer: {insight['layer']} ({insight['score']:.0%})")
                            st.markdown(f"**AI Answer:** {insight['response']}")

                    with col2:
                        # "..." button with tooltip using native Streamlit
                        unique_key = f"chat_btn_hist_{msg_idx}_{insight_idx}"
                        if st.button("⋯", key=unique_key, help="💬 Chat with them"):
                            # Look up the owner's email from the decoy question
                            owner_email = db.get_decoy_owner_email(insight['question'])
                            st.session_state.show_email_composer = True
                            st.session_state.email_insight_context = insight['question']
                            st.session_state.email_subject = f"Re: {insight['question'][:50]}..."
                            st.session_state.email_recipient_email = owner_email or ""
                            st.rerun()


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

            # ===================================================================
            # LAYER 0: Privacy Necessity Router
            # Classify query to determine if decoy generation is needed
            # ===================================================================
            should_generate, classification, feedback_prompt = route_query(prompt, st.session_state.api_key)
            privacy_category = classification.get("category", "AMBIGUOUS")
            privacy_risk = classification.get("privacy_risk", "MEDIUM")

            # Show classification in debug mode
            if st.session_state.debug_mode:
                st.info(f"🚦 Layer 0: {privacy_category} | Privacy Risk: {privacy_risk} | Decoy: {should_generate}")

            # Step 1: Check for peer insights (only if privacy-sensitive)
            peer_insights = []
            if should_generate and privacy_risk in ["MEDIUM", "HIGH"]:
                try:
                    peer_insights = find_stratified_insights(prompt, st.session_state.api_key, st.session_state.debug_mode, exclude_source_id=current_source_id)
                except Exception as e:
                    st.warning(f"Could not search for peer insights: {e}")

            # Display insights with chat buttons
            if peer_insights:
                st.markdown("### 🧬 Peer Wisdom Found")
                for new_insight_idx, insight in enumerate(peer_insights):
                    layer_icon = "🎯" if insight['layer'] == 'Precision' else "💡" if insight['layer'] == 'Resonance' else "🎁"
                    question_preview = insight['question'][:60] + "..." if len(insight['question']) > 60 else insight['question']

                    # Create container for insight + chat button
                    insight_container = st.container()
                    with insight_container:
                        col1, col2 = st.columns([0.92, 0.08])

                        with col1:
                            with st.expander(f"{layer_icon} Someone asked: {question_preview}", expanded=False):
                                st.caption(f"Layer: {insight['layer']} ({insight['score']:.0%})")
                                st.markdown(f"**AI Answer:** {insight['response']}")

                        with col2:
                            # "..." button with tooltip using native Streamlit
                            unique_key = f"chat_btn_new_{new_insight_idx}_{current_source_id[:8]}"
                            if st.button("⋯", key=unique_key, help="💬 Chat with them"):
                                # Look up the owner's email from the decoy question
                                owner_email = db.get_decoy_owner_email(insight['question'])
                                st.session_state.show_email_composer = True
                                st.session_state.email_insight_context = insight['question']
                                st.session_state.email_subject = f"Re: {insight['question'][:50]}..."
                                st.session_state.email_recipient_email = owner_email or ""
                                st.rerun()

            # Step 2: Get AI response
            try:
                print(f"🔵 [APP] Getting AI response for prompt: {prompt[:50]}...")
                response = get_ai_response(prompt, st.session_state.api_key)
                print(f"🔵 [APP] Got AI response, length: {len(response)}")

                st.markdown(response)

                # Save assistant message to database
                print(f"🔵 [APP] Saving assistant message to database...")
                db.save_message(st.session_state.current_session_id, "assistant", response, peer_insights=peer_insights)
                print(f"🔵 [APP] Message saved!")

                # Track this source_id to prevent self-matching in future queries
                st.session_state.generated_decoy_sources.add(current_source_id)

                # ===================================================================
                # LAYER 0 GATE: Only generate decoys if privacy-sensitive
                # ===================================================================
                if not should_generate:
                    print(f"🚦 [L0] Skipping decoy generation - Category: {privacy_category}, Risk: {privacy_risk}")
                    st.caption(f"ℹ️ No privacy protection needed for this query ({privacy_category})")
                else:
                    # Trigger decoy generation (saves to global_decoys table)
                    print(f"🔵 [APP] Preparing decoy generation...")
                    print(f"🔵 [APP] SYNC_DECOY_GENERATION = {SYNC_DECOY_GENERATION}")

                    # Pre-cache Supabase credentials for background thread access
                    os.environ["SUPABASE_URL"] = st.secrets.get("SUPABASE_URL", "")
                    os.environ["SUPABASE_KEY"] = st.secrets.get("SUPABASE_KEY", "")
                    print(f"🔵 [APP] Supabase credentials cached to env")

                    if SYNC_DECOY_GENERATION:
                        # SYNCHRONOUS MODE: For debugging - blocks UI but guarantees saves
                        st.toast("🛡️ Generating privacy decoys...", icon="🔄")
                        try:
                            # Get current user ID for email relay
                            current_user_id = db.get_current_user_id()
                            print(f"🔄 [SYNC] Starting decoy generation for source_id: {current_source_id[:8]}...")
                            print(f"🔄 [SYNC] Owner user_id: {current_user_id[:8] if current_user_id else 'None'}...")
                            generate_decoys(prompt, response, st.session_state.api_key, num_decoys=3, source_id=current_source_id, owner_user_id=current_user_id)
                            print(f"✅ [SYNC] Decoy generation completed!")
                            st.toast("✅ Privacy decoys saved!", icon="✅")
                        except Exception as e:
                            import traceback
                            print(f"❌ [SYNC] Decoy generation failed: {e}")
                            print(f"❌ [SYNC] Traceback: {traceback.format_exc()}")
                            st.warning(f"Decoy generation failed: {e}")
                    else:
                        # ASYNC MODE: Non-blocking background thread
                        print(f"🔵 [APP] Entering ASYNC mode...")

                        # Get current user ID for email relay (must capture before thread)
                        current_user_id = db.get_current_user_id()

                        # Capture current script context for thread
                        current_ctx = get_script_run_ctx()
                        print(f"🔵 [APP] Got script context: {current_ctx}")

                        def generate_decoys_with_callback(p, r, api_key, num_decoys, source_id, owner_user_id):
                            """Wrapper to catch errors and log results."""
                            print(f"🟢 [THREAD-INNER] Thread callback started!")
                            print(f"🟢 [THREAD-INNER] source_id: {source_id[:8]}...")
                            print(f"🟢 [THREAD-INNER] owner_user_id: {owner_user_id[:8] if owner_user_id else 'None'}...")
                            try:
                                print(f"🔄 [THREAD] Starting decoy generation for source_id: {source_id[:8]}...")
                                generate_decoys(p, r, api_key, num_decoys=num_decoys, source_id=source_id, owner_user_id=owner_user_id)
                                print(f"✅ [THREAD] Decoy generation completed for source_id: {source_id[:8]}...")
                            except Exception as e:
                                import traceback
                                print(f"❌ [THREAD] Decoy generation failed: {e}")
                                print(f"❌ [THREAD] Traceback: {traceback.format_exc()}")

                        print(f"🔵 [APP] Creating thread...")
                        generation_thread = threading.Thread(
                            target=generate_decoys_with_callback,
                            args=(prompt, response, st.session_state.api_key, 3, current_source_id, current_user_id),
                            name=f"decoy_gen_{current_source_id[:8]}"
                        )
                        print(f"🔵 [APP] Thread created: {generation_thread.name}")

                        # CRITICAL: Add Streamlit script context to the thread
                        print(f"🔵 [APP] Adding script context to thread...")
                        add_script_run_ctx(generation_thread, current_ctx)
                        print(f"🔵 [APP] Script context added!")

                        print(f"🔵 [APP] Starting thread...")
                        generation_thread.start()
                        print(f"🔵 [APP] Thread started! is_alive={generation_thread.is_alive()}")

                        st.toast("🛡️ Decoy generation started...", icon="🔄")

                    st.caption("🛡️ Privacy protection active for this conversation.")
                
            except Exception as e:
                response = f"❌ Error: {str(e)}"
                st.error(response)
    
    # Add assistant message to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "peer_insights": peer_insights
    })

    # Re-enabled: Safe now that we're using SYNC mode (threads complete before rerun)
    st.rerun()


# ===================================================================
# FOOTER
# ===================================================================
st.divider()
st.caption("🛡️ Confuser MVP - Privacy-preserving AI chat with cross-user knowledge sharing")
st.caption("Powered by DeepSeek AI • Supabase Auth • Layer 1: Semantic Matching • Layer 2: Privacy Perturbation")
