import json
import os
from typing import Optional

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


def extract_country_from_mrz(mrz_text: str) -> Optional[str]:
    lines = mrz_text.split("\n")

    if not lines or len(lines[0]) < 5:
        return None

    country = lines[0][2:5]

    return country if country.isalpha() and country.isupper() else None


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


def resolve_image_path(
        image_path: str, data_dir: Optional[str] = None
) -> Optional[str]:
    """Resolve image path for interactive mode.

    Checks the raw path first, then several common container-friendly fallbacks.
    """
    raw_path = os.path.expanduser(image_path.strip())
    if not raw_path:
        return None

    candidates = [raw_path]

    if not os.path.isabs(raw_path):
        normalized = raw_path[2:] if raw_path.startswith("./") else raw_path
        candidates.extend(
            [
                os.path.join(os.getcwd(), normalized),
            ]
        )

        if data_dir:
            candidates.append(os.path.join(data_dir, normalized))

        if raw_path.startswith("app/"):
            candidates.append(os.path.join("/", raw_path))

    for candidate in candidates:
        absolute_candidate = os.path.abspath(candidate)
        if os.path.isfile(absolute_candidate):
            return absolute_candidate

    return None


def run_pipeline(pipeline: Pipeline, cfg: AppConfig, cli_image: Optional[str]):
    """
    Run pipeline continuously.
    Image source priority:
    1. CLI argument
    2. Config
    3. Interactive input
    """

    run_params = cfg.run.model_dump()
    data_dir = os.getenv("DATA_DIR", "")

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
                resolved_image_path = resolve_image_path(image_path, data_dir=data_dir)

                if not resolved_image_path:
                    print(f"Image not found: {image_path}")
                    continue

                try:
                    result = pipeline.run(
                        resolved_image_path,
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
