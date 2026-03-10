# src/utils.py

import cv2
import numpy as np


# ── Colour palette ────────────────────────────────────────────────────────────
TEAM_COLORS = {
    0:  (235,  80,  60),   # Team A  – blue-ish (BGR)
    1:  ( 60,  60, 220),   # Team B  – red-ish  (BGR)
    -1: (180, 180, 180),   # Unknown / referee
}
POSSESSION_COLOR = (0, 220, 220)   # yellow
BALL_COLOR       = (0, 255,   0)   # green
INTERP_BALL_COLOR = (0, 165, 255)  # orange when interpolated

# HUD background
HUD_BG_COLOR  = (20, 20, 20)
HUD_BG_ALPHA  = 0.55
FONT          = cv2.FONT_HERSHEY_SIMPLEX


# ── Player drawing ─────────────────────────────────────────────────────────────
def draw_player(frame: np.ndarray, player, possessor_id: int | None):
    """
    Draws an ellipse at the feet of the player and a label above the head.
    Highlights the ball possessor in yellow.
    """
    x1, y1, x2, y2 = map(int, player.xyxy)
    team   = getattr(player, "team", -1)
    pid    = player.id
    cls    = getattr(player, "cls", -1)

    # Pick colour
    if pid == possessor_id:
        color = POSSESSION_COLOR
    else:
        color = TEAM_COLORS.get(team, TEAM_COLORS[-1])

    # Ellipse at feet (bottom of box)
    cx      = (x1 + x2) // 2
    cy      = y2
    width   = max(1, (x2 - x1) // 2)
    height  = max(1, width // 3)
    cv2.ellipse(frame, (cx, cy), (width, height), 0, -45, 235, color, 2)

    # Top label: class name + ID
    class_label = {0: "Ball", 1: "GK", 2: "Player", 3: "Ref"}.get(cls, f"C{cls}")
    label = f"{class_label} #{pid}"
    lx, ly = x1, max(y1 - 8, 0)
    (tw, th), bl = cv2.getTextSize(label, FONT, 0.45, 1)

    # Background chip
    cv2.rectangle(frame, (lx, ly - th - bl), (lx + tw + 4, ly + bl), color, -1)
    cv2.putText(frame, label, (lx + 2, ly), FONT, 0.45, (255, 255, 255), 1, cv2.LINE_AA)


def draw_ball(frame: np.ndarray, ball_position: tuple, interpolated: bool = False):
    """Draws the ball as a filled circle. Orange when interpolated."""
    if ball_position is None:
        return
    bx, by = map(int, ball_position)
    color  = INTERP_BALL_COLOR if interpolated else BALL_COLOR
    cv2.circle(frame, (bx, by), 8, (0, 0, 0), -1)   # black outline
    cv2.circle(frame, (bx, by), 6, color,    -1)


# ── HUD overlay ───────────────────────────────────────────────────────────────
def draw_hud(
    frame: np.ndarray,
    frame_id: int,
    fps: float,
    possession_pct: dict[int, float],
    team_names: dict[int, str] | None = None,
):
    """
    Draws a semi-transparent HUD in the top-left corner showing:
    - Frame index
    - Team possession percentages with coloured bars
    """
    if team_names is None:
        team_names = {0: "Team A", 1: "Team B"}

    h, w = frame.shape[:2]
    box_w, box_h = 260, 90
    overlay = frame.copy()
    cv2.rectangle(overlay, (8, 8), (8 + box_w, 8 + box_h), HUD_BG_COLOR, -1)
    cv2.addWeighted(overlay, HUD_BG_ALPHA, frame, 1 - HUD_BG_ALPHA, 0, frame)

    cv2.putText(frame, f"Frame: {frame_id}", (14, 26),
                FONT, 0.5, (220, 220, 220), 1, cv2.LINE_AA)

    y_off = 44
    for team_id, pct in sorted(possession_pct.items()):
        if team_id < 0:
            continue
        name  = team_names.get(team_id, f"Team {team_id}")
        color = TEAM_COLORS.get(team_id, TEAM_COLORS[-1])
        label = f"{name}: {pct:.1f}%"

        # Coloured bar
        bar_len = int((box_w - 20) * pct / 100)
        cv2.rectangle(frame, (14, y_off - 1), (14 + bar_len, y_off + 10), color, -1)
        cv2.putText(frame, label, (14, y_off + 22),
                    FONT, 0.44, (230, 230, 230), 1, cv2.LINE_AA)
        y_off += 36
