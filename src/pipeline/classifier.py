import cv2
from ultralytics import YOLO


class DocumentClassifier:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path, task="classify")

    def classify(self, image_path: str, **kwargs):
        img = cv2.imread(image_path)

        results = self.model.predict(img, **kwargs)

        probs = results[0].probs
        idx = int(probs.top1)

        country = self.model.names[idx]
        confidence = float(probs.top1conf)

        return {
            "country": country,
            "confidence": confidence,
        }
