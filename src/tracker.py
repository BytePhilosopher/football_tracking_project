# src/tracker.py
import supervision as sv
import numpy as np


class Tracker:
    def __init__(self):
        # Tuned for football: longer track buffer handles occlusions,
        # lower minimum hits avoids delay, tighter IoU for dense scenes.
        self.tracker = sv.ByteTrack(
            track_activation_threshold=0.35,
            lost_track_buffer=60,       # ~2 s at 30 fps before ID is retired
            minimum_matching_threshold=0.8,
            minimum_consecutive_frames=2,
        )

    def update(self, detections):
        """
        detections: ultralytics.engine.results.Boxes
        Returns sv.Detections with tracker_id populated.
        """
        if detections is not None and len(detections) > 0:
            xyxy       = detections.xyxy.cpu().numpy()
            confidence = detections.conf.cpu().numpy()
            class_id   = detections.cls.cpu().numpy().astype(int)
            sv_detections = sv.Detections(
                xyxy=xyxy,
                confidence=confidence,
                class_id=class_id,
            )
        else:
            sv_detections = sv.Detections(
                xyxy=np.empty((0, 4)),
                confidence=np.array([]),
                class_id=np.array([], dtype=int),
            )

        return self.tracker.update_with_detections(sv_detections)
