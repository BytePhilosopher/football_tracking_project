# src/tracker.py
"""
ByteTrack wrapper with optional camera-motion compensation.

When a camera_shift (dx, dy) is supplied (from CameraCompensation.update),
the detection boxes are translated into a camera-stabilised coordinate frame
before being passed to ByteTrack, then translated back afterwards.  This
ensures the Kalman-filter predictions inside ByteTrack are not systematically
wrong after a camera pan, reducing ID switches on broadcast footage.
"""
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

    def update(
        self,
        detections,
        camera_shift: tuple[float, float] = (0.0, 0.0),
    ):
        """
        detections    : ultralytics.engine.results.Boxes
        camera_shift  : (dx, dy) camera translation from CameraCompensation
        Returns sv.Detections with tracker_id populated and xyxy in the
        original (un-stabilised) frame coordinates.
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

        dx, dy = camera_shift
        shift  = np.array([dx, dy, dx, dy], dtype=np.float32)

        if (dx != 0.0 or dy != 0.0) and len(sv_detections) > 0:
            # Stabilise: move boxes into a camera-fixed reference frame
            sv_detections.xyxy = sv_detections.xyxy - shift

        tracked = self.tracker.update_with_detections(sv_detections)

        if (dx != 0.0 or dy != 0.0) and len(tracked) > 0:
            # Restore to original screen coordinates for visualisation
            tracked.xyxy = tracked.xyxy + shift

        return tracked
