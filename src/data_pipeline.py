# src/data_pipeline.py
"""
Post-processing data pipeline.

Reads the enriched tracking.csv produced by MetadataLogger and computes:
  - Per-object velocity (px / frame) from consecutive bounding-box centres
  - Cumulative distance travelled
  - Summary statistics: possession %, distance per player, top speed
  - Exports cleaned datasets ready for analysis

Usage (standalone):
    python -m src.data_pipeline \
        --tracking data/annotations/tracking.csv \
        --fps 25 \
        --out data/annotations
"""

import argparse
import csv
import os
from collections import defaultdict
from pathlib import Path

import numpy as np


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_tracking(path: str) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _safe_float(val, default=None):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=-1):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# ── velocity & distance ───────────────────────────────────────────────────────

def compute_kinematics(rows: list[dict], fps: float) -> list[dict]:
    """
    Adds vx_px, vy_px, speed_px_per_frame, speed_km_h columns
    (speed_km_h uses a rough pitch-scale constant; update for your camera).

    px_per_metre default ≈ 10 px/m at typical broadcast resolution.
    """
    PX_PER_METRE = 10.0      # ← calibrate per video if needed

    # Group rows by object_id → sorted by frame
    by_obj: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        obj_id = _safe_int(r.get("object_id"))
        by_obj[obj_id].append(r)

    for obj_id, obj_rows in by_obj.items():
        obj_rows.sort(key=lambda r: _safe_int(r["frame_id"], 0))
        prev_x = prev_y = prev_f = None

        for r in obj_rows:
            fx = _safe_float(r.get("feet_x"))
            fy = _safe_float(r.get("feet_y"))
            fi = _safe_int(r.get("frame_id", 0))

            if prev_x is not None and fx is not None and fi > prev_f:
                df   = fi - prev_f
                vx   = (fx - prev_x) / df
                vy   = (fy - prev_y) / df
                spd_px  = np.hypot(vx, vy)
                spd_ms  = spd_px / PX_PER_METRE / df * fps
                spd_kmh = spd_ms * 3.6
            else:
                vx = vy = spd_px = spd_kmh = 0.0

            r["vx_px"]            = round(vx, 3)
            r["vy_px"]            = round(vy, 3)
            r["speed_px_f"]       = round(spd_px, 3)
            r["speed_km_h"]       = round(spd_kmh, 2)
            prev_x, prev_y, prev_f = fx, fy, fi

    return rows


# ── summary statistics ────────────────────────────────────────────────────────

def build_summary(rows: list[dict], fps: float) -> dict:
    """Returns a summary dict with player stats and team possession."""
    by_obj: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_obj[_safe_int(r["object_id"])].append(r)

    team_possession_frames: dict[int, int] = defaultdict(int)
    player_stats = {}

    for obj_id, obj_rows in by_obj.items():
        if obj_id < 0:
            continue

        class_id = _safe_int(obj_rows[0].get("class_id"))
        team_id  = _safe_int(obj_rows[0].get("team_id"))

        speeds    = [_safe_float(r.get("speed_km_h"), 0.0) for r in obj_rows]
        poss_frames = sum(1 for r in obj_rows if _safe_int(r.get("has_possession")) == 1)
        total_frames = len(obj_rows)

        # Accumulate team possession
        for r in obj_rows:
            if _safe_int(r.get("has_possession")) == 1:
                team_possession_frames[team_id] += 1

        player_stats[obj_id] = {
            "object_id":      obj_id,
            "class_id":       class_id,
            "team_id":        team_id,
            "total_frames":   total_frames,
            "poss_frames":    poss_frames,
            "poss_pct":       round(100.0 * poss_frames / max(1, total_frames), 2),
            "top_speed_km_h": round(max(speeds), 2),
            "avg_speed_km_h": round(float(np.mean(speeds)), 2),
        }

    total_poss = sum(team_possession_frames.values())
    team_poss_pct = {
        t: round(100.0 * v / max(1, total_poss), 2)
        for t, v in team_possession_frames.items()
    }

    return {"players": player_stats, "team_possession_pct": team_poss_pct}


# ── export helpers ────────────────────────────────────────────────────────────

def save_enriched_tracking(rows: list[dict], path: str):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Enriched tracking -> {path}")


def save_player_summary(summary: dict, path: str):
    players = list(summary["players"].values())
    if not players:
        return
    fieldnames = list(players[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(players)
    print(f"Player summary    -> {path}")


def save_possession_summary(summary: dict, path: str):
    rows = [
        {"team_id": t, "possession_pct": p}
        for t, p in summary["team_possession_pct"].items()
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["team_id", "possession_pct"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Possession summary-> {path}")


# ── main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(tracking_csv: str, out_dir: str, fps: float = 25.0):
    os.makedirs(out_dir, exist_ok=True)

    print(f"Loading {tracking_csv} ...")
    rows = _load_tracking(tracking_csv)
    if not rows:
        print("No data found – aborting pipeline.")
        return

    print(f"Computing kinematics for {len(rows)} rows ...")
    rows = compute_kinematics(rows, fps)

    summary = build_summary(rows, fps)

    save_enriched_tracking(rows,    os.path.join(out_dir, "tracking_enriched.csv"))
    save_player_summary(summary,    os.path.join(out_dir, "player_summary.csv"))
    save_possession_summary(summary, os.path.join(out_dir, "possession_summary.csv"))

    print("\n=== Team Possession ===")
    for tid, pct in summary["team_possession_pct"].items():
        print(f"  Team {tid}: {pct:.1f}%")

    print("\n=== Top Speeds ===")
    for s in sorted(summary["players"].values(), key=lambda x: -x["top_speed_km_h"])[:10]:
        print(f"  ID {s['object_id']:4d} | Team {s['team_id']} | "
              f"top {s['top_speed_km_h']:5.1f} km/h | avg {s['avg_speed_km_h']:4.1f} km/h")

    print("\nPipeline complete.")


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Football tracking data pipeline")
    parser.add_argument("--tracking", default="data/annotations/tracking.csv")
    parser.add_argument("--fps",      type=float, default=25.0)
    parser.add_argument("--out",      default="data/annotations")
    args = parser.parse_args()
    run_pipeline(args.tracking, args.out, args.fps)
