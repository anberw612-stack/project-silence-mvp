"""
Internationalization (i18n) Module for Confuser / 城府AI

This module provides multi-language support with:
- Language detection from browser preferences
- Persistent language selection via cookies/localStorage
- Translation loading from JSON files
- Easy-to-use translation function

Supported languages:
- English (en) - Default
- Simplified Chinese (zh)
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import streamlit as st

# Try to import streamlit_js_eval for browser language detection
# Falls back to session state only if not available
try:
    from streamlit_js_eval import streamlit_js_eval
    HAS_JS_EVAL = True
except ImportError:
    HAS_JS_EVAL = False
    streamlit_js_eval = None

# Constants
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'zh': '简体中文'
}
DEFAULT_LANGUAGE = 'en'
LOCALES_DIR = Path(__file__).parent / 'locales'

# Cache for loaded translations
_translations_cache: Dict[str, Dict[str, Any]] = {}


def load_translations(lang: str) -> Dict[str, Any]:
    """
    Load translations from JSON file for the specified language.
    Uses caching to avoid repeated file reads.

    Args:
        lang: Language code ('en' or 'zh')

    Returns:
        Dictionary containing all translations for the language
    """
    if lang in _translations_cache:
        return _translations_cache[lang]

    # Fallback to default if language not supported
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    locale_file = LOCALES_DIR / f'{lang}.json'

    try:
        with open(locale_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translations_cache[lang] = translations
            return translations
    except FileNotFoundError:
        # Fallback to English if file not found
        if lang != DEFAULT_LANGUAGE:
            return load_translations(DEFAULT_LANGUAGE)
        return {}
    except json.JSONDecodeError:
        return {}


def detect_browser_language() -> str:
    """
    Detect user's preferred language from browser settings.
    Uses JavaScript to access navigator.language.

    Returns:
        Language code ('en' or 'zh')
    """
    if not HAS_JS_EVAL:
        return DEFAULT_LANGUAGE

    try:
        # Get browser language via JavaScript
        browser_lang = streamlit_js_eval(
            js_expressions='navigator.language || navigator.userLanguage',
            key='browser_lang_detect'
        )

        if browser_lang:
            # Extract primary language code (e.g., 'zh-CN' -> 'zh')
            primary_lang = browser_lang.split('-')[0].lower()

            if primary_lang in SUPPORTED_LANGUAGES:
                return primary_lang
    except Exception:
        pass

    return DEFAULT_LANGUAGE


def get_stored_language() -> Optional[str]:
    """
    Retrieve stored language preference from localStorage via JavaScript.

    Returns:
        Stored language code or None if not set
    """
    if not HAS_JS_EVAL:
        return None

    try:
        stored_lang = streamlit_js_eval(
            js_expressions='localStorage.getItem("confuser_language")',
            key='stored_lang_get'
        )
        if stored_lang and stored_lang in SUPPORTED_LANGUAGES:
            return stored_lang
    except Exception:
        pass
    return None


def set_stored_language(lang: str) -> None:
    """
    Store language preference in localStorage via JavaScript.

    Args:
        lang: Language code to store
    """
    if not HAS_JS_EVAL:
        return

    try:
        streamlit_js_eval(
            js_expressions=f'localStorage.setItem("confuser_language", "{lang}")',
            key=f'stored_lang_set_{lang}'
        )
    except Exception:
        pass


def init_language() -> str:
    """
    Initialize language setting for the session.
    Priority:
    1. Session state (already selected in this session)
    2. localStorage (previously saved preference)
    3. Browser language detection
    4. Default language (English)

    Returns:
        Selected language code
    """
    # Check session state first
    if 'language' in st.session_state and st.session_state.language:
        return st.session_state.language

    # Check localStorage
    stored_lang = get_stored_language()
    if stored_lang:
        st.session_state.language = stored_lang
        return stored_lang

    # Detect from browser
    detected_lang = detect_browser_language()
    st.session_state.language = detected_lang

    return detected_lang


def set_language(lang: str) -> None:
    """
    Set the current language and persist to localStorage.

    Args:
        lang: Language code to set
    """
    if lang in SUPPORTED_LANGUAGES:
        st.session_state.language = lang
        set_stored_language(lang)
        # Clear translation cache to force reload
        st.rerun()


def get_current_language() -> str:
    """
    Get the current language code.

    Returns:
        Current language code
    """
    return st.session_state.get('language', DEFAULT_LANGUAGE)


def t(key: str, **kwargs) -> str:
    """
    Translate a key to the current language.
    Supports nested keys with dot notation (e.g., 'auth.login').
    Supports string interpolation with keyword arguments.

    Args:
        key: Translation key (e.g., 'auth.login' or 'chat.input_placeholder')
        **kwargs: Variables for string interpolation

    Returns:
        Translated string, or the key itself if not found

    Example:
        t('auth.login')  # Returns 'Login' or '登录'
        t('sidebar.logged_in_as')  # Returns 'Logged in as' or '当前登录'
    """
    lang = get_current_language()
    translations = load_translations(lang)

    # Navigate nested keys
    keys = key.split('.')
    value = translations

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Key not found, return the key itself
            return key

    # Handle string interpolation
    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass

    return value if isinstance(value, str) else key


def render_language_switcher(position: str = 'sidebar', key_prefix: str = '') -> None:
    """
    Render a language switcher component.

    Args:
        position: Where to render ('sidebar' or 'main')
        key_prefix: Prefix for button keys to avoid duplicates
    """
    current_lang = get_current_language()

    # Use unique keys based on position
    selector_key = f'{key_prefix}language_selector' if key_prefix else f'{position}_lang_selector'

    # Inject CSS to make language pills same width
    st.markdown('''
        <style>
        /* Make language switcher pills same width */
        [data-testid="stPills"] > div > div > button {
            min-width: 72px !important;
            justify-content: center !important;
        }
        </style>
    ''', unsafe_allow_html=True)

    # Use pills/segmented control for clean non-editable selection
    # Using text labels without flags for cleaner look
    selected = st.pills(
        "Language",
        options=['en', 'zh'],
        format_func=lambda x: "English" if x == 'en' else "中文",
        default=current_lang,
        key=selector_key,
        label_visibility="collapsed"
    )

    if selected and selected != current_lang:
        set_language(selected)


def get_app_name() -> str:
    """
    Get the app name in the current language.
    Returns 'Confuser' for English, '城府AI' for Chinese.

    Returns:
        Localized app name
    """
    return t('app.name')


def get_font_family() -> str:
    """
    Get the appropriate font-family CSS for the current language.
    Ensures Chinese characters render correctly.

    Returns:
        CSS font-family string
    """
    lang = get_current_language()

    if lang == 'zh':
        # Chinese-optimized font stack
        return (
            "'PingFang SC', 'Microsoft YaHei', 'Hiragino Sans GB', "
            "'WenQuanYi Micro Hei', 'Noto Sans SC', sans-serif"
        )
    else:
        # English font stack
        return (
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
            "'Helvetica Neue', Arial, sans-serif"
        )


def inject_font_css() -> None:
    """
    Inject CSS for proper font rendering and the VAULT luxury theme.
    Should be called early in the app initialization.
    """
    font_family = get_font_family()
    lang = get_current_language()

    # Additional Chinese-specific styles
    chinese_styles = """
        /* Optimize Chinese character rendering */
        * {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* Ensure proper line height for Chinese */
        .stMarkdown, .stText, p, span, div {
            line-height: 1.8;
        }

        /* Better spacing for Chinese buttons */
        .stButton > button {
            letter-spacing: 0.05em;
        }
    """ if lang == 'zh' else ""

    # ═══════════════════════════════════════════════════════════════════════════════
    # VAULT THEME - Luxury Fintech & Cyber-Security Aesthetic
    # ═══════════════════════════════════════════════════════════════════════════════
    vault_theme = """
        /* ═══════════════════════════════════════════════════════════════════════════
           VAULT COLOR PALETTE
           ═══════════════════════════════════════════════════════════════════════════ */
        :root {
            --vault-obsidian: #0B0C10;
            --vault-midnight: #0F172A;
            --vault-charcoal: #1C1C1E;
            --vault-slate: #1E293B;
            --accent-teal: #14B8A6;
            --accent-teal-glow: #0D9488;
            --accent-teal-light: #2DD4BF;
            --accent-gold: #F59E0B;
            --neutral-100: #F4F4F5;
            --neutral-200: #E4E4E7;
            --neutral-300: #D4D4D8;
            --neutral-400: #A1A1AA;
            --neutral-500: #71717A;
            --neutral-600: #52525B;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           GOOGLE FONTS - Elegant Typography
           ═══════════════════════════════════════════════════════════════════════════ */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');

        /* ═══════════════════════════════════════════════════════════════════════════
           NOISE TEXTURE OVERLAY - Removes cheap digital look
           ═══════════════════════════════════════════════════════════════════════════ */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            opacity: 0.025;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
            background-repeat: repeat;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           GLOBAL STYLES - Base theme
           ═══════════════════════════════════════════════════════════════════════════ */
        html, body, .stApp {
            background-color: var(--vault-obsidian) !important;
            color: var(--neutral-200) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* Smooth scrolling */
        html {
            scroll-behavior: smooth;
        }

        /* Selection styling */
        ::selection {
            background-color: rgba(20, 184, 166, 0.3);
            color: white;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           AURORA GRADIENT BACKGROUND - Animated mesh
           ═══════════════════════════════════════════════════════════════════════════ */
        .stApp {
            background:
                radial-gradient(ellipse 80% 50% at 20% -20%, rgba(20, 184, 166, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at 80% -10%, rgba(245, 158, 11, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse 70% 50% at 50% 120%, rgba(20, 184, 166, 0.06) 0%, transparent 50%),
                linear-gradient(180deg, var(--vault-obsidian) 0%, var(--vault-midnight) 100%) !important;
            background-attachment: fixed !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           SIDEBAR - Glassmorphism effect
           ═══════════════════════════════════════════════════════════════════════════ */
        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.85) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        [data-testid="stSidebar"] > div:first-child {
            background: transparent !important;
            padding-top: 2rem !important;
        }

        /* Sidebar title */
        [data-testid="stSidebar"] h1 {
            font-family: 'Playfair Display', Georgia, serif !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
            background: linear-gradient(135deg, var(--neutral-100) 0%, var(--accent-teal-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           MAIN CONTENT AREA
           ═══════════════════════════════════════════════════════════════════════════ */
        .main .block-container {
            padding: 3rem 4rem !important;
            max-width: 1200px !important;
        }

        /* Main title - Elegant serif */
        .main h1 {
            font-family: 'Playfair Display', Georgia, serif !important;
            font-weight: 600 !important;
            font-size: 2.5rem !important;
            letter-spacing: -0.02em !important;
            margin-bottom: 0.5rem !important;
            background: linear-gradient(135deg, var(--neutral-100) 0%, var(--accent-teal-light) 50%, var(--neutral-100) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            background-size: 200% auto;
            animation: text-shimmer 4s ease-in-out infinite;
        }

        @keyframes text-shimmer {
            0%, 100% { background-position: 0% center; }
            50% { background-position: 200% center; }
        }

        /* Section headers */
        .main h2, .main h3 {
            font-family: 'Playfair Display', Georgia, serif !important;
            font-weight: 500 !important;
            color: var(--neutral-100) !important;
            letter-spacing: -0.01em !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           BUTTONS - Ghost & Primary styles
           ═══════════════════════════════════════════════════════════════════════════ */
        /* Ghost buttons (secondary) */
        .stButton > button {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: var(--neutral-200) !important;
            font-weight: 500 !important;
            padding: 0.6rem 1.2rem !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            backdrop-filter: blur(8px) !important;
        }

        .stButton > button:hover {
            background: rgba(20, 184, 166, 0.1) !important;
            border-color: rgba(20, 184, 166, 0.5) !important;
            color: var(--accent-teal-light) !important;
            box-shadow: 0 0 20px rgba(20, 184, 166, 0.2) !important;
            transform: translateY(-1px) !important;
        }

        /* Primary buttons */
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, var(--accent-teal) 0%, var(--accent-teal-light) 100%) !important;
            border: none !important;
            color: var(--vault-obsidian) !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(20, 184, 166, 0.3) !important;
        }

        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {
            box-shadow: 0 6px 25px rgba(20, 184, 166, 0.4) !important;
            transform: translateY(-2px) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           INPUT FIELDS - Glassmorphism
           ═══════════════════════════════════════════════════════════════════════════ */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div,
        .stMultiSelect > div > div {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
            color: var(--neutral-100) !important;
            backdrop-filter: blur(8px) !important;
            transition: all 0.3s ease !important;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--accent-teal) !important;
            box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15), 0 0 20px rgba(20, 184, 166, 0.1) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           CHAT INTERFACE - Premium messaging
           ═══════════════════════════════════════════════════════════════════════════ */
        /* Chat input */
        [data-testid="stChatInput"] {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(12px) !important;
        }

        [data-testid="stChatInput"] textarea {
            background: transparent !important;
            color: var(--neutral-100) !important;
        }

        /* Chat messages */
        [data-testid="stChatMessage"] {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 16px !important;
            padding: 1.25rem !important;
            margin-bottom: 1rem !important;
            backdrop-filter: blur(8px) !important;
        }

        /* User message */
        [data-testid="stChatMessage"][data-testid*="user"] {
            background: rgba(20, 184, 166, 0.08) !important;
            border-color: rgba(20, 184, 166, 0.15) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           EXPANDERS - Shield Card style
           ═══════════════════════════════════════════════════════════════════════════ */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            color: var(--neutral-200) !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }

        .streamlit-expanderHeader:hover {
            background: rgba(20, 184, 166, 0.05) !important;
            border-color: rgba(20, 184, 166, 0.3) !important;
            box-shadow: 0 0 15px rgba(20, 184, 166, 0.1) !important;
        }

        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.01) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-top: none !important;
            border-radius: 0 0 12px 12px !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           TABS - Modern segmented control
           ═══════════════════════════════════════════════════════════════════════════ */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255, 255, 255, 0.02) !important;
            border-radius: 10px !important;
            padding: 4px !important;
            gap: 4px !important;
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            border-radius: 8px !important;
            color: var(--neutral-400) !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: var(--neutral-200) !important;
            background: rgba(255, 255, 255, 0.05) !important;
        }

        .stTabs [aria-selected="true"] {
            background: rgba(20, 184, 166, 0.15) !important;
            color: var(--accent-teal-light) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           METRICS & STATS - Premium cards
           ═══════════════════════════════════════════════════════════════════════════ */
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            padding: 1.25rem !important;
        }

        [data-testid="stMetricValue"] {
            font-family: 'Playfair Display', Georgia, serif !important;
            color: var(--accent-teal-light) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           DIVIDERS - Subtle elegance
           ═══════════════════════════════════════════════════════════════════════════ */
        hr {
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent) !important;
            margin: 1.5rem 0 !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           ALERTS & MESSAGES
           ═══════════════════════════════════════════════════════════════════════════ */
        .stAlert {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 10px !important;
            backdrop-filter: blur(8px) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           PROGRESS BARS - Teal glow
           ═══════════════════════════════════════════════════════════════════════════ */
        .stProgress > div > div {
            background: linear-gradient(90deg, var(--accent-teal) 0%, var(--accent-teal-light) 100%) !important;
            box-shadow: 0 0 10px rgba(20, 184, 166, 0.5) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           SPINNERS - Teal accent
           ═══════════════════════════════════════════════════════════════════════════ */
        .stSpinner > div > div {
            border-top-color: var(--accent-teal) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           CAPTIONS & SMALL TEXT
           ═══════════════════════════════════════════════════════════════════════════ */
        .stCaption, small, .st-emotion-cache-1inwz65 {
            color: var(--neutral-500) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           SCROLLBAR - Thin & elegant
           ═══════════════════════════════════════════════════════════════════════════ */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(20, 184, 166, 0.3);
            border-radius: 3px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(20, 184, 166, 0.5);
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           PILLS / LANGUAGE SWITCHER
           ═══════════════════════════════════════════════════════════════════════════ */
        [data-testid="stPills"] button {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: var(--neutral-400) !important;
            transition: all 0.3s ease !important;
        }

        [data-testid="stPills"] button:hover {
            background: rgba(20, 184, 166, 0.1) !important;
            border-color: rgba(20, 184, 166, 0.3) !important;
        }

        [data-testid="stPills"] button[aria-pressed="true"] {
            background: rgba(20, 184, 166, 0.15) !important;
            border-color: var(--accent-teal) !important;
            color: var(--accent-teal-light) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           FORMS - Premium styling
           ═══════════════════════════════════════════════════════════════════════════ */
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            padding: 2rem !important;
            backdrop-filter: blur(12px) !important;
        }

        /* Hide the "Press Enter to submit form" hint - cleaner look */
        [data-testid="stForm"] [data-testid="InputInstructions"] {
            display: none !important;
        }

        /* Alternative: If you want to keep it but position correctly */
        [data-testid="InputInstructions"] {
            position: static !important;
            margin-top: 4px !important;
            text-align: right !important;
            font-size: 0.75rem !important;
            color: var(--neutral-500) !important;
            opacity: 0.7 !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           DIALOG / MODAL - Glassmorphism
           ═══════════════════════════════════════════════════════════════════════════ */
        [data-testid="stModal"] > div {
            background: rgba(15, 23, 42, 0.95) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 20px !important;
            backdrop-filter: blur(20px) !important;
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           TOAST NOTIFICATIONS
           ═══════════════════════════════════════════════════════════════════════════ */
        [data-testid="stToast"] {
            background: rgba(15, 23, 42, 0.95) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(12px) !important;
        }
    """

    css = f"""
    <style>
        {vault_theme}

        /* Global font family override */
        html, body, [class*="css"] {{
            font-family: {font_family};
        }}

        {chinese_styles}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)


# Convenience function for getting translations with fallback
def _(key: str, **kwargs) -> str:
    """
    Alias for t() function for shorter syntax.
    Common convention in i18n libraries.

    Example:
        _('auth.login')  # Same as t('auth.login')
    """
    return t(key, **kwargs)
