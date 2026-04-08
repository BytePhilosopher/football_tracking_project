# app/utils.py
"""Shared UI: navbar, CSS theme, navigation helpers."""

import streamlit as st
import streamlit.components.v1 as components

# ── Color palette ─────────────────────────────────────────────────────────────
ACCENT       = "#dc2626"
ACCENT_LIGHT = "#ef4444"
ACCENT_DIM   = "#7f1d1d"
BG_DARK      = "#030305"
BG_CARD      = "#0d0d12"
BG_CARD_ALT  = "#111118"
TEXT_PRIMARY  = "#f5f5f5"
TEXT_MUTED    = "#6b6b78"
BORDER        = "rgba(220, 38, 38, 0.12)"

NAV_PAGES = ["Home", "Upload", "Preprocess", "Analysis", "Results"]


def inject_custom_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    *, *::before, *::after {{ box-sizing: border-box; }}

    .stApp {{
        font-family: 'Inter', sans-serif !important;
        background: {BG_DARK} !important;
        color: {TEXT_PRIMARY};
    }}

    /* ── Hide all default Streamlit chrome ───────────────────── */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    .stApp > header,
    #MainMenu,
    footer,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {{
        display: none !important;
    }}

    /* ── Main content area ───────────────────────────────────── */
    .block-container {{
        padding-top: 0 !important;
        padding-bottom: 3rem !important;
        max-width: 1200px;
    }}

    /* ── Navbar iframe sits flush at top ─────────────────────── */
    iframe[title="st_navbar"] {{
        display: block;
        margin: 0 -4rem 2rem -4rem !important;
        width: calc(100% + 8rem) !important;
        border: none;
        overflow: hidden;
    }}

    /* ── Hero ─────────────────────────────────────────────────── */
    .hero {{
        position: relative;
        overflow: hidden;
        border-radius: 20px;
        padding: 5.5rem 2rem 4.5rem;
        text-align: center;
        margin-bottom: 3rem;
        background:
            radial-gradient(ellipse at 50% -10%, rgba(220,38,38,0.14) 0%, transparent 65%),
            linear-gradient(180deg, #07070c 0%, {BG_DARK} 100%);
        border: 1px solid rgba(220,38,38,0.07);
    }}
    .hero::after {{
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 5%, {ACCENT} 50%, transparent 95%);
        opacity: 0.2;
    }}
    .hero-tag {{
        display: inline-block;
        font-size: 0.62rem;
        font-weight: 700;
        color: {ACCENT};
        text-transform: uppercase;
        letter-spacing: 0.18em;
        padding: 0.28rem 0.85rem;
        border: 1px solid rgba(220,38,38,0.22);
        border-radius: 20px;
        margin-bottom: 1.6rem;
        background: rgba(220,38,38,0.06);
    }}
    .hero-title {{
        font-size: 3.4rem;
        font-weight: 900;
        color: {TEXT_PRIMARY};
        letter-spacing: -0.05em;
        line-height: 1.04;
        margin-bottom: 1.3rem;
    }}
    .hero-title span {{
        background: linear-gradient(135deg, {ACCENT} 0%, #f87171 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .hero-sub {{
        font-size: 1rem;
        color: {TEXT_MUTED};
        max-width: 460px;
        margin: 0 auto;
        line-height: 1.7;
    }}

    /* ── Cards ────────────────────────────────────────────────── */
    .card {{
        background: {BG_CARD};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 14px;
        padding: 1.5rem;
        height: 100%;
        transition: border-color 0.25s, transform 0.25s, box-shadow 0.25s;
    }}
    .card:hover {{
        border-color: rgba(220,38,38,0.18);
        transform: translateY(-2px);
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }}
    .card-label {{
        font-size: 0.6rem;
        font-weight: 700;
        color: {ACCENT};
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.55rem;
    }}
    .card-heading {{
        font-size: 1rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.3rem;
    }}
    .card-body {{
        font-size: 0.78rem;
        color: {TEXT_MUTED};
        line-height: 1.55;
    }}

    /* ── Step cards ───────────────────────────────────────────── */
    .step-row {{
        display: flex;
        align-items: stretch;
        gap: 1.2rem;
        margin-bottom: 2.5rem;
    }}
    .step-card {{
        flex: 1;
        background: {BG_CARD};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 14px;
        padding: 2rem 1.5rem;
        text-align: center;
        transition: border-color 0.25s, transform 0.25s;
    }}
    .step-card:hover {{
        border-color: rgba(220,38,38,0.18);
        transform: translateY(-2px);
    }}
    .step-number {{
        font-size: 2.8rem;
        font-weight: 900;
        color: rgba(220,38,38,0.1);
        line-height: 1;
        margin-bottom: 0.6rem;
    }}
    .step-title {{
        font-size: 0.95rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.3rem;
    }}
    .step-desc {{
        font-size: 0.78rem;
        color: {TEXT_MUTED};
        line-height: 1.5;
    }}
    .step-connector {{
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 28px;
        color: rgba(220,38,38,0.12);
        font-size: 1.1rem;
    }}

    /* ── Metric card ──────────────────────────────────────────── */
    .metric {{
        background: {BG_CARD};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 1.1rem 1rem;
        text-align: center;
    }}
    .metric-val {{
        font-size: 1.5rem;
        font-weight: 800;
        color: {ACCENT};
        line-height: 1.2;
        letter-spacing: -0.02em;
    }}
    .metric-label {{
        font-size: 0.65rem;
        color: {TEXT_MUTED};
        margin-top: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }}

    /* ── Pipeline tracker ─────────────────────────────────────── */
    .pipeline {{
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0.5rem 0 2rem;
    }}
    .pipe-step {{
        background: {BG_CARD};
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 8px;
        padding: 0.5rem 1.3rem;
        text-align: center;
        min-width: 110px;
        transition: all 0.2s;
    }}
    .pipe-step.done {{
        border-color: rgba(220,38,38,0.35);
        background: rgba(220,38,38,0.06);
    }}
    .pipe-step.active {{
        border-color: rgba(245,158,11,0.4);
        background: rgba(245,158,11,0.06);
    }}
    .pipe-num {{
        font-size: 0.52rem;
        font-weight: 700;
        color: {ACCENT};
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}
    .pipe-step.active .pipe-num {{ color: #f59e0b; }}
    .pipe-name {{
        font-size: 0.76rem;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}
    .pipe-arrow {{
        color: rgba(255,255,255,0.06);
        font-size: 0.85rem;
        padding: 0 0.5rem;
    }}

    /* ── Section title ────────────────────────────────────────── */
    .section-title {{
        font-size: 1rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin: 2rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.03);
    }}

    hr {{ border-color: rgba(255,255,255,0.03) !important; }}

    /* ── Buttons ──────────────────────────────────────────────── */
    .stButton > button {{
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.01em !important;
        padding: 0.5rem 1.4rem !important;
        transition: all 0.22s ease !important;
        font-family: 'Inter', sans-serif !important;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {ACCENT} 0%, #b91c1c 100%) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 2px 16px rgba(220,38,38,0.15) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 4px 28px rgba(220,38,38,0.35) !important;
        transform: translateY(-1px) !important;
    }}
    .stButton > button[kind="secondary"] {{
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        color: {TEXT_MUTED} !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        border-color: rgba(220,38,38,0.25) !important;
        color: {TEXT_PRIMARY} !important;
    }}

    /* ── Tabs ─────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.2rem;
        background: transparent !important;
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0 !important;
        font-weight: 500 !important;
        font-size: 0.82rem !important;
        color: {TEXT_MUTED} !important;
        padding: 0.5rem 1rem !important;
        background: transparent !important;
        border: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {TEXT_PRIMARY} !important;
        border-bottom: 2px solid {ACCENT} !important;
    }}

    /* ── File uploader ────────────────────────────────────────── */
    [data-testid="stFileUploader"] section {{
        background: {BG_CARD} !important;
        border: 1px dashed rgba(220,38,38,0.2) !important;
        border-radius: 12px !important;
    }}
    [data-testid="stFileUploader"] section:hover {{
        border-color: rgba(220,38,38,0.4) !important;
    }}

    /* ── Dataframe ────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {{
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
    }}

    /* ── Alerts ───────────────────────────────────────────────── */
    [data-testid="stAlert"] {{
        border-radius: 10px !important;
        border-left-width: 3px !important;
    }}

    /* ── Progress bar ─────────────────────────────────────────── */
    [data-testid="stProgressBar"] > div > div {{
        background: linear-gradient(90deg, {ACCENT}, #f87171) !important;
    }}

    /* ── Expander ─────────────────────────────────────────────── */
    [data-testid="stExpander"] {{
        background: {BG_CARD} !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        border-radius: 10px !important;
    }}

    /* ── Page header ──────────────────────────────────────────── */
    .page-header {{
        margin-bottom: 1.8rem;
        padding-bottom: 1.2rem;
        border-bottom: 1px solid rgba(255,255,255,0.03);
    }}
    .page-header h1 {{
        font-size: 1.7rem;
        font-weight: 800;
        color: {TEXT_PRIMARY};
        margin: 0 0 0.2rem;
        letter-spacing: -0.035em;
    }}
    .page-header p {{
        font-size: 0.83rem;
        color: {TEXT_MUTED};
        margin: 0;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_navbar():
    """
    Renders a clean, self-contained navbar using st.components.v1.html.
    The iframe communicates back to Streamlit via postMessage → hidden buttons.
    """
    current = st.session_state.get("page", "Home")

    has_upload     = st.session_state.get("uploaded_video") is not None
    has_preprocess = st.session_state.get("processed_video") is not None
    has_analysis   = st.session_state.get("analysis_done", False)

    progress_states = {
        "Upload": has_upload,
        "Process": has_preprocess,
        "Analysis": has_analysis,
    }
    dots_html = "".join(
        f'<span class="dot {"done" if v else "pending"}" title="{k}"></span>'
        for k, v in progress_states.items()
    )

    links_html = ""
    for name in NAV_PAGES:
        active = ' class="active"' if name == current else ""
        links_html += f'<a href="#" data-page="{name}"{active}>{name}</a>'

    navbar_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: 'Inter', sans-serif;
    background: rgba(3,3,5,0.97);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    height: 52px;
    overflow: hidden;
  }}
  nav {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 52px;
    padding: 0 2rem;
    position: relative;
  }}
  .brand {{
    font-size: 0.92rem;
    font-weight: 800;
    color: #f5f5f5;
    letter-spacing: -0.03em;
    flex-shrink: 0;
    text-decoration: none;
  }}
  .brand span {{ color: #dc2626; }}
  .links {{
    display: flex;
    align-items: center;
    gap: 0.1rem;
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
  }}
  .links a {{
    padding: 0.32rem 0.82rem;
    border-radius: 7px;
    font-size: 0.76rem;
    font-weight: 500;
    color: #6b6b78;
    text-decoration: none;
    border: 1px solid transparent;
    transition: color 0.15s, background 0.15s, border-color 0.15s;
    white-space: nowrap;
  }}
  .links a:hover {{
    color: #f5f5f5;
    background: rgba(255,255,255,0.04);
  }}
  .links a.active {{
    color: #f5f5f5;
    background: rgba(220,38,38,0.1);
    border-color: rgba(220,38,38,0.22);
  }}
  .status {{
    display: flex;
    align-items: center;
    gap: 0.45rem;
    flex-shrink: 0;
  }}
  .dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    display: inline-block;
  }}
  .dot.done {{
    background: #dc2626;
    box-shadow: 0 0 7px rgba(220,38,38,0.6);
  }}
  .dot.pending {{ background: #252530; }}
</style>
</head>
<body>
<nav>
  <a class="brand" href="#">Football<span>Tracker</span></a>
  <div class="links">{links_html}</div>
  <div class="status">{dots_html}</div>
</nav>
<script>
  document.querySelectorAll('.links a').forEach(function(a) {{
    a.addEventListener('click', function(e) {{
      e.preventDefault();
      window.parent.postMessage({{type: 'NAV_CLICK', page: this.dataset.page}}, '*');
    }});
  }});
</script>
</body>
</html>
"""

    # Render the navbar iframe
    components.html(navbar_html, height=52, scrolling=False)

    # JS listener — catches postMessage from the navbar iframe and clicks
    # the matching hidden Streamlit button
    st.markdown("""
    <script>
    (function() {
        if (window._navListenerAdded) return;
        window._navListenerAdded = true;
        window.addEventListener('message', function(e) {
            if (!e.data || e.data.type !== 'NAV_CLICK') return;
            var page = e.data.page;
            // Find the nav button row by its sentinel span, then click the right button
            var sentinel = document.getElementById('_nav_sentinel');
            if (!sentinel) return;
            var row = sentinel.parentElement;
            while (row && row.getAttribute('data-testid') !== 'stHorizontalBlock') {
                row = row.parentElement;
            }
            if (!row) return;
            var btns = row.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].innerText.trim() === page) { btns[i].click(); break; }
            }
        });
    })();
    </script>
    """, unsafe_allow_html=True)

    # Sentinel so JS can locate the button row, then hide the whole row
    st.markdown("""
    <span id="_nav_sentinel" style="display:none"></span>
    <script>
    (function hide() {
        var s = document.getElementById('_nav_sentinel');
        if (!s) { setTimeout(hide, 30); return; }
        var row = s.parentElement;
        while (row && row.getAttribute('data-testid') !== 'stHorizontalBlock') {
            row = row.parentElement;
        }
        if (row) { row.style.cssText = 'position:absolute;opacity:0;pointer-events:none;height:0;overflow:hidden;'; }
        else { setTimeout(hide, 30); }
    })();
    </script>
    """, unsafe_allow_html=True)

    # The actual functional buttons (hidden by JS above)
    cols = st.columns(len(NAV_PAGES))
    for col, name in zip(cols, NAV_PAGES):
        with col:
            if st.button(name, key=f"nav_{name}"):
                st.session_state.page = name
                st.rerun()


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
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
        html += (
            f'<div class="{cls}">'
            f'<div class="pipe-num">Step {i+1}</div>'
            f'<div class="pipe-name">{name}</div>'
            f'</div>'
        )
        if i < len(steps) - 1:
            html += '<div class="pipe-arrow">→</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def nav_button(label: str, target: str, key: str | None = None):
    if st.button(label, use_container_width=True, type="primary", key=key):
        st.session_state.page = target
        st.rerun()


def setup_sidebar():
    pass
