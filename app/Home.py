# app/Home.py
import sys, os, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="Football Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from utils import (
    inject_custom_css, render_navbar, nav_button, nav_to,
    page_header, render_pipeline, setup_sidebar, metric_card,
    ACCENT, TEXT_PRIMARY, TEXT_MUTED, BG_CARD,
)

if "page" not in st.session_state:
    st.session_state.page = "Home"

inject_custom_css()
setup_sidebar()
render_navbar()

current = st.session_state.get("page", "Home")

if current == "Upload":
    from pages import upload_page; upload_page.render()
elif current == "Preprocess":
    from pages import preprocess_page; preprocess_page.render()
elif current == "Analysis":
    from pages import analysis_page; analysis_page.render()
elif current == "Results":
    from pages import results_page; results_page.render()
else:
    # ══════════════════════════════════════════════════════════════════
    #  LANDING PAGE
    # ══════════════════════════════════════════════════════════════════

    # Load hero image
    _IMG_B64 = ""
    _img_path = os.path.join(os.path.dirname(__file__), "images", "images.jpeg")
    if os.path.exists(_img_path):
        with open(_img_path, "rb") as f:
            _IMG_B64 = base64.b64encode(f.read()).decode()

    # All landing-page classes use "lp-" prefix to avoid any conflict
    # with the shared CSS in utils.py
    st.markdown("""
    <style>
    .lp-hero {
        position: relative;
        border-radius: 20px;
        overflow: hidden;
        min-height: 460px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-size: cover;
        background-position: center 30%;
        margin-bottom: 2.5rem;
    }
    .lp-hero::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 20px;
        background: linear-gradient(160deg,
            rgba(3,3,5,0.93) 0%,
            rgba(3,3,5,0.75) 50%,
            rgba(10,0,0,0.88) 100%);
    }
    .lp-hero::after {
        content: "";
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 2px;
        border-radius: 0 0 20px 20px;
        background: linear-gradient(90deg, transparent 5%, #dc2626 50%, transparent 95%);
        opacity: 0.45;
    }
    .lp-inner {
        position: relative;
        z-index: 2;
        text-align: center;
        padding: 4.5rem 2rem 4rem;
        width: 100%;
    }
    .lp-badge {
        display: inline-block;
        font-size: 0.58rem;
        font-weight: 700;
        color: #dc2626;
        text-transform: uppercase;
        letter-spacing: 0.22em;
        padding: 0.28rem 0.95rem;
        border: 1px solid rgba(220,38,38,0.28);
        border-radius: 20px;
        margin-bottom: 1.6rem;
        background: rgba(220,38,38,0.06);
    }
    .lp-h1 {
        font-size: 3.6rem;
        font-weight: 900;
        color: #f5f5f5;
        letter-spacing: -0.05em;
        line-height: 1.06;
        margin: 0 0 1.2rem;
        text-shadow: 0 2px 20px rgba(0,0,0,0.5);
    }
    .lp-h1 em {
        font-style: normal;
        background: linear-gradient(135deg, #dc2626 0%, #f87171 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .lp-tagline {
        font-size: 1.02rem;
        color: rgba(245,245,245,0.6);
        max-width: 460px;
        margin: 0 auto 2.2rem;
        line-height: 1.8;
        justify-content: center;
    }
    .lp-stats {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 2.5rem;
        margin-top: 0.5rem;
    }
    .lp-stat-val {
        font-size: 1.2rem;
        font-weight: 800;
        color: #dc2626;
        letter-spacing: -0.02em;
        line-height: 1;
    }
    .lp-stat-lbl {
        font-size: 0.55rem;
        color: rgba(245,245,245,0.4);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.22rem;
    }
    .lp-sep {
        width: 1px;
        height: 30px;
        background: rgba(255,255,255,0.08);
    }

    /* Section headings */
    .lp-label {
        text-align: center;
        font-size: 0.58rem;
        font-weight: 700;
        color: #6b6b78;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        margin-bottom: 0.6rem;
    }
    .lp-h2 {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 800;
        color: #f5f5f5;
        letter-spacing: -0.04em;
        margin-bottom: 2.2rem;
    }
    .lp-h2 em {
        font-style: normal;
        background: linear-gradient(135deg, #dc2626, #f87171);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Feature cards */
    .lp-feat {
        background: #0d0d12;
        border: 1px solid rgba(255,255,255,0.045);
        border-radius: 14px;
        padding: 1.6rem 1.4rem;
        height: 100%;
        transition: border-color 0.25s, transform 0.25s, box-shadow 0.25s;
    }
    .lp-feat:hover {
        border-color: rgba(220,38,38,0.18);
        transform: translateY(-2px);
        box-shadow: 0 10px 36px rgba(0,0,0,0.45);
    }
    .lp-feat-icon {
        width: 40px; height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        background: rgba(220,38,38,0.07);
        border: 1px solid rgba(220,38,38,0.1);
    }
    .lp-feat-name {
        font-size: 0.88rem;
        font-weight: 700;
        color: #f5f5f5;
        margin-bottom: 0.35rem;
    }
    .lp-feat-desc {
        font-size: 0.76rem;
        color: #6b6b78;
        line-height: 1.6;
    }
    .lp-feat-desc strong {
        color: #dc2626;
        font-weight: 700;
    }

    /* Workflow steps */
    .lp-steps {
        display: flex;
        align-items: stretch;
        gap: 0.8rem;
        margin-bottom: 2.5rem;
    }
    .lp-step {
        flex: 1;
        background: #0d0d12;
        border: 1px solid rgba(255,255,255,0.045);
        border-radius: 14px;
        padding: 1.8rem 1.3rem;
        text-align: center;
        transition: border-color 0.25s, transform 0.25s;
    }
    .lp-step:hover {
        border-color: rgba(220,38,38,0.18);
        transform: translateY(-2px);
    }
    .lp-step-num {
        font-size: 2.6rem;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 0.7rem;
        background: linear-gradient(180deg, rgba(220,38,38,0.45), rgba(220,38,38,0.06));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .lp-step-name {
        font-size: 0.9rem;
        font-weight: 700;
        color: #f5f5f5;
        margin-bottom: 0.3rem;
    }
    .lp-step-desc {
        font-size: 0.76rem;
        color: #6b6b78;
        line-height: 1.6;
    }
    .lp-arrow {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 24px;
        color: rgba(220,38,38,0.22);
        font-size: 1.1rem;
    }

    /* CTA */
    .lp-cta {
        text-align: center;
        background: radial-gradient(ellipse at 50% 0%, rgba(220,38,38,0.06) 0%, transparent 70%);
        border: 1px solid rgba(220,38,38,0.07);
        border-radius: 18px;
        padding: 3rem 2rem;
        margin: 1rem 0 1.5rem;
    }
    .lp-cta-h {
        font-size: 1.4rem;
        font-weight: 800;
        color: #f5f5f5;
        letter-spacing: -0.03em;
        margin-bottom: 0.5rem;
    }
    .lp-cta-p {
        font-size: 0.82rem;
        color: #6b6b78;
        max-width: 400px;
        margin: 0 auto 1.8rem;
        line-height: 1.7;
    }

    /* Footer */
    .lp-footer {
        text-align: center;
        padding: 1.8rem 0 0.8rem;
        border-top: 1px solid rgba(255,255,255,0.03);
        margin-top: 1.5rem;
    }
    .lp-footer span {
        font-size: 0.6rem;
        color: #2e2e3a;
        letter-spacing: 0.04em;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────────────────
    if _IMG_B64:
        bg = f"background-image:url('data:image/jpeg;base64,{_IMG_B64}');"
    else:
        bg = "background:linear-gradient(160deg,#07070c,#0d0d12 50%,#0a0008);"

    st.markdown(f"""
    <div class="lp-hero" style="{bg}">
      <div class="lp-inner">
        <div class="lp-badge">AI-Powered Match Analysis</div>
        <h1 class="lp-h1">Football<br><em>Tracking Pipeline</em></h1>
        <p class="lp-tagline">
          Raw footage in. Full analytics out.<br>
          One click from broadcast video to match insights.
        </p>
        <div class="lp-stats">
          <div><div class="lp-stat-val">YOLOv8</div><div class="lp-stat-lbl">Detection</div></div>
          <div class="lp-sep"></div>
          <div><div class="lp-stat-val">ByteTrack</div><div class="lp-stat-lbl">Tracking</div></div>
          <div class="lp-sep"></div>
          <div><div class="lp-stat-val">DBSCAN</div><div class="lp-stat-lbl">Team ID</div></div>
          <div class="lp-sep"></div>
          <div><div class="lp-stat-val">Real-time</div><div class="lp-stat-lbl">Possession</div></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Start button ──────────────────────────────────────────────────
    _, c, _ = st.columns([2, 1, 2])
    with c:
        nav_button("Start Pipeline", "Upload")

    # ── Features ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="lp-label">Core Capabilities</div>
    <div class="lp-h2">Everything you need for <em>match analysis</em></div>
    """, unsafe_allow_html=True)

    features = [
        ("🎯", "Object Detection",     "YOLOv8",       "Custom-trained at 1280px for precise player, ball & referee detection."),
        ("📍", "Multi-Object Tracking", "ByteTrack",    "Camera-compensated MOT that keeps IDs through occlusions."),
        ("👕", "Team Identification",   "DBSCAN",       "Automatic jersey-color clustering — no manual labelling required."),
        ("📊", "Possession Stats",      "Hysteresis",   "Frame-level possession with temporal smoothing for broadcast accuracy."),
        ("🎬", "Replay Detection",      "Scene-Cut",    "Histogram + optical-flow analysis filters replays automatically."),
        ("⚽", "Ball Interpolation",    "Velocity",     "Smart extrapolation fills frames where the ball is occluded."),
        ("📷", "Camera Compensation",   "Optical Flow", "Lucas-Kanade pan/zoom estimation for stabilised coordinates."),
        ("💾", "Data Export",           "CSV Pipeline", "Velocity, distance & event data ready for downstream analytics."),
    ]

    for i in range(0, len(features), 4):
        row = features[i:i + 4]
        cols = st.columns(4, gap="small")
        for col, (icon, title, tech, desc) in zip(cols, row):
            with col:
                st.markdown(
                    f'<div class="lp-feat">'
                    f'<div class="lp-feat-icon">{icon}</div>'
                    f'<div class="lp-feat-name">{title}</div>'
                    f'<div class="lp-feat-desc"><strong>{tech}</strong> — {desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)

    # ── Workflow ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:2.5rem">
      <div class="lp-label">Workflow</div>
      <div class="lp-h2">Three steps to full match analytics</div>
    </div>
    <div class="lp-steps">
      <div class="lp-step">
        <div class="lp-step-num">01</div>
        <div class="lp-step-name">Upload</div>
        <div class="lp-step-desc">Drop any MP4 match footage — broadcast, drone, or sideline.</div>
      </div>
      <div class="lp-arrow">&rarr;</div>
      <div class="lp-step">
        <div class="lp-step-num">02</div>
        <div class="lp-step-name">Analyze</div>
        <div class="lp-step-desc">Automated detection, tracking, segmentation & possession.</div>
      </div>
      <div class="lp-arrow">&rarr;</div>
      <div class="lp-step">
        <div class="lp-step-num">03</div>
        <div class="lp-step-name">Results</div>
        <div class="lp-step-desc">Interactive charts, annotated video, stats & CSV export.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="lp-cta">
      <div class="lp-cta-h">Ready to analyze your match?</div>
      <div class="lp-cta-p">Upload your footage and let the pipeline handle the rest —
        from raw video to actionable insights.</div>
    </div>
    """, unsafe_allow_html=True)

    _, c2, _ = st.columns([2, 1, 2])
    with c2:
        nav_button("Get Started", "Upload", key="cta_btn")

    # ── Footer ────────────────────────────────────────────────────────
    st.markdown(
        '<div class="lp-footer">'
        '<span>Football Tracking Pipeline &mdash; Built with Streamlit, YOLOv8 &amp; ByteTrack</span>'
        '</div>',
        unsafe_allow_html=True,
    )
