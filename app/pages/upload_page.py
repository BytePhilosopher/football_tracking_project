# app/pages/upload_page.py
"""Upload Page — upload a video, then auto-advance to preprocessing."""

import os
import streamlit as st
from config import RAW_DIR, VIDEO_EXTENSIONS
from utils import page_header, render_pipeline, nav_button, metric_card


def render():
    page_header("Upload Video",
                "Provide a match video to start the automated pipeline.")
    render_pipeline(active=0)
    st.markdown("---")

    left, right = st.columns([3, 2])

    with left:
        st.markdown("##### Upload a video file")
        st.caption(f"Accepted: {', '.join(f'.{e}' for e in VIDEO_EXTENSIONS)}")

        uploaded = st.file_uploader(
            "Choose video",
            type=VIDEO_EXTENSIONS,
            label_visibility="collapsed",
        )

        if uploaded is not None:
            save_path = os.path.join(RAW_DIR, uploaded.name)
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())

            st.session_state.uploaded_video = save_path
            st.session_state.uploaded_video_name = uploaded.name
            # Clear downstream state on new upload
            st.session_state.pop("processed_video", None)
            st.session_state.pop("analysis_done", None)
            st.session_state.pop("tracked_video", None)

            st.success(f"Saved: data/raw/{uploaded.name}")

            size_mb = os.path.getsize(save_path) / (1024 * 1024)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(metric_card("Size", f"{size_mb:.1f} MB"),
                            unsafe_allow_html=True)
            with c2:
                ext = uploaded.name.rsplit(".", 1)[-1].upper()
                st.markdown(metric_card("Format", ext),
                            unsafe_allow_html=True)

        # Or pick existing
        st.markdown("---")
        st.markdown("##### Or select an existing video")
        existing = sorted(
            f for f in os.listdir(RAW_DIR)
            if f.rsplit(".", 1)[-1].lower() in VIDEO_EXTENSIONS
        )
        if existing:
            sel = st.selectbox("Videos in data/raw/",
                               ["-- Select --"] + existing)
            if sel != "-- Select --":
                path = os.path.join(RAW_DIR, sel)
                st.session_state.uploaded_video = path
                st.session_state.uploaded_video_name = sel
        else:
            st.caption("No videos in data/raw/.")

    with right:
        st.markdown("##### Preview")
        if st.session_state.get("uploaded_video"):
            st.video(st.session_state.uploaded_video)
        else:
            st.info("Upload or select a video.")

    # ── Auto-advance ─────────────────────────────────────────────────────────
    st.markdown("---")
    _, right_col = st.columns([3, 1])
    with right_col:
        if st.session_state.get("uploaded_video"):
            nav_button("Next: Run Analysis", "Analysis")
        else:
            st.button("Next: Run Analysis", disabled=True,
                       use_container_width=True)
