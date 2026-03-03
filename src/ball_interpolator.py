# src/ball_interpolator.py

import numpy as np


class BallInterpolator:
    def __init__(self):
        self.last_positions = []  # [(frame_id, (x, y))]

    def update(self, frame_id, ball_obj):
        """
        ball_obj must contain xyxy
        """
        if ball_obj is not None:
            x1, y1, x2, y2 = ball_obj.xyxy
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            self.last_positions.append((frame_id, (cx, cy)))

            if len(self.last_positions) > 10:
                self.last_positions.pop(0)

            return (cx, cy)

        # If ball missing → interpolate
        if len(self.last_positions) >= 2:
            (f1, p1), (f2, p2) = self.last_positions[-2], self.last_positions[-1]

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            return (p2[0] + dx, p2[1] + dy)

        return None