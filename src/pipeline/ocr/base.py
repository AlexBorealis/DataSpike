from abc import ABC, abstractmethod

import numpy as np


class BaseOCR(ABC):
    @abstractmethod
    def read_line(self, img: np.ndarray) -> str:
        pass
