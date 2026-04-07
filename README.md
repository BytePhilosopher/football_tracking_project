# Football Tracking Pipeline

End-to-end match analysis: upload broadcast footage, get player tracking, team segmentation, and possession analytics.

## Quick Start

```bash
pip install -r requirements.txt
cd app
streamlit run Home.py
```

## Pipeline

```
Upload (.mp4) → Preprocess (resize/FPS) → YOLO Detection → ByteTrack → Team Segmentation → Possession → Results
```

## Project Structure

```
app/                    Streamlit application
  Home.py               Entry point
  config.py             Shared paths and constants
  utils.py              Theme and UI components
  pages/                Page modules
    upload_page.py
    preprocess_page.py
    analysis_page.py
    results_page.py

src/                    Core pipeline modules
  detector.py           YOLOv8 inference
  tracker.py            ByteTrack with camera compensation
  camera_compensation.py  Sparse LK optical flow
  team_segmentation.py  DBSCAN jersey-color clustering
  possession.py         Hysteresis possession tracker
  ball_interpolator.py  Velocity-based extrapolation
  replay_detector.py    Scene-cut detection
  metadata.py           Per-frame CSV logger
  data_pipeline.py      Post-processing (velocity, distance, summaries)
  preprocess.py         Video resize and FPS normalization

data/
  raw/                  Input videos
  processed/            Preprocessed and tracked videos
  annotations/          Raw pipeline CSV output
  insights/             Final results and summaries

models/
  best.pt               Trained YOLOv8 weights
```

## GPU

The detection step requires a CUDA GPU for practical speed. Without GPU, it runs on CPU but is significantly slower.

For GPU processing, use the provided `Football_Tracking_Colab.ipynb` on Google Colab with a T4 runtime.

## Tech Stack

| Component | Method |
|-----------|--------|
| Detection | YOLOv8 (custom-trained, 1280px) |
| Tracking | ByteTrack + camera motion compensation |
| Team ID | DBSCAN on HSV hue histograms |
| Possession | Tin/Tout hysteresis with K-frame confirmation |
| Replay filter | Histogram correlation + optical flow |
| Ball tracking | Velocity interpolation (15-frame max gap) |

## Output

- Annotated video with bounding boxes, team colors, possession indicator
- `player_summary.csv` — per-player speed, possession, team
- `possession_summary.csv` — team-level possession percentages
- `tracking_enriched.csv` — frame-by-frame tracking with velocity
