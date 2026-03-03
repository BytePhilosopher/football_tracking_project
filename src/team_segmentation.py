# src/team_segmentation.py

import cv2
import numpy as np
from sklearn.cluster import KMeans


class TeamSegmenter:
    def __init__(self, n_clusters=2):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.team_colors = None  # HSV centroids

    def _extract_dominant_color(self, crop):
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        # Ignore bottom half (reduce grass influence)
        h, w, _ = hsv.shape
        upper_half = hsv[:h // 2, :]

        pixels = upper_half.reshape(-1, 3)

        # Remove low-saturation pixels (grass noise reduction)
        pixels = pixels[pixels[:, 1] > 40]

        if len(pixels) < 10:
            return None

        mean_color = np.mean(pixels, axis=0)
        return mean_color

    def fit(self, frame, tracked_players):
        """
        Fit clustering once using first frame players.
        """
        colors = []

        for obj in tracked_players:
            x1, y1, x2, y2 = map(int, obj.xyxy)
            crop = frame[y1:y2, x1:x2]

            if crop.size == 0:
                continue

            color = self._extract_dominant_color(crop)
            if color is not None:
                colors.append(color)

        if len(colors) < 2:
            return

        self.kmeans = KMeans(n_clusters=self.n_clusters, n_init=10)
        self.kmeans.fit(colors)
        self.team_colors = self.kmeans.cluster_centers_

    def assign_team(self, frame, player_obj):
        """
        Assign team label to a player.
        Returns team_id (0 or 1)
        """
        if self.kmeans is None:
            return None

        x1, y1, x2, y2 = map(int, player_obj.xyxy)
        crop = frame[y1:y2, x1:x2]

        if crop.size == 0:
            return None

        color = self._extract_dominant_color(crop)
        if color is None:
            return None

        team_id = self.kmeans.predict([color])[0]
        return int(team_id)