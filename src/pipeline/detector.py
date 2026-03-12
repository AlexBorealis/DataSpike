import cv2
import numpy as np
from ultralytics import YOLO


class MRZDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path, task="detect")

    def detect(self, image_path: str, **kwargs) -> np.ndarray:
        img = cv2.imread(image_path)

        results = self.model.predict(img, **kwargs)

        boxes = results[0].boxes

        if boxes is None or len(boxes) == 0:
            raise ValueError("MRZ not detected")

        conf = boxes.conf.cpu().numpy()
        best = int(conf.argmax())

        x1, y1, x2, y2 = boxes.xyxy[best].cpu().numpy().astype(int)

        pad = 10

        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(img.shape[1], x2 + pad)
        y2 = min(img.shape[0], y2 + pad)

        return img[y1:y2, x1:x2]
