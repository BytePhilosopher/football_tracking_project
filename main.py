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

# Optional: get class name mapping if available
class_names = None
if hasattr(detector, "model") and hasattr(detector.model, "names"):
    class_names = detector.model.names

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
    # 2️⃣ Tracking
    # -------------------------
    tracked = tracker.update(detections if detections is not None else [])

    if not tracked:
        out.write(frame)
        frame_id += 1
        continue

    players = []
    balls = []

    # -------------------------
    # 3️⃣ Separate Objects
    # -------------------------
    for obj in tracked:

        # If tracker returns tuples instead of objects
        if isinstance(obj, (tuple, list)):
            nums = [x for x in obj if isinstance(x, (int, float))]
            if len(nums) >= 4:
                xyxy = nums[:4]
            else:
                continue

            cls = int(obj[0]) if len(obj) > 0 else -1
            tid = int(obj[1]) if len(obj) > 1 else -1

            obj = SimpleNamespace(cls=cls, id=tid, xyxy=xyxy)

        if not hasattr(obj, "cls") or not hasattr(obj, "xyxy"):
            continue

        # Use class names if available
        if class_names:
            cls_name = class_names.get(obj.cls, "")
            if cls_name.lower() == "player":
                players.append(obj)
            elif cls_name.lower() == "ball":
                balls.append(obj)
        else:
            # Fallback (modify if your classes differ)
            if obj.cls == 0:
                players.append(obj)
            elif obj.cls == 1:
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