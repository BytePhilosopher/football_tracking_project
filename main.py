import cv2
import os
from types import SimpleNamespace

from tqdm import tqdm

from src.ball_interpolator import BallInterpolator
from src.possession import PossessionTracker
from src.detector import Detector
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

TEAM_FIT_FRAMES  = 10     # collect players from this many frames before fitting teams
PLAYER_CLASS_IDS = {1, 2, 3}   # goalkeeper=1, player=2, referee=3  (match your data.yml)
BALL_CLASS_ID    = 0

os.makedirs("data/processed",   exist_ok=True)
os.makedirs("data/annotations", exist_ok=True)

# ──────────────────────────────────────────────
# LOAD MODULES
# ──────────────────────────────────────────────
detector          = Detector(MODEL_PATH, conf=0.35, iou=0.45, imgsz=1280)
tracker           = Tracker()
logger            = MetadataLogger("data/annotations")
team_segmenter    = TeamSegmenter()
ball_interpolator = BallInterpolator()
possession_tracker = PossessionTracker()

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
# MAIN LOOP
# ──────────────────────────────────────────────
frame_id    = 0
team_fitted = False

with tqdm(total=total_frames, unit="frame", desc="Tracking") as pbar:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ── 1. Detection ──────────────────────────────
        detections = detector.detect(frame)

        # ── 2. Tracking ───────────────────────────────
        tracked = tracker.update(detections)

        if tracked is None or len(tracked) == 0:
            out.write(frame)
            frame_id += 1
            pbar.update(1)
            continue

        # ── 3. Split detections into players / balls ──
        players: list = []
        balls:   list = []

        xyxy       = tracked.xyxy
        class_ids  = tracked.class_id
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
        # Accumulate samples for the first TEAM_FIT_FRAMES frames, then fit once.
        if not team_fitted and frame_id <= TEAM_FIT_FRAMES:
            fitted = team_segmenter.fit(frame, players)
            if fitted:
                team_fitted = True

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

print(f"\nOutput video saved: {OUTPUT_VIDEO}")

# Run the post-processing data pipeline
print("\nRunning data pipeline ...")
from src.data_pipeline import run_pipeline
run_pipeline("data/annotations/tracking.csv", "data/annotations", fps=fps)
