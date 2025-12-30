"""
Confuser Web App - Streamlit Interface

A privacy-preserving chat application that enables cross-user knowledge sharing
through AI-powered text perturbation.

Features:
- Supabase Auth (Email/Password)
- Multi-session chat history
- Privacy-preserving peer insights
- Multi-language support (English / 简体中文)
"""

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from openai import OpenAI
from layer0_router import route_query, classify_query
from layer1_matching import SemanticMatcher
from layer2_confuser import perturb_text, sanitize_response_consistency, perturb_pair
from layer3_consistency import check_and_fix_response
from layer4_decoy_factory import generate_decoys
from decoy_worker import DecoyWorker, get_or_create_worker, stop_worker, get_worker_status
import database_manager as db
import auth_ui
from i18n import (
    t, init_language, get_current_language, render_language_switcher,
    get_app_name, inject_font_css, SUPPORTED_LANGUAGES
)
import numpy as np
import threading
import uuid
import os
import json
import time

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
# Initialize language before page config
init_language()

st.set_page_config(
    page_title=f"{get_app_name()} - {t('app.tagline')}",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject font CSS for proper character rendering
inject_font_css()

# Toggle for sync vs async decoy generation
# Set to False to use new background worker architecture
SYNC_DECOY_GENERATION = False  # Use background worker for non-blocking generation

# DEBUG: Print at app start to confirm code version
print("=" * 60)
print("🚀 APP STARTED - CODE VERSION: 2025-12-26-v1-BACKGROUND-WORKER")
print(f"🚀 SYNC_DECOY_GENERATION: {SYNC_DECOY_GENERATION}")
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

# Background worker state
if "decoy_worker" not in st.session_state:
    st.session_state.decoy_worker = None  # Will hold DecoyWorker instance
if "decoy_worker_session_id" not in st.session_state:
    st.session_state.decoy_worker_session_id = str(uuid.uuid4())  # Unique ID for this session's worker
if "last_decoy_count" not in st.session_state:
    st.session_state.last_decoy_count = 0  # Track decoy count for polling
if "worker_task_id" not in st.session_state:
    st.session_state.worker_task_id = None  # Current task ID


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
        # Debug: Print available secrets keys (not values!)
        print(f"   Available secrets keys: {list(st.secrets.keys())}")

        if "email" not in st.secrets:
            print(f"❌ [EMAIL] 'email' section not found in secrets!")
            print(f"   Hint: Add [email] section to your Streamlit secrets")
            return {
                "status": "error",
                "message": "Email secrets not configured. Add [email] section with EMAIL_ADDRESS and EMAIL_PASSWORD."
            }

        print(f"   Email section keys: {list(st.secrets['email'].keys())}")

        bot_email = st.secrets["email"]["EMAIL_ADDRESS"]
        bot_password = st.secrets["email"]["EMAIL_PASSWORD"]

        print(f"   Bot: {bot_email}")

        # Determine SMTP server based on email domain
        if "gmail" in bot_email.lower():
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
        elif "outlook" in bot_email.lower() or "hotmail" in bot_email.lower():
            smtp_server = "smtp.office365.com"
            smtp_port = 587
        elif "yahoo" in bot_email.lower():
            smtp_server = "smtp.mail.yahoo.com"
            smtp_port = 587
        else:
            # Default to Gmail
            smtp_server = "smtp.gmail.com"
            smtp_port = 587

        print(f"   SMTP Server: {smtp_server}:{smtp_port}")

        # Create the email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[Confuser] {subject}"
        msg['From'] = f"Confuser Bot <{bot_email}>"
        msg['To'] = to_email

        # Plain text version (fallback)
        plain_text = f"""
Someone on Confuser wants to connect with you!

Regarding your question:
{insight_context[:200]}{'...' if len(insight_context) > 200 else ''}

Their message:
{body}

---
This is a one-way anonymous notification. The sender's identity is protected.
If the sender included contact information in their message, you can reach out to them directly.

Confuser - Privacy-Preserving AI Chat
"""

        # LinkedIn-style HTML email template
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f2ef;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f2ef; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 20px 40px; text-align: center;">
                            <span style="font-size: 24px; font-weight: bold; color: #0a66c2;">🛡️ Confuser</span>
                        </td>
                    </tr>

                    <!-- Main Card -->
                    <tr>
                        <td>
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 0 1px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.08);">
                                <!-- Notification Header -->
                                <tr>
                                    <td style="padding: 24px 24px 16px 24px;">
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td width="56" valign="top">
                                                    <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; text-align: center; line-height: 48px; font-size: 20px;">
                                                        💬
                                                    </div>
                                                </td>
                                                <td style="padding-left: 12px;">
                                                    <p style="margin: 0; font-size: 16px; font-weight: 600; color: #000000;">Someone wants to connect with you</p>
                                                    <p style="margin: 4px 0 0 0; font-size: 14px; color: #666666;">via Confuser Anonymous Relay</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>

                                <!-- Divider -->
                                <tr>
                                    <td style="padding: 0 24px;">
                                        <hr style="border: none; border-top: 1px solid #e8e8e8; margin: 0;">
                                    </td>
                                </tr>

                                <!-- Context Section -->
                                <tr>
                                    <td style="padding: 20px 24px;">
                                        <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; color: #666666; text-transform: uppercase; letter-spacing: 0.5px;">Regarding your question</p>
                                        <div style="background-color: #f8f9fa; border-left: 3px solid #0a66c2; padding: 12px 16px; border-radius: 0 8px 8px 0;">
                                            <p style="margin: 0; font-size: 14px; color: #333333; font-style: italic;">"{insight_context[:200]}{'...' if len(insight_context) > 200 else ''}"</p>
                                        </div>
                                    </td>
                                </tr>

                                <!-- Message Section -->
                                <tr>
                                    <td style="padding: 0 24px 24px 24px;">
                                        <p style="margin: 0 0 12px 0; font-size: 12px; font-weight: 600; color: #666666; text-transform: uppercase; letter-spacing: 0.5px;">Their Message</p>
                                        <div style="background-color: #ffffff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px;">
                                            <p style="margin: 0; font-size: 15px; color: #000000; line-height: 1.6; white-space: pre-wrap;">{body}</p>
                                        </div>
                                    </td>
                                </tr>

                                <!-- Notice Section -->
                                <tr>
                                    <td style="padding: 0 24px 24px 24px;">
                                        <div style="background-color: #fff8e6; border: 1px solid #ffc107; border-radius: 8px; padding: 12px 16px;">
                                            <p style="margin: 0; font-size: 13px; color: #856404;">
                                                <strong>📌 Note:</strong> This is a one-way anonymous notification. The sender's identity is protected.
                                                If they included contact information in their message, you can reach out to them directly.
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; text-align: center;">
                            <p style="margin: 0 0 8px 0; font-size: 12px; color: #666666;">
                                This email was sent by <strong>Confuser</strong> - Privacy-Preserving AI Chat
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #999999;">
                                🛡️ Your data, your control. We never share your email with other users.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        # Attach both plain text and HTML versions
        text_part = MIMEText(plain_text, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)

        # Connect to SMTP server (auto-detected based on email domain)
        print(f"   Connecting to {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
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
        # Escape quotes for JavaScript - must be done outside f-string
        escaped_question = insight['question'][:100].replace("'", "\\'")
        button_html = f"""
        <div style="margin-top: 8px;">
            <button class="insight-menu-btn" onclick="window.parent.postMessage({{type: 'openComposer', index: {index}, question: '{escaped_question}'}}, '*')">
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

        # One-way communication notice
        st.info(
            "💡 **Note:** This is a one-way anonymous notification. "
            "If you wish the recipient to contact you back, please leave a secure contact method "
            "(e.g., WeChat ID, Telegram, or a temporary email) in your message."
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
    st.title(f"🛡️ {get_app_name()}")

    # --- Language Switcher ---
    render_language_switcher(position='sidebar')

    st.divider()

    # --- User Info & Logout ---
    auth_ui.render_user_info()
    auth_ui.render_logout_button()

    st.divider()

    # --- New Chat Button ---
    if st.button(f"➕ {t('chat.new_chat')}", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()

    st.divider()

    # --- Chat History ---
    st.subheader(f"📜 {t('chat.chat_history')}")
    
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
        st.caption(t('chat.no_messages'))

    st.divider()

    # --- Settings ---
    with st.expander(f"⚙️ {t('nav.settings')}", expanded=False):
        api_key_input = st.text_input(
            t('sidebar.api_key'),
            type="password",
            help=t('sidebar.api_key_placeholder'),
            value=st.session_state.api_key or ""
        )

        if api_key_input:
            st.session_state.api_key = api_key_input
            st.success("✅ API Key set!")
        else:
            st.warning(f"⚠️ {t('errors.api_key_required')}")

        st.session_state.debug_mode = st.checkbox(
            f"🔍 {t('sidebar.debug_mode')}",
            value=st.session_state.debug_mode,
            help=t('sidebar.debug_mode')
        )
    
    st.divider()

    # --- Background Worker Status ---
    worker = st.session_state.get("decoy_worker")
    if worker and worker.is_running():
        st.subheader("🔄 Decoy Generation")
        status = worker.get_status()

        # Progress indicator
        decoys_generated = status.get("decoys_generated", 0)
        target_decoys = 3  # Default target
        progress = min(decoys_generated / target_decoys, 1.0) if target_decoys > 0 else 0

        st.progress(progress, text=f"Generated {decoys_generated}/{target_decoys} decoys")

        # Status text
        worker_status = status.get("status", "unknown")
        if worker_status == "running":
            st.caption("⏳ Background generation in progress...")
            # Show a refresh button and hint about auto-refresh
            if st.button("🔄 Refresh Status", use_container_width=True, key="refresh_worker_status"):
                st.rerun()
            st.caption("💡 Click refresh or switch tabs to check progress")
        elif worker_status == "completed":
            st.caption("✅ Generation complete!")
        elif worker_status == "failed":
            error_msg = status.get("error_message", "Unknown error")
            st.caption(f"❌ Failed: {error_msg}")

        # Stop button
        if st.button("🛑 Stop Generation", use_container_width=True):
            worker.stop()
            st.toast("Stopped background generation", icon="🛑")
            st.rerun()

        st.divider()
    elif worker:
        # Show last completed status briefly
        status = worker.get_status()
        worker_status = status.get("status", "idle")
        if worker_status == "completed":
            decoys_generated = status.get("decoys_generated", 0)
            st.success(f"✅ Last run: {decoys_generated} decoys generated")
            st.divider()
        elif worker_status == "failed":
            error_msg = status.get("error_message", "Unknown error")
            st.error(f"❌ Last run failed: {error_msg[:50]}...")
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

st.title(f"💬 {get_app_name()}")

if st.session_state.current_session_id:
    st.caption(f"Session: {st.session_state.current_session_id[:8]}...")
else:
    st.caption(t('chat.no_messages'))

st.markdown(f"*{t('app.description')}*")

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
if prompt := st.chat_input(t('chat.input_placeholder'), disabled=not st.session_state.api_key):

    if not st.session_state.api_key:
        st.error(f"⚠️ {t('errors.api_key_required')}")
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
                st.markdown(f"### 🧬 {t('peer_insights.title')}")
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

                    # Get Supabase credentials
                    supabase_url = st.secrets.get("SUPABASE_URL", "")
                    supabase_key = st.secrets.get("SUPABASE_KEY", "")

                    # Get current user ID for email relay
                    current_user_id = db.get_current_user_id()

                    if SYNC_DECOY_GENERATION:
                        # SYNCHRONOUS MODE: For debugging - blocks UI but guarantees saves
                        st.toast("🛡️ Generating privacy decoys...", icon="🔄")
                        try:
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
                        # BACKGROUND WORKER MODE: Non-blocking, survives tab switches
                        print(f"🔵 [APP] Using Background Worker mode...")

                        # Get or create worker for this session
                        worker = get_or_create_worker(
                            session_id=st.session_state.decoy_worker_session_id,
                            api_key=st.session_state.api_key,
                            supabase_url=supabase_url,
                            supabase_key=supabase_key
                        )

                        # Store worker reference in session state
                        st.session_state.decoy_worker = worker

                        # Start the background generation
                        task_id = worker.start(
                            original_query=prompt,
                            original_response=response,
                            owner_user_id=current_user_id,
                            source_id=current_source_id
                        )

                        st.session_state.worker_task_id = task_id
                        print(f"🚀 [APP] Background worker started (task_id: {task_id[:8]}...)")

                        st.toast("🛡️ Privacy decoys generating in background...", icon="🔄")

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
