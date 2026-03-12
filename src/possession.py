# src/possession.py
"""
Ball possession tracker with Tin/Tout hysteresis and minimum-switch-duration.

Based on the paper's possession model (§3.4):
  - A player *enters* possession when their feet distance to ball < Tin.
  - The current possessor *loses* possession when their distance > Tout.
    (Tout > Tin creates a hysteresis band that suppresses flickering.)
  - A new candidate must remain the closest player for K consecutive frames
    before possession is transferred.  From Table 4: K too small → oscillation;
    K too large → misses real transitions.  Default K=5 is a robust starting
    point from the paper's sensitivity analysis.
"""

import numpy as np
from collections import defaultdict


class PossessionTracker:
    """
    Determines which player has possession and tracks team-level statistics.

    Parameters
    ----------
    Tin  : float  Distance (px) to *enter* possession.
    Tout : float  Distance (px) to *exit* possession.  Must be ≥ Tin.
    K    : int    Minimum consecutive frames a new candidate must be closest
                  before the current possessor is replaced.
    """

    def __init__(
        self,
        Tin:  float = 50,   # pixels — enter possession
        Tout: float = 70,   # pixels — exit possession  (Tout ≥ Tin)
        K:    int   = 5,    # consecutive frames to confirm a switch
    ):
        assert Tout >= Tin, "Tout must be ≥ Tin"
        self.Tin  = Tin
        self.Tout = Tout
        self.K    = K

        self.current_possessor: int | None = None
        self.current_team:      int | None = None

        # Rolling candidate (proposed new possessor before K frames confirm)
        self._candidate_id:     int | None = None
        self._candidate_frames: int        = 0

        self.possession_frames: dict[int, int] = defaultdict(int)

    # ── update ──────────────────────────────────────────────────────────────

    def update(self, ball_position, tracked_players: list) -> int | None:
        """
        ball_position   : (x, y) or None
        tracked_players : list of SimpleNamespace with .id, .xyxy, .team
        Returns tracker_id of the current possessor (may be None).
        """
        if ball_position is None or not tracked_players:
            if self.current_team is not None and self.current_team >= 0:
                self.possession_frames[self.current_team] += 1
            return self.current_possessor

        bx, by    = ball_position
        min_dist  = float("inf")
        best_id   = None
        best_team = None

        for player in tracked_players:
            x1, _, x2, y2 = player.xyxy
            px = (x1 + x2) / 2.0
            py = float(y2)          # feet position (bottom-centre of bbox)
            d  = np.hypot(px - bx, py - by)
            if d < min_dist:
                min_dist  = d
                best_id   = player.id
                best_team = getattr(player, "team", -1)

        # ── state machine ───────────────────────────────────────────────────

        if self.current_possessor is None:
            # No active possessor — award immediately if within Tin
            if min_dist < self.Tin:
                self.current_possessor = best_id
                self.current_team      = best_team
                self._reset_candidate()

        else:
            cur_dist = self._distance_of(
                self.current_possessor, bx, by, tracked_players
            )

            if best_id == self.current_possessor:
                # Same player still closest — keep possession unconditionally
                self._reset_candidate()

            elif cur_dist is not None and cur_dist <= self.Tout:
                # Current possessor is still within Tout; someone else is
                # closer — accumulate K frames before switching.
                if min_dist < self.Tin:
                    if best_id == self._candidate_id:
                        self._candidate_frames += 1
                    else:
                        self._candidate_id     = best_id
                        self._candidate_frames = 1

                    if self._candidate_frames >= self.K:
                        self.current_possessor = self._candidate_id
                        self.current_team      = best_team
                        self._reset_candidate()
                else:
                    self._reset_candidate()

            else:
                # Current possessor left the Tout zone
                if min_dist < self.Tin:
                    self.current_possessor = best_id
                    self.current_team      = best_team
                else:
                    self.current_possessor = None
                    self.current_team      = None
                self._reset_candidate()

        # ── accumulate team possession frames ────────────────────────────
        if self.current_team is not None and self.current_team >= 0:
            self.possession_frames[self.current_team] += 1

        return self.current_possessor

    # ── utilities ───────────────────────────────────────────────────────────

    def possession_percentages(self) -> dict[int, float]:
        """Returns {team_id: percentage} for all teams seen."""
        total = sum(self.possession_frames.values())
        if total == 0:
            return {}
        return {t: 100.0 * v / total for t, v in self.possession_frames.items()}

    def _reset_candidate(self) -> None:
        self._candidate_id     = None
        self._candidate_frames = 0

    @staticmethod
    def _distance_of(target_id, bx, by, players):
        for p in players:
            if p.id == target_id:
                x1, _, x2, y2 = p.xyxy
                return np.hypot((x1 + x2) / 2.0 - bx, float(y2) - by)
        return None
