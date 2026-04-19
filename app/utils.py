# app/utils.py
"""Shared UI: top navbar, CSS theme, navigation helpers."""

import streamlit as st

# ── Color palette: deep black + bloody red ───────────────────────────────────
ACCENT       = "#dc2626"
ACCENT_LIGHT = "#ef4444"
ACCENT_DIM   = "#7f1d1d"
BG_DARK      = "#030305"
BG_CARD      = "#0a0a0f"
BG_CARD_ALT  = "#111118"
TEXT_PRIMARY  = "#f5f5f5"
TEXT_MUTED    = "#737380"
BORDER        = "rgba(220, 38, 38, 0.12)"

NAV_PAGES = ["Home", "Upload", "Preprocess", "Analysis", "Results"]


def inject_custom_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    .stApp {{
        font-family: 'Inter', sans-serif;
        background: {BG_DARK};
    }}

    /* ── Hide default sidebar completely ───────────────────── */
    [data-testid="stSidebar"] {{
        display: none !important;
    }}
    [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}
    .stApp > header {{
        display: none !important;
    }}

    /* ── Top navbar ────────────────────────────────────────── */
    .navbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.7rem 1.5rem;
        background: rgba(3,3,5,0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255,255,255,0.04);
        margin: -1rem -1rem 1.5rem -1rem;
        position: sticky;
        top: 0;
        z-index: 999;
    }}
    .nav-brand {{
        font-size: 1.1rem;
        font-weight: 800;
        color: {TEXT_PRIMARY};
        letter-spacing: -0.03em;
        white-space: nowrap;
    }}
    .nav-brand span {{
        color: {ACCENT};
    }}
    .nav-links {{
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }}
    .nav-link,
    .nav-link:visited,
    .nav-link:active {{
        padding: 0.4rem 1rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        color: {TEXT_MUTED} !important;
        text-decoration: none !important;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid transparent;
    }}
    .nav-link:hover {{
        color: {TEXT_PRIMARY};
        background: rgba(255,255,255,0.03);
    }}
    .nav-link.active {{
        color: {TEXT_PRIMARY};
        background: rgba(220,38,38,0.08);
        border-color: rgba(220,38,38,0.2);
    }}
    .nav-status {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }}
    .nav-dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }}
    .nav-dot.done {{
        background: {ACCENT};
        box-shadow: 0 0 6px rgba(220,38,38,0.4);
    }}
    .nav-dot.pending {{
        background: #27272a;
    }}

    /* ── Hero ──────────────────────────────────────────────── */
    .hero {{
        position: relative;
        overflow: hidden;
        border-radius: 20px;
        padding: 5rem 2rem 4rem;
        text-align: center;
        margin-bottom: 3rem;
        background: radial-gradient(ellipse at 50% -20%, rgba(220,38,38,0.12) 0%, transparent 70%),
                    linear-gradient(180deg, #06060a 0%, {BG_DARK} 100%);
        border: 1px solid rgba(220,38,38,0.06);
    }}
    .hero::before {{
        content: '';
        position: absolute;
        top: 0; left: 50%; transform: translateX(-50%);
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(220,38,38,0.08) 0%, transparent 70%);
        pointer-events: none;
    }}
    .hero::after {{
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 10%, {ACCENT} 50%, transparent 90%);
        opacity: 0.25;
    }}
    .hero-tag {{
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        color: {ACCENT};
        text-transform: uppercase;
        letter-spacing: 0.15em;
        padding: 0.3rem 0.8rem;
        border: 1px solid rgba(220,38,38,0.2);
        border-radius: 20px;
        margin-bottom: 1.5rem;
        background: rgba(220,38,38,0.05);
    }}
    .hero-title {{
        font-size: 3.2rem;
        font-weight: 900;
        color: {TEXT_PRIMARY};
        letter-spacing: -0.045em;
        line-height: 1.05;
        margin-bottom: 1.2rem;
    }}
    .hero-title span {{
        background: linear-gradient(135deg, {ACCENT} 0%, #f87171 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .hero-sub {{
        font-size: 1.05rem;
        color: {TEXT_MUTED};
        max-width: 480px;
        margin: 0 auto;
        line-height: 1.65;
    }}

    /* ── Cards ─────────────────────────────────────────────── */
    .card {{
        background: {BG_CARD};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 14px;
        padding: 1.6rem;
        height: 100%;
        transition: border-color 0.3s, transform 0.3s, box-shadow 0.3s;
    }}
    .card:hover {{
        border-color: rgba(220,38,38,0.2);
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    }}
    .card-label {{
        font-size: 0.65rem;
        font-weight: 700;
        color: {ACCENT};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.6rem;
    }}
    .card-heading {{
        font-size: 1.05rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.35rem;
    }}
    .card-body {{
        font-size: 0.8rem;
        color: {TEXT_MUTED};
        line-height: 1.55;
    }}

    /* ── Step cards (landing page) ─────────────────────────── */
    .step-row {{
        display: flex;
        align-items: stretch;
        gap: 1.5rem;
        margin-bottom: 2rem;
    }}
    .step-card {{
        flex: 1;
        background: {BG_CARD};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 14px;
        padding: 2rem 1.5rem;
        text-align: center;
        transition: border-color 0.3s, transform 0.3s;
        position: relative;
    }}
    .step-card:hover {{
        border-color: rgba(220,38,38,0.2);
        transform: translateY(-3px);
    }}
    .step-number {{
        font-size: 2.5rem;
        font-weight: 900;
        color: rgba(220,38,38,0.12);
        line-height: 1;
        margin-bottom: 0.5rem;
    }}
    .step-title {{
        font-size: 1rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.3rem;
    }}
    .step-desc {{
        font-size: 0.8rem;
        color: {TEXT_MUTED};
        line-height: 1.5;
    }}
    .step-connector {{
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 30px;
        color: rgba(220,38,38,0.15);
        font-size: 1.2rem;
    }}

    /* ── Metric ────────────────────────────────────────────── */
    .metric {{
        background: {BG_CARD};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }}
    .metric-val {{
        font-size: 1.6rem;
        font-weight: 800;
        color: {ACCENT};
        line-height: 1.2;
    }}
    .metric-label {{
        font-size: 0.7rem;
        color: {TEXT_MUTED};
        margin-top: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* ── Pipeline tracker (sub-pages) ─────────────────────── */
    .pipeline {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin: 1rem 0 1.5rem;
        flex-wrap: wrap;
    }}
    .pipe-step {{
        background: {BG_CARD};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        text-align: center;
        min-width: 100px;
        transition: all 0.2s;
    }}
    .pipe-step.done {{
        border-color: {ACCENT};
        background: rgba(220,38,38,0.06);
    }}
    .pipe-step.active {{
        border-color: #f59e0b;
        background: rgba(245,158,11,0.06);
    }}
    .pipe-num {{
        font-size: 0.55rem;
        font-weight: 700;
        color: {ACCENT};
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}
    .pipe-step.active .pipe-num {{
        color: #f59e0b;
    }}
    .pipe-name {{
        font-size: 0.78rem;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}
    .pipe-arrow {{
        color: rgba(255,255,255,0.06);
        font-size: 0.9rem;
        padding: 0 0.4rem;
    }}

    /* ── Section ───────────────────────────────────────────── */
    .section-title {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin: 2.5rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.03);
    }}

    /* ── Status ────────────────────────────────────────────── */
    .status-done {{ color: {ACCENT}; }}
    .status-active {{ color: #f59e0b; }}
    .status-pending {{ color: #27272a; }}

    /* ── Buttons ───────────────────────────────────────────── */
    .stButton > button {{
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.01em;
        padding: 0.55rem 1.5rem;
        transition: all 0.25s ease;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {ACCENT} 0%, #b91c1c 100%);
        border: none;
        box-shadow: 0 0 20px rgba(220,38,38,0.12);
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 4px 35px rgba(220,38,38,0.3);
        transform: translateY(-2px);
    }}
    .stButton > button[kind="secondary"] {{
        background: transparent;
        border: 1px solid rgba(255,255,255,0.06);
        color: {TEXT_MUTED};
    }}
    .stButton > button[kind="secondary"]:hover {{
        border-color: rgba(220,38,38,0.25);
        color: {TEXT_PRIMARY};
    }}

    /* ── Tabs ──────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.25rem;
        background: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0;
        font-weight: 500;
        font-size: 0.85rem;
    }}
    .stTabs [aria-selected="true"] {{
        border-bottom-color: {ACCENT} !important;
    }}

    hr {{
        border-color: rgba(255,255,255,0.03) !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_navbar():
    """Render the single top navigation bar with clickable styled links."""
    current = st.session_state.get("page", "Home")

    # Sync page from URL query parameter when links are clicked.
    q_page = st.query_params.get("page", current)
    if isinstance(q_page, list):
        q_page = q_page[0] if q_page else current
    if q_page in NAV_PAGES and q_page != current:
        st.session_state.page = q_page
        current = q_page

    has_upload = st.session_state.get("uploaded_video") is not None
    has_preprocess = st.session_state.get("processed_video") is not None
    has_analysis = st.session_state.get("analysis_done", False)

    # Status dots
    dots = [
        ("Upload", has_upload),
        ("Process", has_preprocess),
        ("Analysis", has_analysis),
    ]
    dots_html = ""
    for label, done in dots:
        dot_cls = "nav-dot done" if done else "nav-dot pending"
        dots_html += f'<span class="{dot_cls}" title="{label}"></span>'

    links_html = ""
    for name in NAV_PAGES:
        cls = "nav-link active" if current == name else "nav-link"
        links_html += (
            f'<a class="{cls}" href="?page={name}" target="_self" rel="noopener">'
            f'{name}</a>'
        )

    st.markdown(f"""
    <div class="navbar">
        <div class="nav-brand">Football<span>Tracker</span></div>
        <div class="nav-links">{links_html}</div>
        <div class="nav-status">{dots_html}</div>
    </div>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.6rem; font-weight: 800; color: {TEXT_PRIMARY};
                   margin-bottom: 0.15rem; letter-spacing: -0.03em;">{title}</h1>
        <p style="font-size: 0.85rem; color: {TEXT_MUTED};">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str) -> str:
    return f"""
    <div class="metric">
        <div class="metric-val">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def render_pipeline(active: int = -1, done_up_to: int = -1):
    steps = ["Upload", "Preprocess", "Analysis", "Results"]
    html = '<div class="pipeline">'
    for i, name in enumerate(steps):
        if i <= done_up_to:
            cls = "pipe-step done"
        elif i == active:
            cls = "pipe-step active"
        else:
            cls = "pipe-step"
        html += f'''
        <div class="{cls}">
            <div class="pipe-num">Step {i + 1}</div>
            <div class="pipe-name">{name}</div>
        </div>'''
        if i < len(steps) - 1:
            html += '<div class="pipe-arrow">&#8594;</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def nav_button(label: str, target: str, key: str | None = None):
    if st.button(label, use_container_width=True, type="primary", key=key):
        st.session_state.page = target
        st.query_params["page"] = target
        st.rerun()


# Keep for backwards compat — no longer renders sidebar content
def setup_sidebar():
    pass
