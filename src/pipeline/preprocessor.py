from typing import List, Optional, Tuple

import cv2
import numpy as np


class MRZPreprocessor:
    BLUR_THRESHOLD = 5
    CONTRAST_THRESHOLD = 20
    UPSCALE_HEIGHT = 80

    @staticmethod
    def analyze_quality(img: np.ndarray) -> Tuple[float, float]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        contrast = gray.std()

        return blur, contrast

    @staticmethod
    def _best_channel(img: np.ndarray) -> Tuple[np.ndarray, float, float]:
        b, g, r = cv2.split(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        contrasts = {
            "gray": gray.std(),
            "b": b.std(),
            "g": g.std(),
            "r": r.std(),
        }

        best_name = max(contrasts, key=contrasts.get)

        channel_map = {
            "gray": gray,
            "b": b,
            "g": g,
            "r": r,
        }

        best = channel_map[best_name]

        blur = cv2.Laplacian(best, cv2.CV_64F).var()
        contrast = contrasts[best_name]

        # print(best, blur, contrast)
        return best, blur, contrast

    @staticmethod
    def _enhance_mrz(img: np.ndarray) -> np.ndarray:
        grad = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
        grad = np.abs(grad)

        grad = cv2.normalize(grad, None, 0, 255, cv2.NORM_MINMAX)
        grad = grad.astype(np.uint8)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
        closed = cv2.morphologyEx(grad, cv2.MORPH_CLOSE, kernel)

        blur = cv2.GaussianBlur(closed, (0, 0), 1)

        sharp = cv2.addWeighted(closed, 1.4, blur, -0.4, 0)

        return np.clip(sharp, 0, 255).astype(np.uint8)

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        channel, blur, contrast = self._best_channel(img)

        if blur > self.BLUR_THRESHOLD and contrast > self.CONTRAST_THRESHOLD:
            gray = channel
        else:
            gray = self._enhance_mrz(channel)

        if gray.shape[0] < self.UPSCALE_HEIGHT:
            gray = cv2.resize(
                gray,
                None,
                fx=2,
                fy=2,
                interpolation=cv2.INTER_CUBIC,
            )

        return gray

    @staticmethod
    def _split_lines(img: np.ndarray) -> List[np.ndarray]:
        h = img.shape[0]
        cut = int(h * 0.52)

        return [img[:cut], img[cut:]]

    def process(self, img: np.ndarray) -> List[np.ndarray]:
        processed = self._preprocess(img)

        return self._split_lines(processed)
