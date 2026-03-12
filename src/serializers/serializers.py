import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, FilePath, field_validator

VALID_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
}


class ModelConfig(BaseModel):
    detector: str
    classifier: str

    @field_validator("detector", "classifier")
    @classmethod
    def validate_model_path(cls, v: str):
        if not os.path.exists(v):
            raise ValueError(f"Model path does not exist: {v}")
        return v


class PipelineConfig(BaseModel):
    ocr: Literal["tesseract", "easyocr"] = "tesseract"
    checker: bool = False


class RunConfig(BaseModel):
    device: Literal["cpu", "cuda"] = "cpu"
    verbose: bool = False


class InputConfig(BaseModel):
    image: Path

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: Path):

        if not v.exists():
            raise ValueError(f"Image not found: {v}")

        if not v.is_file():
            raise ValueError(f"Path is not a file: {v}")

        if v.suffix.lower() not in VALID_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format: {v.suffix}. "
                f"Supported: {', '.join(VALID_IMAGE_EXTENSIONS)}"
            )

        return v


class AppConfig(BaseModel):
    input: InputConfig
    model: ModelConfig
    pipeline: PipelineConfig
    run: Optional[RunConfig] = RunConfig()
