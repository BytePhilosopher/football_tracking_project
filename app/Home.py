# app/Home.py
"""Football Tracking Pipeline — Streamlit entry point."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="Football Tracking Pipeline",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from utils import (
    inject_custom_css, render_navbar, page_header,
    nav_button, setup_sidebar, metric_card,
    ACCENT, ACCENT_LIGHT, TEXT_PRIMARY, TEXT_MUTED, BG_CARD, BG_DARK, BORDER,
)

if "page" not in st.session_state:
    st.session_state.page = "Home"

inject_custom_css()
setup_sidebar()
render_navbar()

# ── Page router ──────────────────────────────────────────────────────────────
current = st.session_state.get("page", "Home")

if current == "Upload":
    from pages import upload_page
    upload_page.render()
elif current == "Preprocess":
    from pages import preprocess_page
    preprocess_page.render()
elif current == "Analysis":
    from pages import analysis_page
    analysis_page.render()
elif current == "Results":
    from pages import results_page
    results_page.render()
else:
    # ── HOME ─────────────────────────────────────────────────────────────────

    # Hero
    st.markdown(f"""
    <div class="hero">
        <div class="hero-tag">AI-Powered Match Analysis</div>
        <div class="hero-title">Football<br><span>Tracking Pipeline</span></div>
        <div class="hero-sub">
            Raw footage in. Full analytics out.<br>
            One click from broadcast video to match insights.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Three-step flow — pure HTML for perfect alignment
    st.markdown(f"""
    <div class="step-row">
        <div class="step-card">
            <div class="step-number">01</div>
            <div class="step-title">Upload</div>
            <div class="step-desc">Drop any MP4 match footage</div>
        </div>
        <div class="step-connector">&#8594;</div>
        <div class="step-card">
            <div class="step-number">02</div>
            <div class="step-title">Analyze</div>
            <div class="step-desc">Automated detection, tracking, segmentation</div>
        </div>
        <div class="step-connector">&#8594;</div>
        <div class="step-card">
            <div class="step-number">03</div>
            <div class="step-title">Results</div>
            <div class="step-desc">Charts, stats, annotated video, CSV export</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA
    _, btn, _ = st.columns([2, 1, 2])
    with btn:
        nav_button("Start Pipeline", "Upload")

    # Tech stack — tight grid
    st.markdown('<div class="section-title">Technical Stack</div>',
                unsafe_allow_html=True)

    row1 = st.columns(4, gap="small")
    specs = [
        ("Detection", "YOLOv8", "Custom-trained, 1280px input"),
        ("Tracking", "ByteTrack", "Camera-compensated MOT"),
        ("Team ID", "DBSCAN", "Jersey-color clustering"),
        ("Possession", "Hysteresis", "Tin/Tout + K-frame confirm"),
    ]
    for col, (label, heading, body) in zip(row1, specs):
        with col:
            st.markdown(f"""
            <div class="card">
                <div class="card-label">{label}</div>
                <div class="card-heading">{heading}</div>
                <div class="card-body">{body}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

    row2 = st.columns(4, gap="small")
    specs2 = [
        ("Replay", "Scene-Cut Filter", "Histogram + flow detection"),
        ("Ball", "Interpolation", "Velocity extrapolation"),
        ("Camera", "Optical Flow", "LK pan/zoom compensation"),
        ("Export", "Data Pipeline", "Velocity, distance, CSV"),
    ]
    for col, (label, heading, body) in zip(row2, specs2):
        with col:
            st.markdown(f"""
            <div class="card">
                <div class="card-label">{label}</div>
                <div class="card-heading">{heading}</div>
                <div class="card-body">{body}</div>
            </div>
            """, unsafe_allow_html=True)
