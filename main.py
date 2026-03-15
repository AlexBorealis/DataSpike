import argparse
import json
import os

import yaml
from dotenv import load_dotenv

from src.pipeline.checker import MRZChecker
from src.pipeline.classifier.classifier import DocumentClassifier
from src.pipeline.detector.detector import MRZDetector
from src.pipeline.ocr.easyocr_ocr import EasyOCRReader
from src.pipeline.ocr.tesseract_ocr import TesseractOCRReader
from src.pipeline.pipeline import Pipeline
from src.pipeline.preprocessor import MRZPreprocessor
from src.serializers.serializers import AppConfig


def load_config(config_path: str) -> AppConfig:
    """Load and validate YAML configuration."""
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    load_dotenv(dotenv_path="config/envs/.env")
    source_dir = os.getenv("SOURCE_DIR", "")
    data_dir = os.getenv("DATA_DIR", "")

    # Модифицируем пути моделей
    if "model" in raw_config:
        raw_config["model"]["detector"] = os.path.join(
            source_dir, str(raw_config["model"]["detector"]).lstrip("/")
        )
        raw_config["model"]["classifier"] = os.path.join(
            source_dir, str(raw_config["model"]["classifier"]).lstrip("/")
        )

    # ИСПРАВЛЕНИЕ: Добавляем проверку "if raw_config["input"]["images"]"
    if "input" in raw_config and raw_config["input"].get("images"):
        raw_config["input"]["images"] = [
            os.path.join(data_dir, str(img).lstrip("/"))
            for img in raw_config["input"]["images"]
        ]
    else:
        # Если картинок нет, гарантируем, что Pydantic получит пустой список, а не None
        if "input" in raw_config:
            raw_config["input"]["images"] = []

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


def run_pipeline(pipeline: Pipeline, cfg: AppConfig, cli_image: str | None):
    """
    Run pipeline continuously.
    Image source priority:
    1. CLI argument
    2. Config
    3. Interactive input
    """

    run_params = cfg.run.model_dump()

    print("\nPipeline service started\n")

    try:
        # ---------- CLI IMAGE ----------
        if cli_image:
            try:
                result = pipeline.run(cli_image, **run_params)
                print(json.dumps(result, indent=2))

            except Exception as e:
                print(f"Pipeline error: {e}")

        # ---------- CONFIG IMAGES ----------
        if cfg.input and cfg.input.images:
            for image_path in cfg.input.images:
                print(f"\nProcessing: {image_path}")

                try:
                    result = pipeline.run(
                        image_path,
                        **run_params,
                    )

                    print(json.dumps(result, indent=2))

                except Exception as e:
                    print(f"Pipeline error: {e}")

        # ---------- INTERACTIVE MODE ----------
        print("\nInteractive mode started (type 'exit' to stop)\n")

        while True:
            try:
                image_path = input("Image path: ").strip()
            except EOFError:
                break

            if image_path.lower() in {"exit", "quit"}:
                break

            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                continue

            try:
                result = pipeline.run(
                    image_path,
                    **run_params,
                )

                print(json.dumps(result, indent=2))

            except Exception as e:
                import traceback
                traceback.print_exc()

                print(f"Pipeline error: {e}")

    except KeyboardInterrupt:
        print("\nService interrupted")

    finally:
        print("Pipeline stopped")


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
        help="Optional image path (overrides config)",
    )

    args = parser.parse_args()

    # ---------- LOAD CONFIG ----------
    cfg = load_config(args.config)

    # ---------- BUILD PIPELINE ----------
    pipeline = build_pipeline(cfg)

    # ---------- RUN SERVICE ----------
    run_pipeline(
        pipeline=pipeline,
        cfg=cfg,
        cli_image=args.image,
    )


if __name__ == "__main__":
    main()
