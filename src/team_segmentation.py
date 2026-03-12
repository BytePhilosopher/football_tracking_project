# src/team_segmentation.py
"""
Team classification via DBSCAN on HSV hue histograms.

Follows the paper's approach (§3.3):
  - Crop the upper 15–85 % of each player bounding box (jersey region).
  - Extract a normalised hue histogram (18 bins covering 0–180°).
  - Z-score normalise histograms with StandardScaler before clustering.
  - DBSCAN to discover the two team clusters without specifying k.
  - Falls back to KMeans(k=2) when DBSCAN finds fewer than 2 valid clusters
    (e.g. early frames with little colour variety).
"""

import cv2
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

# Class IDs for referees — always get team -1, excluded from clustering
REFEREE_CLASS_IDS = {3}

N_BINS        = 18     # hue histogram bins  (180 / 18 = 10° per bin)
DBSCAN_EPS    = 2.5    # epsilon in normalised histogram space
DBSCAN_MINPTS = 3      # min points to form a DBSCAN cluster


class TeamSegmenter:
    """
    Assigns players to teams (0 or 1) using unsupervised DBSCAN clustering
    on HSV hue histograms extracted from the jersey region of each bbox.

    Key design choices vs. the previous KMeans-on-mean-HSV approach
    ----------------------------------------------------------------
    - Hue *histogram* (not mean): captures multi-modal colours (stripes,
      logos) and is more discriminative than a single average vector.
    - Upper 15–85 % of bbox: avoids shorts, socks, and pitch bleed.
    - Z-score normalisation: equalises scale across histogram bins so that
      DBSCAN distance is meaningful.
    - DBSCAN: fully unsupervised — no k required; noise points (-1) are
      simply unclassified, so referees/ball-boys naturally fall out.
    """

    def __init__(self, min_samples: int = 12):
        self.min_samples = min_samples
        self._scaler     = StandardScaler()
        self._fitted     = False
        # Cluster centres in *normalised* space, shape (2, N_BINS)
        self._cluster_centers: np.ndarray | None = None
        self._hist_buf: list[np.ndarray] = []

    # ── feature extraction ────────────────────────────────────────────────

    def _extract_hue_histogram(self, crop: np.ndarray) -> np.ndarray | None:
        """
        Returns a normalised hue histogram (shape: N_BINS,) from the jersey
        region (upper 15–85 % of the crop height), or None if unusable.
        """
        if crop is None or crop.size == 0:
            return None

        h, w = crop.shape[:2]
        if h < 10 or w < 8:
            return None

        # Jersey region: skip the top 15 % (head/hair) and bottom 15 % (shorts)
        y_start = max(0, int(h * 0.15))
        y_end   = min(h, int(h * 0.85))
        jersey  = crop[y_start:y_end, :]
        if jersey.size == 0:
            return None

        hsv = cv2.cvtColor(jersey, cv2.COLOR_BGR2HSV)

        # Mask vivid grass (hue 35–85, saturation > 80 in OpenCV 0–180 range)
        grass_mask = (
            (hsv[:, :, 0] > 35) & (hsv[:, :, 0] < 85) & (hsv[:, :, 1] > 80)
        )
        valid_hue = hsv[:, :, 0][~grass_mask]

        if len(valid_hue) < 8:
            return None

        # Hue histogram over [0, 180)
        hist, _ = np.histogram(valid_hue, bins=N_BINS, range=(0, 180))
        hist     = hist.astype(np.float64)
        total    = hist.sum()
        if total > 0:
            hist /= total   # L1 normalise → probability distribution

        return hist

    # ── fitting ────────────────────────────────────────────────────────────

    def fit(self, frame: np.ndarray, players: list) -> bool:
        """
        Collect hue histogram samples from non-referee players in `frame`.
        Returns True (and stores cluster centres) once min_samples are
        accumulated; False while still collecting.
        """
        for obj in players:
            if getattr(obj, "cls", -1) in REFEREE_CLASS_IDS:
                continue
            x1, y1, x2, y2 = map(int, obj.xyxy)
            crop = frame[max(0, y1):y2, max(0, x1):x2]
            hist = self._extract_hue_histogram(crop)
            if hist is not None:
                self._hist_buf.append(hist)

        if len(self._hist_buf) < self.min_samples:
            return False

        self._fit_clusters()
        return True

    def _fit_clusters(self) -> None:
        feats      = np.array(self._hist_buf)          # (N, N_BINS)
        feats_norm = self._scaler.fit_transform(feats) # z-score normalise

        # DBSCAN — discovers clusters without specifying k
        db     = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MINPTS)
        labels = db.fit_predict(feats_norm)

        valid_clusters = set(labels) - {-1}

        if len(valid_clusters) >= 2:
            # Pick the two largest clusters as the two teams
            sizes = {lbl: int((labels == lbl).sum()) for lbl in valid_clusters}
            top2  = sorted(sizes, key=sizes.get, reverse=True)[:2]
            self._cluster_centers = np.array([
                feats_norm[labels == top2[0]].mean(axis=0),
                feats_norm[labels == top2[1]].mean(axis=0),
            ])
            print(
                f"[TeamSegmenter] DBSCAN fitted on {len(feats)} samples. "
                f"Team cluster sizes: {sizes[top2[0]]} / {sizes[top2[1]]}"
            )
        else:
            # Fallback: KMeans(k=2) when DBSCAN can't separate two groups
            km = KMeans(n_clusters=2, n_init=20, random_state=0)
            km.fit(feats_norm)
            self._cluster_centers = km.cluster_centers_
            print(
                f"[TeamSegmenter] DBSCAN returned {len(valid_clusters)} cluster(s) — "
                f"fell back to KMeans(k=2) on {len(feats)} samples."
            )

        self._fitted = True

    # ── assignment ─────────────────────────────────────────────────────────

    def assign_team(self, frame: np.ndarray, player_obj) -> int:
        """Returns 0 or 1 (team index), or -1 for referee / not yet fitted."""
        if getattr(player_obj, "cls", -1) in REFEREE_CLASS_IDS:
            return -1
        if not self._fitted:
            return -1

        x1, y1, x2, y2 = map(int, player_obj.xyxy)
        crop = frame[max(0, y1):y2, max(0, x1):x2]
        hist = self._extract_hue_histogram(crop)
        if hist is None:
            return -1

        hist_norm = self._scaler.transform([hist])[0]
        dists     = np.linalg.norm(self._cluster_centers - hist_norm, axis=1)
        return int(np.argmin(dists))
