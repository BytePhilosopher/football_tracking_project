# app/pages/analysis_page.py
"""
Analysis Page — fully automated pipeline.

One button runs: Preprocess → Detection → Tracking → Post-processing.
No user input required after clicking "Run".
"""

import os
import json
import shutil
import cv2
import numpy as np
from types import SimpleNamespace

import streamlit as st

from config import (
    MODEL_PATH, PROCESSED_DIR, ANNOTATIONS_DIR, INSIGHTS_DIR,
    PLAYER_CLASS_IDS, BALL_CLASS_ID, DEFAULT_CONF, DEFAULT_IOU, DEFAULT_IMGSZ,
    DEFAULT_TARGET_FPS, DEFAULT_RESIZE_W,
)
from utils import (
    page_header, render_pipeline, nav_button, metric_card,
    ACCENT, TEXT_PRIMARY, TEXT_MUTED, BG_CARD,
)


def _preprocess(input_path: str, output_path: str,
                target_fps: int, resize_w: int, progress, status):
    """Stage 1: Normalize FPS and resize."""
    status.text("Stage 1/4 — Preprocessing: resizing and normalizing FPS...")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open: {input_path}")

    orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = max(1, int(orig_fps / target_fps))

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = resize_w / w
    new_h = int(h * scale)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, target_fps, (resize_w, new_h))

    idx = 0
    written = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % interval == 0:
            frame = cv2.resize(frame, (resize_w, new_h))
            out.write(frame)
            written += 1
        idx += 1
        if total > 0:
            progress.progress(
                min(idx / total * 0.15, 0.15),  # 0-15% of total progress
                text=f"Preprocessing: frame {idx:,}/{total:,}"
            )

    cap.release()
    out.release()
    return {"frames": written, "w": resize_w, "h": new_h, "fps": target_fps}


def _run_tracking(video_path: str, progress, status):
    """Stage 2-3: Detection + tracking + team segmentation + possession."""
    from src.detector import Detector
    from src.replay_detector import ReplayDetector
    from src.tracker import Tracker
    from src.camera_compensation import CameraCompensation
    from src.team_segmentation import TeamSegmenter
    from src.ball_interpolator import BallInterpolator
    from src.possession import PossessionTracker
    from src.metadata import MetadataLogger
    from src.utils import draw_player, draw_ball, draw_hud

    status.text("Stage 2/4 — Loading YOLO model...")
    detector = Detector(MODEL_PATH, conf=DEFAULT_CONF, iou=DEFAULT_IOU,
                        imgsz=DEFAULT_IMGSZ)
    tracker = Tracker()
    cam_comp = CameraCompensation()
    replay_det = ReplayDetector(
        hist_threshold=0.70, flow_threshold=25.0,
        entry_frames=3, exit_frames=4, cooldown_frames=8,
    )
    logger = MetadataLogger(ANNOTATIONS_DIR)
    team_seg = TeamSegmenter()
    ball_interp = BallInterpolator()
    poss_tracker = PossessionTracker(Tin=50, Tout=70, K=5)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open: {video_path}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    vname = os.path.splitext(os.path.basename(video_path))[0]
    out_path = os.path.join(PROCESSED_DIR, f"{vname}_tracked.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

    def reset():
        tracker.tracker.reset()
        ball_interp.__init__(
            history=ball_interp.history, vel_window=ball_interp.vel_window,
            max_gap=ball_interp.max_gap, decay=ball_interp.decay,
        )
        poss_tracker._reset_candidate()
        poss_tracker.current_possessor = None
        poss_tracker.current_team = None
        cam_comp._prev_gray = None
        cam_comp._prev_pts = None

    fid = 0
    team_fitted = False
    prev_replay = False
    n_replays = 0
    n_replay_frames = 0

    status.text("Stage 3/4 — Running detection and tracking...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        shift = cam_comp.update(frame)
        flow = (shift[0] ** 2 + shift[1] ** 2) ** 0.5
        in_replay = replay_det.update(frame, fid, flow)

        if in_replay != prev_replay:
            reset()
            if in_replay:
                n_replays += 1
        prev_replay = in_replay

        if in_replay:
            out.write(frame)
            n_replay_frames += 1
            fid += 1
            if total > 0:
                pct = 0.15 + (fid / total * 0.70)  # 15-85%
                progress.progress(min(pct, 0.85),
                                  text=f"Tracking: frame {fid:,}/{total:,} (replay skip)")
            continue

        dets = detector.detect(frame)
        tracked = tracker.update(dets, shift)

        if tracked is None or len(tracked) == 0:
            out.write(frame)
            fid += 1
            if total > 0:
                pct = 0.15 + (fid / total * 0.70)
                progress.progress(min(pct, 0.85))
            continue

        players, balls = [], []
        xyxy = tracked.xyxy
        cids = tracked.class_id
        tids = tracked.tracker_id
        confs = (tracked.confidence
                 if tracked.confidence is not None
                 else [None] * len(xyxy))

        for box, cid, tid, conf in zip(xyxy, cids, tids, confs):
            x1, y1, x2, y2 = box
            obj = SimpleNamespace(
                cls=int(cid),
                id=int(tid) if tid is not None else -1,
                xyxy=[x1, y1, x2, y2],
                conf=float(conf) if conf is not None else 0.0,
                team=-1,
            )
            if int(cid) in PLAYER_CLASS_IDS:
                players.append(obj)
            elif int(cid) == BALL_CLASS_ID:
                balls.append(obj)

        if not team_fitted:
            team_fitted = team_seg.fit(frame, players)
        for p in players:
            p.team = team_seg.assign_team(frame, p)

        ball_obj = balls[0] if balls else None
        ball_pos = ball_interp.update(fid, ball_obj)
        b_interp = ball_interp.is_interpolating
        poss_id = poss_tracker.update(ball_pos, players)

        ann = frame.copy()
        for p in players:
            draw_player(ann, p, poss_id)
        draw_ball(ann, ball_pos, interpolated=b_interp)
        draw_hud(ann, fid, fps, poss_tracker.possession_percentages())

        logger.log(fid, tracked, players=players, possessor_id=poss_id,
                   ball_position=ball_pos, ball_interpolated=b_interp)

        out.write(ann)
        fid += 1
        if total > 0:
            pct = 0.15 + (fid / total * 0.70)
            progress.progress(min(pct, 0.85),
                              text=f"Tracking: frame {fid:,}/{total:,}")

    cap.release()
    out.release()
    logger.save()

    return {
        "output_video": out_path,
        "total_frames": fid,
        "fps": fps,
        "resolution": f"{w}x{h}",
        "replays_detected": n_replays,
        "replay_frames_skipped": n_replay_frames,
    }


def _run_postprocessing(fps: float, progress, status):
    """Stage 4: Compute kinematics, summaries, copy to insights."""
    from src.data_pipeline import run_pipeline

    status.text("Stage 4/4 — Computing velocity, distance, and possession stats...")
    progress.progress(0.88, text="Post-processing...")

    tracking_csv = os.path.join(ANNOTATIONS_DIR, "tracking.csv")
    if os.path.exists(tracking_csv):
        run_pipeline(tracking_csv, ANNOTATIONS_DIR, fps=fps)

    progress.progress(0.95, text="Saving insights...")

    for fname in ["tracking_enriched.csv", "player_summary.csv",
                  "possession_summary.csv", "metadata.csv"]:
        src = os.path.join(ANNOTATIONS_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(INSIGHTS_DIR, fname))

    progress.progress(1.0, text="Pipeline complete")


def _full_pipeline(raw_video: str, progress, status):
    """Run the entire pipeline end-to-end."""
    target_fps = st.session_state.get("target_fps", DEFAULT_TARGET_FPS)
    resize_w = st.session_state.get("resize_width", DEFAULT_RESIZE_W)

    # Stage 1: Preprocess
    vname = os.path.splitext(os.path.basename(raw_video))[0]
    preprocessed_path = os.path.join(PROCESSED_DIR, f"{vname}_preprocessed.mp4")
    pre_info = _preprocess(raw_video, preprocessed_path,
                           target_fps, resize_w, progress, status)
    st.session_state.processed_video = preprocessed_path

    # Stage 2-3: Detection + Tracking
    track_result = _run_tracking(preprocessed_path, progress, status)

    # Stage 4: Post-processing
    _run_postprocessing(track_result["fps"], progress, status)

    # Save summary
    summary = {
        "video": os.path.basename(raw_video),
        "preprocess": pre_info,
        **track_result,
    }
    with open(os.path.join(INSIGHTS_DIR, "pipeline_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def render():
    page_header("Analysis",
                "Run the full pipeline automatically on your uploaded video.")

    analysis_done = st.session_state.get("analysis_done", False)
    has_video = st.session_state.get("uploaded_video") is not None

    done_up_to = -1
    if has_video:
        done_up_to = 0
    if st.session_state.get("processed_video"):
        done_up_to = 1
    if analysis_done:
        done_up_to = 3

    render_pipeline(done_up_to=done_up_to)
    st.markdown("---")

    raw_video = st.session_state.get("uploaded_video")

    if not raw_video or not os.path.exists(raw_video):
        st.warning("No video uploaded. Go to the Upload page first.")
        _, r = st.columns([3, 1])
        with r:
            nav_button("Go to Upload", "Upload")
        return

    # ── Show what will be processed ──────────────────────────────────────────
    st.markdown("##### Input")
    c1, c2 = st.columns([2, 1])
    with c1:
        vname = st.session_state.get("uploaded_video_name", "video.mp4")
        cap = cv2.VideoCapture(raw_video)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        dur = total / fps if fps > 0 else 0
        cap.release()

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(metric_card("Video", vname), unsafe_allow_html=True)
        with m2:
            st.markdown(metric_card("Resolution", f"{w}x{h}"),
                        unsafe_allow_html=True)
        with m3:
            st.markdown(metric_card("Frames", f"{total:,}"),
                        unsafe_allow_html=True)
        with m4:
            mm, ss = divmod(int(dur), 60)
            st.markdown(metric_card("Duration", f"{mm}m {ss}s"),
                        unsafe_allow_html=True)

    with c2:
        with st.expander("Preview"):
            st.video(raw_video)

    # ── GPU check ────────────────────────────────────────────────────────────
    try:
        import torch
        has_gpu = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if has_gpu else None
    except ImportError:
        has_gpu = False
        gpu_name = None

    st.markdown("---")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(metric_card("Device", gpu_name or "CPU"),
                    unsafe_allow_html=True)
    with g2:
        if has_gpu:
            est = "~2-5 min for a 5-min video"
        else:
            est = "Slow on CPU — may take a while"
        st.markdown(metric_card("Estimate", est), unsafe_allow_html=True)

    if not has_gpu:
        st.caption(
            "No GPU detected. The pipeline will run on CPU. "
            "This works but is slower than GPU. For faster processing, "
            "use Google Colab with a T4 GPU."
        )

    # ── Model check ──────────────────────────────────────────────────────────
    if not os.path.exists(MODEL_PATH):
        st.error(
            "Model weights not found at models/best.pt. "
            "Place the trained YOLO model in the models/ directory."
        )
        return

    # ── Run button ───────────────────────────────────────────────────────────
    st.markdown("---")

    if analysis_done:
        result = st.session_state.get("analysis_results", {})

        st.success("Pipeline completed successfully.")

        if result:
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.markdown(metric_card("Frames Processed",
                                        f"{result.get('total_frames', 0):,}"),
                            unsafe_allow_html=True)
            with r2:
                st.markdown(metric_card("Output FPS",
                                        f"{result.get('fps', 0):.1f}"),
                            unsafe_allow_html=True)
            with r3:
                st.markdown(metric_card("Replays Detected",
                                        str(result.get("replays_detected", 0))),
                            unsafe_allow_html=True)
            with r4:
                st.markdown(metric_card("Replay Frames",
                                        f"{result.get('replay_frames_skipped', 0):,}"),
                            unsafe_allow_html=True)

        col_rerun, col_results = st.columns(2)
        with col_rerun:
            if st.button("Re-run Pipeline", use_container_width=True):
                st.session_state.analysis_done = False
                st.session_state.pop("analysis_results", None)
                st.session_state.pop("processed_video", None)
                st.session_state.pop("tracked_video", None)
                st.rerun()
        with col_results:
            nav_button("View Results", "Results", key="an_to_results")

    else:
        st.markdown(f"""
        <div style="background: {BG_CARD}; border: 1px solid rgba(255,255,255,0.05);
                    border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem;
                    font-size: 0.88rem; color: {TEXT_MUTED}; line-height: 1.6;">
            Clicking <strong style="color: {TEXT_PRIMARY};">Run Full Pipeline</strong>
            will automatically:
            <br>1. Preprocess the video (resize + FPS normalization)
            <br>2. Run YOLO object detection on every frame
            <br>3. Track players with ByteTrack + camera compensation
            <br>4. Segment teams, track possession, detect replays
            <br>5. Compute velocity, distance, and export all stats
            <br><br>
            The output will be an annotated video and CSV data files.
        </div>
        """, unsafe_allow_html=True)

        if st.button("Run Full Pipeline", type="primary",
                      use_container_width=True):
            progress = st.progress(0, text="Starting pipeline...")
            status = st.empty()

            try:
                result = _full_pipeline(raw_video, progress, status)
                st.session_state.analysis_done = True
                st.session_state.analysis_results = result
                st.session_state.tracked_video = result.get("output_video")

                status.empty()
                st.success("Pipeline complete. Redirecting to results...")
                st.session_state.page = "Results"
                st.rerun()

            except Exception as e:
                st.error(f"Pipeline failed: {e}")
                import traceback
                st.code(traceback.format_exc())

    # Navigation
    st.markdown("---")
    left, _, right = st.columns([1, 2, 1])
    with left:
        nav_button("Back to Upload", "Upload", key="an_back")
    with right:
        if analysis_done:
            nav_button("View Results", "Results", key="an_next")
