# src/detector.py
from ultralytics import YOLO
import numpy as np


class Detector:
    def __init__(self, model_path, conf=0.35, iou=0.45, imgsz=1280):
        self.model = YOLO(model_path)
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz

    def detect(self, frame):
        results = self.model(
            frame,
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            verbose=False,
        )[0]
        return results.boxes
