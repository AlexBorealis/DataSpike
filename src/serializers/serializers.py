import os
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator

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
    images: Optional[List[str]] = None

    @field_validator("images")
    @classmethod
    def validate_image(cls, v):
        if v is None:
            return v

        for img in v:
            path = Path(img)

            if not path.exists():
                raise ValueError(f"Image not found: {path}")

            if not path.is_file():
                raise ValueError(f"Path is not a file: {path}")

            if path.suffix.lower() not in VALID_IMAGE_EXTENSIONS:
                raise ValueError(
                    f"Unsupported image format: {path.suffix}. "
                    f"Supported: {', '.join(VALID_IMAGE_EXTENSIONS)}"
                )

        return v


class AppConfig(BaseModel):
    input: InputConfig
    model: ModelConfig
    pipeline: PipelineConfig
    run: Optional[RunConfig] = RunConfig()
