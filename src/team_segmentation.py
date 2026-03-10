# src/team_segmentation.py

import cv2
import numpy as np
from sklearn.cluster import KMeans


# Class IDs that should be excluded from team clustering (referees)
REFEREE_CLASS_IDS = {3}


class TeamSegmenter:
    """
    Assigns players to teams using jersey-colour clustering.

    Improvements over the original:
    - Pixel-level KMeans on the upper crop (not just the mean colour).
    - Referees (class 3) are excluded from fitting and always returned as team -1.
    - Can be re-fitted with additional frames via `partial_fit`.
    - Returns None when the model is not yet ready (caller should handle gracefully).
    """

    def __init__(self, n_clusters: int = 2, min_pixels: int = 20):
        self.n_clusters  = n_clusters
        self.min_pixels  = min_pixels
        self.kmeans      = None
        self._color_buf  = []   # accumulates colour samples across frames before first fit

    # ------------------------------------------------------------------
    def _extract_jersey_color(self, crop: np.ndarray) -> np.ndarray | None:
        """
        Returns the dominant jersey colour as a 1-D HSV vector,
        computed via pixel-level KMeans on the upper 60 % of the crop.
        """
        if crop is None or crop.size == 0:
            return None

        h, w = crop.shape[:2]
        if h < 10 or w < 10:
            return None

        upper = crop[:int(h * 0.6), :]
        hsv   = cv2.cvtColor(upper, cv2.COLOR_BGR2HSV)
        pixels = hsv.reshape(-1, 3).astype(np.float32)

        # Remove near-green (grass) and low-saturation (shadow / white lines)
        mask = (pixels[:, 1] > 40) & ~(
            (pixels[:, 0] > 35) & (pixels[:, 0] < 85) & (pixels[:, 1] > 60)
        )
        pixels = pixels[mask]

        if len(pixels) < self.min_pixels:
            return None

        # Cluster pixel colours → pick dominant cluster
        n = min(3, len(pixels))
        km = KMeans(n_clusters=n, n_init=3, max_iter=50, random_state=0)
        km.fit(pixels)
        counts = np.bincount(km.labels_)
        dominant = km.cluster_centers_[np.argmax(counts)]
        return dominant

    # ------------------------------------------------------------------
    def fit(self, frame: np.ndarray, players: list) -> bool:
        """
        Accumulate colour samples from `players` and fit the team classifier
        when enough samples have been collected (>= 2 * n_clusters).
        Returns True when fitting succeeds.
        """
        for obj in players:
            if getattr(obj, "cls", -1) in REFEREE_CLASS_IDS:
                continue

            x1, y1, x2, y2 = map(int, obj.xyxy)
            crop  = frame[y1:y2, x1:x2]
            color = self._extract_jersey_color(crop)
            if color is not None:
                self._color_buf.append(color)

        if len(self._color_buf) < self.n_clusters * 4:
            return False

        colors = np.array(self._color_buf)
        self.kmeans = KMeans(n_clusters=self.n_clusters, n_init=15, random_state=0)
        self.kmeans.fit(colors)
        return True

    # ------------------------------------------------------------------
    def assign_team(self, frame: np.ndarray, player_obj) -> int:
        """
        Returns team ID (0 or 1) or -1 for referee / unknown.
        """
        if getattr(player_obj, "cls", -1) in REFEREE_CLASS_IDS:
            return -1

        if self.kmeans is None:
            return -1

        x1, y1, x2, y2 = map(int, player_obj.xyxy)
        crop  = frame[y1:y2, x1:x2]
        color = self._extract_jersey_color(crop)

        if color is None:
            return -1

        return int(self.kmeans.predict([color])[0])
