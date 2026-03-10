# src/ball_interpolator.py

import numpy as np
from collections import deque


class BallInterpolator:
    """
    Tracks ball position with smoothed velocity-based extrapolation.

    Improvements over the original:
    - Keeps a rolling window of the last `history` detections.
    - Velocity is averaged over the last `vel_window` steps for stability.
    - Extrapolation is capped at `max_gap` frames; after that returns None
      so the caller knows the ball is genuinely lost.
    - Velocity decays slightly each missed frame (ball slows when unseen).
    """

    def __init__(self, history: int = 20, vel_window: int = 5, max_gap: int = 15, decay: float = 0.92):
        self.history    = history       # number of detected positions to remember
        self.vel_window = vel_window    # frames used to estimate velocity
        self.max_gap    = max_gap       # give up extrapolation after this many missed frames
        self.decay      = decay         # per-frame velocity decay when extrapolating

        self._positions: deque = deque(maxlen=history)  # (frame_id, cx, cy)
        self._gap       = 0             # consecutive frames without detection
        self._extrap_pos = None         # last extrapolated position
        self._extrap_vel = None         # (vx, vy) used during extrapolation

    # ------------------------------------------------------------------
    def update(self, frame_id: int, ball_obj) -> tuple | None:
        if ball_obj is not None:
            x1, y1, x2, y2 = ball_obj.xyxy
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            self._positions.append((frame_id, cx, cy))
            self._gap        = 0
            self._extrap_pos = None
            self._extrap_vel = None
            return (cx, cy)

        # ---- ball missing ----
        self._gap += 1

        if self._gap > self.max_gap or len(self._positions) < 2:
            return None

        # Compute / propagate velocity
        if self._extrap_vel is None:
            self._extrap_vel = self._estimate_velocity()
            last = self._positions[-1]
            self._extrap_pos = np.array([last[1], last[2]], dtype=float)
        else:
            # Apply decay each frame we extrapolate
            self._extrap_vel = (self._extrap_vel[0] * self.decay,
                                self._extrap_vel[1] * self.decay)

        self._extrap_pos = (
            self._extrap_pos[0] + self._extrap_vel[0],
            self._extrap_pos[1] + self._extrap_vel[1],
        )
        return (float(self._extrap_pos[0]), float(self._extrap_pos[1]))

    # ------------------------------------------------------------------
    def _estimate_velocity(self):
        """Average velocity over the last `vel_window` detected positions."""
        pts = list(self._positions)
        n   = min(self.vel_window, len(pts) - 1)
        vxs, vys = [], []
        for i in range(len(pts) - n, len(pts)):
            f0, x0, y0 = pts[i - 1]
            f1, x1, y1 = pts[i]
            df = max(1, f1 - f0)
            vxs.append((x1 - x0) / df)
            vys.append((y1 - y0) / df)
        return float(np.mean(vxs)), float(np.mean(vys))

    # ------------------------------------------------------------------
    @property
    def is_interpolating(self) -> bool:
        return self._gap > 0 and self._extrap_pos is not None
