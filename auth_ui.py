"""
Authentication UI Module

Handles user authentication (Login/Register) using Supabase Auth.
Provides login/register forms and session management.
With multi-language support (English / 简体中文).
"""

import streamlit as st
from database_manager import get_supabase_client, create_or_get_profile
from i18n import t, init_language, get_app_name, inject_font_css, render_language_switcher


def init_auth_state():
    """
    Initialize authentication-related session state variables.
    """
    if "user" not in st.session_state:
        st.session_state.user = None
    
    if "auth_error" not in st.session_state:
        st.session_state.auth_error = None
    
    if "auth_success" not in st.session_state:
        st.session_state.auth_success = None


def is_logged_in() -> bool:
    """
    Check if a user is currently logged in.
    
    Returns:
        bool: True if user is logged in, False otherwise
    """
    return st.session_state.get("user") is not None


def get_current_user():
    """
    Get the current logged-in user.
    
    Returns:
        User object or None
    """
    return st.session_state.get("user")


def sign_up(email: str, password: str) -> bool:
    """
    Register a new user with email and password.
    
    Args:
        email (str): User's email
        password (str): User's password
        
    Returns:
        bool: True if signup successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            st.session_state.user = response.user
            st.session_state.auth_error = None
            st.session_state.auth_success = "Account created successfully! Please check your email to confirm."
            
            # Create user profile
            create_or_get_profile(response.user.id, email)
            
            return True
        else:
            st.session_state.auth_error = "Signup failed. Please try again."
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            st.session_state.auth_error = "This email is already registered. Please login instead."
        elif "password" in error_msg.lower():
            st.session_state.auth_error = "Password must be at least 6 characters."
        else:
            st.session_state.auth_error = f"Signup error: {error_msg}"
        return False


def sign_in(email: str, password: str) -> bool:
    """
    Sign in an existing user with email and password.
    
    Args:
        email (str): User's email
        password (str): User's password
        
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            st.session_state.user = response.user
            st.session_state.auth_error = None
            st.session_state.auth_success = f"Welcome back, {email}!"
            
            # Ensure profile exists
            create_or_get_profile(response.user.id, email)
            
            return True
        else:
            st.session_state.auth_error = "Login failed. Please check your credentials."
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            st.session_state.auth_error = "Invalid email or password."
        elif "not confirmed" in error_msg.lower():
            st.session_state.auth_error = "Please confirm your email before logging in."
        else:
            st.session_state.auth_error = f"Login error: {error_msg}"
        return False


def sign_out():
    """
    Sign out the current user.
    """
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        
        # Clear session state
        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.current_session_id = None
        st.session_state.auth_error = None
        st.session_state.auth_success = "Logged out successfully."
        
    except Exception as e:
        print(f"Logout error: {e}")
        # Still clear local state even if API call fails
        st.session_state.user = None


def render_auth_page():
    """
    Render the login/register page.
    This should be called when the user is NOT logged in.
    """
    # Initialize language for auth page
    init_language()

    st.set_page_config(
        page_title=f"{get_app_name()} - {t('auth.login')}",
        page_icon="🛡️",
        layout="centered"
    )

    # Inject font CSS for proper character rendering
    inject_font_css()

    # Language switcher at top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        render_language_switcher(position='sidebar')

    st.title(f"🛡️ {get_app_name()}")
    st.markdown(f"*{t('app.description')}*")

    st.divider()

    # Display any auth messages
    if st.session_state.get("auth_error"):
        st.error(st.session_state.auth_error)
        st.session_state.auth_error = None

    if st.session_state.get("auth_success"):
        st.success(st.session_state.auth_success)
        st.session_state.auth_success = None

    # Tab selection for Login/Register
    tab1, tab2 = st.tabs([f"🔐 {t('auth.login')}", f"📝 {t('auth.register')}"])

    with tab1:
        render_login_form()

    with tab2:
        render_register_form()

    st.divider()
    st.caption(f"🛡️ {t('app.description')}")


def render_login_form():
    """
    Render the login form.
    """
    with st.form("login_form", clear_on_submit=False):
        st.subheader(t('auth.welcome_back'))

        email = st.text_input(
            t('auth.email'),
            placeholder="your@email.com",
            key="login_email"
        )

        password = st.text_input(
            t('auth.password'),
            type="password",
            placeholder="••••••••",
            key="login_password"
        )

        submit = st.form_submit_button(t('auth.login_button'), use_container_width=True, type="primary")

        if submit:
            if not email or not password:
                st.error(t('auth.login_error'))
            else:
                with st.spinner(t('auth.logging_in')):
                    if sign_in(email, password):
                        st.rerun()


def render_register_form():
    """
    Render the registration form.
    """
    with st.form("register_form", clear_on_submit=False):
        st.subheader(t('auth.create_account'))

        email = st.text_input(
            t('auth.email'),
            placeholder="your@email.com",
            key="register_email"
        )

        password = st.text_input(
            t('auth.password'),
            type="password",
            placeholder="••••••••",
            key="register_password"
        )

        password_confirm = st.text_input(
            t('auth.confirm_password'),
            type="password",
            placeholder="••••••••",
            key="register_password_confirm"
        )

        submit = st.form_submit_button(t('auth.register_button'), use_container_width=True, type="primary")

        if submit:
            if not email or not password:
                st.error(t('auth.register_error'))
            elif password != password_confirm:
                st.error(t('auth.password_mismatch'))
            elif len(password) < 6:
                st.error(t('auth.register_error'))
            else:
                with st.spinner(t('auth.registering')):
                    if sign_up(email, password):
                        st.rerun()


def render_logout_button():
    """
    Render a logout button (to be placed in sidebar).
    """
    if st.button(f"🚪 {t('nav.logout')}", use_container_width=True):
        sign_out()
        st.rerun()


def render_user_info():
    """
    Render current user info (to be placed in sidebar).
    """
    user = get_current_user()
    if user:
        st.caption(f"👤 {t('sidebar.logged_in_as')}: {user.email}")

