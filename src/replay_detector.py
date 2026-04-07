# src/replay_detector.py
"""
Replay / scene-cut detector for broadcast football footage.

The Problem
-----------
Broadcast video frequently cuts to slow-motion replays, then back to live
play.  The tracking pipeline has no awareness of these cuts, so it:
  1. Computes a massive bogus camera_shift (optical flow sees the whole scene
     change at once).
  2. Retires all ByteTrack IDs during the replay and assigns new ones when
     live play resumes → ID explosion and ghost tracks.
  3. Extrapolates the ball position across the replay using pre-cut velocity
     → fake ball positions in the CSV.
  4. Generates enormous speed spikes when a player's position jumps back to
     the real pitch after the replay ends.

Detection approach
------------------
We use two independent, complementary signals:

  1. Histogram correlation  (primary, cheap, frame-level)
     Convert to grayscale, compute a 64-bin normalised histogram, compare
     consecutive frames with HISTCMP_CORREL.  Normal camera pans keep
     correlation > 0.85.  A hard cut (replay start/end) drops it below
     HIST_THRESH (default 0.70).

  2. Optical-flow magnitude  (secondary, from CameraCompensation)
     The caller can pass `flow_magnitude` (pixels/frame) from
     CameraCompensation.update().  A normal pan is < ~8 px/frame at 25fps.
     At a scene cut, LK optical flow produces a huge, mostly invalid shift.

Both signals must agree (OR logic: either alone can flag a cut) because:
  - A very fast camera pan can fool the histogram signal.
  - A flash / VAR screen can fool the flow signal.

State machine
-------------
  LIVE     → SCENE_CUT  when a cut is detected
  SCENE_CUT→ REPLAY     after ENTRY_FRAMES consecutive cut frames (avoids
                         single-frame false positives from camera flashes)
  REPLAY   → LIVE       when similarity returns above HIST_THRESH for
                         EXIT_FRAMES consecutive frames

The caller (main.py) should:
  - Skip detection / tracking / logging while `is_replay` is True.
  - Call `reset_pipeline_state()` at BOTH the entry and exit boundaries
    (the boundary frames themselves are also unreliable).
"""

import cv2
import numpy as np
from enum import Enum, auto


class _State(Enum):
    LIVE       = auto()
    SCENE_CUT  = auto()   # candidate entry; waiting for ENTRY_FRAMES
    REPLAY     = auto()


class ReplayDetector:
    """
    Detects replay / scene-cut boundaries in broadcast football video.

    Parameters
    ----------
    hist_threshold : float
        Frame-to-frame grayscale histogram correlation below this triggers a
        cut.  Range [−1, 1]; typical live-play value ≈ 0.88–0.99.
        Default 0.70 is conservative — lower it (e.g. 0.60) if you get false
        positives on fast pans.
    flow_threshold : float
        Median optical-flow magnitude (px/frame) above this also triggers a
        cut.  Default 25.0.  Set to float('inf') to disable.
    entry_frames : int
        Number of consecutive cut frames needed to confirm a replay has
        started (avoids reacting to a single-frame camera flash).
    exit_frames : int
        Number of consecutive live frames needed to confirm the replay has
        ended (avoids reacting to a brief moment of similarity mid-replay).
    cooldown_frames : int
        After exiting a replay, ignore new detections for this many frames.
        The first frame back to live play is a mix of cut + live; its data
        is unreliable.
    """

    def __init__(
        self,
        hist_threshold:  float = 0.70,
        flow_threshold:  float = 25.0,
        entry_frames:    int   = 3,
        exit_frames:     int   = 4,
        cooldown_frames: int   = 8,
    ):
        self.hist_threshold  = hist_threshold
        self.flow_threshold  = flow_threshold
        self.entry_frames    = entry_frames
        self.exit_frames     = exit_frames
        self.cooldown_frames = cooldown_frames

        self._state          = _State.LIVE
        self._prev_hist      = None           # last histogram (64-bin, normalised)
        self._cut_streak     = 0              # consecutive cut frames seen
        self._live_streak    = 0              # consecutive live frames seen
        self._cooldown       = 0              # frames remaining in cooldown
        self._replay_start   = None           # frame index when replay began
        self._n_replays      = 0              # total replays detected
        self._n_replay_frames= 0              # total frames spent in replays

    # ── public API ───────────────────────────────────────────────────────────

    def update(
        self,
        frame:          np.ndarray,
        frame_id:       int = 0,
        flow_magnitude: float | None = None,
    ) -> bool:
        """
        Feed the current BGR frame.

        Parameters
        ----------
        frame          : current BGR frame
        frame_id       : index used only for logging
        flow_magnitude : optional |median LK flow| from CameraCompensation;
                         if None, the flow signal is not used.

        Returns
        -------
        bool : True while the frame is classified as a replay / scene cut
               (caller should skip it for tracking purposes).
        """
        curr_hist = self._compute_hist(frame)

        # ── compute similarity signals ────────────────────────────────────
        is_cut = False

        if self._prev_hist is not None:
            corr = float(cv2.compareHist(
                self._prev_hist, curr_hist, cv2.HISTCMP_CORREL
            ))
            if corr < self.hist_threshold:
                is_cut = True
        else:
            corr = 1.0

        if flow_magnitude is not None and flow_magnitude > self.flow_threshold:
            is_cut = True

        self._prev_hist = curr_hist

        # ── state machine ─────────────────────────────────────────────────
        if self._cooldown > 0:
            self._cooldown -= 1
            return False

        if self._state == _State.LIVE:
            if is_cut:
                self._cut_streak  += 1
                self._live_streak  = 0
                if self._cut_streak >= self.entry_frames:
                    self._state        = _State.REPLAY
                    self._replay_start = frame_id
                    self._n_replays   += 1
                    self._cut_streak   = 0
                    return True
            else:
                self._cut_streak = 0
            return False

        elif self._state == _State.REPLAY:
            self._n_replay_frames += 1
            if not is_cut:
                self._live_streak += 1
                if self._live_streak >= self.exit_frames:
                    # Replay has ended — enter cooldown before resuming
                    self._state       = _State.LIVE
                    self._live_streak = 0
                    self._cooldown    = self.cooldown_frames
                    return False      # this frame: still unreliable → caller skips
            else:
                self._live_streak = 0
            return True

        return False  # unreachable

    @property
    def is_replay(self) -> bool:
        """True while currently inside a detected replay."""
        return self._state == _State.REPLAY

    @property
    def stats(self) -> dict:
        return {
            "n_replays":       self._n_replays,
            "n_replay_frames": self._n_replay_frames,
        }

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_hist(frame: np.ndarray) -> np.ndarray:
        """Normalised 64-bin grayscale histogram."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
        cv2.normalize(hist, hist)
        return hist
