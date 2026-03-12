import argparse
import json

import yaml

from src.pipeline.checker import MRZChecker
from src.pipeline.classifier import DocumentClassifier
from src.pipeline.detector import MRZDetector
from src.pipeline.ocr.easyocr_ocr import EasyOCRReader
from src.pipeline.ocr.tesseract_ocr import TesseractOCRReader
from src.pipeline.pipeline import Pipeline
from src.pipeline.preprocessor import MRZPreprocessor
from src.serializers.serializers import AppConfig


def load_config(config_path: str) -> AppConfig:
    """Load and validate YAML configuration."""
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    return AppConfig(**raw_config)


def build_pipeline(cfg: AppConfig) -> Pipeline:
    """Create pipeline from config."""

    detector = MRZDetector(str(cfg.model.detector))
    classifier = DocumentClassifier(str(cfg.model.classifier))

    preprocessor = MRZPreprocessor()

    checker = MRZChecker() if cfg.pipeline.checker else None

    if cfg.pipeline.ocr == "tesseract":
        ocr_class = TesseractOCRReader
        ocr_kwargs = {"lang": "eng"}

    else:
        ocr_class = EasyOCRReader
        ocr_kwargs = {
            "min_size": 10,
            "contrast_ths": 0.05,
            "adjust_contrast": 0.5,
            "text_threshold": 0.4,
            "low_text": 0.3,
            "beamWidth": 5,
        }

    pipeline = Pipeline(
        detector=detector,
        preprocessor=preprocessor,
        ocr=ocr_class,
        ocr_kwargs=ocr_kwargs,
        checker=checker,
        classifier=classifier,
    )

    return pipeline


def main():
    parser = argparse.ArgumentParser(
        description="MRZ extraction and document classification pipeline"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "--image",
        help="Override image path from config",
    )

    args = parser.parse_args()

    # ---------- LOAD CONFIG ----------
    cfg = load_config(args.config)

    # ---------- OVERRIDE IMAGE ----------
    image_path = args.image if args.image else str(cfg.input.image)

    # ---------- BUILD PIPELINE ----------
    pipeline = build_pipeline(cfg)

    # ---------- RUN ----------
    result = pipeline.run(
        image_path,
        **cfg.run.model_dump(),
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
