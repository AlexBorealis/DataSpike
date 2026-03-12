import os
import sys
import traceback

from ultralytics import YOLO

DATASET_DIR = os.path.join(os.getenv("DATA_DIR"), "processed", "classify", "images")
MODELS_DIR = os.path.join(
    os.getenv("SOURCE_DIR"), "src", "models", "prod_models", "yolo"
)
RESULTS_DIR = os.path.join(os.getenv("SOURCE_DIR"), "results", "yolo", "classify")

model_path = os.path.join(MODELS_DIR, "yolo11n-cls.pt")
freeze = 7

model = YOLO(model_path)
try:
    results = model.train(
        data=DATASET_DIR,
        project=RESULTS_DIR,
        name="exp_1",
        optimizer="AdamW",
        epochs=10,
        imgsz=640,
        batch=16,
        cos_lr=True,
        amp=False,
        patience=10,
        # аугментации
        hsv_h=0.015,
        hsv_s=0.4,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.9,
        fliplr=0.5,
        flipud=0.0,
        mosaic=0.0,
        mixup=0.0,
        # сначала с freeze, потом без
        freeze=freeze,  # или 10 на первом этапе
        plots=True,
        save=True,
    )
except Exception as e:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb = traceback.extract_tb(exc_traceback)
    filename, line_number, func_name, text = tb[-1]
    print(f"Error occurred in file: {filename}")
    print(f"Line {line_number}: {text}")
    print(f"Error message: {e}")
