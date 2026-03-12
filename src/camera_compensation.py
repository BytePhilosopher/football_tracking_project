# src/camera_compensation.py
"""
Optical-flow-based camera-motion compensation for broadcast football footage.

Motivation (paper §3.1 / Norfair + optical flow):
  In broadcast footage the camera constantly pans and zooms to follow the
  ball.  Without compensation, a tracker's Kalman-filter predictions are
  anchored to absolute pixel positions and will therefore be systematically
  wrong after each camera movement, causing ID switches and lost tracks.

  This module estimates the dominant inter-frame camera translation with
  sparse Lucas-Kanade optical flow on background feature points (grass,
  stands).  The median flow vector of all tracked points is used — the
  median is robust against foreground motion (players, ball) which appears
  as outliers.

Usage (in main.py):
    cam_comp = CameraCompensation()
    ...
    camera_shift = cam_comp.update(frame)   # returns (dx, dy) in pixels
    tracked      = tracker.update(detections, camera_shift)
"""

import cv2
import numpy as np


class CameraCompensation:
    """
    Estimates inter-frame camera translation using sparse Lucas-Kanade
    optical flow.

    Feature points are detected with Shi-Tomasi corner detection and
    re-detected whenever the tracked count falls below MIN_FEATURES or
    every REFRESH_EVERY frames (to stay on background features and avoid
    accumulating drift).
    """

    MAX_FEATURES  = 200    # maximum feature points to track per frame
    MIN_FEATURES  = 30     # re-detect features when count falls below this
    REFRESH_EVERY = 30     # force re-detection every N frames
    LK_WIN_SIZE   = (21, 21)

    def __init__(self):
        self._prev_gray:   np.ndarray | None = None
        self._prev_pts:    np.ndarray | None = None   # shape (N, 1, 2) float32
        self._frame_count: int = 0

        self._feature_params = dict(
            maxCorners  = self.MAX_FEATURES,
            qualityLevel= 0.01,
            minDistance = 10,
            blockSize   = 7,
        )
        self._lk_params = dict(
            winSize  = self.LK_WIN_SIZE,
            maxLevel = 3,
            criteria = (
                cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 0.03
            ),
        )

    # ── public API ──────────────────────────────────────────────────────────

    def update(self, frame: np.ndarray) -> tuple[float, float]:
        """
        Feed the current BGR frame; returns the estimated camera translation
        (dx, dy) in pixels since the previous frame.

        Returns (0.0, 0.0) on the first call (no previous frame available)
        or when tracking quality is too low.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self._frame_count += 1

        need_redetect = (
            self._prev_gray is None
            or self._prev_pts is None
            or len(self._prev_pts) < self.MIN_FEATURES
            or self._frame_count % self.REFRESH_EVERY == 0
        )

        if need_redetect:
            self._prev_pts  = cv2.goodFeaturesToTrack(
                gray, **self._feature_params
            )
            self._prev_gray = gray
            return 0.0, 0.0

        # Sparse LK optical flow
        curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(
            self._prev_gray, gray,
            self._prev_pts, None,
            **self._lk_params,
        )

        dx, dy = 0.0, 0.0

        if curr_pts is not None and status is not None:
            good_prev = self._prev_pts[status == 1]
            good_curr = curr_pts[status == 1]

            if len(good_curr) >= 4:
                flow = good_curr - good_prev          # (N, 2)
                # Median is robust to foreground objects (players moving)
                dx = float(np.median(flow[:, 0]))
                dy = float(np.median(flow[:, 1]))
                # Keep only successfully tracked points for the next frame
                self._prev_pts = good_curr.reshape(-1, 1, 2)
            else:
                # Too few surviving points — force re-detection next frame
                self._prev_pts = None

        self._prev_gray = gray
        return dx, dy
