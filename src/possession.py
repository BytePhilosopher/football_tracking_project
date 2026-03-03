# src/possession.py

import numpy as np


class PossessionTracker:
    def __init__(self, distance_threshold=50):
        self.distance_threshold = distance_threshold
        self.current_possessor = None

    def update(self, ball_position, tracked_players):
        """
        ball_position: (x, y)
        tracked_players: list of player objects with id and xyxy
        """
        if ball_position is None:
            return self.current_possessor

        min_dist = float("inf")
        possessor_id = None

        bx, by = ball_position

        for player in tracked_players:
            x1, y1, x2, y2 = player.xyxy
            px = int((x1 + x2) / 2)
            py = int((y1 + y2) / 2)

            dist = np.sqrt((px - bx) ** 2 + (py - by) ** 2)

            if dist < min_dist:
                min_dist = dist
                possessor_id = player.id

        if min_dist < self.distance_threshold:
            self.current_possessor = possessor_id

        return self.current_possessor