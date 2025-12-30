"""
Elegant SVG Icon System for Confuser

Provides inline SVG icons styled to match the Vault luxury theme.
Uses Lucide-style icons (thin strokes, minimal aesthetic).

All icons return HTML strings that can be used with st.markdown(unsafe_allow_html=True)
"""

# ═══════════════════════════════════════════════════════════════════════════════
# ICON CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Default icon style - thin strokes, teal accent
ICON_STYLE = {
    'size': 20,
    'stroke_width': 1.5,
    'color': '#14B8A6',  # accent-teal
    'color_muted': '#71717A',  # neutral-500
    'color_light': '#E4E4E7',  # neutral-200
}


def _svg(paths: str, size: int = None, color: str = None, stroke_width: float = None,
         viewbox: str = "0 0 24 24", filled: bool = False, no_margin: bool = False) -> str:
    """
    Generate an inline SVG icon.

    Args:
        paths: SVG path data
        size: Icon size in pixels
        color: Stroke/fill color
        stroke_width: Stroke width
        viewbox: SVG viewBox
        filled: Whether to use fill instead of stroke
        no_margin: If True, removes default right margin (for centered icons)
    """
    s = size or ICON_STYLE['size']
    c = color or ICON_STYLE['color']
    sw = stroke_width or ICON_STYLE['stroke_width']

    fill_attr = f'fill="{c}"' if filled else 'fill="none"'
    stroke_attr = '' if filled else f'stroke="{c}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
    margin = '' if no_margin else 'margin-right:8px;'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="{viewbox}" {fill_attr} {stroke_attr} style="display:inline-block;vertical-align:middle;flex-shrink:0;{margin}">{paths}</svg>'''


# ═══════════════════════════════════════════════════════════════════════════════
# BRAND / MAIN ICONS
# ═══════════════════════════════════════════════════════════════════════════════

def shield(size: int = 24, color: str = None, no_margin: bool = False) -> str:
    """Shield icon - brand symbol for protection/security"""
    return _svg(
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        size=size, color=color or ICON_STYLE['color'], no_margin=no_margin
    )


def shield_check(size: int = 24, color: str = None) -> str:
    """Shield with checkmark - verified protection"""
    return _svg(
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
        '<path d="m9 12 2 2 4-4"/>',
        size=size, color=color or ICON_STYLE['color']
    )


def lock(size: int = 20, color: str = None) -> str:
    """Lock icon - security/privacy"""
    return _svg(
        '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>'
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
        size=size, color=color or ICON_STYLE['color']
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NAVIGATION / UI ICONS
# ═══════════════════════════════════════════════════════════════════════════════

def message_square(size: int = 20, color: str = None, no_margin: bool = False) -> str:
    """Chat/message icon"""
    return _svg(
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        size=size, color=color or ICON_STYLE['color_light'], no_margin=no_margin
    )


def plus(size: int = 20, color: str = None) -> str:
    """Plus/add icon"""
    return _svg(
        '<path d="M5 12h14"/><path d="M12 5v14"/>',
        size=size, color=color or ICON_STYLE['color']
    )


def plus_circle(size: int = 20, color: str = None) -> str:
    """Plus in circle - new item"""
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M8 12h8"/><path d="M12 8v8"/>',
        size=size, color=color or ICON_STYLE['color']
    )


def history(size: int = 20, color: str = None) -> str:
    """History/clock icon"""
    return _svg(
        '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>'
        '<path d="M3 3v5h5"/>'
        '<path d="M12 7v5l4 2"/>',
        size=size, color=color or ICON_STYLE['color_light']
    )


def scroll(size: int = 20, color: str = None) -> str:
    """Scroll/document icon - for history"""
    return _svg(
        '<path d="M8 21h12a2 2 0 0 0 2-2v-2H10v2a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v3h4"/>'
        '<path d="M19 17V5a2 2 0 0 0-2-2H4"/>',
        size=size, color=color or ICON_STYLE['color_light']
    )


def trash(size: int = 18, color: str = None) -> str:
    """Trash/delete icon"""
    return _svg(
        '<path d="M3 6h18"/>'
        '<path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>'
        '<path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>'
        '<line x1="10" x2="10" y1="11" y2="17"/>'
        '<line x1="14" x2="14" y1="11" y2="17"/>',
        size=size, color=color or ICON_STYLE['color_muted']
    )


def settings(size: int = 20, color: str = None) -> str:
    """Settings/gear icon"""
    return _svg(
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
        size=size, color=color or ICON_STYLE['color_light']
    )


def log_out(size: int = 20, color: str = None) -> str:
    """Logout/exit icon"""
    return _svg(
        '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
        '<polyline points="16 17 21 12 16 7"/>'
        '<line x1="21" x2="9" y1="12" y2="12"/>',
        size=size, color=color or ICON_STYLE['color_muted']
    )


def user(size: int = 20, color: str = None) -> str:
    """User/profile icon"""
    return _svg(
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>',
        size=size, color=color or ICON_STYLE['color_muted']
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS / FEEDBACK ICONS
# ═══════════════════════════════════════════════════════════════════════════════

def check(size: int = 20, color: str = None) -> str:
    """Checkmark - success"""
    return _svg(
        '<polyline points="20 6 9 17 4 12"/>',
        size=size, color=color or '#14B8A6'
    )


def check_circle(size: int = 20, color: str = None) -> str:
    """Checkmark in circle - verified"""
    return _svg(
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/>',
        size=size, color=color or '#14B8A6'
    )


def x_circle(size: int = 20, color: str = None) -> str:
    """X in circle - error/failed"""
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
        size=size, color=color or '#EF4444'
    )


def alert_triangle(size: int = 20, color: str = None) -> str:
    """Warning triangle"""
    return _svg(
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<path d="M12 9v4"/><path d="M12 17h.01"/>',
        size=size, color=color or '#F59E0B'
    )


def loader(size: int = 20, color: str = None) -> str:
    """Loading spinner"""
    return _svg(
        '<path d="M21 12a9 9 0 1 1-6.219-8.56"/>',
        size=size, color=color or ICON_STYLE['color']
    )


def refresh(size: int = 20, color: str = None) -> str:
    """Refresh/reload icon"""
    return _svg(
        '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>'
        '<path d="M21 3v5h-5"/>'
        '<path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>'
        '<path d="M3 21v-5h5"/>',
        size=size, color=color or ICON_STYLE['color']
    )


def stop_circle(size: int = 20, color: str = None) -> str:
    """Stop icon"""
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<rect width="6" height="6" x="9" y="9"/>',
        size=size, color=color or '#EF4444'
    )


# ═══════════════════════════════════════════════════════════════════════════════
# INSIGHT / FEATURE ICONS
# ═══════════════════════════════════════════════════════════════════════════════

def target(size: int = 20, color: str = None) -> str:
    """Target/precision icon"""
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<circle cx="12" cy="12" r="6"/>'
        '<circle cx="12" cy="12" r="2"/>',
        size=size, color=color or ICON_STYLE['color']
    )


def lightbulb(size: int = 20, color: str = None) -> str:
    """Lightbulb/idea icon - resonance"""
    return _svg(
        '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>'
        '<path d="M9 18h6"/>'
        '<path d="M10 22h4"/>',
        size=size, color=color or '#F59E0B'
    )


def gift(size: int = 20, color: str = None) -> str:
    """Gift/surprise icon - serendipity"""
    return _svg(
        '<polyline points="20 12 20 22 4 22 4 12"/>'
        '<rect width="20" height="5" x="2" y="7"/>'
        '<line x1="12" x2="12" y1="22" y2="7"/>'
        '<path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/>'
        '<path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>',
        size=size, color=color or '#A855F7'
    )


def sparkles(size: int = 20, color: str = None) -> str:
    """Sparkles/magic icon"""
    return _svg(
        '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>'
        '<path d="M5 3v4"/><path d="M19 17v4"/>'
        '<path d="M3 5h4"/><path d="M17 19h4"/>',
        size=size, color=color or ICON_STYLE['color']
    )


def bar_chart(size: int = 20, color: str = None) -> str:
    """Stats/analytics icon"""
    return _svg(
        '<line x1="12" x2="12" y1="20" y2="10"/>'
        '<line x1="18" x2="18" y1="20" y2="4"/>'
        '<line x1="6" x2="6" y1="20" y2="16"/>',
        size=size, color=color or ICON_STYLE['color_light']
    )


def search(size: int = 20, color: str = None) -> str:
    """Search/debug icon"""
    return _svg(
        '<circle cx="11" cy="11" r="8"/>'
        '<path d="m21 21-4.3-4.3"/>',
        size=size, color=color or ICON_STYLE['color_muted']
    )


def play(size: int = 16, color: str = None) -> str:
    """Play/active icon"""
    return _svg(
        '<polygon points="5 3 19 12 5 21 5 3"/>',
        size=size, color=color or ICON_STYLE['color'], filled=True
    )


def chevron_right(size: int = 16, color: str = None) -> str:
    """Chevron right - navigation"""
    return _svg(
        '<path d="m9 18 6-6-6-6"/>',
        size=size, color=color or ICON_STYLE['color_muted']
    )


def more_horizontal(size: int = 20, color: str = None, no_margin: bool = False) -> str:
    """More options (three dots)"""
    return _svg(
        '<circle cx="12" cy="12" r="1"/>'
        '<circle cx="19" cy="12" r="1"/>'
        '<circle cx="5" cy="12" r="1"/>',
        size=size, color=color or ICON_STYLE['color_muted'], filled=True, no_margin=no_margin
    )


def pin(size: int = 20, color: str = None, no_margin: bool = False) -> str:
    """Pin/sticky icon"""
    return _svg(
        '<path d="M12 17v5"/>'
        '<path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/>',
        size=size, color=color or ICON_STYLE['color_muted'], no_margin=no_margin
    )


def mail(size: int = 20, color: str = None) -> str:
    """Email/message icon"""
    return _svg(
        '<rect width="20" height="16" x="2" y="4" rx="2"/>'
        '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
        size=size, color=color or ICON_STYLE['color']
    )


def key(size: int = 20, color: str = None) -> str:
    """API key icon"""
    return _svg(
        '<circle cx="7.5" cy="15.5" r="5.5"/>'
        '<path d="m21 2-9.6 9.6"/>'
        '<path d="m15.5 7.5 3 3L22 7l-3-3"/>',
        size=size, color=color or ICON_STYLE['color']
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def icon_text(icon_html: str, text: str, gap: int = 8) -> str:
    """
    Combine an icon with text in a styled span.

    Args:
        icon_html: The SVG icon HTML
        text: Text to display after the icon
        gap: Gap between icon and text in pixels
    """
    return f'''<span style="display:inline-flex;align-items:center;gap:{gap}px;">{icon_html}<span>{text}</span></span>'''


def brand_logo(size: int = 32) -> str:
    """
    Generate the Confuser brand logo - a shield with a modern design.
    """
    return f'''
    <div style="display:inline-flex;align-items:center;gap:12px;">
        <div style="
            width:{size}px;
            height:{size}px;
            background:linear-gradient(135deg, rgba(20,184,166,0.2) 0%, rgba(20,184,166,0.05) 100%);
            border:1px solid rgba(20,184,166,0.3);
            border-radius:8px;
            display:flex;
            align-items:center;
            justify-content:center;
        ">
            {shield(size=int(size*0.6), color='#14B8A6')}
        </div>
    </div>
    '''
