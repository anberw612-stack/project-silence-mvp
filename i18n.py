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

    # Use pills/segmented control for clean non-editable selection
    selected = st.pills(
        "Language",
        options=['en', 'zh'],
        format_func=lambda x: "EN 🇺🇸" if x == 'en' else "中文 🇨🇳",
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
    Inject CSS for proper font rendering based on current language.
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

    css = f"""
    <style>
        /* Global font family */
        html, body, [class*="css"] {{
            font-family: {font_family};
        }}

        /* Streamlit specific overrides */
        .stApp {{
            font-family: {font_family};
        }}

        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {{
            font-family: {font_family};
        }}

        /* Chat messages */
        .stChatMessage {{
            font-family: {font_family};
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
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
