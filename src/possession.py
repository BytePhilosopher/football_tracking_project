# src/possession.py

import numpy as np
from collections import defaultdict


class PossessionTracker:
    """
    Determines which player has possession and tracks team-level stats.

    Improvements over the original:
    - Uses feet position (bottom-centre of bounding box) instead of the
      centroid, which is more physically meaningful for ball proximity.
    - Adds hysteresis: the current possessor keeps the ball until another
      player is at least `hysteresis` pixels closer, reducing flickering.
    - Maintains frame-level possession counts per team for HUD display.
    """

    def __init__(self, distance_threshold: int = 60, hysteresis: int = 15):
        self.distance_threshold = distance_threshold
        self.hysteresis         = hysteresis

        self.current_possessor   = None   # tracker_id
        self.current_team        = None   # team_id of possessor
        self.possession_frames: dict[int, int] = defaultdict(int)  # team_id → frame count

    # ------------------------------------------------------------------
    def update(self, ball_position, tracked_players: list):
        """
        ball_position : (x, y) or None
        tracked_players : list of SimpleNamespace with .id, .xyxy, .team
        Returns tracker_id of current possessor (may be None).
        """
        if ball_position is None or not tracked_players:
            # Accumulate time for the last known possessor's team
            if self.current_team is not None and self.current_team >= 0:
                self.possession_frames[self.current_team] += 1
            return self.current_possessor

        bx, by = ball_position
        min_dist      = float("inf")
        best_id       = None
        best_team     = None

        for player in tracked_players:
            x1, _, x2, y2 = player.xyxy
            # Feet position = bottom-centre of bounding box
            px = (x1 + x2) / 2.0
            py = float(y2)
            dist = np.hypot(px - bx, py - by)

            if dist < min_dist:
                min_dist  = dist
                best_id   = player.id
                best_team = getattr(player, "team", -1)

        # Hysteresis: only switch possessor if the new candidate is
        # meaningfully closer, or if we had no possessor yet.
        if min_dist < self.distance_threshold:
            if self.current_possessor is None or best_id == self.current_possessor:
                self.current_possessor = best_id
                self.current_team      = best_team
            else:
                # Compute distance of current possessor to ball
                cur_dist = self._distance_of(self.current_possessor, bx, by, tracked_players)
                if cur_dist is None or (min_dist + self.hysteresis) < cur_dist:
                    self.current_possessor = best_id
                    self.current_team      = best_team

        if self.current_team is not None and self.current_team >= 0:
            self.possession_frames[self.current_team] += 1

        return self.current_possessor

    # ------------------------------------------------------------------
    def possession_percentages(self) -> dict[int, float]:
        """Returns {team_id: percentage} for all teams seen."""
        total = sum(self.possession_frames.values())
        if total == 0:
            return {}
        return {t: 100.0 * v / total for t, v in self.possession_frames.items()}

    # ------------------------------------------------------------------
    @staticmethod
    def _distance_of(target_id, bx, by, players):
        for p in players:
            if p.id == target_id:
                x1, _, x2, y2 = p.xyxy
                px = (x1 + x2) / 2.0
                py = float(y2)
                return np.hypot(px - bx, py - by)
        return None
