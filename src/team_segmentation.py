# src/team_segmentation.py

import cv2
import numpy as np
from sklearn.cluster import KMeans


# Class IDs for referees — excluded from team clustering
REFEREE_CLASS_IDS = {3}


class TeamSegmenter:
    """
    Assigns players to teams using jersey-colour clustering (KMeans, k=2).

    The model only labels ball / goalkeeper / player / referee — it does NOT
    label teams.  This module recovers team identity from jersey colour.

    Key design choices
    ------------------
    - Colour feature = mean HSV of the upper-body crop, after masking grass
      (saturated green pixels in OpenCV HSV hue 35-85, saturation > 80).
      We deliberately keep dark, grey, and white jerseys — only vivid grass
      is removed.
    - No per-crop KMeans (previous approach) — it failed for small/distant
      bounding boxes where only a handful of pixels survive.
    - Fitting accumulates samples across as many frames as needed until
      min_samples (default 12) distinct player crops are collected.
    - After the first successful fit, assignment runs every frame.
    - Referees always get team -1.
    """

    def __init__(self, n_clusters: int = 2, min_samples: int = 12):
        self.n_clusters  = n_clusters
        self.min_samples = min_samples
        self.kmeans: KMeans | None = None
        self._color_buf: list[np.ndarray] = []

    # ── colour extraction ──────────────────────────────────────────────────

    def _extract_jersey_color(self, crop: np.ndarray) -> np.ndarray | None:
        """
        Returns a 3-element HSV mean vector representing the jersey colour,
        or None if the crop is unusable.

        Uses only the top 55 % of the bounding box (chest/shoulders area)
        and masks out grass-green pixels.  The remaining pixels — including
        dark, white, and grey jerseys — are averaged.
        """
        if crop is None or crop.size == 0:
            return None

        h, w = crop.shape[:2]
        if h < 8 or w < 8:
            return None

        # Top 55 % = torso / jersey area, avoids shorts & pitch
        torso = crop[:max(1, int(h * 0.55)), :]
        hsv   = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float64)

        # Mask grass: vivid green hue (OpenCV H is 0-180, green ≈ 35-85)
        # Only remove pixels that are BOTH green-hued AND highly saturated (real grass).
        grass = (hsv[:, 0] > 35) & (hsv[:, 0] < 85) & (hsv[:, 1] > 80)
        pixels = hsv[~grass]

        # Accept crops that still have at least 8 valid pixels
        if len(pixels) < 8:
            return None

        return pixels.mean(axis=0)   # shape (3,)  [H, S, V]

    # ── fitting ────────────────────────────────────────────────────────────

    def fit(self, frame: np.ndarray, players: list) -> bool:
        """
        Collect colour samples from non-referee players in `frame`.
        Returns True (and stores the fitted KMeans) once min_samples are
        accumulated; False while still collecting.
        """
        for obj in players:
            if getattr(obj, "cls", -1) in REFEREE_CLASS_IDS:
                continue
            x1, y1, x2, y2 = map(int, obj.xyxy)
            crop  = frame[max(0, y1):y2, max(0, x1):x2]
            color = self._extract_jersey_color(crop)
            if color is not None:
                self._color_buf.append(color)

        if len(self._color_buf) < self.min_samples:
            return False

        colors = np.array(self._color_buf)
        self.kmeans = KMeans(n_clusters=self.n_clusters, n_init=20, random_state=0)
        self.kmeans.fit(colors)
        print(f"[TeamSegmenter] Fitted on {len(colors)} samples. "
              f"Cluster centres (HSV): {self.kmeans.cluster_centers_.astype(int).tolist()}")
        return True

    # ── assignment ─────────────────────────────────────────────────────────

    def assign_team(self, frame: np.ndarray, player_obj) -> int:
        """
        Returns 0 or 1 (team index), or -1 for referee / not yet fitted.
        """
        if getattr(player_obj, "cls", -1) in REFEREE_CLASS_IDS:
            return -1
        if self.kmeans is None:
            return -1

        x1, y1, x2, y2 = map(int, player_obj.xyxy)
        crop  = frame[max(0, y1):y2, max(0, x1):x2]
        color = self._extract_jersey_color(crop)
        if color is None:
            return -1

        return int(self.kmeans.predict([color])[0])
