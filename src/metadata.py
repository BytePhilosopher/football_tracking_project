# src/metadata.py

import os
import csv
from supervision.detection.core import Detections


TRACKING_HEADER = [
    "frame_id", "object_id", "class_id", "confidence",
    "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2",
    "feet_x", "feet_y",
    "team_id", "has_possession",
    "ball_x", "ball_y", "ball_interpolated",
]


class MetadataLogger:
    """
    Logs per-frame tracking data to CSV.

    Improvements over the original:
    - Writes tracking.csv with full context: team, possession flag,
      ball position, feet position, and whether ball was interpolated.
    - Flushes every N frames to avoid total data loss on crash.
    - Separate metadata.csv (legacy) and tracking.csv (enriched pipeline).
    """

    def __init__(self, output_dir: str = "data/annotations", flush_every: int = 100):
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir  = output_dir
        self.flush_every = flush_every

        self._tracking_path = os.path.join(output_dir, "tracking.csv")
        self._meta_path     = os.path.join(output_dir, "metadata.csv")

        # Open tracking.csv immediately and write header
        self._tracking_file   = open(self._tracking_path, "w", newline="")
        self._tracking_writer = csv.writer(self._tracking_file)
        self._tracking_writer.writerow(TRACKING_HEADER)

        # Legacy metadata buffer
        self._meta_rows: list = []
        self._meta_header = [
            "frame_id", "object_id", "class_id", "confidence",
            "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2",
        ]
        self._frame_count = 0

    # ------------------------------------------------------------------
    def log(
        self,
        frame_id: int,
        detections: Detections,
        players: list | None = None,
        possessor_id: int | None = None,
        ball_position: tuple | None = None,
        ball_interpolated: bool = False,
    ):
        """
        Parameters
        ----------
        frame_id          : current frame index
        detections        : sv.Detections (tracked)
        players           : list of SimpleNamespace with .id, .team
        possessor_id      : tracker_id of the player with possession
        ball_position     : (bx, by) or None
        ball_interpolated : True when ball_position was extrapolated
        """
        team_map: dict[int, int] = {}
        if players:
            for p in players:
                team_map[p.id] = getattr(p, "team", -1)

        bx       = ball_position[0] if ball_position else ""
        by       = ball_position[1] if ball_position else ""
        b_interp = int(ball_interpolated) if ball_position else ""

        if detections.tracker_id is not None:
            for i in range(len(detections.xyxy)):
                obj_id     = int(detections.tracker_id[i])
                class_id   = int(detections.class_id[i])
                confidence = float(detections.confidence[i])
                x1, y1, x2, y2 = detections.xyxy[i]
                feet_x   = (x1 + x2) / 2.0
                feet_y   = float(y2)
                team_id  = team_map.get(obj_id, -1)
                has_poss = int(obj_id == possessor_id) if possessor_id is not None else 0

                self._tracking_writer.writerow([
                    frame_id, obj_id, class_id, round(confidence, 4),
                    round(float(x1), 1), round(float(y1), 1),
                    round(float(x2), 1), round(float(y2), 1),
                    round(feet_x, 1), round(feet_y, 1),
                    team_id, has_poss,
                    round(float(bx), 1) if bx != "" else "",
                    round(float(by), 1) if by != "" else "",
                    b_interp,
                ])

                self._meta_rows.append([
                    frame_id, obj_id, class_id, round(confidence, 4),
                    round(float(x1), 1), round(float(y1), 1),
                    round(float(x2), 1), round(float(y2), 1),
                ])

        self._frame_count += 1
        if self._frame_count % self.flush_every == 0:
            self._tracking_file.flush()

    # ------------------------------------------------------------------
    def save(self):
        """Flush tracking.csv and write legacy metadata.csv."""
        self._tracking_file.flush()
        self._tracking_file.close()

        with open(self._meta_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self._meta_header)
            writer.writerows(self._meta_rows)

        print(f"Tracking data     -> {self._tracking_path}")
        print(f"Metadata (legacy) -> {self._meta_path}")

    def close(self):
        self.save()
