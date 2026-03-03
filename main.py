import cv2
import os

from src.ball_interpolator import BallInterpolator
from src.possession import PossessionTracker
from src.preprocess import preprocess_video
from src.detector import Detector
from src.team_segmentation import TeamSegmenter
from src.tracker import Tracker
from src.metadata import MetadataLogger
from src.utils import draw_boxes

RAW_VIDEO = "data/raw/168.mp4"
PROCESSED_VIDEO = "data/processed/168_processed.mp4"
MODEL_PATH = "models/best.pt"   # ✅ use your trained model

# Step 1: Preprocess
preprocess_video(RAW_VIDEO, PROCESSED_VIDEO)

# Step 2: Load modules
detector = Detector(MODEL_PATH)
tracker = Tracker()
logger = MetadataLogger("data/annotations")

team_segmenter = TeamSegmenter()
ball_interpolator = BallInterpolator()
possession_tracker = PossessionTracker()

cap = cv2.VideoCapture(PROCESSED_VIDEO)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(
    "data/processed/output.mp4",
    fourcc,
    15,
    (1280, int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
)

frame_id = 0
team_fitted = False  # ensure clustering happens once

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # ----------------------------------
    # 1️⃣ Detection
    # ----------------------------------
    detections = detector.detect(frame)

    # ----------------------------------
    # 2️⃣ Tracking
    # ----------------------------------
    tracked = tracker.update(detections if detections is not None else None)

    if not tracked:
        out.write(frame)
        frame_id += 1
        continue

    # ----------------------------------
    # 3️⃣ Separate Players & Ball
    # ----------------------------------
    players = []
    balls = []

    for obj in tracked:
        # assuming:
        # obj.cls -> class id
        # obj.xyxy -> bounding box
        # obj.id -> track id

        if obj.cls == 0:   # player class
            players.append(obj)
        elif obj.cls == 1: # ball class
            balls.append(obj)

    # ----------------------------------
    # 4️⃣ Team Clustering (fit once)
    # ----------------------------------
    if not team_fitted and len(players) >= 2:
        team_segmenter.fit(frame, players)
        team_fitted = True

    for player in players:
        team_id = team_segmenter.assign_team(frame, player)
        player.team = team_id  # dynamically attach attribute

    # ----------------------------------
    # 5️⃣ Ball Interpolation
    # ----------------------------------
    ball_obj = balls[0] if len(balls) > 0 else None
    ball_position = ball_interpolator.update(frame_id, ball_obj)

    # ----------------------------------
    # 6️⃣ Possession Detection
    # ----------------------------------
    possessor_id = possession_tracker.update(ball_position, players)

    # ----------------------------------
    # 7️⃣ Visualization Enhancements
    # ----------------------------------
    annotated = frame.copy()

    # Draw players
    for player in players:
        x1, y1, x2, y2 = map(int, player.xyxy)

        if hasattr(player, "team"):
            if player.team == 0:
                color = (255, 0, 0)  # Blue
            elif player.team == 1:
                color = (0, 0, 255)  # Red
            else:
                color = (200, 200, 200)
        else:
            color = (200, 200, 200)

        # Highlight possessor
        if player.id == possessor_id:
            color = (0, 255, 255)  # Yellow highlight

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

    # Draw ball
    if ball_position is not None:
        bx, by = ball_position
        cv2.circle(annotated, (bx, by), 6, (0, 255, 0), -1)

    # ----------------------------------
    # 8️⃣ Logging
    # ----------------------------------
    logger.log(frame_id, tracked)

    out.write(annotated)
    frame_id += 1

cap.release()
out.release()
logger.save()