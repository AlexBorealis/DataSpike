import numpy as np
import pytesseract

from .base import BaseOCR


class TesseractOCRReader(BaseOCR):
    OEM = 3
    PSM = 7
    WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"

    def __init__(self, **kwargs):
        self.config = self._build_config()
        self.kwargs = kwargs

    def _build_config(self) -> str:
        """Собираем конфиг для pytesseract"""
        return (
            f"--oem {self.OEM} "
            f"--psm {self.PSM} "
            f"-c tessedit_char_whitelist={self.WHITELIST}"
        )

    def read_line(self, img: np.ndarray) -> str:
        """
        :param img: изображение строки MRZ
        """
        text = pytesseract.image_to_string(img, config=self.config, **self.kwargs)
        return text.strip().replace(" ", "")
