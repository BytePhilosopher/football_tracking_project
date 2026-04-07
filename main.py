import cv2
import os
from types import SimpleNamespace

from tqdm import tqdm

from src.ball_interpolator import BallInterpolator
from src.camera_compensation import CameraCompensation
from src.possession import PossessionTracker
from src.detector import Detector
from src.replay_detector import ReplayDetector
from src.team_segmentation import TeamSegmenter
from src.tracker import Tracker
from src.metadata import MetadataLogger
from src.utils import draw_player, draw_ball, draw_hud

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
RAW_VIDEO    = "data/raw/168.mp4"
MODEL_PATH   = "models/best.pt"
OUTPUT_VIDEO = "data/processed/168_tracked.mp4"

PLAYER_CLASS_IDS = {1, 2, 3}   # goalkeeper=1, player=2, referee=3
BALL_CLASS_ID    = 0

os.makedirs("data/processed",   exist_ok=True)
os.makedirs("data/annotations", exist_ok=True)

# ──────────────────────────────────────────────
# LOAD MODULES
# ──────────────────────────────────────────────
detector           = Detector(MODEL_PATH, conf=0.35, iou=0.45, imgsz=1280)
tracker            = Tracker()
cam_comp           = CameraCompensation()
replay_detector    = ReplayDetector(
    hist_threshold=0.70,   # correlation < 0.70  → scene cut
    flow_threshold=25.0,   # |flow| > 25 px/frame → scene cut
    entry_frames=3,        # 3 consecutive cut frames to enter replay
    exit_frames=4,         # 4 consecutive live frames to exit replay
    cooldown_frames=8,     # skip 8 frames after replay ends (transition frames)
)
logger             = MetadataLogger("data/annotations")
team_segmenter     = TeamSegmenter()
ball_interpolator  = BallInterpolator()
possession_tracker = PossessionTracker(Tin=50, Tout=70, K=5)

# ──────────────────────────────────────────────
# VIDEO SETUP
# ──────────────────────────────────────────────
cap = cv2.VideoCapture(RAW_VIDEO)
if not cap.isOpened():
    raise RuntimeError("Cannot open video: " + RAW_VIDEO)

width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps    = cap.get(cv2.CAP_PROP_FPS) or 25.0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out    = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, fps, (width, height))

print(f"Input  : {RAW_VIDEO}")
print(f"Output : {OUTPUT_VIDEO}")
print(f"Video  : {width}x{height} @ {fps:.1f} fps  ({total_frames} frames)")

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def reset_stateful_components():
    """
    Called at every replay boundary (entry AND exit).

    Clears all state that accumulates across frames so that the pipeline
    starts fresh when live play resumes:
      - ByteTrack: discards all active tracks; IDs restart from where they
        left off before the replay (avoids ghost tracks).
      - BallInterpolator: forgets velocity history so it doesn't extrapolate
        using pre-replay ball motion.
      - PossessionTracker: resets possession candidate; prevents awarding
        possession based on stale pre-replay state.
      - CameraCompensation: forces feature re-detection on the next live
        frame so the flow estimate starts clean.
    """
    tracker.tracker.reset()
    ball_interpolator.__init__(
        history=ball_interpolator.history,
        vel_window=ball_interpolator.vel_window,
        max_gap=ball_interpolator.max_gap,
        decay=ball_interpolator.decay,
    )
    possession_tracker._reset_candidate()
    possession_tracker.current_possessor = None
    possession_tracker.current_team      = None
    cam_comp._prev_gray = None
    cam_comp._prev_pts  = None


# ──────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────
frame_id        = 0
team_fitted     = False
prev_in_replay  = False   # track transitions to call reset at boundaries

with tqdm(total=total_frames, unit="frame", desc="Tracking") as pbar:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ── 1b. Camera-motion compensation ────────────
        # Must run before replay detection so we can pass flow magnitude.
        camera_shift   = cam_comp.update(frame)
        flow_magnitude = (camera_shift[0] ** 2 + camera_shift[1] ** 2) ** 0.5

        # ── 1c. Replay detection ───────────────────────
        in_replay = replay_detector.update(frame, frame_id, flow_magnitude)

        # Reset state at every replay boundary (entry and exit)
        if in_replay != prev_in_replay:
            reset_stateful_components()
            if in_replay:
                tqdm.write(f"[ReplayDetector] Replay started at frame {frame_id}")
            else:
                tqdm.write(f"[ReplayDetector] Replay ended   at frame {frame_id}")
        prev_in_replay = in_replay

        # Skip replay frames entirely — write the raw frame for visual continuity
        if in_replay:
            out.write(frame)
            frame_id += 1
            pbar.update(1)
            continue

        # ── 1. Detection ──────────────────────────────
        detections = detector.detect(frame)

        # ── 2. Tracking ───────────────────────────────
        tracked = tracker.update(detections, camera_shift)

        if tracked is None or len(tracked) == 0:
            out.write(frame)
            frame_id += 1
            pbar.update(1)
            continue

        # ── 3. Split detections into players / balls ──
        players: list = []
        balls:   list = []

        xyxy        = tracked.xyxy
        class_ids   = tracked.class_id
        tracker_ids = tracked.tracker_id
        confidences = tracked.confidence if tracked.confidence is not None else [None] * len(xyxy)

        for box, cls_id, track_id, conf in zip(xyxy, class_ids, tracker_ids, confidences):
            x1, y1, x2, y2 = box
            cls_id   = int(cls_id)
            track_id = int(track_id) if track_id is not None else -1

            obj = SimpleNamespace(
                cls=cls_id,
                id=track_id,
                xyxy=[x1, y1, x2, y2],
                conf=float(conf) if conf is not None else 0.0,
                team=-1,
            )

            if cls_id in PLAYER_CLASS_IDS:
                players.append(obj)
            elif cls_id == BALL_CLASS_ID:
                balls.append(obj)

        # ── 4. Team segmentation ──────────────────────
        if not team_fitted:
            team_fitted = team_segmenter.fit(frame, players)

        for player in players:
            player.team = team_segmenter.assign_team(frame, player)

        # ── 5. Ball interpolation ─────────────────────
        ball_obj      = balls[0] if balls else None
        ball_position = ball_interpolator.update(frame_id, ball_obj)
        ball_interp   = ball_interpolator.is_interpolating

        # ── 6. Possession ─────────────────────────────
        possessor_id = possession_tracker.update(ball_position, players)

        # ── 7. Draw ───────────────────────────────────
        annotated = frame.copy()

        for player in players:
            draw_player(annotated, player, possessor_id)

        draw_ball(annotated, ball_position, interpolated=ball_interp)

        poss_pct = possession_tracker.possession_percentages()
        draw_hud(annotated, frame_id, fps, poss_pct)

        # ── 8. Log ────────────────────────────────────
        logger.log(
            frame_id,
            tracked,
            players=players,
            possessor_id=possessor_id,
            ball_position=ball_position,
            ball_interpolated=ball_interp,
        )

        out.write(annotated)
        frame_id += 1
        pbar.update(1)

# ──────────────────────────────────────────────
# CLEANUP & PIPELINE
# ──────────────────────────────────────────────
cap.release()
out.release()
logger.save()

replay_stats = replay_detector.stats
print(f"\nOutput video saved: {OUTPUT_VIDEO}")
print(f"Replays detected  : {replay_stats['n_replays']}")
print(f"Replay frames skipped: {replay_stats['n_replay_frames']}")

# Run the post-processing data pipeline
print("\nRunning data pipeline ...")
from src.data_pipeline import run_pipeline
run_pipeline("data/annotations/tracking.csv", "data/annotations", fps=fps)
