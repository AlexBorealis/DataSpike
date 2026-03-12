import easyocr
import numpy as np

from .base import BaseOCR


class EasyOCRReader(BaseOCR):
    ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"

    def __init__(self, **kwargs):
        self.reader = easyocr.Reader(lang_list=["en"])
        self.kwargs = kwargs

    def read_line(self, img: np.ndarray) -> str:
        """
        :param img: изображение строки MRZ
        """
        result = self.reader.readtext(
            img, detail=0, allowlist=self.ALLOWLIST, **self.kwargs
        )

        if not result:
            return ""

        return result[0].replace(" ", "")
