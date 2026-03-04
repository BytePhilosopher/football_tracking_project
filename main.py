import cv2
import os
from types import SimpleNamespace

from src.ball_interpolator import BallInterpolator
from src.possession import PossessionTracker
from src.detector import Detector
from src.team_segmentation import TeamSegmenter
from src.tracker import Tracker
from src.metadata import MetadataLogger

# -----------------------------
# PATHS
# -----------------------------
RAW_VIDEO = "data/raw/168.mp4"
MODEL_PATH = "models/best.pt"
OUTPUT_VIDEO = "data/processed/output.mp4"

os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/annotations", exist_ok=True)

# -----------------------------
# LOAD MODULES
# -----------------------------
detector = Detector(MODEL_PATH)
tracker = Tracker()
logger = MetadataLogger("data/annotations")

team_segmenter = TeamSegmenter()
ball_interpolator = BallInterpolator()
possession_tracker = PossessionTracker()

# -----------------------------
# VIDEO SETUP
# -----------------------------
cap = cv2.VideoCapture(RAW_VIDEO)

if not cap.isOpened():
    raise RuntimeError("❌ Cannot open video.")

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(
    OUTPUT_VIDEO,
    fourcc,
    fps if fps > 0 else 25,
    (width, height)
)

print(f"Video Resolution: {width}x{height} @ {fps}fps")

frame_id = 0
team_fitted = False

# -----------------------------
# MAIN LOOP
# -----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # -------------------------
    # 1️⃣ Detection
    # -------------------------
    detections = detector.detect(frame)

    # -------------------------
    # 2️⃣ Tracking (ByteTrack via Supervision)
    # -------------------------
    tracked = tracker.update(detections)

    if tracked is None or len(tracked) == 0:
        out.write(frame)
        frame_id += 1
        continue

    players = []
    balls = []

    # -------------------------
    # 3️⃣ Extract Objects from sv.Detections
    # -------------------------
    xyxy = tracked.xyxy
    class_ids = tracked.class_id
    tracker_ids = tracked.tracker_id

    for box, cls_id, track_id in zip(xyxy, class_ids, tracker_ids):

        x1, y1, x2, y2 = box
        cls_id = int(cls_id)
        track_id = int(track_id) if track_id is not None else -1

        obj = SimpleNamespace(
            cls=cls_id,
            id=track_id,
            xyxy=[x1, y1, x2, y2]
        )

        # Class filtering based on your data.yml
        if cls_id in [1, 2, 3]:   # goalkeeper, players, referee
            players.append(obj)

        elif cls_id == 0:         # ball
            balls.append(obj)

    # -------------------------
    # 4️⃣ Team Clustering
    # -------------------------
    if not team_fitted and len(players) >= 2:
        team_segmenter.fit(frame, players)
        team_fitted = True

    for player in players:
        try:
            player.team = team_segmenter.assign_team(frame, player)
        except:
            player.team = -1

    # -------------------------
    # 5️⃣ Ball Interpolation
    # -------------------------
    ball_obj = balls[0] if len(balls) > 0 else None
    ball_position = ball_interpolator.update(frame_id, ball_obj)

    # -------------------------
    # 6️⃣ Possession Detection
    # -------------------------
    possessor_id = possession_tracker.update(ball_position, players)

    # -------------------------
    # 7️⃣ Drawing
    # -------------------------
    annotated = frame.copy()

    for player in players:
        x1, y1, x2, y2 = map(int, player.xyxy)

        # Default color
        color = (200, 200, 200)

        if hasattr(player, "team"):
            if player.team == 0:
                color = (255, 0, 0)
            elif player.team == 1:
                color = (0, 0, 255)

        if player.id == possessor_id:
            color = (0, 255, 255)

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated,
            f"ID:{player.id}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

    # Draw Ball
    if ball_position is not None:
        bx, by = map(int, ball_position)
        cv2.circle(annotated, (bx, by), 6, (0, 255, 0), -1)

    # -------------------------
    # 8️⃣ Logging
    # -------------------------
    logger.log(frame_id, tracked)

    out.write(annotated)
    frame_id += 1

# -----------------------------
# CLEANUP
# -----------------------------
cap.release()
out.release()
logger.save()

print("✅ Processing complete. Output saved to:", OUTPUT_VIDEO)