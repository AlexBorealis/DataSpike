import os
from typing import Optional

import yaml
from dotenv import load_dotenv

from src.serializers.serializers import AppConfig


def extract_country_from_mrz(mrz_text: str) -> Optional[str]:
    """Extract issuing country code from the first MRZ line.

    Expected format for first line starts with document type + country code,
    for example `P<USA...`, where `USA` is at positions [2:5].
    """
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
