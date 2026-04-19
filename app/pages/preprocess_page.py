# app/pages/preprocess_page.py
"""
Preprocess Page — shows preprocessing status/details.

Preprocessing now runs automatically as part of the Analysis pipeline.
This page lets users see what happened and adjust settings for re-runs.
"""

import os
import cv2
import streamlit as st
from config import PROCESSED_DIR, DEFAULT_TARGET_FPS, DEFAULT_RESIZE_W
from utils import page_header, metric_card


def _video_info(path: str) -> dict:
    cap = cv2.VideoCapture(path)
    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS) or 25.0,
        "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
    }
    info["duration"] = info["frames"] / info["fps"] if info["fps"] > 0 else 0
    cap.release()
    return info


def render():
    page_header("Preprocessing",
                "Preprocessing runs automatically when you start analysis. "
                "This page shows details and lets you adjust settings.")

    done = st.session_state.get("processed_video") is not None
    st.markdown("---")

    raw = st.session_state.get("uploaded_video")
    proc = st.session_state.get("processed_video")

    if not raw or not os.path.exists(raw):
        st.warning("No video uploaded yet. Use the top navigation bar to go to Upload.")
        return

    # Show raw video info
    st.markdown("##### Input Video")
    info = _video_info(raw)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("Resolution",
                                f"{info['width']}x{info['height']}"),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("FPS", f"{info['fps']:.1f}"),
                    unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Frames", f"{info['frames']:,}"),
                    unsafe_allow_html=True)
    with c4:
        m, s = divmod(int(info["duration"]), 60)
        st.markdown(metric_card("Duration", f"{m}m {s}s"),
                    unsafe_allow_html=True)

    # Settings that will be used
    st.markdown("---")
    st.markdown("##### Preprocessing Settings")
    st.caption("These settings are applied automatically when you run the analysis.")

    s1, s2 = st.columns(2)
    with s1:
        fps = st.slider("Target FPS", 5, 60, DEFAULT_TARGET_FPS,
                         key="preprocess_fps",
                         help="Lower = faster processing")
    with s2:
        width = st.select_slider("Output Width (px)",
                                  [640, 960, 1280, 1920],
                                  value=DEFAULT_RESIZE_W,
                                  key="preprocess_width")

    # Store settings in session for the analysis page to use
    st.session_state.target_fps = fps
    st.session_state.resize_width = width

    scale = width / info["width"]
    new_h = int(info["height"] * scale)
    interval = max(1, int(info["fps"] / fps))
    est_frames = info["frames"] // interval

    st.caption(
        f"Output will be {width}x{new_h} at {fps} FPS "
        f"(~{est_frames:,} frames, sampling every {interval}th frame)"
    )

    # Show before/after if already preprocessed
    if proc and os.path.exists(proc):
        st.markdown("---")
        st.markdown("##### Preprocessed Output")

        pinfo = _video_info(proc)
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown(metric_card("Output Resolution",
                                    f"{pinfo['width']}x{pinfo['height']}"),
                        unsafe_allow_html=True)
        with p2:
            st.markdown(metric_card("Output FPS", f"{pinfo['fps']:.1f}"),
                        unsafe_allow_html=True)
        with p3:
            st.markdown(metric_card("Output Frames", f"{pinfo['frames']:,}"),
                        unsafe_allow_html=True)

        b, a = st.columns(2)
        with b:
            st.caption("Original")
            st.video(raw)
        with a:
            st.caption("Preprocessed")
            st.video(proc)

    st.markdown("---")
    st.caption("Use the top navigation bar to switch pages.")
