# app/pages/results_page.py
"""Results Page — auto-loads all pipeline outputs and displays interactive charts."""

import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import INSIGHTS_DIR, ANNOTATIONS_DIR, PROCESSED_DIR
from utils import (
    page_header, metric_card,
    ACCENT, TEXT_PRIMARY, TEXT_MUTED, BG_CARD,
)

TEAM_COLORS = {0: "#dc2626", 1: "#3b82f6", -1: "#52525b"}
TEAM_NAMES  = {0: "Team A", 1: "Team B", -1: "Unassigned"}

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(3,3,5,0)",
    font=dict(family="Inter, sans-serif", color="#737380"),
    title_font=dict(size=13, color="#f5f5f5", weight=700),
    margin=dict(t=40, b=30, l=40, r=20),
)


def _load_csv(name: str) -> pd.DataFrame | None:
    for d in [INSIGHTS_DIR, ANNOTATIONS_DIR]:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return pd.read_csv(p)
    return None


def _load_summary() -> dict:
    p = os.path.join(INSIGHTS_DIR, "pipeline_summary.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {}


def _find_tracked_video() -> str | None:
    v = st.session_state.get("tracked_video")
    if v and os.path.exists(v):
        return v
    if os.path.exists(PROCESSED_DIR):
        for f in sorted(os.listdir(PROCESSED_DIR)):
            if "tracked" in f and f.endswith(".mp4"):
                return os.path.join(PROCESSED_DIR, f)
    return None


def render():
    page_header("Results",
                "Pipeline output: possession, player stats, speed analysis, and downloads.")
    st.markdown("---")

    # ── Load all data ────────────────────────────────────────────────────────
    player_df = _load_csv("player_summary.csv")
    poss_df = _load_csv("possession_summary.csv")
    track_df = _load_csv("tracking_enriched.csv")
    summary = _load_summary()
    tracked_video = _find_tracked_video()

    if player_df is None and poss_df is None and track_df is None:
        st.warning("No results found. Use the top navigation bar to open Analysis and run the pipeline.")
        return

    # ── Summary metrics ──────────────────────────────────────────────────────
    if summary:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(metric_card("Video", summary.get("video", "-")),
                        unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card("Frames", f"{summary.get('total_frames', 0):,}"),
                        unsafe_allow_html=True)
        with c3:
            st.markdown(metric_card("Resolution", summary.get("resolution", "-")),
                        unsafe_allow_html=True)
        with c4:
            st.markdown(metric_card("Replays Skipped",
                                    str(summary.get("replays_detected", 0))),
                        unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Tracked video preview ────────────────────────────────────────────────
    if tracked_video:
        with st.expander("Tracked Video Preview"):
            st.video(tracked_video)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_poss, tab_player, tab_speed, tab_track, tab_dl = st.tabs([
        "Possession", "Players", "Speed", "Tracking Data", "Downloads",
    ])

    # ── POSSESSION ───────────────────────────────────────────────────────────
    with tab_poss:
        if poss_df is not None and not poss_df.empty:
            poss_df = poss_df.copy()
            poss_df["team"] = poss_df["team_id"].map(TEAM_NAMES)
            colors = [TEAM_COLORS.get(t, "#6b7280") for t in poss_df["team_id"]]

            chart_col, data_col = st.columns([2, 1])

            with chart_col:
                fig = go.Figure(go.Pie(
                    labels=poss_df["team"],
                    values=poss_df["possession_pct"],
                    hole=0.55,
                    marker=dict(colors=colors),
                    textinfo="label+percent",
                    textfont=dict(size=13),
                ))
                fig.update_layout(**PLOTLY_LAYOUT, height=380,
                                  title="Team Possession")
                st.plotly_chart(fig, use_container_width=True)

            with data_col:
                st.markdown("<br><br>", unsafe_allow_html=True)
                for _, row in poss_df.iterrows():
                    st.markdown(metric_card(
                        row["team"], f"{row['possession_pct']:.1f}%"
                    ), unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

            # Per-player possession bar chart
            if player_df is not None and "poss_pct" in player_df.columns:
                top = player_df.nlargest(10, "poss_pct").copy()
                if not top.empty:
                    top["team"] = top["team_id"].map(TEAM_NAMES)
                    fig2 = px.bar(
                        top, x="object_id", y="poss_pct", color="team",
                        color_discrete_map={v: TEAM_COLORS[k]
                                            for k, v in TEAM_NAMES.items()},
                        labels={"object_id": "Player ID",
                                "poss_pct": "Possession %"},
                        title="Top 10 Players by Possession Time",
                    )
                    fig2.update_layout(**PLOTLY_LAYOUT, height=380)
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No possession data available.")

    # ── PLAYERS ──────────────────────────────────────────────────────────────
    with tab_player:
        if player_df is not None and not player_df.empty:
            df = player_df.copy()
            if "team_id" in df.columns:
                df["team"] = df["team_id"].map(TEAM_NAMES)
            if "class_id" in df.columns:
                df["role"] = df["class_id"].map(
                    {0: "Ball", 1: "GK", 2: "Player", 3: "Referee"})

            # Filters
            f1, f2 = st.columns(2)
            with f1:
                if "team" in df.columns:
                    teams = st.multiselect(
                        "Team", df["team"].unique().tolist(),
                        default=df["team"].unique().tolist())
                else:
                    teams = []
            with f2:
                if "role" in df.columns:
                    roles = st.multiselect(
                        "Role", df["role"].unique().tolist(),
                        default=df["role"].unique().tolist())
                else:
                    roles = []

            mask = pd.Series(True, index=df.index)
            if teams and "team" in df.columns:
                mask &= df["team"].isin(teams)
            if roles and "role" in df.columns:
                mask &= df["role"].isin(roles)
            filtered = df[mask]

            st.dataframe(filtered, use_container_width=True,
                         hide_index=True, height=400)

            # Key metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(metric_card("Players", str(len(filtered))),
                            unsafe_allow_html=True)
            with m2:
                if "top_speed_km_h" in filtered.columns and len(filtered) > 0:
                    st.markdown(metric_card(
                        "Max Speed", f"{filtered['top_speed_km_h'].max():.1f} km/h"
                    ), unsafe_allow_html=True)
            with m3:
                if "avg_speed_km_h" in filtered.columns and len(filtered) > 0:
                    st.markdown(metric_card(
                        "Avg Speed", f"{filtered['avg_speed_km_h'].mean():.1f} km/h"
                    ), unsafe_allow_html=True)
            with m4:
                if "total_frames" in filtered.columns and len(filtered) > 0:
                    st.markdown(metric_card(
                        "Avg Visibility",
                        f"{filtered['total_frames'].mean():.0f} frames"
                    ), unsafe_allow_html=True)
        else:
            st.info("No player data available.")

    # ── SPEED ────────────────────────────────────────────────────────────────
    with tab_speed:
        if player_df is not None and "top_speed_km_h" in player_df.columns:
            sdf = player_df.copy()
            sdf["team"] = sdf["team_id"].map(TEAM_NAMES)

            # Histogram
            fig3 = px.histogram(
                sdf, x="top_speed_km_h", color="team", nbins=20,
                color_discrete_map={v: TEAM_COLORS[k]
                                    for k, v in TEAM_NAMES.items()},
                labels={"top_speed_km_h": "Top Speed (km/h)"},
                title="Top Speed Distribution",
                barmode="overlay", opacity=0.75,
            )
            fig3.update_layout(**PLOTLY_LAYOUT, height=380)
            st.plotly_chart(fig3, use_container_width=True)

            # Leaderboard bar chart
            top10 = sdf.nlargest(10, "top_speed_km_h")
            fig4 = px.bar(
                top10, x="object_id", y="top_speed_km_h", color="team",
                text="top_speed_km_h",
                color_discrete_map={v: TEAM_COLORS[k]
                                    for k, v in TEAM_NAMES.items()},
                labels={"object_id": "Player ID",
                        "top_speed_km_h": "Top Speed (km/h)"},
                title="Fastest Players",
            )
            fig4.update_traces(texttemplate="%{text:.1f}",
                               textposition="outside")
            fig4.update_layout(**PLOTLY_LAYOUT, height=380)
            st.plotly_chart(fig4, use_container_width=True)

            # Scatter: avg vs top speed
            if "avg_speed_km_h" in sdf.columns:
                fig5 = px.scatter(
                    sdf, x="avg_speed_km_h", y="top_speed_km_h",
                    color="team", hover_data=["object_id"],
                    color_discrete_map={v: TEAM_COLORS[k]
                                        for k, v in TEAM_NAMES.items()},
                    labels={"avg_speed_km_h": "Avg Speed (km/h)",
                            "top_speed_km_h": "Top Speed (km/h)"},
                    title="Speed Profile: Average vs Peak",
                )
                fig5.update_layout(**PLOTLY_LAYOUT, height=380)
                st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No speed data available.")

    # ── TRACKING DATA ────────────────────────────────────────────────────────
    with tab_track:
        if track_df is not None and not track_df.empty:
            st.caption(f"{len(track_df):,} rows (showing first 500)")
            st.dataframe(track_df.head(500), use_container_width=True,
                         hide_index=True, height=400)

            if ("frame_id" in track_df.columns
                    and "object_id" in track_df.columns):
                per_frame = (track_df.groupby("frame_id")["object_id"]
                             .nunique().reset_index())
                per_frame.columns = ["frame_id", "objects"]
                fig6 = px.line(
                    per_frame, x="frame_id", y="objects",
                    title="Active Tracked Objects Over Time",
                    labels={"frame_id": "Frame", "objects": "Objects"},
                )
                fig6.update_traces(line=dict(color=ACCENT, width=1))
                fig6.update_layout(**PLOTLY_LAYOUT, height=320)
                st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No tracking data available.")

    # ── DOWNLOADS ────────────────────────────────────────────────────────────
    with tab_dl:
        st.markdown("##### Export Data")

        downloads = [
            ("Player Summary", "player_summary.csv", player_df,
             "Per-player stats: speed, possession, team."),
            ("Possession", "possession_summary.csv", poss_df,
             "Team-level possession percentages."),
            ("Tracking Data", "tracking_enriched.csv", track_df,
             "Frame-by-frame tracking with velocity."),
        ]

        cols = st.columns(3)
        for col, (title, fname, df, desc) in zip(cols, downloads):
            with col:
                st.markdown(f"""
                <div class="card" style="text-align: center;">
                    <div class="card-label">CSV</div>
                    <div class="card-heading">{title}</div>
                    <div class="card-body">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if df is not None:
                    st.download_button(
                        f"Download {fname}",
                        data=df.to_csv(index=False),
                        file_name=fname, mime="text/csv",
                        use_container_width=True,
                        key=f"dl_{fname}",
                    )
                else:
                    st.button("Not available", disabled=True,
                               use_container_width=True, key=f"na_{fname}")

        st.markdown("---")

        if tracked_video:
            with open(tracked_video, "rb") as vf:
                st.download_button(
                    "Download Tracked Video (MP4)",
                    data=vf.read(),
                    file_name=os.path.basename(tracked_video),
                    mime="video/mp4", use_container_width=True,
                )

        if summary:
            st.download_button(
                "Download Pipeline Summary (JSON)",
                data=json.dumps(summary, indent=2),
                file_name="pipeline_summary.json",
                mime="application/json", use_container_width=True,
            )

    # ── Session action ───────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("Start New Analysis", use_container_width=True):
        # Reset all pipeline state
        for k in ["uploaded_video", "uploaded_video_name",
                  "processed_video", "analysis_done",
                  "analysis_results", "tracked_video"]:
            st.session_state.pop(k, None)
        st.session_state.page = "Upload"
        st.query_params["page"] = "Upload"
        st.rerun()
